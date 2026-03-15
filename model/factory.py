import os
import sys
from abc import ABC, abstractmethod
from typing import Any, Optional
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.embeddings import DashScopeEmbeddings
from utils.config_handler import config
from utils.logger_handler import logger

class BaseModelFactory(ABC):
    """
    模型工厂的抽象基类。
    定义了创建模型实例的标准接口。
    """
    @abstractmethod
    def generator(self) -> Any:
        """
        生成并返回具体的模型实例。
        """
        pass

class ChatModelFactory(BaseModelFactory):
    """
    用于创建对话模型实例(如 DeepSeek、OpenAI)的工厂类。
    """
    def generator(self) -> ChatOpenAI:
        # 加载配置
        agent_config = config.get('agent')
        model_name = agent_config.get('chat_model')
        chat_api_key = agent_config.get('chat_api_key', os.getenv('OPENAI_API_KEY'))
        # 优先使用 chat_base_url，兼容 base_url
        base_url = agent_config.get('chat_base_url') or agent_config.get('base_url', os.getenv('OPENAI_BASE_URL'))
        temperature = agent_config.get('temperature', 0.7)
        
        logger.info(f"正在初始化对话模型: {model_name}")
        
        # 返回 LangChain ChatOpenAI 实例（兼容 DeepSeek/通义千问等）
        return ChatOpenAI(
            model_name=model_name,
            openai_api_key=chat_api_key,
            openai_api_base=base_url,
            temperature=temperature
        )

class VectorModelFactory(BaseModelFactory):
    """
    用于为 RAG 创建嵌入(Embedding)模型实例的工厂类。
    """
    def generator(self) -> Any:
        # 加载配置
        agent_config = config.get('agent')
        model_name = agent_config.get('embedding_model')
        embed_api_key = agent_config.get('embed_api_key') or os.getenv('DASHSCOPE_API_KEY') or os.getenv('OPENAI_API_KEY')
        embedding_base_url = agent_config.get('embedding_base_url')
        
        logger.info(f"正在初始化向量模型: {model_name}")
        
        # 使用 DashScopeEmbeddings
        return DashScopeEmbeddings(
            model=model_name,
            dashscope_api_key=embed_api_key
        )
        
chat_model = ChatModelFactory().generator()
vector_model =  VectorModelFactory().generator()

if __name__ == "__main__":
    print("=== 测试 ModelFactory ===")

    # 1. 测试对话模型工厂
    print("\n[ChatModelFactory]")
    print(f"✅ 已创建对话模型: {type(chat_model).__name__}")
    print(f"   模型名称: {chat_model.model_name}")
    
    try:
        from langchain_core.messages import HumanMessage
        print("   正在发送测试消息: '介绍一下原神'...")
        response = chat_model.invoke([HumanMessage(content="介绍一下原神")])
        print(f"   🤖 模型回复: {response.content}")
    except Exception as e:
        print(f"   ❌ 对话测试失败: {e}")
    
    # 2. 测试向量模型工厂
    print("\n[VectorModelFactory]")

    print(f"✅ 已创建向量模型: {type(vector_model).__name__}")
    print(f"   模型名称: {getattr(vector_model, 'model', getattr(vector_model, 'model_name', 'Unknown'))}")
