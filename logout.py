import requests
from plyer import notification  # 跨平台通知
# from win10toast import ToastNotifier  # 仅Windows，备选

# ================== 配置区 ==================
# 如果下线接口需要动态 IP，请运行下面函数自动获取，或手动填入
# 当前本机 IP 一般会自动获取（有线网卡）
# 下面提供自动获取本机 IP 的方法（优先选取 100.125.x.x 段）
import socket

def get_local_ip():
    """获取本机有线 IP（优先匹配校园网段）"""
    try:
        hostname = socket.gethostname()
        ips = socket.gethostbyname_ex(hostname)[2]
        # 校园网常见 IP 段：100.125.x.x 或 10.x.x.x，根据你的情况调整
        preferred_prefixes = ['100.125.', '10.']
        for prefix in preferred_prefixes:
            for ip in ips:
                if ip.startswith(prefix):
                    return ip
        # 如果都不匹配，返回第一个非 localhost IP
        for ip in ips:
            if not ip.startswith('127.'):
                return ip
    except:
        pass
    return None

WLAN_AC_IP = "211.137.223.239"     # 服务器 IP，通常固定
WLAN_USER_IP = get_local_ip() or "100.125.93.72"   # 自动获取或手动填
SSID = "edu"
LOGOUT_URL = "http://111.26.29.113:7119/portalLogout.wlan"
# ===========================================

def send_notification(title, message, success=True):
    """发送系统桌面通知"""
    try:
        notification.notify(
            title=title,
            message=message,
            app_name="校园网控制",
            timeout=5,  # 通知显示时间（秒）
            # 可指定图标路径，如：app_icon="path/to/icon.ico"
        )
    except Exception as e:
        print(f"通知发送失败: {e}")
        # 备用：用 win10toast
        # toaster = ToastNotifier()
        # toaster.show_toast(title, message, duration=5)

def logout():
    """静默下线主函数"""
    # 1. 先检查是否已断网，避免重复下线
    print("正在检查网络状态...")
    try:
        resp = requests.get("https://www.baidu.com", timeout=3)
        if resp.status_code != 200:
            send_notification("网络状态", "当前网络不可用，无需下线", success=False)
            print("当前已离线，无需操作。")
            return
    except:
        send_notification("网络状态", "当前网络不可用，无需下线", success=False)
        print("当前已离线，无需操作。")
        return

    # 2. 发送下线请求
    params = {
        "wlanAcIp": WLAN_AC_IP,
        "wlanUserIp": WLAN_USER_IP,
        "ssid": SSID
    }
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": f"http://111.26.29.113:7119/portal.wlan?wlanacname=&wlanacip={WLAN_AC_IP}&wlanuserip={WLAN_USER_IP}&ssid={SSID}"
    }

    print("正在发送下线请求...")
    try:
        r = requests.post(LOGOUT_URL, data=params, headers=headers, timeout=10)
        print(f"请求已发送，状态码: {r.status_code}")
    except Exception as e:
        send_notification("下线失败", f"请求异常: {e}", success=False)
        print(f"请求异常: {e}")
        return

    # 3. 验证是否下线成功（尝试访问百度，超时则成功）
    try:
        test = requests.get("https://www.baidu.com", timeout=5)
        if test.status_code == 200:
            send_notification("下线结果", "网络仍然连通，可能未成功下线", success=False)
            print("仍能访问百度，下线可能失败。")
            return
    except:
        # 超时或连接错误，说明网络已断，成功！
        pass

    send_notification("下线成功", "CMCC-5G 校园网已断开，网络已离线", success=True)
    print("已成功下线，通知已发送。")

if __name__ == "__main__":
    logout()