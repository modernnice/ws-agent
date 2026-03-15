import uuid
import streamlit as st
from langchain_core.messages import HumanMessage

from frontend.ui.text_utils import sanitize_text


def init_session_state():
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "thread_id" not in st.session_state:
        st.session_state.thread_id = str(uuid.uuid4())
    if "sessions" not in st.session_state:
        st.session_state.sessions = {}
    if "show_settings" not in st.session_state:
        st.session_state.show_settings = False
    if "ui_messages_by_thread" not in st.session_state:
        st.session_state.ui_messages_by_thread = {}
    if "chat_input_box" not in st.session_state:
        st.session_state.chat_input_box = ""
    if "chat_input_prefill" not in st.session_state:
        st.session_state.chat_input_prefill = ""


def render_sidebar(agent):
    with st.sidebar:
        st.title("Weiß Schwarz Agent")
        if st.button("新建对话", key="new_chat"):
            if st.session_state.messages and st.session_state.thread_id not in st.session_state.sessions:
                first_msg = st.session_state.messages[0]
                title = first_msg.content[:20] + "..." if isinstance(first_msg, HumanMessage) else "New Chat"
                st.session_state.sessions[st.session_state.thread_id] = title
            if st.session_state.messages:
                st.session_state.ui_messages_by_thread[st.session_state.thread_id] = st.session_state.messages
            st.session_state.thread_id = str(uuid.uuid4())
            st.session_state.messages = []
            st.session_state.show_settings = False
            st.session_state.chat_input_box = ""
            st.session_state.chat_input_prefill = ""
            st.rerun()
        st.divider()
        st.subheader("历史记录")
        for tid, title in list(st.session_state.sessions.items())[::-1]:
            if st.button(title, key=tid):
                st.session_state.thread_id = tid
                if tid in st.session_state.ui_messages_by_thread:
                    st.session_state.messages = st.session_state.ui_messages_by_thread[tid]
                else:
                    config = {"configurable": {"thread_id": tid}}
                    state = agent.get_state(config)
                    if state.values and "messages" in state.values:
                        st.session_state.messages = state.values["messages"]
                    else:
                        st.session_state.messages = []
                    st.session_state.ui_messages_by_thread[tid] = st.session_state.messages
                st.session_state.show_settings = False
                st.session_state.chat_input_box = ""
                st.session_state.chat_input_prefill = ""
                st.rerun()
        if st.button("⚙️ 设置", key="settings_btn"):
            st.session_state.show_settings = True
            st.rerun()


def group_messages_by_role(messages):
    grouped_messages = []
    if not messages:
        return grouped_messages
    current_group = []
    first_msg = messages[0]
    current_role = "user" if isinstance(first_msg, HumanMessage) else "assistant"
    for msg in messages:
        msg_role = "user" if isinstance(msg, HumanMessage) else "assistant"
        if msg_role != current_role:
            grouped_messages.append((current_role, current_group))
            current_group = [msg]
            current_role = msg_role
        else:
            current_group.append(msg)
    if current_group:
        grouped_messages.append((current_role, current_group))
    return grouped_messages


def extract_user_content(msg):
    return sanitize_text(msg.content)
