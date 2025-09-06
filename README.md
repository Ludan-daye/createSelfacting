# V2Ray 自动部署工具

一个自动化安装和配置 V2Ray 服务端的 Python 脚本，支持自动下载 V2Ray 核心文件、生成配置文件、创建系统服务，并自动生成各种客户端的配置文件。

## 功能特点

- 🚀 **全自动安装**: 一键安装 V2Ray 服务端
- 📦 **内置核心**: 自动下载最新版本的 V2Ray 核心文件
- 🔧 **自动配置**: 自动生成服务端配置文件和系统服务
- 🔗 **多协议支持**: 生成 VMess 协议配置
- 📱 **多客户端支持**: 自动生成 Clash、V2RayNG、Surge 等客户端配置
- 🌐 **智能检测**: 自动检测系统架构和公网IP
- 📊 **完整日志**: 详细的访问和错误日志

## 系统要求

- **操作系统**: Linux (Ubuntu/Debian/CentOS/RHEL/Fedora)
- **权限**: Root 权限
- **Python**: Python 3.6+
- **网络**: 能够访问 GitHub 下载文件

## 快速开始

### 方法一：使用安装脚本

```bash
# 下载项目文件
wget -O v2ray-auto-deploy.tar.gz https://github.com/your-repo/archive/main.tar.gz
tar -xzf v2ray-auto-deploy.tar.gz
cd v2ray-auto-deploy

# 运行安装脚本
sudo bash install.sh
```

### 方法二：直接运行 Python 脚本

```bash
# 安装依赖
sudo apt update && sudo apt install -y python3 python3-pip
sudo pip3 install pyyaml

# 运行部署脚本
sudo python3 deploy_v2ray.py
```

## 配置说明

### 默认配置

- **端口**: 10086
- **协议**: VMess
- **传输**: TCP + HTTP 伪装
- **UUID**: 自动生成
- **额外ID**: 0

### 生成的文件

安装完成后，会在 `client_configs` 目录生成以下配置文件：

```
client_configs/
├── vmess_link.txt          # VMess 订阅链接
├── clash.yaml              # Clash 配置文件
├── v2rayng.json           # V2RayNG 配置文件
├── surge.conf             # Surge 配置文件
└── connection_info.txt    # 连接信息汇总
```

## 客户端配置

### 1. Clash

将 `client_configs/clash.yaml` 文件导入 Clash 客户端，或者复制内容到配置文件中。

### 2. V2RayNG (Android)

1. 打开 V2RayNG
2. 点击右上角 "+"
3. 选择 "从剪贴板导入"
4. 复制 `vmess_link.txt` 中的链接

### 3. V2RayU (macOS)

1. 打开 V2RayU
2. 点击 "服务器" → "添加服务器"
3. 选择 "通过剪贴板导入"
4. 复制 `vmess_link.txt` 中的链接

### 4. Surge

将 `client_configs/surge.conf` 文件导入 Surge，或者复制内容到配置文件中。

### 5. 手动配置

参考 `connection_info.txt` 文件中的连接信息：

- **服务器地址**: 你的服务器 IP
- **端口**: 10086
- **用户ID**: 自动生成的 UUID
- **额外ID**: 0
- **传输协议**: TCP
- **伪装类型**: HTTP

## 服务管理

```bash
# 查看服务状态
systemctl status v2ray

# 启动服务
systemctl start v2ray

# 停止服务
systemctl stop v2ray

# 重启服务
systemctl restart v2ray

# 开机自启
systemctl enable v2ray

# 查看实时日志
journalctl -u v2ray -f

# 查看访问日志
tail -f /var/log/v2ray/access.log

# 查看错误日志
tail -f /var/log/v2ray/error.log
```

## 防火墙配置

如果服务器开启了防火墙，需要开放相应端口：

```bash
# Ubuntu/Debian (ufw)
sudo ufw allow 10086

# CentOS/RHEL (firewalld)
sudo firewall-cmd --permanent --add-port=10086/tcp
sudo firewall-cmd --reload

# CentOS/RHEL (iptables)
sudo iptables -A INPUT -p tcp --dport 10086 -j ACCEPT
sudo service iptables save
```

## 卸载

```bash
# 停止并禁用服务
sudo systemctl stop v2ray
sudo systemctl disable v2ray

# 删除服务文件
sudo rm -f /etc/systemd/system/v2ray.service

# 删除程序文件
sudo rm -rf /usr/local/v2ray
sudo rm -rf /etc/v2ray
sudo rm -rf /var/log/v2ray

# 重新加载 systemd
sudo systemctl daemon-reload
```

## 故障排除

### 1. 服务启动失败

```bash
# 查看详细错误信息
sudo journalctl -u v2ray -n 50

# 检查配置文件语法
/usr/local/v2ray/v2ray test -config /etc/v2ray/config.json

# 手动运行测试
sudo /usr/local/v2ray/v2ray run -config /etc/v2ray/config.json
```

### 2. 客户端无法连接

1. 检查服务器防火墙设置
2. 确认端口没有被占用
3. 验证客户端配置信息是否正确
4. 检查服务器网络连接

### 3. 下载失败

如果 GitHub 访问受限，脚本会自动尝试镜像源下载。

## 安全建议

1. **定期更新**: 定期更新 V2Ray 到最新版本
2. **防火墙**: 只开放必要的端口
3. **监控**: 定期检查日志文件
4. **备份**: 备份配置文件和客户端信息

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request!

## 免责声明

本工具仅供学习和技术研究使用，请遵守当地法律法规。