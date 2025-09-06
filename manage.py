#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import uuid
import subprocess
import argparse
from pathlib import Path

class V2rayManager:
    def __init__(self):
        self.config_file = "/etc/v2ray/config.json"
        self.service_name = "v2ray"
        self.log_dir = "/var/log/v2ray"

    def load_config(self):
        """加载配置文件"""
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载配置文件失败: {e}")
            return None

    def save_config(self, config):
        """保存配置文件"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"保存配置文件失败: {e}")
            return False

    def restart_service(self):
        """重启服务"""
        try:
            subprocess.run(['systemctl', 'restart', self.service_name], check=True)
            print("服务重启成功!")
            return True
        except subprocess.CalledProcessError as e:
            print(f"服务重启失败: {e}")
            return False

    def get_service_status(self):
        """获取服务状态"""
        try:
            result = subprocess.run(['systemctl', 'is-active', self.service_name],
                                  capture_output=True, text=True)
            return result.stdout.strip()
        except:
            return "unknown"

    def add_user(self, email=None):
        """添加新用户"""
        config = self.load_config()
        if not config:
            return False

        new_uuid = str(uuid.uuid4())
        new_user = {
            "id": new_uuid,
            "alterId": 0
        }
        
        if email:
            new_user["email"] = email

        # 添加到第一个inbound的clients中
        if "inbounds" in config and len(config["inbounds"]) > 0:
            if "settings" not in config["inbounds"][0]:
                config["inbounds"][0]["settings"] = {}
            if "clients" not in config["inbounds"][0]["settings"]:
                config["inbounds"][0]["settings"]["clients"] = []
            
            config["inbounds"][0]["settings"]["clients"].append(new_user)
            
            if self.save_config(config):
                print(f"用户添加成功!")
                print(f"UUID: {new_uuid}")
                if email:
                    print(f"Email: {email}")
                return new_uuid
            else:
                print("保存配置失败!")
                return False
        else:
            print("配置文件格式错误!")
            return False

    def remove_user(self, user_id):
        """删除用户"""
        config = self.load_config()
        if not config:
            return False

        if "inbounds" in config and len(config["inbounds"]) > 0:
            clients = config["inbounds"][0]["settings"].get("clients", [])
            
            # 查找并删除用户
            original_count = len(clients)
            config["inbounds"][0]["settings"]["clients"] = [
                client for client in clients if client["id"] != user_id
            ]
            
            if len(config["inbounds"][0]["settings"]["clients"]) < original_count:
                if self.save_config(config):
                    print(f"用户 {user_id} 删除成功!")
                    return True
                else:
                    print("保存配置失败!")
                    return False
            else:
                print("未找到指定的用户!")
                return False
        else:
            print("配置文件格式错误!")
            return False

    def list_users(self):
        """列出所有用户"""
        config = self.load_config()
        if not config:
            return

        if "inbounds" in config and len(config["inbounds"]) > 0:
            clients = config["inbounds"][0]["settings"].get("clients", [])
            
            if not clients:
                print("没有找到用户")
                return

            print(f"{'序号':<5} {'UUID':<38} {'Email':<20}")
            print("-" * 65)
            
            for i, client in enumerate(clients, 1):
                email = client.get("email", "N/A")
                print(f"{i:<5} {client['id']:<38} {email:<20}")
        else:
            print("配置文件格式错误!")

    def change_port(self, new_port):
        """修改端口"""
        config = self.load_config()
        if not config:
            return False

        if "inbounds" in config and len(config["inbounds"]) > 0:
            old_port = config["inbounds"][0].get("port", "unknown")
            config["inbounds"][0]["port"] = int(new_port)
            
            if self.save_config(config):
                print(f"端口已从 {old_port} 修改为 {new_port}")
                print("请记得更新防火墙规则!")
                return True
            else:
                print("保存配置失败!")
                return False
        else:
            print("配置文件格式错误!")
            return False

    def show_config(self):
        """显示当前配置"""
        config = self.load_config()
        if not config:
            return

        if "inbounds" in config and len(config["inbounds"]) > 0:
            inbound = config["inbounds"][0]
            port = inbound.get("port", "N/A")
            protocol = inbound.get("protocol", "N/A")
            clients = inbound.get("settings", {}).get("clients", [])
            
            print("="*50)
            print("V2Ray 服务器配置信息")
            print("="*50)
            print(f"协议: {protocol}")
            print(f"端口: {port}")
            print(f"用户数量: {len(clients)}")
            print(f"服务状态: {self.get_service_status()}")
            print("="*50)
        else:
            print("配置文件格式错误!")

    def show_logs(self, log_type="error", lines=50):
        """显示日志"""
        if log_type == "error":
            log_file = f"{self.log_dir}/error.log"
        elif log_type == "access":
            log_file = f"{self.log_dir}/access.log"
        else:
            print("日志类型错误! 支持: error, access")
            return

        try:
            if os.path.exists(log_file):
                subprocess.run(['tail', f'-{lines}', log_file])
            else:
                print(f"日志文件 {log_file} 不存在")
        except Exception as e:
            print(f"读取日志失败: {e}")

def main():
    parser = argparse.ArgumentParser(description='V2Ray 管理工具')
    parser.add_argument('action', choices=['status', 'add-user', 'remove-user', 'list-users', 
                                          'change-port', 'config', 'logs', 'restart'],
                       help='操作类型')
    parser.add_argument('--email', help='用户邮箱 (用于 add-user)')
    parser.add_argument('--uuid', help='用户UUID (用于 remove-user)')
    parser.add_argument('--port', type=int, help='新端口 (用于 change-port)')
    parser.add_argument('--type', choices=['error', 'access'], default='error',
                       help='日志类型 (用于 logs)')
    parser.add_argument('--lines', type=int, default=50, help='显示日志行数')

    args = parser.parse_args()
    manager = V2rayManager()

    # 检查权限
    if os.geteuid() != 0:
        print("请使用root权限运行此脚本!")
        sys.exit(1)

    if args.action == 'status':
        manager.show_config()
    
    elif args.action == 'add-user':
        uuid = manager.add_user(args.email)
        if uuid:
            print("请重启服务以使配置生效: systemctl restart v2ray")
    
    elif args.action == 'remove-user':
        if not args.uuid:
            print("请指定要删除的用户UUID: --uuid <uuid>")
        else:
            if manager.remove_user(args.uuid):
                print("请重启服务以使配置生效: systemctl restart v2ray")
    
    elif args.action == 'list-users':
        manager.list_users()
    
    elif args.action == 'change-port':
        if not args.port:
            print("请指定新端口: --port <port>")
        else:
            if manager.change_port(args.port):
                print("请重启服务以使配置生效: systemctl restart v2ray")
    
    elif args.action == 'config':
        config = manager.load_config()
        if config:
            print(json.dumps(config, indent=2, ensure_ascii=False))
    
    elif args.action == 'logs':
        manager.show_logs(args.type, args.lines)
    
    elif args.action == 'restart':
        manager.restart_service()

if __name__ == "__main__":
    main()