import os
import yaml
import requests
from langchain_core.tools import tool
from utils.logger_handler import logger

def load_config():
    """加载配置文件"""
    try:
        with open('/Volumes/T7/WS_Agent/config/agent.yml', 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            return config
    except Exception as e:
        logger.error(f"加载配置文件失败: {e}")
        return None

@tool
def search_web(query: str) -> str:
    """
    使用百度 AI 搜索 API 进行联网检索。
    当用户询问关于实时天气、新闻、股票等需要联网才能获取的信息时，使用此工具。
    
    Args:
        query: 用户的搜索查询。
        
    Returns:
        str: 搜索结果的总结。
    """
    config = load_config()
    if not config:
        return "配置加载失败，无法执行搜索。"
    
    # 获取配置
    base_url = config.get('BAIDU_AI_SEARCH_URL')
    api_key = config.get('BAIDU_AI_SEARCH_API_KEY')
    
    if not api_key or not base_url:
        return "缺少百度 AI 搜索的 API Key 或 URL 配置。"
        
    try:
        logger.info(f"工具调用: search_web query='{query}'")
        
        # 构造请求 URL (确保以 /chat/completions 结尾)
        url = base_url
        if not url.endswith('/chat/completions'):
             url = url.rstrip('/') + '/chat/completions'

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "messages": [{"role": "user", "content": query}],
            "model": "ernie-4.5-turbo-128k",
            "stream": False,
            "search_source": "baidu_search_v2"
        }
        
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        answer = data["choices"][0]["message"]["content"]
        references = data.get("references", [])
        
        # 格式化输出，包含参考来源
        result = f"{answer}\n\n参考来源:\n"
        for i, ref in enumerate(references, 1):
            result += f"{i}. {ref.get('title', '未知标题')} - {ref.get('url', '无链接')}\n"
            
        logger.info("搜索成功")
        return result
        
    except Exception as e:
        logger.error(f"联网搜索失败: {e}")
        return f"联网搜索过程中发生错误: {e}"

if __name__ == "__main__":
    # 简单的命令行测试
    import sys
    
    query = "https://ws-tcg.com/deckrecipe/detail/wgp2025world-finalworld这个网站有什么"
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        
    print(f"正在搜索: {query}")
    print("-" * 20)
    # search_web 是一个 StructuredTool 对象，使用 .invoke 来调用
    print(search_web.invoke(query))
