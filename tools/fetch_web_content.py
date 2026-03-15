import http.client
import json
import yaml
import logging
from pathlib import Path
from langchain_core.tools import tool

# Set up logging
logger = logging.getLogger(__name__)

# Load config
def load_config():
    config_path = Path(__file__).resolve().parent.parent / "config" / "agent.yml"
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Failed to load config from {config_path}: {e}")
        return {}

config = load_config()
SHUYANAI_API_KEY = config.get("SHUYANAI_API_KEY", "")
SHUYANAI_READER_URL_FULL = config.get("SHUYANAI_READER_URL", "https://api.shuyanai.com/v1/reader")

@tool
def fetch_web_content(url: str) -> str:
    """
    Fetches the content of a web page using the ShuyanAI Reader API.
    This tool converts web pages (including dynamic ones) into HTML format.
    It automatically filters out lines containing the copyright symbol '©'.

    Args:
        url (str): The URL of the web page to fetch.

    Returns:
        str: The content of the web page in HTML format, or an error message.
    """
    if not SHUYANAI_API_KEY:
        return "Error: SHUYANAI_API_KEY not found in config."

    # Ensure API Key starts with 'Bearer '
    api_key_header = SHUYANAI_API_KEY
    if not api_key_header.startswith("Bearer "):
       api_key_header = f"Bearer {SHUYANAI_API_KEY}"

    logger.info(f"Fetching {url} using ShuyanAI Reader API")

    try:
        # Parse host and path from the full URL
        from urllib.parse import urlparse
        parsed_url = urlparse(SHUYANAI_READER_URL_FULL)
        host = parsed_url.netloc
        path = parsed_url.path

        conn = http.client.HTTPSConnection("api.dataeyes.ai")
        payload = json.dumps({
            "url": url,
            "format": "html"
        })
        headers = {
            'Authorization': api_key_header,
            'Content-Type': 'application/json'
        }
        
        conn.request("POST", path, payload, headers)
        res = conn.getresponse()
        data = res.read()
        
        if res.status != 200:
            return f"Error: API returned status {res.status}. Response: {data.decode('utf-8')}"
            
        result_json = json.loads(data.decode("utf-8"))
        
        # Check if the API returned a success message
        if result_json.get("message") != "success":
             return f"Error: API returned message: {result_json.get('message')}"

        html_content = result_json.get("data", {}).get("html", "")
        
        if not html_content:
             return "Warning: Retrieved content is empty."

        # Filter out lines containing '©'
        filtered_lines = []
        for line in html_content.splitlines():
            if "©" not in line:
                filtered_lines.append(line)
        
        final_content = "\n".join(filtered_lines)
        return final_content

    except Exception as e:
        logger.error(f"Error fetching content from {url}: {e}")
        return f"Error fetching content: {str(e)}"

if __name__ == "__main__":
    # Test URL
    test_url = "https://ws-tcg.com/deckrecipe/"
    print(f"Testing fetch_web_content with URL: {test_url}")
    
    # Configure logging to console for testing
    logging.basicConfig(level=logging.INFO)
    
    result = fetch_web_content.invoke(test_url)
    
    print("\n" + "="*50)
    print("FETCH RESULT:")
    print("="*50)
    print(result)
    print("="*50)
