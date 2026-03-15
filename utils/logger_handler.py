import os
import logging
import re
import sys
from datetime import datetime
from typing import Optional

# 定义敏感数据模式
SENSITIVE_PATTERNS = {
    'email': r'[\w\.-]+@[\w\.-]+\.\w+',
    'phone': r'(?:(?:\+|00)86)?1[3-9]\d{9}',  # 简单的中国手机号匹配模式
    'api_key': r'(?:api_key|apikey|secret|token|access_token)\s*[:=]\s*[\'\"]?([a-zA-Z0-9_\-\.]{8,})[\'\"]?',
    'password': r'(?:password|passwd|pwd)\s*[:=]\s*[\'\"]?([^\s\'\",]+)[\'\"]?'
}

class SensitiveDataFilter(logging.Filter):
    """
    第二阶段：敏感信息拦截
    """
    def filter(self, record):
        if not isinstance(record.msg, str):
            return True
            
        msg = record.msg
        for key, pattern in SENSITIVE_PATTERNS.items():
            # 对于特定的键值对模式（如 api_key, password），我们只掩盖值，不掩盖键
            if key in ['api_key', 'password']:
                # 查找所有匹配项
                matches = re.finditer(pattern, msg, re.IGNORECASE)
                for match in matches:
                    full_match = match.group(0)
                    sensitive_value = match.group(1)
                    # 将完整匹配字符串中的敏感值替换为星号
                    masked_match = full_match.replace(sensitive_value, '*' * 6)
                    msg = msg.replace(full_match, masked_match)
            else:
                # 对于独立模式（如 email, phone），掩盖整个字符串
                msg = re.sub(pattern, '******', msg)
        
        record.msg = msg
        return True

def setup_logger(name: str = "app", log_dir: str = "logs") -> logging.Logger:
    """
    设置一个遵循要求的四阶段逻辑的日志记录器。
    """
    # 第四阶段：防重触发与单例保障
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
        
    logger.setLevel(logging.DEBUG)
    
    # 第一阶段：环境初始化
    # 确保日志目录存在
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    abs_log_dir = os.path.join(base_dir, log_dir)
    
    if not os.path.exists(abs_log_dir):
        os.makedirs(abs_log_dir)
        
    # 标准日志格式
    # "时间戳、模块名称、代码行号" 标签
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(filename)s:%(lineno)d - %(levelname)s - %(message)s'
    )
    
    # 第二阶段：敏感信息拦截（过滤器）
    sensitive_filter = SensitiveDataFilter()
    
    # 第三阶段：多路分发与差异化管理
    
    # 1. 控制台出口（面向开发者） - 较高级别 (INFO)
    # console_handler = logging.StreamHandler(sys.stdout)
    # console_handler.setLevel(logging.INFO)
    # console_handler.setFormatter(formatter)
    # console_handler.addFilter(sensitive_filter)
    # logger.addHandler(console_handler)
    
    # 2. 文件存储出口（面向长期存档） - 详细级别 (DEBUG)，按日期命名，使用 utf-8 编码
    today_str = datetime.now().strftime('%Y-%m-%d')
    log_file_path = os.path.join(abs_log_dir, f'app_{today_str}.log')
    
    file_handler = logging.FileHandler(log_file_path, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    file_handler.addFilter(sensitive_filter)
    logger.addHandler(file_handler)
    
    return logger

# 创建一个默认的日志实例以便轻松导入
logger = setup_logger()


if __name__ == "__main__":
    print("测试日志记录器...")
    
    # 1. 普通日志
    logger.info("这是一条 INFO 消息。")
    logger.debug("这是一条 DEBUG 消息（应该只出现在文件中）。")
    
    # 2. 敏感数据日志
    logger.info("用户邮箱是 test@example.com")
    logger.info("用户手机号是 13812345678")
    logger.info("正在连接 api_key='1234567890abcdef'")
    logger.info("用户 password='my_secret_password'")
    
    print("日志已写入。请检查 logs 目录下的文件。")
