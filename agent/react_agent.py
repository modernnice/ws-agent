import os
from pathlib import Path
from typing import Optional, Dict, Any, List
from deepagents import create_deep_agent
from deepagents.backends import LocalShellBackend
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage, BaseMessage
from model.factory import chat_model
from utils.prompt_loader import load_prompt
from utils.logger_handler import logger
from tools.search_tool import search_web
from tools.fetch_web_content import fetch_web_content

# 1. 资源路径配置
# 技能目录: skills
_root = Path(__file__).resolve().parent.parent # WS_Agent root
# 技能路径应相对于 backend 的 root_dir
# 这里我们将 backend root 设为项目根目录，所以 skills 路径为 skills
SKILLS_RELATIVE_PATH = "skills"

# 2. 加载系统提示词
system_prompt = load_prompt("main_path")
if not system_prompt:
    logger.warning("未找到系统提示词配置，使用默认提示词。")
    system_prompt = "You are a helpful AI assistant."

# 3. 初始化 Checkpointer (用于状态持久化)
checkpointer = MemorySaver()

# 4. 初始化 LocalShellBackend
# 这样 agent 才能读取磁盘上的文件并执行脚本
backend = LocalShellBackend(root_dir=_root)

# 5. 创建 Deep Agent
# 使用 deepagents 库封装好的 create_deep_agent 函数
# 自动加载 skills 目录下的技能，并集成文件系统工具
agent = create_deep_agent(
    model=chat_model,
    skills=[SKILLS_RELATIVE_PATH], # 传递相对路径列表
    tools=[search_web, fetch_web_content], # 注册联网搜索工具和 MCP fetch 工具
    system_prompt=system_prompt,
    checkpointer=checkpointer,
    backend=backend, # 显式传入文件系统后端
)

def run_agent_stream(user_input: str):
    """
    运行 Agent 并流式输出结果
    :param user_input: 用户输入的问题
    """
    # print(f"Deep Agent 收到用户输入: {user_input}") # Force print to stdout
    logger.info(f"Deep Agent 收到用户输入: {user_input}")
    
    # 构造 LangGraph 标准输入格式
    # deepagents 使用标准的 messages 列表
    inputs = {"messages": [{"role": "user", "content": user_input}]}
    
    # 配置 config，必须包含 thread_id 以启用 checkpointer
    config = {"configurable": {"thread_id": "default_thread"}}
    
    try:
        # 使用 stream 模式运行图
        # deepagents 返回的是 CompiledStateGraph
        # 启用 subgraphs=True 以获取子图（task/skill）的执行事件
        for event in agent.stream(inputs, config=config, stream_mode="values", subgraphs=True):
            # 处理 event 是 tuple (namespace, state) 的情况 (当 subgraphs=True 时)
            if isinstance(event, tuple):
                namespace, state = event
                # 无论 namespace 是否为空，都要处理 state
                if "messages" in state and state["messages"]:
                    last_msg = state["messages"][-1]
                    # 如果 namespace 不为空，说明是子图事件
                    if namespace:
                        sub_task_name = namespace[-1]
                        if last_msg.type == "ai":
                            if last_msg.tool_calls:
                                for tc in last_msg.tool_calls:
                                    print(f"\n<details>")
                                    print(f"<summary>子任务 [{sub_task_name}] 调用工具: {tc['name']}</summary>")
                                    print(f"参数: {tc['args']}")
                                    print(f"</details>\n")
                            if last_msg.content:
                                print(f"\n[子任务 {sub_task_name}]: {last_msg.content}\n")
                        elif last_msg.type == "tool":
                            print(f"\n<details>")
                            print(f"<summary>子任务 [{sub_task_name}] 工具结果: {last_msg.name if hasattr(last_msg, 'name') else 'Result'}</summary>")
                            content_preview = last_msg.content[:500] + "..." if len(last_msg.content) > 500 else last_msg.content
                            print(f"{content_preview}")
                            print(f"</details>\n")
                    else:
                        # 主图事件
                        if last_msg.type == "ai":
                            if last_msg.tool_calls:
                                for tool_call in last_msg.tool_calls:
                                    print(f"\n<details>")
                                    print(f"<summary>正在调用工具: {tool_call['name']}</summary>")
                                    print(f"参数: {tool_call['args']}")
                                    print(f"</details>\n")
                            if last_msg.content:
                                print(last_msg.content)
                        elif last_msg.type == "tool":
                            print(f"\n<details>")
                            print(f"<summary>工具执行结果: {last_msg.name if hasattr(last_msg, 'name') else 'Result'}</summary>")
                            content_preview = last_msg.content[:1000] + "..." if len(last_msg.content) > 1000 else last_msg.content
                            print(f"{content_preview}")
                            print(f"</details>\n")
            else:
                # 兼容非 subgraphs=True 的情况（理论上这里不会走到，因为我们设置了 subgraphs=True）
                if "messages" in event and event["messages"]:
                    last_msg = event["messages"][-1]
                    if last_msg.type == "ai":
                        if last_msg.content:
                            print(last_msg.content)
        
    except Exception as e:
        logger.error(f"Agent 运行出错: {e}")
        print(f"Error: {e}") # Force print to stdout

if __name__ == "__main__":
    # 测试代码
    # print("=== 开始测试 Deep Agent ===")

    # print("\n--- 测试 Case 1: 查卡牌 (预期调用 category='card') ---")
    # run_agent_stream("潜水艇在WS里是什么意思")
    
    # print("\n--- 测试 Case 2: 查规则 (预期调用 category='rule') ---")
    run_agent_stream("查询一下卡名中有高松灯的卡牌")

    # print("\n--- 测试 Case 3: 联网搜索 (预期调用 search_web) ---")
    #run_agent_stream("使用tool，查询一下有哪些网站有关于黑白双翼的攻略")

    # print("\n=== 测试结束 ===")
