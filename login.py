import requests
import re
import time
import socket
from plyer import notification

# ================== 配置区 ==================
USERNAME = ""          # 你的校园网账号
PASSWORD = ""                # 你的密码
PORTAL_URL = "http://111.26.29.113:7119/portal.wlan?wlanacname=&wlanacip=211.137.223.239&wlanuserip=100.125.93.72&ssid=edu"
LOGIN_ACTION = "http://111.26.29.113:7119/portalLogin.wlan"
# ===========================================

def get_local_ip():
    """获取本机有线 IP，优先匹配校园网段（100.125.x.x 或 10.x.x.x）"""
    try:
        hostname = socket.gethostname()
        ips = socket.gethostbyname_ex(hostname)[2]
        for prefix in ['100.125.', '10.']:
            for ip in ips:
                if ip.startswith(prefix):
                    return ip
        for ip in ips:
            if not ip.startswith('127.'):
                return ip
    except:
        pass
    return None

def send_notification(title, message, success=True):
    """发送系统桌面通知"""
    try:
        notification.notify(
            title=title,
            message=message,
            app_name="校园网控制",
            timeout=5
        )
    except:
        # 备用方案（Windows 专用，需要 pip install win10toast）
        try:
            from win10toast import ToastNotifier
            toaster = ToastNotifier()
            toaster.show_toast(title, message, duration=5)
        except:
            pass

def login():
    # 1. 检查是否已经联网
    print("正在检查网络状态...")
    try:
        resp = requests.get("https://www.baidu.com", timeout=3)
        if resp.status_code == 200:
            send_notification("已联网", "网络正常，无需登录")
            print("网络已连接，操作取消。")
            return
    except:
        print("当前未联网，开始登录流程...")

    # 2. 获取动态 token（portalLogin）
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36"
    })
    try:
        print("正在获取认证页面...")
        r = session.get(PORTAL_URL, timeout=10)
        r.encoding = 'utf-8'
        html = r.text
    except Exception as e:
        send_notification("登录失败", f"无法访问认证页面: {e}", success=False)
        print(f"访问认证页面失败: {e}")
        return

    # 提取 portalLogin
    match = re.search(r'name="portalLogin"\s+value\s*=\s*"([^"]+)"', html)
    if not match:
        send_notification("登录失败", "页面中未找到 portalLogin 字段", success=False)
        print("无法提取 portalLogin，页面可能已更新。")
        return
    portalLogin = match.group(1)
    print(f"已获取 portalLogin: {portalLogin[:10]}...")

    # 3. 构造登录参数（自动获取本机 IP）
    wlanAcIp = "211.137.223.239"
    wlanUserIp = get_local_ip()
    if not wlanUserIp:
        # 如果自动获取失败，尝试从页面 URL 或本机解析
        wlanUserIp = "100.125.93.72"   # 可手动替换为你的当前 IP
        print(f"自动获取 IP 失败，使用备用: {wlanUserIp}")
    else:
        print(f"检测到本机 IP: {wlanUserIp}")

    payload = {
        "wlanAcName": "",
        "wlanAcIp": wlanAcIp,
        "wlanUserIp": wlanUserIp,
        "ssid": "edu",
        "portalLogin": portalLogin,
        "passType": "1",
        "userName": USERNAME,
        "userPwd": PASSWORD,
        "saveUser": "on"       # 如果希望记住密码，保留此参数
    }

    headers = {
        "Referer": PORTAL_URL,
        "Origin": "http://111.26.29.113:7119",
        "Content-Type": "application/x-www-form-urlencoded"
    }

    # 4. 发送登录请求
    timestamp = int(time.time() * 1000)
    post_url = f"{LOGIN_ACTION}?{timestamp}"
    print("正在发送登录请求...")
    try:
        r = session.post(post_url, data=payload, headers=headers, timeout=10)
        print(f"登录请求状态码: {r.status_code}")
    except Exception as e:
        send_notification("登录失败", f"请求异常: {e}", success=False)
        print(f"登录请求失败: {e}")
        return

    # 5. 验证登录结果（等待3秒后测试百度）
    time.sleep(3)
    try:
        test = requests.get("https://www.baidu.com", timeout=5)
        if test.status_code == 200:
            send_notification("登录成功", "校园网已连接，可以上网啦！")
            print("登录成功，网络已连通。")
        else:
            send_notification("登录结果不明", f"百度返回状态码: {test.status_code}", success=False)
            print(f"警告：百度返回 {test.status_code}，可能需要手动检查。")
    except requests.exceptions.RequestException:
        send_notification("登录失败", "无法访问百度，请检查账号或网络", success=False)
        print("登录可能失败，无法访问外网。")

if __name__ == "__main__":
    login()
