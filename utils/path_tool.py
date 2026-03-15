import os

def get_project_root() -> str:
    current_path = os.path.dirname(os.path.abspath(__file__))
    while True:
        # 如果当前目录下有 .git 或 requirements.txt，就认为这是根目录
        if os.path.exists(os.path.join(current_path, ".git")) or \
           os.path.exists(os.path.join(current_path, "requirements.txt")):
            return current_path
        
        # 向上跳一级
        parent_path = os.path.dirname(current_path)
        
        # 如果跳到顶了还没找到，就报错防止死循环
        if parent_path == current_path:
            raise Exception("未找到工程根目录")
        current_path = parent_path

def get_abs_path(relative_path: str) -> str:
    """
    将工程内的相对路径转为绝对路径（统一路径基准）
    :param relative_path: 相对于工程根目录的路径，如 "config/rag.yml"
    :return: 绝对路径
    """
    project_root = get_project_root()
    return os.path.join(project_root, relative_path)

if __name__ == "__main__":
    print("=== 测试路径工具 path_tool.py ===")
    
    try:
        root_path = get_project_root()
        print(f"✅ 项目根目录: {root_path}")
    except Exception as e:
        print(f"❌ 获取项目根目录失败: {e}")
    
    test_rel_path = "config/rag.yml"
    abs_path = get_abs_path(test_rel_path)
    print(f"✅ 相对路径 '{test_rel_path}' -> 绝对路径: {abs_path}")
    
    # 验证文件是否存在（可选，视具体文件情况而定）
    if os.path.exists(abs_path):
        print("   (文件存在)")
    else:
        print("   (文件不存在，但路径计算正确)")
