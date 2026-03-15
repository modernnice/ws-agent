import streamlit as st
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from agent.react_agent import agent
from frontend.ui.config_panel import render_settings_page
from frontend.ui.rendering import render_assistant_group
from frontend.ui.session_helpers import init_session_state, render_sidebar, group_messages_by_role, extract_user_content
from frontend.ui.text_utils import bubble_html, sanitize_text, extract_tool_calls, resolve_tool_display_name
from utils.logger_handler import logger


st.set_page_config(page_title="Weiß Schwarz Agent 助手", page_icon="🤖", layout="wide")


def load_css():
    try:
        with open("frontend/style.css", "r") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.error("找不到 frontend/style.css！")


def render_chat_history():
    grouped_messages = group_messages_by_role(st.session_state.messages)
    for group_idx, (role, messages) in enumerate(grouped_messages):
        avatar = "frontend/avatar.jpg" if role == "assistant" else None
        with st.chat_message(role, avatar=avatar):
            if role == "user":
                for msg in messages:
                    if isinstance(msg, HumanMessage):
                        user_content = extract_user_content(msg)
                        if user_content:
                            st.markdown(bubble_html("user-bubble", user_content), unsafe_allow_html=True)
            else:
                render_assistant_group(
                    messages,
                    show_cursor=False,
                    collapse_intermediate_ai=True,
                    secondary_collapse=True,
                    key_prefix=f"group_{group_idx}",
                )


def render_starter_prompts():
    st.markdown('<div class="starter-prompts-spacer"></div>', unsafe_allow_html=True)
    _, center_col, _ = st.columns([1, 10, 1], gap="small")
    with center_col:
        st.markdown('<div class="starter-prompt-title">可以尝试这样与Agent对话...</div>', unsafe_allow_html=True)
        prompts = [
            "查询一下卡名中有高松灯的卡牌",
            "最新的上位卡组有哪些？",
            "当前的本地数据库是最新的吗",
        ]
        columns = st.columns(3, gap="medium")
        for idx, prompt_text in enumerate(prompts):
            with columns[idx]:
                if st.button(prompt_text, key=f"starter_prompt_{idx + 1}", use_container_width=True):
                    st.session_state.chat_input_prefill = prompt_text
                    st.rerun()


def apply_chat_input_prefill():
    pending = st.session_state.get("chat_input_prefill")
    if pending:
        st.session_state.chat_input_box = pending
        st.session_state.chat_input_prefill = ""


def handle_stream_response(prompt):
    with st.chat_message("assistant", avatar="frontend/avatar.jpg"):
        message_placeholder = st.empty()
        status_container = st.status("思考中...", expanded=False)
        seen_tool_status = set()
        pending_execute_status_names = []
        inputs = {"messages": [HumanMessage(content=prompt)]}
        config = {"configurable": {"thread_id": st.session_state.thread_id}}
        try:
            accumulated_messages = []
            current_message = None
            display_msgs = []
            for event in agent.stream(inputs, config=config, stream_mode="messages", subgraphs=True):
                chunk = None
                if isinstance(event, tuple):
                    first_elem = event[0]
                    if isinstance(first_elem, tuple):
                        chunk_data = event[1]
                        if isinstance(chunk_data, tuple) and len(chunk_data) >= 1:
                            chunk = chunk_data[0]
                        else:
                            chunk = chunk_data
                    elif isinstance(first_elem, (AIMessage, HumanMessage, ToolMessage)):
                        chunk = first_elem
                    else:
                        chunk = first_elem
                else:
                    chunk = event
                is_chunk = chunk.__class__.__name__ == "AIMessageChunk"
                if is_chunk:
                    if current_message is None:
                        current_message = chunk
                    else:
                        try:
                            current_message = current_message + chunk
                        except TypeError:
                            accumulated_messages.append(current_message)
                            current_message = chunk
                else:
                    if current_message:
                        accumulated_messages.append(current_message)
                        current_message = None
                    accumulated_messages.append(chunk)
                msg_to_check = current_message if current_message else chunk
                if isinstance(msg_to_check, AIMessage):
                    try:
                        tool_calls = extract_tool_calls(msg_to_check)
                        for tool_call in tool_calls:
                            name = tool_call["name"]
                            display_name = resolve_tool_display_name(name, tool_call.get("args", {}))
                            if name == "execute" and display_name != "execute":
                                pending_execute_status_names.append(display_name)
                            if name and name not in seen_tool_status:
                                seen_tool_status.add(name)
                                status_container.write(f"正在调用工具: {display_name}")
                                status_container.update(label=f"正在调用 {display_name}...", state="running")
                    except Exception:
                        pass
                if isinstance(chunk, ToolMessage):
                    tool_name = sanitize_text(chunk.name if hasattr(chunk, "name") else "Result")
                    display_name = resolve_tool_display_name(tool_name, chunk.content if hasattr(chunk, "content") else "")
                    if tool_name == "execute" and display_name == "execute" and pending_execute_status_names:
                        display_name = pending_execute_status_names.pop(0)
                    tool_content = sanitize_text(chunk.content)
                    tool_preview = tool_content[:200]
                    status_container.write(f"工具输出: {display_name} {tool_preview}...")
                display_msgs = accumulated_messages + ([current_message] if current_message else [])
                if display_msgs:
                    with message_placeholder.container():
                        render_assistant_group(display_msgs, show_cursor=True, collapse_intermediate_ai=False)
            status_container.update(label="完成", state="complete", expanded=False)
            finalized_assistant = []
            for msg in display_msgs:
                if isinstance(msg, HumanMessage):
                    continue
                finalized_assistant.append(msg)
            st.session_state.messages.extend(finalized_assistant)
            st.session_state.ui_messages_by_thread[st.session_state.thread_id] = st.session_state.messages
            st.rerun()
        except Exception as e:
            st.error(f"错误: {e}")
            logger.error(f"Stream error: {e}")


def render_chat_page():
    st.title("Weiß Schwarz Agent 助手")
    apply_chat_input_prefill()
    prompt = st.chat_input("请输入您的问题...", key="chat_input_box")
    if not st.session_state.messages and not prompt:
        render_starter_prompts()
    render_chat_history()
    if prompt:
        with st.chat_message("user"):
            st.markdown(bubble_html("user-bubble", prompt), unsafe_allow_html=True)
        st.session_state.messages.append(HumanMessage(content=prompt))
        st.session_state.ui_messages_by_thread[st.session_state.thread_id] = st.session_state.messages
        handle_stream_response(prompt)


load_css()
init_session_state()
render_sidebar(agent)
if st.session_state.show_settings:
    render_settings_page()
else:
    render_chat_page()
