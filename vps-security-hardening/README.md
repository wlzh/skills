# VPS Security Hardening

> VPS 安全加固自动化工具
> 版本: 1.0.1 | 作者: github.com/wlzh | 参考: https://x.com/gxjdian/status/2033751314208059507

## 概述

自动化 VPS 安全加固流程，基于「7招安全加固」最佳实践。

## 功能

| Phase | 功能 | 说明 |
|-------|------|------|
| 1 | SSH 连接测试 | 检测 root 密码登录 |
| 2 | 系统更新 | apt update && apt upgrade |
| 3 | 安装依赖 | sudo, ufw, fail2ban |
| 4 | 创建 sudo 用户 | 禁用 root 密码登录 |
| 5 | SSH 安全配置 | 端口、密钥登录、超时 |
| 6 | Fail2ban | 防暴力破解 (可选) |
| 7 | SSH 配置验证 | 检查配置正确性 |
| 8 | UFW 防火墙 | 开放新端口，删除 22 |
| 9 | 重启服务 | ssh, fail2ban |
| 10 | Docker 安全检查 | 检测暴露端口容器 |

## 使用方法

```bash
./scripts/harden-vps.sh \
  --ip <VPS_IP> \
  --root-pass <ROOT_PASSWORD> \
  --user <NEW_USER> \
  --user-pass <NEW_USER_PASSWORD> \
  --port <SSH_PORT>
```

### 可选参数

- `--no-fail2ban` - 跳过 Fail2ban 安装
- `--with-notify` - 配置 SSH 登录通知 (需要 webhook URL)

## 前置条件

### 1. 开启 root 密码登录

如果 VPS 不支持 root 密码登录，请先通过 VNC/控制台 执行：

```bash
sed -i 's/^#\?PasswordAuthentication.*/PasswordAuthentication yes/' /etc/ssh/sshd_config
sed -i 's/^#\?PermitRootLogin.*/PermitRootLogin yes/' /etc/ssh/sshd_config
systemctl restart ssh
passwd root
```

### 2. 安装 sshpass (本地)

```bash
# macOS
brew install hudochenkov/sshpass/sshpass

# Ubuntu/Debian
sudo apt install sshpass -y

# CentOS/RHEL
sudo yum install sshpass -y
```

## 更新日志

### v1.0.1 (2026-03-17)
- 新增 Phase 10: Docker 安全检查
- 改进 UFW 22 端口删除逻辑 (多种方式 + 验证)
- 修复 sshpass 密码传递问题 (改用 -e 环境变量)
- 添加前置条件检查提示

### v1.0.0 (2026-03-17)
- 初始版本
- 7 招安全加固功能

## 安全提醒

1. **VPS 平台防火墙** - 确保已开放新 SSH 端口
2. **SSH 密钥登录** - 建议配置后禁用密码认证
3. **Docker 安全** - Docker 会绕过 UFW，注意端口暴露

## License

MIT
