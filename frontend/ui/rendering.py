import re
import streamlit as st
from langchain_core.messages import AIMessage, ToolMessage

from frontend.ui.media import render_markdown_and_images
from frontend.ui.text_utils import (
    sanitize_text,
    extract_tool_calls,
    tool_args_to_text,
    resolve_tool_display_name,
)


def build_assistant_blocks(messages):
    blocks = []
    for msg in messages:
        if isinstance(msg, AIMessage):
            content = sanitize_text(msg.content)
            tool_calls = extract_tool_calls(msg)
            current = {"type": "ai", "content": content, "tool_calls": tool_calls}
            if blocks and blocks[-1]["type"] == "ai" and blocks[-1]["tool_calls"] == tool_calls:
                prev_content = blocks[-1]["content"]
                if content.startswith(prev_content) or prev_content.startswith(content):
                    if len(content) >= len(prev_content):
                        blocks[-1] = current
                    continue
            if blocks and blocks[-1] == current:
                continue
            blocks.append(current)
        elif isinstance(msg, ToolMessage):
            tool_name = sanitize_text(msg.name if hasattr(msg, "name") else "Result")
            tool_content = sanitize_text(msg.content)
            current = {"type": "tool", "name": tool_name, "content": tool_content}
            if blocks and blocks[-1] == current:
                continue
            blocks.append(current)
    return blocks


def render_message(content):
    content = sanitize_text(content)
    if not content:
        return
    current_pos = 0
    pattern = re.compile(r'<details\s*>(?:\s*<summary>(.*?)</summary>)?(.*?)</details>', re.DOTALL | re.IGNORECASE)
    matches = list(pattern.finditer(content))
    if not matches:
        render_markdown_and_images(content)
        return
    for match in matches:
        start, end = match.span()
        pre_text = content[current_pos:start]
        if pre_text.strip():
            render_markdown_and_images(pre_text)
        summary_text = sanitize_text(match.group(1))
        if not summary_text:
            summary_text = "详细信息"
        detail_body = sanitize_text(match.group(2))
        with st.expander(summary_text.strip()):
            render_markdown_and_images(detail_body.strip())
        current_pos = end
    post_text = content[current_pos:]
    if post_text.strip():
        render_markdown_and_images(post_text)


def render_assistant_group(messages, show_cursor=False, collapse_intermediate_ai=False, secondary_collapse=False, key_prefix=""):
    blocks = build_assistant_blocks(messages)
    ai_indices = [i for i, block in enumerate(blocks) if block["type"] == "ai"]
    last_ai_idx = ai_indices[-1] if ai_indices else -1
    thought_step = 0
    collapsed_items = []
    pending_messages = []
    pending_execute_names = []
    for idx, block in enumerate(blocks):
        if block["type"] == "ai":
            for tool_call in block["tool_calls"]:
                display_name = resolve_tool_display_name(tool_call["name"], tool_call["args"])
                if sanitize_text(tool_call["name"]) == "execute" and display_name != "execute":
                    pending_execute_names.append(display_name)
                if secondary_collapse:
                    collapsed_items.append({
                        "kind": "tool_call",
                        "title": f"🔧 正在调用工具: {display_name}",
                        "content": tool_args_to_text(tool_call["args"]),
                        "raw_args": tool_call["args"]
                    })
                else:
                    with st.expander(f"正在调用工具: {display_name}"):
                        st.code(tool_args_to_text(tool_call["args"]))
            if block["content"]:
                if collapse_intermediate_ai and idx != last_ai_idx:
                    thought_step += 1
                    if secondary_collapse:
                        collapsed_items.append({
                            "kind": "thought",
                            "title": f"🧠 思考过程 {thought_step}",
                            "content": block["content"]
                        })
                    else:
                        with st.expander(f"思考过程 {thought_step}"):
                            render_markdown_and_images(block["content"])
                else:
                    is_last_ai = idx == last_ai_idx
                    if show_cursor and is_last_ai:
                        stream_content = block["content"].rstrip("\r\n")
                        text = f"{stream_content}▌"
                    else:
                        text = block["content"]
                    if secondary_collapse:
                        pending_messages.append(text)
                    else:
                        render_message(text)
        elif block["type"] == "tool":
            display_name = resolve_tool_display_name(block["name"], block["content"])
            if sanitize_text(block["name"]) == "execute" and display_name == "execute" and pending_execute_names:
                display_name = pending_execute_names.pop(0)
            if secondary_collapse:
                collapsed_items.append({
                    "kind": "tool_output",
                    "title": f"📤 工具输出: {display_name}",
                    "content": block["content"]
                })
            else:
                with st.expander(f"工具输出: {display_name}"):
                    render_markdown_and_images(block["content"])
    if secondary_collapse and collapsed_items:
        with st.expander(f"思考过程与工具调用：共 {len(collapsed_items)} 项"):
            for idx, item in enumerate(collapsed_items):
                key = f"process_item_{st.session_state.thread_id}_{key_prefix}_{idx}"
                if st.toggle(item["title"], key=key, value=False):
                    if item["kind"] == "tool_call":
                        st.code(tool_args_to_text(item.get("raw_args", item["content"])))
                    else:
                        render_markdown_and_images(item["content"])
    if secondary_collapse and pending_messages:
        for text in pending_messages:
            render_message(text)
