#!/bin/bash

# V2Ray自动安装脚本

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}       V2Ray 自动安装部署脚本${NC}"
echo -e "${GREEN}========================================${NC}"

# 检查是否为root用户
if [[ $EUID -ne 0 ]]; then
   echo -e "${RED}请使用root权限运行此脚本!${NC}"
   echo "使用命令: sudo bash install.sh"
   exit 1
fi

# 检查系统类型
if [[ ! -f /etc/os-release ]]; then
    echo -e "${RED}不支持的操作系统${NC}"
    exit 1
fi

source /etc/os-release

echo -e "${YELLOW}检测到系统: $NAME $VERSION${NC}"

# 安装Python3和pip
echo -e "${YELLOW}安装依赖包...${NC}"

if [[ "$ID" == "ubuntu" || "$ID" == "debian" ]]; then
    apt update
    apt install -y python3 python3-pip wget curl unzip
elif [[ "$ID" == "centos" || "$ID" == "rhel" ]]; then
    yum install -y python3 python3-pip wget curl unzip
elif [[ "$ID" == "fedora" ]]; then
    dnf install -y python3 python3-pip wget curl unzip
else
    echo -e "${YELLOW}未识别的发行版，尝试手动安装依赖...${NC}"
fi

# 安装Python依赖
pip3 install pyyaml

# 运行部署脚本
echo -e "${YELLOW}开始部署V2Ray...${NC}"

if [[ -f "deploy_v2ray.py" ]]; then
    python3 deploy_v2ray.py
else
    echo -e "${RED}未找到部署脚本 deploy_v2ray.py${NC}"
    exit 1
fi

echo -e "${GREEN}安装完成！${NC}"
echo -e "${YELLOW}客户端配置文件已保存在 client_configs 目录中${NC}"
echo -e "${YELLOW}可以使用以下命令管理V2Ray服务:${NC}"
echo "启动服务: systemctl start v2ray"
echo "停止服务: systemctl stop v2ray"
echo "重启服务: systemctl restart v2ray"
echo "查看状态: systemctl status v2ray"
echo "查看日志: journalctl -u v2ray -f"