# step_runner.py
import os
import time
from datetime import datetime
from ui_tars.action_parser import parse_action_to_structure_output, parsing_response_to_pyautogui_code
from utils.screenshot import take_screenshot
from utils.llm_caller import call_ui_tars
from utils.validator import validate_step_with_model

SCREEN_WIDTH = 2560  # 根据实际分辨率修改
SCREEN_HEIGHT = 1440

LOG_DIR = "logs"


def run_test_from_instruction(instruction):
    os.makedirs(LOG_DIR, exist_ok=True)
    print(f"\n🚀 开始执行任务: {instruction}\n")

    # Step 1: 初始截图
    img_path = take_screenshot(save_dir=LOG_DIR, name="step0_start.png")
    print(f"📸 已截图: {img_path}")

    # Step 2: 调用 UI-TARS 获取结构化指令
    model_response_text = call_ui_tars(instruction, img_path)
    print(f"🤖 模型响应:\n{model_response_text}\n")

    # Step 3: 解析结构化指令为操作步骤
    steps = parse_action_to_structure_output(
        model_response_text,
        factor=1000,
        origin_resized_height=SCREEN_HEIGHT,
        origin_resized_width=SCREEN_WIDTH
    )

    # Step 4: 逐步执行操作
    for idx, step in enumerate(steps):
        print(f"\n🧪 第 {idx+1} 步: {step['action_type']}, 输入: {step['action_inputs']}")

        max_attempts = 3
        for attempt in range(max_attempts):
            # Step 4.1: 执行前截图
            before_img = take_screenshot(LOG_DIR, name=f"step{idx+1}_before_try{attempt}.png")

            # Step 4.2: 验证是否满足前置条件
            if validate_step_with_model(step, before_img):
                break
            else:
                print(f"🔁 第 {attempt+1} 次前置验证失败，尝试调整状态...\n")
                time.sleep(1.0)  # 可插入额外辅助操作
        else:
            print("⚠️ 前置验证连续失败，跳过此步骤")
            continue

        # Step 4.3: 生成 PyAutoGUI 代码并执行
        py_code = parsing_response_to_pyautogui_code(step, SCREEN_HEIGHT, SCREEN_WIDTH)
        print(f"🧠 执行代码:\n{py_code}\n")

        try:
            exec(py_code)
        except Exception as e:
            print(f"❌ 步骤执行异常: {e}")

        time.sleep(1.5)  # 可根据页面响应调整

        # Step 4.4: 执行后截图
        after_img = take_screenshot(LOG_DIR, name=f"step{idx+1}_after.png")
        print(f"✅ 步骤 {idx+1} 完成，截图保存于 {after_img}")


if __name__ == '__main__':
    run_test_from_instruction("在搜索框输入：QWen2.5-VL")
