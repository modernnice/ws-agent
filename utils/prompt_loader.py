from utils.config_handler import config
from utils.path_tool import get_abs_path
from utils.logger_handler import logger

def load_prompt(prompt_config_key: str) -> str:
    try:
        rel_path = config.get('prompts', prompt_config_key)
        if not rel_path:
            raise ValueError(f"'{prompt_config_key}' 缺失对应的prompts配置项")
            
        full_path = get_abs_path(rel_path)
        with open(full_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logger.error(f"加载prompt失败: '{prompt_config_key}': {e}")
        return ""

if __name__ == "__main__":
    print("=== 测试 PromptLoader ===")
    
    # 1. 测试读取存在的 Prompt
    key = "rag_path"
    content = load_prompt(key)
    print(f"✅ 读取成功: {content.strip()}")

    # 2. 测试读取不存在的 Prompt (应触发日志报错)
    invalid_key = "non_existent_key"
    content = load_prompt(invalid_key)
    if not content:
        print("✅ 正确处理了缺失的 Key (返回空字符串)")
