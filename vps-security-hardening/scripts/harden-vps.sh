#!/bin/bash
#
# VPS Security Hardening Script
# Author: github.com/wlzh
# Version: 1.0.0
# Date: 2026-03-17
# Reference: https://x.com/gxjdian/status/2033751314208059507
#
# Usage:
#   ./harden-vps.sh --ip <IP> --root-pass <PASSWORD> --user <USERNAME> --user-pass <PASSWORD> --port <PORT>
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Default values
VPS_IP=""
ROOT_PASS=""
NEW_USER=""
NEW_USER_PASS=""
SSH_PORT=""
INSTALL_FAIL2BAN=true
CONFIGURE_NOTIFY=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --ip) VPS_IP="$2"; shift 2 ;;
        --root-pass) ROOT_PASS="$2"; shift 2 ;;
        --user) NEW_USER="$2"; shift 2 ;;
        --user-pass) NEW_USER_PASS="$2"; shift 2 ;;
        --port) SSH_PORT="$2"; shift 2 ;;
        --no-fail2ban) INSTALL_FAIL2BAN=false; shift ;;
        --with-notify) CONFIGURE_NOTIFY=true; shift ;;
        --help|-h) 
            echo "Usage: $0 --ip <IP> --root-pass <PASSWORD> --user <USERNAME> --user-pass <PASSWORD> --port <PORT>"
            echo ""
            echo "Options:"
            echo "  --no-fail2ban    Skip fail2ban installation"
            echo "  --with-notify    Configure SSH login notification (requires webhook URL)"
            exit 0
            ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

# Validate required parameters
if [[ -z "$VPS_IP" || -z "$ROOT_PASS" || -z "$NEW_USER" || -z "$NEW_USER_PASS" || -z "$SSH_PORT" ]]; then
    echo -e "${RED}Error: Missing required parameters${NC}"
    echo "Usage: $0 --ip <IP> --root-pass <PASSWORD> --user <USERNAME> --user-pass <PASSWORD> --port <PORT>"
    exit 1
fi

# Check sshpass
if ! command -v sshpass &> /dev/null; then
    echo -e "${RED}Error: sshpass is not installed${NC}"
    echo "Install with:"
    echo "  macOS: brew install hudochenkov/sshpass/sshpass"
    echo "  Ubuntu/Debian: sudo apt install sshpass -y"
    echo "  CentOS/RHEL: sudo yum install sshpass -y"
    exit 1
fi

# SSH command prefix - use environment variable for password (more reliable)
SSHPASS_BIN=$(which sshpass 2>/dev/null || echo "/usr/local/bin/sshpass")
export SSHPASS="${ROOT_PASS}"
SSH_CMD="${SSHPASS_BIN} -e ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null root@${VPS_IP}"

echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}        VPS Security Hardening Script v1.0.0               ${NC}"
echo -e "${CYAN}        Author: github.com/wlzh                            ${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo ""

# ============================================
# Pre-flight Check: Root Password Login
# ============================================
echo -e "${RED}══════════════════════════════════════════════════════════${NC}"
echo -e "${RED}  🔴 前置条件检查：root 密码登录${NC}"
echo -e "${RED}══════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${YELLOW}如果 VPS 不支持 root 密码登录，请先通过 VNC/控制台 执行以下命令：${NC}"
echo ""
echo -e "  ${CYAN}sed -i 's/^#\\?PasswordAuthentication.*/PasswordAuthentication yes/' /etc/ssh/sshd_config${NC}"
echo -e "  ${CYAN}sed -i 's/^#\\?PermitRootLogin.*/PermitRootLogin yes/' /etc/ssh/sshd_config${NC}"
echo -e "  ${CYAN}systemctl restart ssh${NC}"
echo -e "  ${CYAN}passwd root${NC}"
echo ""
echo -e "${YELLOW}执行完成后，按 Enter 继续...（Ctrl+C 取消）${NC}"
# Auto-continue in non-interactive mode
if [ -t 0 ]; then
    read -r
else
    echo "(Auto-continuing...)"
fi

# ============================================
# Phase 1: Test SSH Connection & Detect OS
# ============================================
echo -e "${YELLOW}[Phase 1/9] Testing SSH connection & detecting OS...${NC}"
if ! $SSH_CMD "echo 'SSH connection successful'" 2>/dev/null; then
    echo -e "${RED}Error: Cannot connect to VPS via SSH${NC}"
    echo -e "${YELLOW}Possible reasons:${NC}"
    echo "  1. Root password login is disabled"
    echo "  2. Wrong password"
    echo "  3. Firewall blocking port 22"
    echo ""
    echo -e "${YELLOW}If root password login is disabled, enable it via VPS console:${NC}"
    echo "  sed -i 's/^#\\?PasswordAuthentication.*/PasswordAuthentication yes/' /etc/ssh/sshd_config"
    echo "  sed -i 's/^#\\?PermitRootLogin.*/PermitRootLogin yes/' /etc/ssh/sshd_config"
    echo "  systemctl restart ssh"
    echo "  passwd root"
    exit 1
fi
echo -e "${GREEN}[✓] SSH connection successful${NC}"

# Detect Ubuntu version
UBUNTU_VERSION=$($SSH_CMD "lsb_release -rs 2>/dev/null || cat /etc/os-release | grep VERSION_ID | cut -d'\"' -f2")
UBUNTU_MAJOR=$(echo "$UBUNTU_VERSION" | cut -d'.' -f1)
echo -e "${CYAN}[i] Detected Ubuntu version: ${UBUNTU_VERSION}${NC}"

if [[ "$UBUNTU_MAJOR" -ge 22 && "$UBUNTU_MAJOR" -le 23 ]]; then
    echo -e "${YELLOW}[i] Ubuntu 22.10-23.10 detected, will use socket activation workaround${NC}"
    USE_SOCKET_ACTIVATION=true
else
    USE_SOCKET_ACTIVATION=false
fi

# ============================================
# Phase 2: System Update
# ============================================
echo -e "${YELLOW}[Phase 2/9] Updating system packages...${NC}"
$SSH_CMD "apt update -qq && apt upgrade -y -qq" || {
    echo -e "${RED}Error: System update failed${NC}"
    exit 1
}
echo -e "${GREEN}[✓] System updated${NC}"

# ============================================
# Phase 3: Install Required Packages
# ============================================
echo -e "${YELLOW}[Phase 3/9] Checking required packages...${NC}"
$SSH_CMD "
    which sudo || apt install sudo -y -qq
    which ufw || apt install ufw -y -qq
    which fail2ban-client || apt install fail2ban -y -qq
    echo 'Packages installed'
"
echo -e "${GREEN}[✓] Required packages installed${NC}"

# ============================================
# Phase 4: Create Sudo User
# ============================================
echo -e "${YELLOW}[Phase 4/9] Creating sudo user: ${NEW_USER}...${NC}"
$SSH_CMD "
    # Check if user exists
    if id '${NEW_USER}' &>/dev/null; then
        echo 'User ${NEW_USER} already exists'
    else
        useradd -m -G sudo -s /bin/bash '${NEW_USER}'
        echo '${NEW_USER}:${NEW_USER_PASS}' | chpasswd
        echo 'User ${NEW_USER} created'
    fi
    id '${NEW_USER}'
"
echo -e "${GREEN}[✓] User ${NEW_USER} created${NC}"

# ============================================
# Phase 5: Configure SSH
# ============================================
echo -e "${YELLOW}[Phase 5/9] Configuring SSH security...${NC}"

if [ "$USE_SOCKET_ACTIVATION" = true ]; then
    # Ubuntu 22.10-23.10: Use socket activation config
    $SSH_CMD "
        # Create socket override directory
        mkdir -p /etc/systemd/system/ssh.socket.d
        
        # Create listen config
        cat > /etc/systemd/system/ssh.socket.d/listen.conf << 'SSHEOF'
[Socket]
ListenStream=
ListenStream=${SSH_PORT}
SSHEOF

        # Disable socket activation, use traditional service
        systemctl disable --now ssh.socket 2>/dev/null || true
        systemctl enable --now ssh.service 2>/dev/null || true

        echo 'Socket activation configured'
    "
fi

# Create SSH hardening config (works for all versions)
$SSH_CMD "
    # Backup existing cloud configs
    for f in /etc/ssh/sshd_config.d/*.conf; do
        if [ -f \"\$f\" ] && [ \"\$f\" != \"/etc/ssh/sshd_config.d/99-hardening.conf\" ]; then
            mv \"\$f\" \"\$f.bak\" 2>/dev/null || true
        fi
    done

    # Create hardening config
    mkdir -p /etc/ssh/sshd_config.d
    cat > /etc/ssh/sshd_config.d/99-hardening.conf << 'SSHEOF'
# VPS Security Hardening - generated by vps-security-hardening skill
# Author: github.com/wlzh
# Version: 1.0.0
# Date: $(date +%Y-%m-%d)

Port ${SSH_PORT}
PermitRootLogin prohibit-password
PasswordAuthentication yes
PubkeyAuthentication yes
MaxAuthTries 3
ClientAliveInterval 300
ClientAliveCountMax 2
SSHEOF

    # Validate SSH config
    sshd -t && echo 'SSH config validated'
"
echo -e "${GREEN}[✓] SSH configuration created${NC}"

# ============================================
# Phase 6: Configure Fail2ban
# ============================================
if [ "$INSTALL_FAIL2BAN" = true ]; then
    echo -e "${YELLOW}[Phase 6/9] Configuring Fail2ban...${NC}"
    $SSH_CMD "
        # Create jail.local config
        cat > /etc/fail2ban/jail.local << 'F2BEOF'
[sshd]
ignoreip = 127.0.0.1/8
enabled = true
filter = sshd
port = ${SSH_PORT}
maxretry = 5
findtime = 300
bantime = 600
logpath = /var/log/auth.log
action = %(action_)s
F2BEOF

        # Enable and start fail2ban
        systemctl enable fail2ban 2>/dev/null || true
        systemctl restart fail2ban
        systemctl is-active fail2ban
    "
    echo -e "${GREEN}[✓] Fail2ban configured${NC}"
else
    echo -e "${YELLOW}[Phase 6/9] Skipping Fail2ban (--no-fail2ban)${NC}"
fi

# ============================================
# Phase 7: Verify SSH Config
# ============================================
echo -e "${YELLOW}[Phase 7/9] Verifying SSH configuration...${NC}"
SSH_VERIFY=$($SSH_CMD "sshd -T | grep -iE '^(port|permitrootlogin|passwordauthentication|pubkeyauthentication) '")
echo "$SSH_VERIFY"

# Check values
PORT_CHECK=$(echo "$SSH_VERIFY" | grep -i "^port " | awk '{print $2}')
ROOT_CHECK=$(echo "$SSH_VERIFY" | grep -i "^permitrootlogin " | awk '{print $2}')
PASS_CHECK=$(echo "$SSH_VERIFY" | grep -i "^passwordauthentication " | awk '{print $2}')

if [[ "$PORT_CHECK" != "$SSH_PORT" ]]; then
    echo -e "${RED}Error: SSH port not configured correctly. Expected: $SSH_PORT, Got: $PORT_CHECK${NC}"
    exit 1
fi

if [[ "$ROOT_CHECK" != "prohibit-password" && "$ROOT_CHECK" != "without-password" ]]; then
    echo -e "${YELLOW}Warning: PermitRootLogin is $ROOT_CHECK (expected: prohibit-password)${NC}"
fi

if [[ "$PASS_CHECK" != "yes" ]]; then
    echo -e "${RED}Error: PasswordAuthentication not configured correctly. Expected: yes, Got: $PASS_CHECK${NC}"
    exit 1
fi

echo -e "${GREEN}[✓] SSH configuration verified${NC}"

# ============================================
# Phase 8: Configure UFW Firewall
# ============================================
echo -e "${YELLOW}[Phase 8/9] Configuring UFW firewall...${NC}"

echo -e "${RED}══════════════════════════════════════════════════════════${NC}"
echo -e "${RED}  ⚠️  CRITICAL WARNING ⚠️${NC}"
echo -e "${RED}══════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}Make sure VPS platform firewall has opened port ${SSH_PORT}!${NC}"
echo -e "${YELLOW}Press Ctrl+C to abort if not done yet...${NC}"
echo -e "${RED}══════════════════════════════════════════════════════════${NC}"
sleep 5

$SSH_CMD "
    # Set default policies
    ufw default deny incoming
    ufw default allow outgoing

    # Allow new SSH port BEFORE enabling UFW
    ufw allow ${SSH_PORT}/tcp comment 'SSH custom port'

    # Enable UFW
    ufw --force enable

    # Delete default port 22 - try multiple methods
    # Method 1: Delete by rule name
    ufw --force delete allow 22 2>/dev/null || true
    ufw --force delete allow 22/tcp 2>/dev/null || true
    
    # Method 2: Delete by rule number (find and delete)
    for rule_num in \$(ufw status numbered | grep -E '^\[.*\] 22 ' | grep -oE '^\[ *[0-9]+\]' | tr -d '[]' | sort -rn); do
        ufw --force delete \$rule_num 2>/dev/null || true
    done
    for rule_num in \$(ufw status numbered | grep -E '^\[.*\] 22 \(v6\)' | grep -oE '^\[ *[0-9]+\]' | tr -d '[]' | sort -rn); do
        ufw --force delete \$rule_num 2>/dev/null || true
    done

    # Show status
    ufw status verbose
"
echo -e "${GREEN}[✓] UFW firewall configured${NC}"

# Verify port 22 is removed
UFW_STATUS=$($SSH_CMD "ufw status | grep -E '^22 ' || true")
if [ -n "$UFW_STATUS" ]; then
    echo -e "${RED}══════════════════════════════════════════════════════════${NC}"
    echo -e "${RED}  ⚠️  WARNING: Port 22 is still in UFW rules!${NC}"
    echo -e "${RED}══════════════════════════════════════════════════════════${NC}"
    echo "$UFW_STATUS"
    echo -e "${YELLOW}Please manually remove with: sudo ufw delete allow 22${NC}"
else
    echo -e "${GREEN}[✓] Port 22 removed from UFW${NC}"
fi

# ============================================
# Phase 9: Restart Services
# ============================================
echo -e "${YELLOW}[Phase 9/9] Restarting services...${NC}"
$SSH_CMD "
    systemctl daemon-reload
    systemctl restart ssh.service
    systemctl restart fail2ban 2>/dev/null || true
    echo 'SSH: '\$(systemctl is-active ssh.service)
    echo 'Fail2ban: '\$(systemctl is-active fail2ban 2>/dev/null || echo 'not installed')
"
echo -e "${GREEN}[✓] Services restarted${NC}"

# ============================================
# Phase 10: Docker Security Check & Fix
# ============================================
echo -e "${YELLOW}[Phase 10/10] Checking Docker security...${NC}"
DOCKER_CHECK=$($SSH_CMD "which docker &>/dev/null && echo 'installed' || echo 'not_installed'")

if [ "$DOCKER_CHECK" = "installed" ]; then
    echo -e "${YELLOW}[!] Docker is installed on this VPS${NC}"
    DOCKER_VERSION=$($SSH_CMD "docker --version 2>/dev/null | head -1")
    echo -e "${CYAN}[i] ${DOCKER_VERSION}${NC}"

    # Check if Docker daemon.json exists and has iptables setting
    DOCKER_IPTABLES=$($SSH_CMD "cat /etc/docker/daemon.json 2>/dev/null | grep -c 'iptables' || echo 0")

    if [ "$DOCKER_IPTABLES" -eq 0 ]; then
        echo -e "${YELLOW}[!] Docker is configured to bypass UFW (default behavior)${NC}"
        echo -e "${YELLOW}[i] Configuring Docker to respect UFW firewall...${NC}"

        # Backup existing daemon.json if exists
        $SSH_CMD "if [ -f /etc/docker/daemon.json ]; then sudo cp /etc/docker/daemon.json /etc/docker/daemon.json.bak; fi"

        # Create or update daemon.json
        $SSH_CMD "
            if [ -f /etc/docker/daemon.json ]; then
                # Merge with existing config
                sudo sed -i 's/}/, \"iptables\": false}/' /etc/docker/daemon.json 2>/dev/null || \
                echo '{\"iptables\": false}' | sudo tee /etc/docker/daemon.json
            else
                echo '{\"iptables\": false}' | sudo tee /etc/docker/daemon.json
            fi
        "

        # Restart Docker
        echo -e "${YELLOW}[i] Restarting Docker service...${NC}"
        $SSH_CMD "sudo systemctl restart docker"
        echo -e "${GREEN}[✓] Docker configured to respect UFW firewall${NC}"
    else
        echo -e "${GREEN}[✓] Docker already configured to respect UFW${NC}"
    fi

    # Check if user can access docker (might need sudo)
    DOCKER_TEST=$($SSH_CMD "docker ps &>/dev/null && echo 'ok' || echo 'need_sudo'")

    if [ "$DOCKER_TEST" = "ok" ]; then
        DOCKER_CONTAINERS=$($SSH_CMD "docker ps --format '{{.Names}}' 2>/dev/null | wc -l")
        DOCKER_EXPOSED=$($SSH_CMD "docker ps --format '{{.Ports}}' 2>/dev/null | grep -c '0.0.0.0' || echo 0")
    else
        # Try with sudo
        DOCKER_CONTAINERS=$($SSH_CMD "sudo docker ps --format '{{.Names}}' 2>/dev/null | wc -l")
        DOCKER_EXPOSED=$($SSH_CMD "sudo docker ps --format '{{.Ports}}' 2>/dev/null | grep -c '0.0.0.0' || echo 0")
    fi

    echo -e "${CYAN}[i] Docker containers running: ${DOCKER_CONTAINERS}${NC}"

    if [ "$DOCKER_EXPOSED" -gt 0 ]; then
        echo -e "${RED}══════════════════════════════════════════════════════════${NC}"
        echo -e "${RED}  ⚠️  DOCKER EXPOSED PORTS WARNING ⚠️${NC}"
        echo -e "${RED}══════════════════════════════════════════════════════════${NC}"
        echo -e "${YELLOW}[!] ${DOCKER_EXPOSED} container(s) have ports exposed to 0.0.0.0${NC}"
        echo ""
        echo -e "${CYAN}Exposed containers:${NC}"
        if [ "$DOCKER_TEST" = "ok" ]; then
            $SSH_CMD "docker ps --format '  - {{.Names}}: {{.Ports}}' 2>/dev/null | grep '0.0.0.0'"
        else
            $SSH_CMD "sudo docker ps --format '  - {{.Names}}: {{.Ports}}' 2>/dev/null | grep '0.0.0.0'"
        fi
        echo ""
        echo -e "${YELLOW}Note: Docker now respects UFW. Make sure to add UFW rules for needed ports:${NC}"
        echo "  sudo ufw allow <PORT>/tcp"
        echo -e "${RED}══════════════════════════════════════════════════════════${NC}"
        DOCKER_WARNING="true"
    else
        echo -e "${GREEN}[✓] No containers with exposed ports detected${NC}"
    fi
else
    echo -e "${GREEN}[✓] Docker not installed, skipping security check${NC}"
fi

# ============================================
# Generate Report
# ============================================
echo ""
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}                    VPS 安全加固报告${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "执行时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo -e "VPS IP: ${VPS_IP}"
echo -e "系统版本: $($SSH_CMD "lsb_release -ds 2>/dev/null || cat /etc/os-release | grep PRETTY_NAME | cut -d'\"' -f2")"
echo ""
echo -e "${GREEN}[✓] 系统更新: apt update && apt upgrade 完成${NC}"
echo -e "${GREEN}[✓] 新用户: ${NEW_USER} 已创建并加入 sudo 组${NC}"
echo -e "${GREEN}[✓] SSH 端口: ${SSH_PORT}${NC}"
echo -e "${GREEN}[✓] Root 登录: 仅允许密钥登录 (prohibit-password)${NC}"
echo -e "${GREEN}[✓] 密码认证: 已启用（普通用户）${NC}"
if [ "$INSTALL_FAIL2BAN" = true ]; then
    echo -e "${GREEN}[✓] Fail2ban: 已安装并启动${NC}"
fi
echo -e "${GREEN}[✓] UFW 防火墙: 已启用${NC}"
echo ""
echo -e "${BLUE}────────────────────────────────────────────────────────────${NC}"
echo -e "${BLUE}防火墙状态:${NC}"
$SSH_CMD "ufw status verbose"
echo ""
echo -e "${BLUE}────────────────────────────────────────────────────────────${NC}"
if [ "$INSTALL_FAIL2BAN" = true ]; then
    echo -e "${BLUE}Fail2ban 状态:${NC}"
    $SSH_CMD "fail2ban-client status sshd 2>/dev/null || echo 'Fail2ban sshd jail not active'"
    echo ""
fi
echo -e "${BLUE}────────────────────────────────────────────────────────────${NC}"
echo -e "${BLUE}SSH 配置验证:${NC}"
$SSH_CMD "sshd -T | grep -iE '^(port|permitrootlogin|passwordauthentication|pubkeyauthentication) '"
echo ""
echo -e "${BLUE}────────────────────────────────────────────────────────────${NC}"
echo -e "${BLUE}SSH 服务状态:${NC}"
$SSH_CMD "systemctl is-active ssh.service"
echo ""
if [ "$DOCKER_CHECK" = "installed" ]; then
    echo -e "${BLUE}────────────────────────────────────────────────────────────${NC}"
    echo -e "${BLUE}Docker 状态:${NC}"
    echo -e "  版本: $($SSH_CMD "docker --version 2>/dev/null | head -1")"
    echo -e "  容器数: ${DOCKER_CONTAINERS:-0}"
    if [ "${DOCKER_EXPOSED:-0}" -gt 0 ]; then
        echo -e "  ${RED}暴露端口容器: ${DOCKER_EXPOSED}${NC}"
    else
        echo -e "  ${GREEN}暴露端口容器: 0${NC}"
    fi
    echo ""
fi
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}                    登录信息${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "  ${YELLOW}新登录命令:${NC}"
echo -e "  ${CYAN}ssh -p ${SSH_PORT} ${NEW_USER}@${VPS_IP}${NC}"
echo ""
echo -e "  ${YELLOW}用户名:${NC} ${NEW_USER}"
echo -e "  ${YELLOW}密码:${NC} ${NEW_USER_PASS}"
echo ""
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${RED}                    ⚠️ 重要提醒${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "1. 请确保 VPS 平台防火墙已开放端口 ${SSH_PORT}"
echo -e "2. 建议配置 SSH 密钥登录后禁用密码认证"
echo -e "3. 保存好新用户密码"
echo -e "4. 如使用 Docker，注意端口映射安全："
echo -e "   - 内部服务不暴露端口"
echo -e "   - 反代服务只监听 127.0.0.1"
echo -e "   - Docker 会绕过 UFW 防火墙！"
echo ""
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}           VPS Security Hardening Complete!${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
