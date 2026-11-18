import json
import os
import urllib.error
import urllib.request
from tools import TOOLS, TOOL_MAP

API_KEY = os.environ.get("DASHSCOPE_API_KEY")
if not API_KEY:
    raise RuntimeError("请先在终端设置环境变量 DASHSCOPE_API_KEY！")

BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
MODEL_NAME = "qwen4-max"

SYSTEM_PROMPT = """你是一个能操作本地文件的编程助手，请善用工具完成任务。

<tone>
语言极度简洁、客观，直接说明操作结果，禁止任何寒暄、客套话或长篇大论。
</tone>

<context>
- 运行环境：Windows 系统。
- 合法工作根目录：D:\\FileOrganizerTest（你只能操作该目录及其子目录下的文件，严禁越权访问其他盘符或系统目录）。
- 你只能通过提供的工具感知和操作文件系统，无法凭空读取本地文件。
</context>

<instructions>
执行任务时必须严格遵守以下分步顺序：
1. 先侦察：在读取、修改或移动任何文件前，若未百分之百确认准确路径，必须先调用 list_files 获取真实文件列表。
2. 先读后改：当需要修改或删除已有文件的部分内容时，必须先调用 read_file 读取完整内容，在内存中完成修改后，再调用 write_file 将完整新内容写入，防止直接覆盖导致数据丢失。
3. 执行与汇报：确认所有工具调用均成功完成并达到用户目标后，停止调用工具并输出最终汇报。
</instructions>

<examples>
<example>
用户指令：把 notes.txt 里的第 2 行删掉
思考与行动路径：
- 第 1 步：调用 list_files 确认 D:\\FileOrganizerTest 下存在 notes.txt。
- 第 2 步：调用 read_file 读取 notes.txt 全部内容（发现共 3 行：第1行、第2行、第3行）。
- 第 3 步：保留第 1 行和第 3 行，调用 write_file 将更新后的完整文本写入 notes.txt。
- 第 4 步：输出简洁汇报。
</example>
</examples>

<constraints>
- 严禁编造工具清单之外的函数名，严禁猜测不存在的文件路径。
- 遇到报错必须自愈：如果某次工具调用返回错误信息，必须分析报错原因并修正参数后再重试，严禁使用一模一样的参数重复调用。
- 严禁操作 D:\\FileOrganizerTest 目录之外的任何路径。
</constraints>

<output_format>
任务完成后，严格按以下格式输出（不超过 5 行）：
状态：已完成 / 失败（附简短原因）
操作明细：
- [动作] 文件路径：一句话说明结果
</output_format>"""


def ask_llm(messages: list) -> dict:
    payload = json.dumps({
        "model": MODEL_NAME,
        "messages": messages,
        "tools": TOOLS,
        "temperature": 0.1
    }).encode("utf-8")

    req = urllib.request.Request(
        BASE_URL,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEY}"
        },
        method="POST"
    )
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with opener.open(req, timeout=20) as res:
            data = json.loads(res.read().decode("utf-8"))
            return data["choices"][0]["message"]
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"百炼请求失败 [{e.code}]: {err_body}") from e


def chat_loop():
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ]
    print("🤖 本地文件 Agent 已启动（输入 exit 退出，输入 clear 清空上下文记忆）")

    while True:
        user_input = input("\n你: ").strip()
        if not user_input:
            continue
        if user_input.lower() in ("exit", "quit"):
            print("已退出。")
            break
        if user_input.lower() == "clear":
            messages = [messages[0]]
            print("🧹 上下文记忆已清空。")
            continue

        messages.append({"role": "user", "content": user_input})

        # 单轮任务最多允许连续调用 10 步工具
        for step in range(10):
            msg = ask_llm(messages)
            messages.append(msg)

            tool_calls = msg.get("tool_calls")
            if not tool_calls:
                print(f"\nAgent:\n{msg.get('content')}")
                break  # 跳出工具循环，等待你的下一条指令

            for tc in tool_calls:
                func_name = tc["function"]["name"]
                args = json.loads(tc["function"]["arguments"])
                print(f"  [第{step+1}步] 调用工具: {func_name} | 参数: {args}")

                if func_name not in TOOL_MAP:
                    result = f"错误：未知的工具名 '{func_name}'"
                else:
                    try:
                        result = TOOL_MAP[func_name](**args)
                    except Exception as e:
                        result = f"工具执行出错: {e}"

                messages.append({
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "content": str(result)
                })
        else:
            print("\n⚠️ 已达到单轮最大工具调用步数上限（10步），任务提前终止。")


if __name__ == "__main__":
    chat_loop()
