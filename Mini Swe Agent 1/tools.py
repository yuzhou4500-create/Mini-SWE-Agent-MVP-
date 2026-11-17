from pathlib import Path

# 1. 列目录函数
def list_files(dir_path: str) -> str:
    folder = Path(dir_path)
    if not folder.exists() or not folder.is_dir():
        return f"错误：路径不存在或不是文件夹 ({dir_path})"
    
    files = [f"{item.name} ({item.resolve()})" for item in folder.iterdir() if item.is_file()]
    return "\n".join(files) if files else "文件夹为空"

# 2. 读文件
def read_file(file_path: str) -> str:
    p = Path(file_path)
    if not p.is_file():
        return f"错误：找不到文件 ({file_path})"
    return p.read_text(encoding="utf-8", errors="replace")

# 3. 写文件
def write_file(file_path: str, content: str) -> str:
    p = Path(file_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return f"成功写入文件：{file_path}"

# 接线员字典
TOOL_MAP = {
    "list_files": list_files,
    "read_file": read_file,
    "write_file": write_file,
}

# 给百炼看的完整菜单
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "查看指定文件夹下有哪些文件",
            "parameters": {
                "type": "object",
                "properties": {
                    "dir_path": {"type": "string", "description": "文件夹路径"}
                },
                "required": ["dir_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "读取指定文本文件的全部内容",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "要读取的文件路径"}
                },
                "required": ["file_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "向指定路径写入文本内容（若文件或父目录不存在会自动创建，若已存在则会覆盖原内容）",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "目标文件路径"},
                    "content": {"type": "string", "description": "要写入的完整文本内容"}
                },
                "required": ["file_path", "content"]
            }
        }
    }
]