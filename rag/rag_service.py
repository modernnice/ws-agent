import sys
import os
from typing import List, Optional

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.documents import Document
from langchain_core.runnables import RunnableParallel, RunnablePassthrough

from rag.vector_store import VectorStore
from model.factory import chat_model
from utils.prompt_loader import load_prompt
from utils.logger_handler import logger

class RagSummarizeService:
    # 类变量，用于缓存提示词，避免重复IO读取
    _PROMPT_TEXT: Optional[str] = None

    def __init__(self, vector_store: VectorStore):
        """
        初始化 RAG 摘要服务
        :param vector_store: 已经初始化好的 VectorStore 实例
        """
        logger.info("初始化 RagSummarizeService...")
        self.vector_store = vector_store
        self.k = self.vector_store.cfg.get("k", 3)
        # 将数据库实例包装成 retriever，设定返回最相关的 3 条结果
        self.retriever = self.vector_store.vector_db.as_retriever(search_kwargs={"k": self.k})
        
        # 1. 资源懒加载：检查并加载提示词
        self._load_prompt_if_needed()
        
        # 2. 构建 LCEL 执行链
        self.chain = self._build_chain()
        logger.info("RAG 服务初始化完成")

    @classmethod
    def _load_prompt_if_needed(cls):
        """
        懒加载提示词逻辑
        """
        if cls._PROMPT_TEXT is None:
            logger.info("首次加载 RAG 提示词...")
            try:
                # 使用 prompt_loader 加载提示词
                # 注意：load_prompt 内部已经处理了路径获取和读取，但为了满足"错误拦截"要求，
                # 我们检查返回值。如果 load_prompt 失败返回空字符串，我们需要在这里抛出异常。
                content = load_prompt("rag_path")
                
                if not content:
                    raise ValueError("提示词文件内容为空或读取失败")
                
                cls._PROMPT_TEXT = content
                logger.info("提示词加载并缓存成功")
            except Exception as e:
                logger.error(f"加载 RAG 提示词失败: {e}")
                raise e

    def _build_chain(self):
        """
        构建 LCEL 流水线: prompt | model | output_parser
        """
        prompt_template = ChatPromptTemplate.from_template(self._PROMPT_TEXT)
        output_parser = StrOutputParser()
        
        # 组装流水线
        # 注意：这里我们只构建后半部分的处理链，完整的链式调用在 rag_summarize 中通过 invoke 触发
        # 或者是直接构建一个接收 {"context": ..., "input": ...} 的链
        chain = prompt_template | chat_model | output_parser
        return chain

    def _format_docs(self, docs: List[Document]) -> str:
        """
        格式化文档：添加【参考资料n】前缀，并进行内容去重
        """
        formatted_docs = []
        seen_content = set()
        
        # 索引计数器，仅对未重复的文档计数
        idx = 1
        
        for doc in docs:
            content = doc.page_content.strip()
            
            # 简单去重：如果完全相同的内容已经出现过，则跳过
            if content in seen_content:
                continue
            
            seen_content.add(content)
            
            source = doc.metadata.get("source", "未知来源")
            # 尝试获取文件名
            filename = os.path.basename(source)
            
            formatted_docs.append(f"【参考资料{idx}】(来源: {filename}):\n{content}")
            idx += 1
        
        return "\n\n".join(formatted_docs)

    def rag_summarize(self, query: str, filter_dict: dict = None) -> str:
        """
        执行 RAG 核心流水线
        :param query: 用户问题
        :param filter_dict: 过滤条件 (可选)
        :return: 总结回答
        """
        logger.info(f"开始 RAG 处理流程，问题: {query}，过滤: {filter_dict}")
        
        try:
            # 1. 语义检索 (Retrieval)
            # 动态调整检索逻辑：如果有 filter_dict，使用带过滤的 search；否则使用默认 retriever
            if filter_dict:
                docs = self.vector_store.search(query, k=self.k, filter_dict=filter_dict)
            else:
                docs = self.retriever.invoke(query)
                
            logger.info(f"检索到 {len(docs)} 条相关文档")
            
            # 2. 上下文增强 (Augmentation)
            context = self._format_docs(docs)
            
            # 3. 填充模版与推理 (Generation)
            # 准备输入字典
            input_data = {
                "context": context,
                "input": query
            }
            
            # 链式触发
            logger.info("调用大模型进行推理...")
            result = self.chain.invoke(input_data)
            
            # 4. 结果返回
            logger.info("RAG 推理完成")
            return result
            
        except Exception as e:
            logger.error(f"RAG 执行过程中发生错误: {e}")
            return f"抱歉，处理您的问题时出现错误: {e}"

if __name__ == "__main__":
    # 测试代码
    try:
        print("=== 测试 RagSummarizeService ===")
        # 1. 初始化 VectorStore (假设已经有数据入库)
        vs = VectorStore()
        # 注意：如果是首次运行且没有数据，需要先 load_document，但这里假设已经有库了
        # vs.load_document() 
        
        # 2. 初始化 RAG 服务
        rag = RagSummarizeService(vs)
        
        # 3. 执行测试
        q = "检索オグリキャップ"
        print(f"\nQ: {q}")
        answer = rag.rag_summarize(q, filter_dict={"category": "card"})
        print(f"\nA: {answer}")
        
    except Exception as e:
        logger.error(f"测试失败: {e}")
