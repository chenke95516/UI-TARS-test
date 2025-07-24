import os
import time
from datetime import datetime
from ui_tars.action_parser import parse_action_to_structure_output, parsing_response_to_pyautogui_code
from utils.screenshot import take_screenshot
from utils.llm_caller_input import call_ui_tars
from utils.validator import validate_step_with_model

SCREEN_WIDTH = 2560  # 根据实际分辨率修改
SCREEN_HEIGHT = 1440

LOG_DIR = "logs"
MAX_STEPS = 10  # 最大步骤限制，防止无限循环


def run_test_from_instruction(instruction):
    os.makedirs(LOG_DIR, exist_ok=True)
    print(f"\n🚀 开始执行任务: {instruction}\n")

    # 初始化状态
    current_step = 0
    history = []  # 保存历史交互记录
    img_path = take_screenshot(save_dir=LOG_DIR, name="step0_start.png")
    print(f"📸 初始截图: {img_path}")

    while current_step < MAX_STEPS:
        # Step 2: 调用 UI-TARS 获取当前步骤指令（传入历史记录）
        model_response_text = call_ui_tars(instruction, img_path, history=history)
        print(f"🤖 第 {current_step+1} 步模型响应:\n{model_response_text}\n")
        history.append(model_response_text)  # 记录历史

        # Step 3: 解析指令
        steps = parse_action_to_structure_output(
            model_response_text,
            factor=1000,
            origin_resized_height=SCREEN_HEIGHT,
            origin_resized_width=SCREEN_WIDTH
        )

        # 检查是否完成任务
        if any(step["action_type"] == "finished" for step in steps):
            print("✅ 任务已完成")
            break

        # Step 4: 执行当前步骤
        for step in steps:
            print(f"\n🧪 第 {current_step+1} 步: {step['action_type']}, 输入: {step['action_inputs']}")

            max_attempts = 3
            for attempt in range(max_attempts):
                # 执行前截图
                before_img = take_screenshot(LOG_DIR, name=f"step{current_step+1}_before_try{attempt}.png")

                # 验证前置条件
                if validate_step_with_model(step, before_img):
                    break
                else:
                    print(f"🔁 第 {attempt+1} 次前置验证失败，尝试调整...\n")
                    time.sleep(1.0)
            else:
                print("⚠️ 前置验证连续失败，跳过此步骤")
                continue

            # 生成并执行代码
            py_code = parsing_response_to_pyautogui_code(step, SCREEN_HEIGHT, SCREEN_WIDTH)
            print(f"🧠 执行代码:\n{py_code}\n")

            try:
                exec(py_code)
            except Exception as e:
                print(f"❌ 步骤执行异常: {e}")

            time.sleep(1.5)  # 等待界面响应

            # 执行后截图（更新当前界面状态）
            img_path = take_screenshot(LOG_DIR, name=f"step{current_step+1}_after.png")
            print(f"✅ 步骤 {current_step+1} 完成，截图保存于 {img_path}")

        current_step += 1

    if current_step >= MAX_STEPS:
        print(f"⚠️ 已达到最大步骤限制({MAX_STEPS}步)，任务可能未完成")


if __name__ == '__main__':
    run_test_from_instruction("在搜索框输入：QWen2.5-VL")