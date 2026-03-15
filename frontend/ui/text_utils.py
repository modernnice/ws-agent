import json
import html
import re


def sanitize_text(value):
    if value is None:
        return ""
    text = value if isinstance(value, str) else str(value)
    return "".join(
        ch for ch in text
        if ch in "\n\r\t" or (32 <= ord(ch) <= 0x10FFFF and not 0xD800 <= ord(ch) <= 0xDFFF)
    )


def normalize_tool_calls(tool_calls):
    if not tool_calls:
        return []
    normalized = []
    for call in tool_calls:
        name = sanitize_text(call.get("name", "unknown"))
        args = call.get("args", {})
        normalized.append({"name": name, "args": args})
    return normalized


def extract_tool_calls(msg):
    if hasattr(msg, "tool_calls") and msg.tool_calls:
        return normalize_tool_calls(msg.tool_calls)
    if hasattr(msg, "tool_call_chunks") and msg.tool_call_chunks:
        calls = {}
        for chunk in msg.tool_call_chunks:
            index = chunk.get("index") if isinstance(chunk, dict) else getattr(chunk, "index", None)
            if index is None:
                index = 0
            if index not in calls:
                calls[index] = {"name": "", "args": "", "id": ""}
            c_name = chunk.get("name") if isinstance(chunk, dict) else getattr(chunk, "name", None)
            c_args = chunk.get("args") if isinstance(chunk, dict) else getattr(chunk, "args", None)
            c_id = chunk.get("id") if isinstance(chunk, dict) else getattr(chunk, "id", None)
            if c_name:
                calls[index]["name"] += c_name
            if c_args:
                calls[index]["args"] += c_args
            if c_id:
                calls[index]["id"] += c_id
        result = []
        for idx in sorted(calls.keys()):
            call = calls[idx]
            args_val = call["args"]
            try:
                args_val = json.loads(call["args"])
            except Exception:
                pass
            result.append({"name": call["name"], "args": args_val})
        return result
    return []


def tool_args_to_text(args):
    if isinstance(args, str):
        return sanitize_text(args)
    try:
        return sanitize_text(json.dumps(args, ensure_ascii=False, indent=2))
    except Exception:
        return sanitize_text(str(args))


def bubble_html(css_class, text):
    safe_text = html.escape(sanitize_text(text)).replace("\n", "<br>")
    return f'<div class="{css_class}">{safe_text}</div>'


def infer_script_name_from_text(text):
    value = sanitize_text(text)
    if not value:
        return ""
    match = re.search(r'([A-Za-z0-9_./-]+/)?([A-Za-z0-9_-]+)\.py\b', value)
    if match:
        return match.group(2)
    return ""


def resolve_tool_display_name(tool_name, payload):
    name = sanitize_text(tool_name)
    if name != "execute":
        return name
    script_name = ""
    if isinstance(payload, dict):
        script_name = infer_script_name_from_text(payload.get("command", ""))
        if not script_name:
            script_name = infer_script_name_from_text(json.dumps(payload, ensure_ascii=False))
    else:
        script_name = infer_script_name_from_text(payload)
    return script_name or "execute"
