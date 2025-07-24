import base64
import json
import time
import pyautogui
from openai import OpenAI
from PIL import ImageGrab

from codes.ui_tars.prompt import COMPUTER_USE_DOUBAO,MOBILE_USE_DOUBAO,GROUNDING_DOUBAO

# 配置API参数
DEEPSEEK_API_BASE = "http://localhost:8000/v1/chat/completions"
DEEPSEEK_API_MODEL = "ui-tars"

# 初始化客户端
client = OpenAI(
    base_url=DEEPSEEK_API_BASE,
    api_key="empty"  # 本地部署通常无需实际API密钥
)


# 加载prompt模板（源自prompt.py）
def get_prompt_template(template_type="computer", language="English"):
    """获取对应场景的提示词模板"""
    if template_type == "computer":
        return COMPUTER_USE_DOUBAO.format(language=language, instruction="{instruction}")
    elif template_type == "mobile":
        return MOBILE_USE_DOUBAO.format(language=language, instruction="{instruction}")
    else:
        return GROUNDING_DOUBAO.format(instruction="{instruction}")


# 截图并转换为base64
def capture_screenshot():
    screenshot = ImageGrab.grab()
    buffer = base64.b64encode(screenshot.tobytes()).decode("utf-8")
    return f"data:image/png;base64,{buffer}"


# 生成模型指令
def generate_model_prompt(user_input, template_type="computer"):
    prompt_template = get_prompt_template(template_type)
    return prompt_template.replace("{instruction}", user_input)


# 调用模型获取步骤分析
def get_model_action(user_input, history=[], template_type="computer"):
    # 捕获当前屏幕状态
    screenshot = capture_screenshot()

    # 构建消息列表
    messages = [
                   {"role": "system", "content": generate_model_prompt(user_input, template_type)}
               ] + history

    # 添加截图到消息
    messages.append({
        "role": "user",
        "content": [
            {"type": "image_url", "image_url": {"url": screenshot}},
            {"type": "text", "text": "基于当前截图和任务，分析下一步操作"}
        ]
    })

    # 调用API
    response = client.chat.completions.create(
        model=DEEPSEEK_API_MODEL,
        messages=messages,
        max_tokens=500,
        temperature=0.2
    )

    return response.choices[0].message.content, messages


# 解析模型输出并执行
def execute_action(action_str, screen_width, screen_height):
    from codes.ui_tars.action_parser import parse_action_to_structure_output, parsing_response_to_pyautogui_code

    # 解析动作
    parsed_dict = parse_action_to_structure_output(
        action_str,
        factor=1000,
        origin_resized_height=screen_height,
        origin_resized_width=screen_width,
        model_type="qwen25vl"
    )

    # 转换为可执行代码
    pyautogui_code = parsing_response_to_pyautogui_code(
        responses=parsed_dict,
        image_height=screen_height,
        image_width=screen_width
    )

    # 执行动作
    try:
        exec(pyautogui_code)
        return True, pyautogui_code
    except Exception as e:
        return False, f"执行失败: {str(e)}"


# 主流程
def run_automation(user_input):
    # 获取屏幕尺寸
    screen_width, screen_height = pyautogui.size()
    history = []

    while True:
        # 获取模型分析结果
        action_str, messages = get_model_action(user_input, history)
        history = messages  # 更新历史记录

        print(f"模型分析: {action_str}")

        # 检查是否完成任务
        if "finished(" in action_str:
            print("任务完成")
            break

        # 执行动作
        success, result = execute_action(action_str, screen_width, screen_height)
        print(f"执行结果: {result}")

        # 等待操作生效
        time.sleep(2)


# 示例：执行用户输入的任务
if __name__ == "__main__":
    # user_task = input("请输入任务指令: ")
    run_automation("打开谷歌，导航到百度，搜索自动化测试")