import paramiko
import requests
import json
from datetime import datetime
import time
import threading

Logging_file = 'monitor.log'

# 1. 替换成你自己的 Webhook (关键词模式)
KEYWORD_WEBHOOK_URL = "https://oapi.dingtalk.com/robot/send?access_token=3ce35f6141115e81b556ad5bc8a7491d76183dbbac40574deddf0a5b63661d4b" 

# --- 主机列表配置 ---
HOSTS = [
    {'ip': '192.168.164.100', 'port': 22, 'user': 'root', 'pass': '666666'},
    {'ip': '192.168.164.100', 'port': 22, 'user': 'root', 'pass': '666666'},
    {'ip': '192.168.164.100', 'port': 22, 'user': 'root', 'pass': '666666'},    
]
# 生成环境下 使用ssh 密钥
# --- 告警阈值 ---
CPU_THRESHOLD = 85.0
MEM_THRESHOLD = 90.0
DISK_THRESHOLD = 95.0

# --- 1.主监控函数 ---
def monitor_all_hosts():
    threads = []
    for host in HOSTS:
        # 为每个主机创建一个线程
        thread = threading.Thread(target=monitor_host_worker, args=(host,))
        threads.append(thread)
        thread.start()
        
    # 等待所有线程完成
    for thread in threads:
        thread.join()
    
    print("\n--- 本轮监控完成 ---")

# --- 2.通过 SSHClient 获取远程主机状态 ---
def get_remote_stat(host, command):
    """
    通过 SSHClient 在远程主机上执行命令并返回纯净结果。
    """

    ip = host['ip']
    port = host.get('port', 22)
    username = host['user']
    password = host['pass']
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(hostname=ip, port=port, username=username, password=password, timeout=5)
        
        # 执行命令
        stdin, stdout, stderr = client.exec_command(command)
        
        # 读取输出并清理
        output = stdout.read().decode('utf-8').strip()
        
        # 检查错误输出
        error = stderr.read().decode('utf-8').strip()
        if error:
            print(f"[{ip}] 命令执行错误: {error}")
            return None
        
        return output

    except Exception as e:
        print(f"[{ip}] SSH连接或命令执行失败: {e}")
        return None
        
    finally:
        # 确保连接被关闭
        if client:
            client.close()

# --- 3.提取 CPU、内存、磁盘使用率 ---
def extract_usage(host):
    ip = host['ip']
    stats = {'ip': ip, 'cpu': None, 'mem': None, 'disk': None}
    
    # --- 1. 获取 CPU 使用率 ---
    CPU_COMMAND = 'top -bn1 | grep "Cpu(s)" | sed "s/.*, *\\([0-9.]*\\)%* id.*/\\1/" | awk \'{print 100 - $1}\''
    cpu_output = get_remote_stat(host, CPU_COMMAND)
    if cpu_output:
        try:
            stats['cpu'] = float(cpu_output)
        except ValueError:
            print(f"[{ip}] CPU解析失败: {cpu_output}")

    # --- 2. 获取内存使用率 ---
    MEM_COMMAND = 'free -m | awk \'NR==2{printf "%.2f", $3*100/$2}\''
    mem_output = get_remote_stat(host, MEM_COMMAND)
    if mem_output:
        try:
            stats['mem'] = float(mem_output)
        except ValueError:
            print(f"[{ip}] 内存解析失败: {mem_output}")
            
    # --- 3. 获取磁盘使用率 (根分区) ---
    DISK_COMMAND = 'df -h / | awk \'NR==2{print $5}\' | sed \'s/%//\''
    disk_output = get_remote_stat(host, DISK_COMMAND)
    if disk_output:
        try:
            stats['disk'] = float(disk_output)
        except ValueError:
            print(f"[{ip}] 磁盘解析失败: {disk_output}")
            
    return stats

# --- 4.检查阈值并发送告警 ---
def check_and_alert(stats):
    ip = stats['ip']
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 封装告警逻辑，避免代码重复
    def _do_alert(resource, usage, threshold):
        if usage is not None and usage > threshold:
            alert_content = f"【prom】,【⚠️ {resource} 告警】{ip}: {usage:.2f}% > {threshold}%请检查！time:{timestamp}"
            send_dingtalk_alert_keyword(
                webhook_url=KEYWORD_WEBHOOK_URL,
                content=alert_content,
                at_mobiles=["18296976275"]
            )
            print(f"【⚠️ {resource} 告警】{ip}: {usage:.2f}% > {threshold}%")

    _do_alert("CPU", stats['cpu'], CPU_THRESHOLD)
    _do_alert("内存", stats['mem'], MEM_THRESHOLD)
    _do_alert("磁盘", stats['disk'], DISK_THRESHOLD)

    # 打印正常日志
    print(f"[{ip}] CPU:{stats['cpu']:.2f}%, MEM:{stats['mem']:.2f}%, DISK:{stats['disk']:.2f}%")
# --- 5.发送钉钉告警函数 ---
def send_dingtalk_alert_keyword(webhook_url, content, at_mobiles=None, is_at_all=False):

    """
    使用“关键词”方式发送钉钉 Text 消息
    注意：content 中必须包含你设置的关键词
    """
    
    # 注意：关键词必须在 content 中
    if "prom" not in content:
        print("错误：消息内容必须包含关键词 'prom'")
        return

    payload = {
        "msgtype": "text",
        "text": {
            "content": content
        },
        "at": {
            "atMobiles": at_mobiles if at_mobiles else [],
            "isAtAll": is_at_all
        }
    }
    
    headers = {'Content-Type': 'application/json'}
    
    try:
        response = requests.post(
            webhook_url,  # URL 不需要签名
            data=json.dumps(payload),
            headers=headers,
            timeout=10
        )
        result = response.json()
        if result.get("errcode") == 0:
            print("钉钉告警发送成功！")
        else:
            print(f"钉钉告警发送失败: {result}")
            
    except Exception as e:
        print(f"发送钉钉告警时发生错误: {e}")

# --- 6.日志记录 ---
def log_message(stats):
    """将日志消息写入日志文件"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(Logging_file, 'a') as f:
        f.write(f"{timestamp}  IP:{stats['ip']}, CPU:{stats['cpu']:.2f}%, MEM:{stats['mem']:.2f}%, DISK:{stats['disk']:.2f}%\n")

# --- 7.处理单个主机监控的 Worker 函数 ---
def monitor_host_worker(host):
    """多线程 Worker 函数，负责单个主机的监控、日志和告警"""
    print(f"\n--- 正在监控 {host['ip']} ---")
    stats = extract_usage(host)
    log_message(stats) # 记录日志

    if stats['cpu'] is not None and stats['mem'] is not None and stats['disk'] is not None:
        check_and_alert(stats)
    else:
        # 如果连接或数据采集失败，也发送告警通知，以便及时发现连接问题
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        alert_content = f"【prom】,【❗ 连接告警】{host['ip']} 无法连接或获取数据。请检查 SSH 服务。time:{timestamp}"
        send_dingtalk_alert_keyword(KEYWORD_WEBHOOK_URL, alert_content)
        print(f"【❗ 失败】无法获取 {host['ip']} 的完整数据。已发送告警。")

# --- 主程序入口 ---

if __name__ == "__main__":
    while True:
        monitor_all_hosts()
        time.sleep(60)  # 每1分钟监控一次
    