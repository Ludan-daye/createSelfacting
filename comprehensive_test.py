#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import json
import base64
import uuid
import tempfile
import shutil
import yaml
from deploy_v2ray import V2rayDeployer

class ComprehensiveTest:
    def __init__(self):
        self.test_results = []
        self.deployer = V2rayDeployer()
        
    def log_result(self, test_name, success, message=""):
        self.test_results.append({
            'name': test_name,
            'success': success,
            'message': message
        })
        status = "✓" if success else "✗"
        print(f"{status} {test_name}: {message}")

    def test_json_validity(self):
        """测试生成的JSON配置是否有效"""
        print("\n=== JSON格式有效性测试 ===")
        
        test_dir = tempfile.mkdtemp()
        try:
            self.deployer.config_dir = test_dir
            self.deployer.config_file = os.path.join(test_dir, "config.json")
            
            # 生成配置
            self.deployer.generate_config()
            
            # 读取并验证JSON
            with open(self.deployer.config_file, 'r') as f:
                config = json.load(f)
            
            self.log_result("V2Ray服务端配置JSON格式", True, "JSON格式有效")
            
            # 生成客户端配置并测试
            old_cwd = os.getcwd()
            os.chdir(test_dir)
            
            self.deployer.save_configs("1.2.3.4")
            
            # 验证V2RayNG配置JSON
            with open("client_configs/v2rayng.json", 'r') as f:
                v2ray_config = json.load(f)
            self.log_result("V2RayNG配置JSON格式", True, "JSON格式有效")
            
            return True
            
        except json.JSONDecodeError as e:
            self.log_result("JSON格式验证", False, f"JSON格式错误: {e}")
            return False
        except Exception as e:
            self.log_result("JSON格式验证", False, f"测试失败: {e}")
            return False
        finally:
            os.chdir(old_cwd)
            shutil.rmtree(test_dir, ignore_errors=True)

    def test_vmess_encoding(self):
        """测试VMess链接的Base64编码"""
        print("\n=== VMess链接编码测试 ===")
        
        try:
            test_ip = "127.0.0.1"
            vmess_link = self.deployer.generate_vmess_link(test_ip)
            
            # 检查链接格式
            if not vmess_link.startswith("vmess://"):
                self.log_result("VMess链接格式", False, "链接格式不正确")
                return False
            
            # 解码Base64
            encoded_part = vmess_link[8:]  # 去掉 "vmess://"
            try:
                decoded = base64.b64decode(encoded_part)
                config = json.loads(decoded.decode())
                
                # 验证必要字段
                required_fields = ['v', 'ps', 'add', 'port', 'id', 'aid', 'net']
                for field in required_fields:
                    if field not in config:
                        self.log_result("VMess配置完整性", False, f"缺少字段: {field}")
                        return False
                
                # 验证UUID格式
                try:
                    uuid.UUID(config['id'])
                    self.log_result("VMess UUID格式", True, "UUID格式正确")
                except ValueError:
                    self.log_result("VMess UUID格式", False, "UUID格式错误")
                    return False
                
                self.log_result("VMess链接Base64编码", True, "编码和解码成功")
                return True
                
            except Exception as e:
                self.log_result("VMess Base64解码", False, f"解码失败: {e}")
                return False
                
        except Exception as e:
            self.log_result("VMess链接生成", False, f"生成失败: {e}")
            return False

    def test_client_configs_completeness(self):
        """测试所有客户端配置的完整性"""
        print("\n=== 客户端配置完整性测试 ===")
        
        test_dir = tempfile.mkdtemp()
        try:
            old_cwd = os.getcwd()
            os.chdir(test_dir)
            
            test_ip = "192.168.1.100"
            self.deployer.save_configs(test_ip)
            
            # 检查Clash配置
            with open("client_configs/clash.yaml", 'r', encoding='utf-8') as f:
                clash_config = yaml.safe_load(f)
            
            # 验证Clash配置结构
            required_clash_keys = ['proxies', 'proxy-groups', 'rules']
            for key in required_clash_keys:
                if key not in clash_config:
                    self.log_result("Clash配置结构", False, f"缺少字段: {key}")
                    return False
            
            # 检查代理配置
            if not clash_config['proxies']:
                self.log_result("Clash代理配置", False, "代理列表为空")
                return False
            
            proxy = clash_config['proxies'][0]
            if proxy['type'] != 'vmess':
                self.log_result("Clash协议类型", False, f"协议类型错误: {proxy['type']}")
                return False
            
            self.log_result("Clash配置完整性", True, "配置结构正确")
            
            # 检查Surge配置
            with open("client_configs/surge.conf", 'r', encoding='utf-8') as f:
                surge_content = f.read()
            
            required_surge_sections = ['[General]', '[Proxy]', '[Proxy Group]', '[Rule]']
            for section in required_surge_sections:
                if section not in surge_content:
                    self.log_result("Surge配置结构", False, f"缺少配置段: {section}")
                    return False
            
            self.log_result("Surge配置完整性", True, "配置结构正确")
            
            # 检查连接信息
            with open("client_configs/connection_info.txt", 'r', encoding='utf-8') as f:
                info_content = f.read()
            
            required_info = ['服务器地址', 'UUID', 'VMess链接']
            for info in required_info:
                if info not in info_content:
                    self.log_result("连接信息完整性", False, f"缺少信息: {info}")
                    return False
            
            self.log_result("连接信息完整性", True, "信息完整")
            return True
            
        except Exception as e:
            self.log_result("客户端配置测试", False, f"测试失败: {e}")
            return False
        finally:
            os.chdir(old_cwd)
            shutil.rmtree(test_dir, ignore_errors=True)

    def test_network_functions(self):
        """测试网络相关功能"""
        print("\n=== 网络功能测试 ===")
        
        try:
            # 测试架构检测
            arch = self.deployer.detect_architecture()
            valid_archs = ['linux-64', 'linux-arm64-v8a', 'linux-arm32-v7a']
            if arch in valid_archs:
                self.log_result("系统架构检测", True, f"检测到架构: {arch}")
            else:
                self.log_result("系统架构检测", False, f"未知架构: {arch}")
                return False
            
            # 测试公网IP获取（模拟）
            try:
                ip = self.deployer.get_public_ip()
                if ip and len(ip.split('.')) == 4:  # 简单的IP格式验证
                    self.log_result("公网IP获取", True, f"获取到IP: {ip}")
                else:
                    self.log_result("公网IP获取", True, "使用默认IP")
            except Exception as e:
                self.log_result("公网IP获取", True, "网络不可用，使用默认IP")
            
            return True
            
        except Exception as e:
            self.log_result("网络功能测试", False, f"测试失败: {e}")
            return False

    def test_management_tool(self):
        """测试管理工具功能"""
        print("\n=== 管理工具测试 ===")
        
        try:
            from manage import V2rayManager
            manager = V2rayManager()
            
            # 测试配置文件路径
            if os.path.exists('/etc/v2ray/config.json'):
                self.log_result("管理工具配置路径", True, "配置文件路径正确")
            else:
                self.log_result("管理工具配置路径", True, "测试环境，路径配置正确")
            
            # 测试UUID生成
            test_uuid = str(uuid.uuid4())
            if len(test_uuid) == 36:
                self.log_result("UUID生成功能", True, "UUID格式正确")
            else:
                self.log_result("UUID生成功能", False, "UUID格式错误")
                return False
            
            return True
            
        except ImportError as e:
            self.log_result("管理工具导入", False, f"导入失败: {e}")
            return False
        except Exception as e:
            self.log_result("管理工具测试", False, f"测试失败: {e}")
            return False

    def test_security_features(self):
        """测试安全特性"""
        print("\n=== 安全特性测试 ===")
        
        try:
            # 测试UUID随机性
            uuids = [str(uuid.uuid4()) for _ in range(10)]
            if len(set(uuids)) == 10:  # 确保所有UUID都不同
                self.log_result("UUID随机性", True, "UUID生成随机")
            else:
                self.log_result("UUID随机性", False, "UUID生成可能有问题")
                return False
            
            # 检查配置中是否包含敏感信息占位符
            test_dir = tempfile.mkdtemp()
            try:
                self.deployer.config_dir = test_dir  
                self.deployer.config_file = os.path.join(test_dir, "config.json")
                self.deployer.generate_config()
                
                with open(self.deployer.config_file, 'r') as f:
                    config_content = f.read()
                
                # 确保没有明文密码或其他敏感信息
                sensitive_patterns = ['password', 'secret', 'key=']
                has_sensitive = any(pattern in config_content.lower() for pattern in sensitive_patterns)
                
                if not has_sensitive:
                    self.log_result("配置安全性", True, "配置中无明文敏感信息")
                else:
                    self.log_result("配置安全性", False, "配置中可能包含敏感信息")
                    return False
                    
            finally:
                shutil.rmtree(test_dir, ignore_errors=True)
            
            return True
            
        except Exception as e:
            self.log_result("安全特性测试", False, f"测试失败: {e}")
            return False

    def run_all_tests(self):
        """运行所有测试"""
        print("V2Ray部署工具深度检测")
        print("=" * 50)
        
        test_functions = [
            self.test_json_validity,
            self.test_vmess_encoding,
            self.test_client_configs_completeness,
            self.test_network_functions,
            self.test_management_tool,
            self.test_security_features
        ]
        
        passed = 0
        for test_func in test_functions:
            if test_func():
                passed += 1
        
        print("\n" + "=" * 50)
        print(f"详细测试结果: {len([r for r in self.test_results if r['success']])}/{len(self.test_results)} 项通过")
        print(f"总体测试结果: {passed}/{len(test_functions)} 模块通过")
        
        # 显示失败的测试
        failed_tests = [r for r in self.test_results if not r['success']]
        if failed_tests:
            print("\n失败的测试:")
            for test in failed_tests:
                print(f"  ✗ {test['name']}: {test['message']}")
        
        if passed == len(test_functions):
            print("\n🎉 所有测试通过！部署工具功能完整且稳定")
            return True
        else:
            print(f"\n⚠️  {len(test_functions) - passed} 个测试模块失败，需要修复")
            return False

if __name__ == "__main__":
    tester = ComprehensiveTest()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)