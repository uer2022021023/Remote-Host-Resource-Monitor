
 
# 🧠 Remote Host Resource Monitor

### — 多主机资源监控与钉钉告警系统

一个基于 **Paramiko + Requests + Threading** 的轻量级远程主机监控脚本，支持通过 **SSH** 获取 CPU、内存、磁盘使用率，并在超过设定阈值时通过 **钉钉机器人** 自动发送告警。

---

## 🚀 功能特性

* ✅ 支持多台主机同时监控（多线程）
* ✅ 实时采集 CPU / 内存 / 磁盘 使用率
* ✅ 超过阈值自动发送 **钉钉群告警**
* ✅ 支持关键词模式告警（免签名）
* ✅ 自动记录日志到本地文件 `monitor.log`
* ✅ 每隔 1 分钟自动循环检测

---

## 🧩 环境依赖

Python ≥ 3.7
需要以下依赖库：

```bash
pip install paramiko requests
```

---

## ⚙️ 配置说明

打开脚本后，修改以下配置项 👇

### 1. 钉钉 Webhook

替换为你自己的 **钉钉机器人 Webhook**（关键词模式）：

```python
KEYWORD_WEBHOOK_URL = "https://oapi.dingtalk.com/robot/send?access_token=xxxxxx"
```

> ⚠️ 注意：钉钉机器人必须设置关键词（如 `prom`），否则消息会被拒绝。

---

### 2. 主机列表配置

在 `HOSTS` 中添加需要监控的主机信息：

```python
HOSTS = [
    {'ip': '192.168.1.10', 'port': 22, 'user': 'root', 'pass': 'password'},
    {'ip': '192.168.1.11', 'port': 22, 'user': 'root', 'pass': 'password'},
]
```

> 💡 如果在生产环境中，请使用 **SSH 密钥认证**，避免明文密码。

---

### 3. 阈值设置

自定义资源使用率告警阈值（单位：%）：

```python
CPU_THRESHOLD = 85.0
MEM_THRESHOLD = 90.0
DISK_THRESHOLD = 95.0
```

---

## 📦 使用方法

1. 克隆项目

   ```bash
   git clone https://github.com/uer2022021023/remote-monitor.git
   cd remote-monitor
   ```

2. 安装依赖

   ```bash
   pip install -r requirements.txt
   ```

   （可手动创建 `requirements.txt` 内容如下）：

   ```
   paramiko
   requests
   ```

3. 启动监控

   ```bash
   python monitor.py
   ```

脚本会每 60 秒自动执行一次监控，并在终端输出状态信息。

---

## 🧾 日志记录

监控日志会保存在当前目录下的 `monitor.log` 文件中：

```
2025-10-23 18:30:01  IP:192.168.1.10, CPU:45.23%, MEM:72.11%, DISK:61.09%
2025-10-23 18:31:01  IP:192.168.1.11, CPU:88.02%, MEM:91.02%, DISK:70.00%
```

---

## 🛎️ 告警示例

当任一指标超过阈值时，会自动向钉钉群发送告警：

```
【prom】,【⚠️ CPU 告警】192.168.1.11: 92.30% > 85% 请检查！time:2025-10-23 18:32:01
```

---

## 🧠 技术要点

* 使用 `paramiko` 远程执行命令
* 通过 `threading` 实现多主机并行监控
* 采用 `requests` 调用钉钉机器人 API
* 输出日志 + 实时控制台打印

---

## 📜 License

本项目采用 [MIT License](LICENSE)。自由修改、使用和分发。


