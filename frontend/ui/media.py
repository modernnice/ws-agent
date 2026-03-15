import re
import requests
import streamlit as st

from frontend.ui.text_utils import sanitize_text


def extract_image_urls(text):
    value = sanitize_text(text)
    if not value:
        return []
    markdown_pattern = re.compile(r'!\[[^\]]*\]\((https?://[^)\s]+)\)', re.IGNORECASE)
    pattern = re.compile(r'https?://[^\s<>"\']+?\.(?:png|jpe?g|gif|webp)(?:\?[^\s<>"\']*)?', re.IGNORECASE)
    urls = []
    for match in markdown_pattern.finditer(value):
        url = match.group(1).rstrip(").,;")
        if url not in urls:
            urls.append(url)
    for match in pattern.finditer(value):
        url = match.group(0).rstrip(").,;")
        if url not in urls:
            urls.append(url)
    return urls


@st.cache_data(show_spinner=False)
def fetch_image_bytes(url):
    try:
        response = requests.get(
            sanitize_text(url),
            timeout=15,
            headers={
                "User-Agent": "Mozilla/5.0",
                "Referer": "https://en.ws-tcg.com/"
            }
        )
        if response.status_code == 200 and response.content:
            return response.content
    except Exception:
        return None
    return None


def render_markdown_and_images(text):
    value = sanitize_text(text)
    if not value:
        return
    display_text = re.sub(r'!\[[^\]]*\]\((https?://[^)\s]+)\)', r'\1', value, flags=re.IGNORECASE)
    st.markdown(display_text)
    for image_url in extract_image_urls(value):
        image_bytes = fetch_image_bytes(image_url)
        if image_bytes:
            st.image(image_bytes, width=320)
        else:
            st.image(image_url, width=320)
