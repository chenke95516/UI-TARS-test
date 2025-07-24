import os
from datetime import datetime
from PIL import ImageGrab

def take_screenshot(save_dir="logs", name=None):
    os.makedirs(save_dir, exist_ok=True)
    if name is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        name = f"screenshot_{timestamp}.png"
    save_path = os.path.join(save_dir, name)
    image = ImageGrab.grab()
    image.save(save_path)
    return save_path
