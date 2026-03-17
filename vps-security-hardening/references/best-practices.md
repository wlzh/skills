# VPS 安全加固参考指南

> 基于「VPS被黑?这7招让你的服务器固若金汤!」整理

## SSH 安全最佳实践

### 1. SSH 配置参数说明

| 参数 | 推荐值 | 说明 |
|------|--------|------|
| `Port` | 非标准端口 (22222-65535) | 避免自动化扫描 |
| `PermitRootLogin` | `prohibit-password` | 禁止 root 密码登录（比 without-password 更严格） |
| `PasswordAuthentication` | `no` (密钥登录后) | 禁用密码认证 |
| `PubkeyAuthentication` | `yes` | 启用密钥认证 |
| `MaxAuthTries` | `3` | 限制认证尝试次数 |
| `ClientAliveInterval` | `300` | 5 分钟检测客户端存活 |
| `ClientAliveCountMax` | `2` | 2 次无响应断开 |
| `PermitEmptyPasswords` | `no` | 禁止空密码 |

### 2. Ubuntu 版本与 SSH 配置方式

| Ubuntu 版本 | SSH 配置方式 |
|-------------|-------------|
| 22.10, 23.04, 23.10 | socket 激活，需配置 `/etc/systemd/system/ssh.socket.d/` |
| 24.04+ | 直接修改 `/etc/ssh/sshd_config` 或 `sshd_config.d/` |

**Ubuntu 22.10-23.10 socket 激活配置：**

```bash
sudo mkdir -p /etc/systemd/system/ssh.socket.d
sudo vim /etc/systemd/system/ssh.socket.d/listen.conf
```

```ini
[Socket]
ListenStream=
ListenStream=2233
```

```bash
sudo systemctl daemon-reload
sudo systemctl restart ssh.socket
sudo systemctl restart ssh.service
```

**禁用 socket 激活（改用传统服务）：**

```bash
sudo systemctl disable --now ssh.socket
sudo systemctl enable --now ssh.service
```

### 3. SSH 密钥生成

```bash
# 生成 ED25519 密钥（推荐）
ssh-keygen -t ed25519 -C "your@email.com"

# 或生成 RSA 密钥（兼容性好）
ssh-keygen -t rsa -b 4096 -C "your@email.com"

# 复制公钥到服务器
ssh-copy-id -p ${SSH_PORT} ${USER}@${VPS_IP}
```

### 4. 禁用密码登录（密钥配置成功后）

```bash
# 修改配置
sudo sed -i 's/^#\?PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config.d/99-hardening.conf

# 重启 SSH
sudo systemctl restart ssh
```

## Fail2ban 配置

### 安装

```bash
sudo apt install fail2ban -y
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

### 推荐配置 (`/etc/fail2ban/jail.local`)

```ini
[sshd]
ignoreip = 127.0.0.1/8    # 白名单 IP，不会被封
enabled = true
filter = sshd
port = 2233               # 改成你的 SSH 端口
maxretry = 5              # 允许失败 5 次
findtime = 300            # 5 分钟内
bantime = 600             # 封禁 10 分钟
logpath = /var/log/auth.log
action = %(action_)s
```

**参数说明：**
- `maxretry`: 允许失败的次数
- `findtime`: 检测时间窗口（秒）
- `bantime`: 封禁时长（秒），设为 `-1` 永久封禁（不推荐）

### 常用命令

```bash
# 查看状态
sudo fail2ban-client status sshd

# 解封 IP
sudo fail2ban-client set sshd unbanip <IP>

# 查看日志
sudo tail -f /var/log/fail2ban.log
```

## UFW 防火墙规则

### 基本设置

```bash
# 设置默认策略
sudo ufw default deny incoming
sudo ufw default allow outgoing

# 允许 SSH 端口（记得改成你的端口！）
sudo ufw allow 2233/tcp

# 允许 HTTP/HTTPS（如果有网站）
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# 启用防火墙
sudo ufw enable
```

### 常用命令

```bash
# 查看状态
sudo ufw status verbose

# 查看编号规则
sudo ufw status numbered

# 允许特定 IP
sudo ufw allow from 1.2.3.4

# 允许特定 IP 访问特定端口
sudo ufw allow from 1.2.3.4 to any port 2233

# 允许 IP 段
sudo ufw allow from 192.168.1.0/24

# 删除规则（按编号）
sudo ufw delete 3

# 删除规则（按内容）
sudo ufw delete allow 80/tcp

# 重置所有规则
sudo ufw reset

# 禁用防火墙（紧急情况）
sudo ufw disable
```

### 记录日志

```bash
# 记录 SSH 连接尝试
sudo ufw allow log 2233/tcp
```

## SSH 登录通知（企业微信）

### 配置 PAM

```bash
sudo vim /etc/pam.d/sshd
# 添加以下行：
session optional pam_exec.so /usr/local/bin/notify_ssh_login.sh
```

### 通知脚本

```bash
sudo vim /usr/local/bin/notify_ssh_login.sh
```

```bash
#!/bin/bash
if [ "$PAM_TYPE" != "open_session" ]; then
    exit 0
fi

ip=$PAM_RHOST
date=$(date +"%e %b %Y, %a %r")
name=$PAM_USER
webhook_url="https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=你的webhook密钥"

curl -s -X POST "$webhook_url" \
    -H "Content-Type: application/json" \
    -d "{
        \"msgtype\": \"markdown\",
        \"markdown\": {
            \"content\": \"**SSH登录提醒**\n> 登录用户: $name\n> 客户端IP: $ip\n> 登录时间: $date\"
        }
    }"
```

```bash
sudo chmod +x /usr/local/bin/notify_ssh_login.sh
```

## Docker 安全配置（第七招）

### 问题

Docker 会直接修改 iptables 规则，**绕过 UFW 防火墙**！

### 解决方案

**1. 内部服务不暴露端口**

```yaml
services:
  redis:
    image: redis:alpine
    # 不需要 ports 配置！
    # 容器间通过容器名访问
```

**2. 需要反代的服务只监听 127.0.0.1**

```yaml
services:
  app:
    image: myapp:latest
    ports:
      - "127.0.0.1:3000:3000"  # 只在本地监听
```

**3. 需要公网访问的服务才暴露端口**

```yaml
services:
  web:
    image: nginx:latest
    ports:
      - "80:80"
      - "443:443"
```

### 完整示例 - RSSHub

```yaml
services:
  rsshub:
    image: diygod/rsshub:latest
    restart: always
    ports:
      - "127.0.0.1:1200:1200"  # 只在本地监听，通过 Nginx 反代
    environment:
      NODE_ENV: production
      CACHE_TYPE: redis
      REDIS_URL: "redis://redis:6379/"
      PUPPETEER_WS_ENDPOINT: "ws://browserless:3000"
    depends_on:
      - redis
      - browserless

  browserless:
    image: browserless/chrome
    restart: always
    # 不需要暴露端口

  redis:
    image: redis:alpine
    restart: always
    # 不需要暴露端口
    volumes:
      - ./data:/data
```

## 云服务商防火墙配置

### AWS EC2
- Security Groups → Inbound Rules → Add Rule
- Type: Custom TCP, Port: ${SSH_PORT}, Source: 0.0.0.0/0 或特定 IP

### 阿里云 ECS
- 安全组 → 配置规则 → 添加安全组规则
- 协议类型: TCP, 端口范围: ${SSH_PORT}, 授权对象: 0.0.0.0/0

### 腾讯云 CVM
- 安全组 → 入站规则 → 添加规则
- 协议端口: TCP:${SSH_PORT}, 来源: 0.0.0.0/0

## 安全检查清单

- [ ] 系统已更新 (`apt update && apt upgrade`)
- [ ] sudo 用户已创建
- [ ] SSH 端口已修改
- [ ] root 密码登录已禁用
- [ ] Fail2ban 已安装并运行
- [ ] UFW 防火墙已配置
- [ ] 云平台防火墙已开放新端口
- [ ] SSH 密钥已配置（推荐）
- [ ] SSH 登录通知已配置（可选）
- [ ] Docker 端口映射已检查（如适用）

## 故障排除

### 无法 SSH 连接

1. 检查云平台防火墙是否开放端口
2. 检查 UFW 是否允许该端口
3. 通过 VNC/控制台登录检查配置
4. 检查 SSH 服务状态: `systemctl status ssh`

### 被防火墙锁死

1. 通过云平台 VNC/控制台登录
2. 禁用 UFW: `ufw disable`
3. 或添加规则: `ufw allow ${SSH_PORT}/tcp`

### SSH 配置错误

1. 检查语法: `sshd -t`
2. 查看生效配置: `sshd -T | grep -i port`
3. 恢复默认: `rm /etc/ssh/sshd_config.d/99-hardening.conf && systemctl restart ssh`

### Fail2ban 误封

1. 查看被封 IP: `fail2ban-client status sshd`
2. 解封 IP: `fail2ban-client set sshd unbanip <IP>`
3. 添加白名单: 修改 `jail.local` 中的 `ignoreip`
