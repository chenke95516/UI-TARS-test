import base64
import requests
from codes.ui_tars.prompt import COMPUTER_USE_DOUBAO

DEEPSEEK_API_BASE = "http://localhost:8000/v1/chat/completions"
DEEPSEEK_API_MODEL = "ui-tars"

def call_ui_tars(instruction: str, image_path: str,
                 history: list = None,  # 新增历史记录参数
                 api_url: str = DEEPSEEK_API_BASE,
                 model: str = DEEPSEEK_API_MODEL) -> str:
    """
    调用 UI-TARS 模型进行图文识别，返回 Thought + Action 指令文本
    支持通过历史记录参数传递上下文信息

    Args:
        instruction (str): 用户自然语言任务指令
        image_path (str): 截图路径（PNG/JPEG）
        history (list): 历史交互记录列表，每个元素为模型之前的响应文本
        api_url (str): API 地址（OpenAI 接口兼容）
        model (str): 使用的模型名

    Returns:
        str: 模型返回的完整文本（包含 Thought 和 Action）
    """
    try:
        # 读取图像并编码为 base64
        with open(image_path, "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode("utf-8")

        # 生成带历史记录的提示词
        user_prompt = COMPUTER_USE_DOUBAO.format(
            instruction=instruction,
            language="Chinese"
        )

        # 处理历史记录，构造对话上下文
        messages = [
            {"role": "system", "content": "You are a GUI agent. You will see screenshots, instructions and action history. Use them to complete the current task."}
        ]

        # 添加历史交互记录
        if history and isinstance(history, list):
            for idx, hist in enumerate(history):
                # 历史记录中用户角色的内容（复用原始指令）
                messages.append({
                    "role": "user",
                    "content": [{"type": "text", "text": f"历史步骤 {idx+1} 指令: {instruction}"}]
                })
                # 历史记录中助手角色的响应
                messages.append({
                    "role": "assistant",
                    "content": [{"type": "text", "text": hist}]
                })

        # 添加当前步骤的用户指令和截图
        messages.append({
            "role": "user",
            "content": [
                {"type": "text", "text": user_prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}}
            ]
        })

        payload = {
            "model": model,
            "messages": messages,
            "temperature": 0.2,
            "top_p": 1.0,
            "stream": False
        }

        headers = {"Content-Type": "application/json"}

        # 发送请求
        response = requests.post(api_url, json=payload, headers=headers, timeout=60)
        response.raise_for_status()

        result = response.json()
        return result["choices"][0]["message"]["content"]

    except Exception as e:
        print(f"❌ 调用 UI-TARS 模型失败: {e}")
        return ""