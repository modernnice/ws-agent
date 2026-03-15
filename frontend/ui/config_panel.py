import os
import yaml
import streamlit as st


AGENT_CONFIG_PATH = "config/agent.yml"
CHROMA_CONFIG_PATH = "config/chroma.yaml"


def load_yaml_config(config_path):
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}


def save_yaml_config(config_path, new_config):
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(new_config, f, default_flow_style=False, allow_unicode=True, sort_keys=False)


def render_settings_page():
    st.title("配置设置")
    if st.button("← 返回对话"):
        st.session_state.show_settings = False
        st.rerun()
    tabs = st.tabs(["Agent 配置", "RAG 配置"])

    with tabs[0]:
        st.info("在下方修改配置。更改将保存到 `config/agent.yml`。")
        config_data = load_yaml_config(AGENT_CONFIG_PATH)
        with st.form("agent_config_form"):
            updated_config = {}
            st.subheader("模型配置")
            updated_config["chat_model"] = st.text_input("对话模型 (Chat Model)", value=config_data.get("chat_model", ""))
            updated_config["embedding_model"] = st.text_input("嵌入模型 (Embedding Model)", value=config_data.get("embedding_model", ""))
            st.subheader("API 密钥")
            updated_config["chat_api_key"] = st.text_input("对话 API Key (Chat API Key)", value=config_data.get("chat_api_key", ""), type="password")
            updated_config["embed_api_key"] = st.text_input("嵌入 API Key (Embed API Key)", value=config_data.get("embed_api_key", ""), type="password")
            updated_config["BAIDU_AI_SEARCH_API_KEY"] = st.text_input("网页搜索 API Key", value=config_data.get("BAIDU_AI_SEARCH_API_KEY", ""), type="password")
            updated_config["SHUYANAI_API_KEY"] = st.text_input("网页读取 API Key", value=config_data.get("SHUYANAI_API_KEY", ""), type="password")
            st.subheader("服务地址 (URLs)")
            current_base_url = config_data.get("base_url", "")
            chat_base_url_val = config_data.get("chat_base_url", current_base_url)
            embedding_base_url_val = config_data.get("embedding_base_url", "")
            updated_config["chat_base_url"] = st.text_input("对话模型 URL (Chat Model URL)", value=chat_base_url_val)
            updated_config["embedding_base_url"] = st.text_input("嵌入模型 URL (Embedding Model URL)", value=embedding_base_url_val)
            updated_config["BAIDU_AI_SEARCH_URL"] = st.text_input("网页搜索 URL", value=config_data.get("BAIDU_AI_SEARCH_URL", ""))
            updated_config["SHUYANAI_READER_URL"] = st.text_input("网页读取 URL", value=config_data.get("SHUYANAI_READER_URL", ""))
            for k, v in config_data.items():
                if k not in updated_config and k not in ["ZHIPU_API_KEY", "base_url"]:
                    updated_config[k] = v
            submitted = st.form_submit_button("保存 Agent 配置")
            if submitted:
                save_yaml_config(AGENT_CONFIG_PATH, updated_config)
                st.success("Agent 配置保存成功！请重启应用以生效。")

    with tabs[1]:
        st.info("在下方修改 RAG 参数。更改将保存到 `config/chroma.yaml`。")
        chroma_config = load_yaml_config(CHROMA_CONFIG_PATH)
        with st.form("rag_config_form"):
            updated_rag_config = dict(chroma_config)
            updated_rag_config["k"] = int(
                st.number_input("检索条数 (k)", min_value=1, step=1, value=int(chroma_config.get("k", 8)))
            )
            updated_rag_config["chunk_size"] = int(
                st.number_input("分块大小 (chunk_size)", min_value=1, step=1, value=int(chroma_config.get("chunk_size", 200)))
            )
            updated_rag_config["chunk_overlap"] = int(
                st.number_input("分块重叠 (chunk_overlap)", min_value=0, step=1, value=int(chroma_config.get("chunk_overlap", 20)))
            )
            submitted_rag = st.form_submit_button("保存 RAG 配置")
            if submitted_rag:
                save_yaml_config(CHROMA_CONFIG_PATH, updated_rag_config)
                st.success("RAG 配置保存成功！请重启应用以生效。")
