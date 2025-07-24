# call_ui_tars.py

import base64
import requests
from codes.ui_tars.prompt import COMPUTER_USE_DOUBAO

DEEPSEEK_API_BASE = "http://localhost:8000/v1/chat/completions"
DEEPSEEK_API_MODEL = "ui-tars"

def call_ui_tars(instruction: str, image_path: str,
                 api_url: str = DEEPSEEK_API_BASE,
                 model: str = DEEPSEEK_API_MODEL) -> str:
    """
    调用 UI-TARS 模型进行图文识别，返回 Thought + Action 指令文本

    Args:
        instruction (str): 用户自然语言任务指令
        image_path (str): 截图路径（PNG/JPEG）
        api_url (str): API 地址（OpenAI 接口兼容）
        model (str): 使用的模型名

    Returns:
        str: 模型返回的完整文本（包含 Thought 和 Action）
    """
    try:
        # 读取图像并编码为 base64
        with open(image_path, "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode("utf-8")

        # 生成 prompt
        user_prompt = COMPUTER_USE_DOUBAO.format(
            instruction=instruction,
            language="Chinese"  # 或 "中文"
        )

        # 构造消息体
        messages = [
            {"role": "system", "content": "You are a GUI agent. You will see screenshots and instructions."},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}}
                ]
            }
        ]

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
