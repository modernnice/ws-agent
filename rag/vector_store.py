
import os, sys, hashlib
from typing import List, Optional
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from utils.config_handler import config
from utils.logger_handler import logger
from utils.path_tool import get_abs_path
from utils.file_handler import FileHandler
from model.factory import vector_model

class VectorStore:
    def __init__(self):
        """初始化向量存储系统"""
        logger.info("初始化向量存储系统...")
        self.cfg = config.get('chroma', {})
        self.persist_dir = get_abs_path(self.cfg.get('persist_directory', 'chroma_db'))
        self.collection = self.cfg.get('collection_name', 'default_collection')
        self.md5_path = get_abs_path(self.cfg.get('md5_hex_store', 'md5.txt'))
        self.data_path = get_abs_path(self.cfg.get('data_path', 'data'))
        
        self.vector_db = Chroma(
            collection_name=self.collection,
            embedding_function=vector_model,
            persist_directory=self.persist_dir
        )
        logger.info(f"已连接向量数据库: {self.persist_dir}")
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.cfg.get('chunk_size', 500),
            chunk_overlap=self.cfg.get('chunk_overlap', 50),
            separators=self.cfg.get('separators', ["\n\n", "\n", " ", ""])
        )

    def _manage_md5(self, md5: str = None) -> set:
        """加载或保存MD5记录"""
        if md5:
            with open(self.md5_path, 'a', encoding='utf-8') as f: f.write(f"{md5}\n")
            return set()
        if not os.path.exists(self.md5_path): return set()
        with open(self.md5_path, 'r', encoding='utf-8') as f: return set(l.strip() for l in f if l.strip())

    def load_document(self):
        """扫描并加载新文档"""
        if not os.path.exists(self.data_path): return logger.warning(f"目录不存在: {self.data_path}")
        processed, count = self._manage_md5(), 0
        exts = [f".{e}" if not e.startswith('.') else e for e in self.cfg.get('allow_knowledge_file_type', ['pdf', 'json'])]
        files = FileHandler.get_files_by_extensions(self.data_path, exts)
        logger.info(f"扫描到 {len(files)} 个文件")

        for f_path in files:
            try:
                md5 = FileHandler.calculate_file_hash(f_path)
                if md5 in processed: 
                    # logger.info(f"已入库，跳过: {f_path}")
                    continue
                
                # 特殊处理 JSON 文件：按对象直接入库，跳过切分
                if f_path.lower().endswith('.json'):
                    import json
                    with open(f_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    splits = []
                    # 处理 JSON 列表（卡片数组）
                    if isinstance(data, list):
                        for item in data:
                            content = json.dumps(item, ensure_ascii=False, indent=2)
                            splits.append(Document(page_content=content, metadata={"source": f_path, "type": "json_object", "category": "card"}))
                    # 处理单个 JSON 对象
                    elif isinstance(data, dict):
                        content = json.dumps(data, ensure_ascii=False, indent=2)
                        splits.append(Document(page_content=content, metadata={"source": f_path, "type": "json_object", "category": "card"}))
                    
                    if splits:
                        self.vector_db.add_documents(splits)
                        self._manage_md5(md5)
                        processed.add(md5)
                        count += 1
                        logger.info(f"JSON入库成功: {os.path.basename(f_path)} ({len(splits)}个对象)")
                    continue

                docs = FileHandler.read_file_content(f_path)
                if not docs: 
                    logger.warning(f"跳过空文件: {f_path}")
                    continue
                
                # 为所有加载的文档添加 category: rule 标签
                for doc in docs:
                    doc.metadata["category"] = "rule"
                
                splits = self.splitter.split_documents(docs)
                if splits:
                    self.vector_db.add_documents(splits)
                    self._manage_md5(md5)
                    processed.add(md5)
                    count += 1
                    logger.info(f"入库成功: {os.path.basename(f_path)} ({len(splits)}片段)")
            except Exception as e:
                logger.error(f"处理失败 {f_path}: {e}")
        logger.info(f"加载完成，新增: {count}")

    def search(self, query: str, k: int = 10, filter_dict: dict = None):
        """语义检索"""
        logger.info(f"检索: {query} | 过滤条件: {filter_dict}")
        if filter_dict:
            return self.vector_db.similarity_search(query, k=k, filter=filter_dict)
        return self.vector_db.as_retriever(search_kwargs={"k": k}).invoke(query)

if __name__ == "__main__":
    try:
        vs = VectorStore()
        vs.load_document()
        q = 'Proud Runner, Lemon'
        print(f"\n{'='*10} 检索: {q} {'='*10}")
        for i, doc in enumerate(vs.search(q)):
            print(f"\n[{i+1}] {doc.metadata.get('source')} :\n{doc.page_content.strip()}")
    except Exception as e:
        logger.error(f"测试失败: {e}")
