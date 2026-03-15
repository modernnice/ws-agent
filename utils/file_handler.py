import sys
import os
import hashlib
import json
from typing import List, Optional, Union
from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader
from utils.logger_handler import logger


class FileHandler:
    @staticmethod
    def calculate_file_hash(file_path: str) -> Optional[str]:
        if not os.path.exists(file_path) or not os.access(file_path, os.R_OK):
            logger.error(f"文件不存在或无权限: {file_path}")
            return None
            
        try:
            md5_hash = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    md5_hash.update(chunk)
            return md5_hash.hexdigest()
        except Exception as e:
            logger.error(f"计算哈希失败 {file_path}: {e}")
            return None

    @staticmethod
    def get_files_by_extensions(directory: str, extensions: List[str]) -> List[str]:
        if not os.path.exists(directory):
            logger.error(f"目录不存在: {directory}")
            return []
            
        exts = {e.lower() if e.startswith('.') else f'.{e.lower()}' for e in extensions}
        matched = []
        for root, _, files in os.walk(directory):
            matched.extend([os.path.join(root, f) for f in files if os.path.splitext(f)[1].lower() in exts])
        return matched

    @staticmethod
    def read_file_content(file_path: str) -> Union[List[Document], str, None]:
        if not os.path.exists(file_path):
            logger.error(f"文件未找到: {file_path}")
            return None
            
        ext = os.path.splitext(file_path)[1].lower()
        try:
            if ext == '.pdf':
                loader = PyPDFLoader(file_path)
                return loader.load()
            
            elif ext == '.json':
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                content = json.dumps(data, indent=2, ensure_ascii=False)
                return [Document(page_content=content, metadata={"source": file_path, "type": "json"})]
            
            else:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                return [Document(page_content=content, metadata={"source": file_path, "type": "text"})]
                
        except Exception as e:
            logger.error(f"读取文件失败 {file_path}: {e}")
            return None

if __name__ == "__main__":
    test_file = "/Volumes/Kais的外接硬盘/WS_Agent/data/Card_DB/DB/5HY_W83.json"
    print("=== 测试 FileHandler (LangChain Version) ===")
    
    # 1. 测试哈希
    if file_hash := FileHandler.calculate_file_hash(test_file):
        print(f"✅ 文件哈希: {file_hash}")
    
    # 2. 测试筛选
    db_dir = os.path.dirname(test_file)
    json_files = FileHandler.get_files_by_extensions(db_dir, ['.json'])
    print(f"✅ 发现 json文件数: {len(json_files)}")
    
    # 3. 测试读取 (Expect List[Document])
    print(f"\n尝试读取: {test_file}")
    docs = FileHandler.read_file_content(test_file)
    if docs and isinstance(docs, list) and isinstance(docs[0], Document):
        print(f"✅ 读取成功 (返回 {len(docs)} 个 Document 对象)")
        print(f"📄 内容预览 (前200字符): {docs[0].page_content[:200]}...")
        print(f"🏷️  元数据: {docs[0].metadata}")
    else:
        print(f"❌ 读取失败或类型错误: {type(docs)}")
