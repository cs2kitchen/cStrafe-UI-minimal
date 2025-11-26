# main.py
import sys
import argparse
import threading
import os
import signal
from input_events import InputListener
from overlay import Overlay

# 导入托盘图标相关库
try:
    import pystray
    from PIL import Image, ImageDraw
except ImportError:
    print("警告: 未安装 pystray 或 Pillow，托盘图标功能不可用。")
    pystray = None
    Image = None

def resource_path(relative_path):
    """获取资源绝对路径，处理 Nuitka 打包和开发环境"""
    try:
        # Nuitka 打包后的路径
        base_path = sys._MEIPASS
    except AttributeError:
        # 开发环境
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    path = os.path.join(base_path, relative_path)
    print(f"尝试加载资源: {path}")  # 调试信息
    return path

def create_default_icon():
    """创建默认图标（红色方块）"""
    image = Image.new('RGB', (64, 64), color='red')
    dc = ImageDraw.Draw(image)
    dc.rectangle((16, 16, 48, 48), fill='white')
    return image

def create_tray_icon():
    """创建托盘图标"""
    if pystray is None:
        return None
    
    icon_path = resource_path("cs-icon.png")
    try:
        if os.path.exists(icon_path):
            image = Image.open(icon_path)
            print(f"成功加载图标: {icon_path}")
        else:
            print(f"图标文件不存在: {icon_path}，使用默认图标")
            image = create_default_icon()
    except Exception as e:
        print(f"加载图标失败: {e}，使用默认图标")
        image = create_default_icon()
    
    menu = pystray.Menu(pystray.MenuItem("退出", lambda icon, item: os.kill(os.getpid(), signal.SIGINT)))
    icon = pystray.Icon("cStrafe", image, "cStrafe - 按右键退出", menu)
    return icon

def run_tray_icon():
    """在后台线程中运行托盘图标"""
    if pystray is None:
        return
    icon = create_tray_icon()
    if icon:
        icon.run()

def run_local_mode():
    overlay = Overlay()
    
    def on_shot(result):
        overlay.update_result(result)

    listener = InputListener(on_shot_callback=on_shot)
    listener.start()
    
    try:
        overlay.run()
    except KeyboardInterrupt:
        pass
    finally:
        listener.stop()

def run_server_mode():
    import server 
    
    print("Running Server Mode for OBS/Web.")
    print("Add 'Browser Source' in OBS: http://127.0.0.1:8000")
    print("Or open browser on another device: http://<PC_IP>:8000")
    server.start_server()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--server", action="store_true")
    args = parser.parse_args()

    exe_name = sys.argv[0].lower()
    
    # 只在本地模式下启动托盘图标
    if not (args.server or "server" in exe_name):
        tray_thread = threading.Thread(target=run_tray_icon, daemon=True)
        tray_thread.start()

    if args.server or "server" in exe_name:
        run_server_mode()
    else:
        run_local_mode()
