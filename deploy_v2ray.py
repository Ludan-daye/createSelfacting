#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import uuid
import base64
import urllib.request
import tarfile
import zipfile
import subprocess
import platform
import socket
from pathlib import Path
import yaml

class V2rayDeployer:
    def __init__(self):
        self.v2ray_version = "v5.20.0"
        self.install_dir = "/usr/local/v2ray"
        self.config_dir = "/etc/v2ray"
        self.log_dir = "/var/log/v2ray"
        self.config_file = f"{self.config_dir}/config.json"
        self.service_file = "/etc/systemd/system/v2ray.service"
        
        # 生成随机UUID作为用户ID
        self.user_uuid = str(uuid.uuid4())
        self.port = 10086
        self.alter_id = 0
        
    def get_public_ip(self):
        """获取服务器公网IP"""
        try:
            response = urllib.request.urlopen('https://ipinfo.io/ip', timeout=10)
            return response.read().decode().strip()
        except:
            try:
                response = urllib.request.urlopen('https://api.ipify.org', timeout=10)
                return response.read().decode().strip()
            except:
                return "YOUR_SERVER_IP"

    def detect_architecture(self):
        """检测系统架构"""
        arch = platform.machine().lower()
        if arch in ['x86_64', 'amd64']:
            return 'linux-64'
        elif arch in ['aarch64', 'arm64']:
            return 'linux-arm64-v8a'
        elif arch.startswith('arm'):
            return 'linux-arm32-v7a'
        else:
            raise Exception(f"不支持的架构: {arch}")

    def download_v2ray(self):
        """下载v2ray核心文件"""
        arch = self.detect_architecture()
        filename = f"v2ray-{arch}.zip"
        url = f"https://github.com/v2fly/v2ray-core/releases/download/{self.v2ray_version}/{filename}"
        
        print(f"正在下载v2ray {self.v2ray_version} for {arch}...")
        
        try:
            urllib.request.urlretrieve(url, filename)
            print("下载完成!")
            return filename
        except Exception as e:
            print(f"下载失败: {e}")
            print("尝试使用镜像源...")
            mirror_url = f"https://ghproxy.com/{url}"
            urllib.request.urlretrieve(mirror_url, filename)
            print("镜像源下载完成!")
            return filename

    def install_v2ray(self):
        """安装v2ray"""
        filename = self.download_v2ray()
        
        # 创建目录
        os.makedirs(self.install_dir, exist_ok=True)
        os.makedirs(self.config_dir, exist_ok=True)
        os.makedirs(self.log_dir, exist_ok=True)
        
        # 解压文件
        print("正在解压v2ray...")
        with zipfile.ZipFile(filename, 'r') as zip_ref:
            zip_ref.extractall(self.install_dir)
        
        # 设置执行权限
        v2ray_bin = os.path.join(self.install_dir, 'v2ray')
        os.chmod(v2ray_bin, 0o755)
        
        # 删除下载的压缩包
        os.remove(filename)
        
        print(f"v2ray已安装到: {self.install_dir}")

    def generate_config(self):
        """生成v2ray配置文件"""
        config = {
            "log": {
                "access": f"{self.log_dir}/access.log",
                "error": f"{self.log_dir}/error.log",
                "loglevel": "warning"
            },
            "inbounds": [
                {
                    "port": self.port,
                    "protocol": "vmess",
                    "settings": {
                        "clients": [
                            {
                                "id": self.user_uuid,
                                "alterId": self.alter_id
                            }
                        ]
                    },
                    "streamSettings": {
                        "network": "tcp",
                        "tcpSettings": {
                            "header": {
                                "type": "http",
                                "request": {
                                    "version": "1.1",
                                    "method": "GET",
                                    "path": ["/"],
                                    "headers": {
                                        "Host": ["www.cloudflare.com", "www.amazon.com"],
                                        "User-Agent": [
                                            "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.75 Safari/537.36",
                                            "Mozilla/5.0 (iPhone; CPU iPhone OS 10_0_2 like Mac OS X) AppleWebKit/601.1 (KHTML, like Gecko) CriOS/53.0.2785.109 Mobile/14A456 Safari/601.1.46"
                                        ],
                                        "Accept-Encoding": ["gzip, deflate"],
                                        "Connection": ["keep-alive"],
                                        "Pragma": "no-cache"
                                    }
                                }
                            }
                        }
                    }
                }
            ],
            "outbounds": [
                {
                    "protocol": "freedom",
                    "settings": {}
                }
            ]
        }
        
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        print(f"配置文件已生成: {self.config_file}")

    def create_systemd_service(self):
        """创建systemd服务"""
        service_content = f"""[Unit]
Description=V2Ray Service
Documentation=https://www.v2ray.com/
After=network.target nss-lookup.target

[Service]
User=root
CapabilityBoundingSet=CAP_NET_ADMIN CAP_NET_BIND_SERVICE
AmbientCapabilities=CAP_NET_ADMIN CAP_NET_BIND_SERVICE
NoNewPrivileges=true
ExecStart={self.install_dir}/v2ray run -config {self.config_file}
Restart=on-failure
RestartPreventExitStatus=23

[Install]
WantedBy=multi-user.target
"""
        
        with open(self.service_file, 'w') as f:
            f.write(service_content)
        
        print(f"Systemd服务文件已创建: {self.service_file}")

    def generate_vmess_link(self, server_ip):
        """生成vmess链接"""
        vmess_config = {
            "v": "2",
            "ps": f"V2Ray-{server_ip}",
            "add": server_ip,
            "port": self.port,
            "id": self.user_uuid,
            "aid": self.alter_id,
            "net": "tcp",
            "type": "http",
            "host": "",
            "path": "",
            "tls": ""
        }
        
        json_str = json.dumps(vmess_config, separators=(',', ':'))
        encoded = base64.b64encode(json_str.encode()).decode()
        return f"vmess://{encoded}"

    def generate_clash_config(self, server_ip):
        """生成Clash配置"""
        clash_config = {
            "mixed-port": 7890,
            "allow-lan": False,
            "mode": "Rule",
            "log-level": "info",
            "ipv6": False,
            "dns": {
                "enable": True,
                "ipv6": False,
                "listen": "0.0.0.0:53",
                "enhanced-mode": "fake-ip",
                "fake-ip-range": "198.18.0.1/16",
                "fake-ip-filter": [
                    "*.lan",
                    "localhost.ptlogin2.qq.com"
                ],
                "nameserver": [
                    "119.29.29.29",
                    "223.5.5.5"
                ]
            },
            "proxies": [
                {
                    "name": f"V2Ray-{server_ip}",
                    "type": "vmess",
                    "server": server_ip,
                    "port": self.port,
                    "uuid": self.user_uuid,
                    "alterId": self.alter_id,
                    "cipher": "auto",
                    "network": "tcp",
                    "http-opts": {
                        "method": "GET",
                        "path": ["/"],
                        "headers": {
                            "Connection": ["keep-alive"]
                        }
                    }
                }
            ],
            "proxy-groups": [
                {
                    "name": "Proxy",
                    "type": "select",
                    "proxies": [f"V2Ray-{server_ip}", "DIRECT"]
                }
            ],
            "rules": [
                "DOMAIN-SUFFIX,google.com,Proxy",
                "DOMAIN-SUFFIX,youtube.com,Proxy",
                "DOMAIN-SUFFIX,github.com,Proxy",
                "DOMAIN-SUFFIX,twitter.com,Proxy",
                "DOMAIN-SUFFIX,facebook.com,Proxy",
                "GEOIP,CN,DIRECT",
                "MATCH,Proxy"
            ]
        }
        
        return yaml.dump(clash_config, allow_unicode=True, default_flow_style=False)

    def generate_v2rayng_config(self, server_ip):
        """生成V2RayNG配置"""
        config = {
            "policy": {},
            "log": {
                "access": "",
                "error": "",
                "loglevel": "warning"
            },
            "inbounds": [
                {
                    "tag": "socks",
                    "port": 10808,
                    "listen": "127.0.0.1",
                    "protocol": "socks",
                    "sniffing": {
                        "enabled": True,
                        "destOverride": ["http", "tls"]
                    },
                    "settings": {
                        "auth": "noauth",
                        "udp": True,
                        "userLevel": 8
                    }
                },
                {
                    "tag": "http",
                    "port": 10809,
                    "listen": "127.0.0.1",
                    "protocol": "http",
                    "sniffing": {
                        "enabled": True,
                        "destOverride": ["http", "tls"]
                    },
                    "settings": {
                        "userLevel": 8
                    }
                }
            ],
            "outbounds": [
                {
                    "tag": "proxy",
                    "protocol": "vmess",
                    "settings": {
                        "vnext": [
                            {
                                "address": server_ip,
                                "port": self.port,
                                "users": [
                                    {
                                        "id": self.user_uuid,
                                        "alterId": self.alter_id,
                                        "email": "t@t.tt",
                                        "security": "auto"
                                    }
                                ]
                            }
                        ]
                    },
                    "streamSettings": {
                        "network": "tcp",
                        "tcpSettings": {
                            "header": {
                                "type": "http",
                                "request": {
                                    "version": "1.1",
                                    "method": "GET",
                                    "path": ["/"],
                                    "headers": {
                                        "Host": ["www.cloudflare.com", "www.amazon.com"],
                                        "User-Agent": [
                                            "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.75 Safari/537.36",
                                            "Mozilla/5.0 (iPhone; CPU iPhone OS 10_0_2 like Mac OS X) AppleWebKit/601.1 (KHTML, like Gecko) CriOS/53.0.2785.109 Mobile/14A456 Safari/601.1.46"
                                        ],
                                        "Accept-Encoding": ["gzip, deflate"],
                                        "Connection": ["keep-alive"],
                                        "Pragma": "no-cache"
                                    }
                                }
                            }
                        }
                    },
                    "mux": {
                        "enabled": False,
                        "concurrency": -1
                    }
                },
                {
                    "tag": "direct",
                    "protocol": "freedom",
                    "settings": {}
                },
                {
                    "tag": "blocked",
                    "protocol": "blackhole",
                    "settings": {
                        "response": {
                            "type": "http"
                        }
                    }
                }
            ],
            "routing": {
                "domainStrategy": "IPIfNonMatch",
                "rules": []
            }
        }
        
        return json.dumps(config, indent=2, ensure_ascii=False)

    def generate_surge_config(self, server_ip):
        """生成Surge配置"""
        surge_config = f"""[General]
loglevel = notify
dns-server = 119.29.29.29, 223.5.5.5
skip-proxy = 127.0.0.1, 192.168.0.0/16, 10.0.0.0/8, 172.16.0.0/12, 100.64.0.0/10, localhost, *.local

[Proxy]
V2Ray = vmess, {server_ip}, {self.port}, username={self.user_uuid}, alter-id={self.alter_id}, tfo=false

[Proxy Group]
Proxy = select, V2Ray, DIRECT

[Rule]
DOMAIN-SUFFIX,google.com,Proxy
DOMAIN-SUFFIX,youtube.com,Proxy
DOMAIN-SUFFIX,github.com,Proxy
DOMAIN-SUFFIX,twitter.com,Proxy
DOMAIN-SUFFIX,facebook.com,Proxy
GEOIP,CN,DIRECT
FINAL,Proxy
"""
        return surge_config

    def save_configs(self, server_ip):
        """保存所有配置文件"""
        configs_dir = "client_configs"
        os.makedirs(configs_dir, exist_ok=True)
        
        # VMess链接
        vmess_link = self.generate_vmess_link(server_ip)
        with open(f"{configs_dir}/vmess_link.txt", 'w') as f:
            f.write(vmess_link)
        
        # Clash配置
        clash_config = self.generate_clash_config(server_ip)
        with open(f"{configs_dir}/clash.yaml", 'w', encoding='utf-8') as f:
            f.write(clash_config)
        
        # V2RayNG配置
        v2rayng_config = self.generate_v2rayng_config(server_ip)
        with open(f"{configs_dir}/v2rayng.json", 'w', encoding='utf-8') as f:
            f.write(v2rayng_config)
        
        # Surge配置
        surge_config = self.generate_surge_config(server_ip)
        with open(f"{configs_dir}/surge.conf", 'w', encoding='utf-8') as f:
            f.write(surge_config)
        
        # 连接信息
        info = f"""V2Ray服务器信息:
服务器地址: {server_ip}
端口: {self.port}
用户ID(UUID): {self.user_uuid}
额外ID: {self.alter_id}
传输协议: TCP
伪装类型: HTTP
伪装域名: www.cloudflare.com

VMess链接:
{vmess_link}

客户端配置文件已保存到 client_configs 目录:
- vmess_link.txt (VMess订阅链接)
- clash.yaml (Clash配置文件)
- v2rayng.json (V2RayNG配置文件)
- surge.conf (Surge配置文件)
"""
        
        with open(f"{configs_dir}/connection_info.txt", 'w', encoding='utf-8') as f:
            f.write(info)
        
        return info

    def start_service(self):
        """启动v2ray服务"""
        try:
            subprocess.run(['systemctl', 'daemon-reload'], check=True)
            subprocess.run(['systemctl', 'enable', 'v2ray'], check=True)
            subprocess.run(['systemctl', 'start', 'v2ray'], check=True)
            
            status = subprocess.run(['systemctl', 'is-active', 'v2ray'], 
                                  capture_output=True, text=True)
            if status.stdout.strip() == 'active':
                print("V2Ray服务启动成功!")
                return True
            else:
                print("V2Ray服务启动失败!")
                return False
        except subprocess.CalledProcessError as e:
            print(f"启动服务时出错: {e}")
            return False

    def deploy(self):
        """执行完整部署"""
        print("开始部署V2Ray...")
        
        # 检查是否为root用户
        if os.geteuid() != 0:
            print("请使用root权限运行此脚本!")
            sys.exit(1)
        
        try:
            # 安装v2ray
            self.install_v2ray()
            
            # 生成配置文件
            self.generate_config()
            
            # 创建systemd服务
            self.create_systemd_service()
            
            # 启动服务
            if self.start_service():
                # 获取公网IP并生成客户端配置
                server_ip = self.get_public_ip()
                info = self.save_configs(server_ip)
                
                print("\n" + "="*50)
                print("部署完成!")
                print("="*50)
                print(info)
                print("="*50)
                
                return True
            else:
                print("服务启动失败，请检查日志!")
                return False
                
        except Exception as e:
            print(f"部署过程中出错: {e}")
            return False

if __name__ == "__main__":
    deployer = V2rayDeployer()
    deployer.deploy()