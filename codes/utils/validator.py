# utils/validator.py
import time
from .llm_caller import call_ui_tars
from codes.ui_tars.action_parser import parse_action_to_structure_output, parsing_response_to_pyautogui_code
import pyautogui


def validate_step_with_model(step, image_path, max_retries=2):
    """
    通过 UI-TARS 模型验证截图是否满足当前步骤的前置条件，
    若不满足，将自动生成“补偿动作”执行后重新验证。
    """
    action = step["action_type"]
    inputs = step["action_inputs"]

    hint = _generate_check_prompt(action, inputs)
    print(f"🔍 验证提示: {hint}")

    for retry in range(max_retries):
        result_text = call_ui_tars(hint, image_path)
        print(f"🤖 验证模型响应 #{retry+1}:\n{result_text}")


        if "Action:" in result_text:
            return True

        # 若验证失败，尝试自动修复 UI 状态
        print("🛠️ 尝试自动修正前置状态...")
        recovery_actions = parse_action_to_structure_output(
            result_text,
            factor=1000,
            origin_resized_height=1440,
            origin_resized_width=2560
        )

        for a in recovery_actions:
            print("⚙️ 执行修正动作:", a["action_type"])
            code = parsing_response_to_pyautogui_code(a, 1440, 2560)
            print(code)
            try:
                exec(code)
            except Exception as e:
                print(f"⚠️ 修正失败: {e}")
        time.sleep(1.2)

    return False


def _generate_check_prompt(action, inputs):
    if action == "click":
        return "截图中是否有可点击目标？"
    elif action == "type":
        return "截图中是否已定位到输入框？"
    elif action == "hotkey":
        return "当前截图是否满足快捷键操作前置条件？"
    else:
        return f"截图中是否可以执行动作 {action}？"
