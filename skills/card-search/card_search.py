from rag.rag_service import RagSummarizeService
from rag.vector_store import VectorStore
from utils.logger_handler import logger

# 全局单例初始化
# 注意：这里我们通过全局变量来持有服务实例，避免每次调用工具都重新初始化
try:
    _vector_store = VectorStore()
    _rag_service = RagSummarizeService(_vector_store)
except Exception as e:
    logger.error(f"初始化 RAG 服务失败: {e}")
    _rag_service = None

def search_knowledge_base(query: str, category: str = "all") -> str:
    """
    检索知识库（规则书和卡牌数据库）以回答用户问题。
    当用户询问关于 Weiss Schwarz (WS) 的规则、卡牌效果、卡牌信息或游戏机制时，必须使用此工具。
    
    Args:
        query: 用户的搜索查询或问题。
        category: 搜索类别，可选值为 "card" (仅查卡牌), "rule" (仅查规则), "all" (查所有)。
                  默认为 "all"。根据用户问题的侧重点选择最合适的类别。
    """
    if not _rag_service:
        return "知识库服务暂时不可用。"
    
    try:
        logger.info(f"工具调用: search_knowledge_base query='{query}' category='{category}'")
        
        # 构建过滤字典
        filter_dict = None
        if category == "card":
            filter_dict = {"category": "card"}
        elif category == "rule":
            filter_dict = {"category": "rule"}
            
        return _rag_service.rag_summarize(query, filter_dict=filter_dict)
    except Exception as e:
        logger.error(f"知识库检索失败: {e}")
        return f"检索过程中发生错误: {e}"

if __name__ == "__main__":
    import argparse
    import sys

    # 命令行参数解析
    parser = argparse.ArgumentParser(description="Search the Weiss Schwarz knowledge base.")
    parser.add_argument("query", nargs="+", help="The search query keywords.")
    parser.add_argument("--category", choices=["card", "rule", "all"], default="all", help="The category to search: 'card', 'rule', or 'all'. Default is 'all'.")
    
    args = parser.parse_args()
    query = " ".join(args.query)
    
    print(f"Executing search for query: '{query}' with category: '{args.category}'")
    
    # 调用工具函数
    result = search_knowledge_base(query, category=args.category)
    print("===== Search Result =====")
    print(result)
