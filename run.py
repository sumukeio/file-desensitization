import webbrowser
import threading
import time
import uvicorn

def open_browser():
    time.sleep(1.5)
    webbrowser.open("http://127.0.0.1:8000")

if __name__ == "__main__":
    print("=" * 60)
    print("   🛡️ AI-Mask 智能文件脱敏站 正在启动...")
    print("   访问地址: http://127.0.0.1:8000")
    print("=" * 60)
    threading.Thread(target=open_browser, daemon=True).start()
    uvicorn.run("backend.app.main:app", host="127.0.0.1", port=8000, reload=True)
