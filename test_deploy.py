#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import json
import tempfile
import shutil
from deploy_v2ray import V2rayDeployer

def test_config_generation():
    """测试配置文件生成"""
    print("测试配置文件生成...")
    
    # 创建临时目录用于测试
    test_dir = tempfile.mkdtemp()
    
    try:
        deployer = V2rayDeployer()
        deployer.config_dir = test_dir
        deployer.config_file = os.path.join(test_dir, "config.json")
        
        # 生成配置文件
        deployer.generate_config()
        
        # 检查文件是否生成
        if os.path.exists(deployer.config_file):
            print("✓ 配置文件生成成功")
            
            # 读取并验证JSON格式
            with open(deployer.config_file, 'r') as f:
                config = json.load(f)
            
            # 验证必要的配置项
            required_keys = ['log', 'inbounds', 'outbounds']
            for key in required_keys:
                if key in config:
                    print(f"✓ 找到必要的配置项: {key}")
                else:
                    print(f"✗ 缺少配置项: {key}")
                    return False
            
            # 验证inbound配置
            inbound = config['inbounds'][0]
            if inbound['protocol'] == 'vmess' and 'clients' in inbound['settings']:
                print("✓ VMess协议配置正确")
                client = inbound['settings']['clients'][0]
                if 'id' in client and len(client['id']) == 36:  # UUID长度
                    print("✓ UUID格式正确")
                else:
                    print("✗ UUID格式错误")
                    return False
            else:
                print("✗ VMess协议配置错误")
                return False
            
            print("✓ 配置文件验证通过")
            return True
        else:
            print("✗ 配置文件生成失败")
            return False
            
    except Exception as e:
        print(f"✗ 配置文件测试失败: {e}")
        return False
    finally:
        # 清理临时目录
        shutil.rmtree(test_dir, ignore_errors=True)

def test_client_configs():
    """测试客户端配置生成"""
    print("\n测试客户端配置生成...")
    
    test_dir = tempfile.mkdtemp()
    
    try:
        deployer = V2rayDeployer()
        test_ip = "1.2.3.4"
        
        # 更改工作目录到测试目录
        old_cwd = os.getcwd()
        os.chdir(test_dir)
        
        # 生成客户端配置
        info = deployer.save_configs(test_ip)
        
        # 检查生成的文件
        expected_files = [
            'client_configs/vmess_link.txt',
            'client_configs/clash.yaml',
            'client_configs/v2rayng.json',
            'client_configs/surge.conf',
            'client_configs/connection_info.txt'
        ]
        
        all_files_exist = True
        for file_path in expected_files:
            if os.path.exists(file_path):
                print(f"✓ 生成文件: {file_path}")
            else:
                print(f"✗ 缺少文件: {file_path}")
                all_files_exist = False
        
        # 验证VMess链接格式
        with open('client_configs/vmess_link.txt', 'r') as f:
            vmess_link = f.read().strip()
            if vmess_link.startswith('vmess://'):
                print("✓ VMess链接格式正确")
            else:
                print("✗ VMess链接格式错误")
                all_files_exist = False
        
        # 验证JSON配置文件
        with open('client_configs/v2rayng.json', 'r') as f:
            v2ray_config = json.load(f)
            if 'outbounds' in v2ray_config and len(v2ray_config['outbounds']) > 0:
                print("✓ V2RayNG配置文件格式正确")
            else:
                print("✗ V2RayNG配置文件格式错误")
                all_files_exist = False
        
        if all_files_exist:
            print("✓ 所有客户端配置文件生成成功")
            return True
        else:
            print("✗ 客户端配置文件生成不完整")
            return False
            
    except Exception as e:
        print(f"✗ 客户端配置测试失败: {e}")
        return False
    finally:
        os.chdir(old_cwd)
        shutil.rmtree(test_dir, ignore_errors=True)

def test_architecture_detection():
    """测试系统架构检测"""
    print("\n测试系统架构检测...")
    
    try:
        deployer = V2rayDeployer()
        arch = deployer.detect_architecture()
        print(f"✓ 检测到系统架构: {arch}")
        
        # 验证架构格式
        valid_archs = ['linux-64', 'linux-arm64-v8a', 'linux-arm32-v7a']
        if arch in valid_archs:
            print("✓ 架构检测结果有效")
            return True
        else:
            print(f"✗ 未知的架构: {arch}")
            return False
            
    except Exception as e:
        print(f"✗ 架构检测失败: {e}")
        return False

def test_service_file_generation():
    """测试systemd服务文件生成"""
    print("\n测试systemd服务文件生成...")
    
    test_file = tempfile.mktemp()
    
    try:
        deployer = V2rayDeployer()
        deployer.service_file = test_file
        
        deployer.create_systemd_service()
        
        if os.path.exists(test_file):
            with open(test_file, 'r') as f:
                content = f.read()
                
            # 检查必要的systemd配置项
            required_sections = ['[Unit]', '[Service]', '[Install]']
            for section in required_sections:
                if section in content:
                    print(f"✓ 找到systemd配置段: {section}")
                else:
                    print(f"✗ 缺少systemd配置段: {section}")
                    return False
            
            # 检查关键配置
            if 'ExecStart=' in content and 'v2ray' in content:
                print("✓ ExecStart配置正确")
            else:
                print("✗ ExecStart配置错误")
                return False
                
            print("✓ systemd服务文件生成成功")
            return True
        else:
            print("✗ systemd服务文件生成失败")
            return False
            
    except Exception as e:
        print(f"✗ systemd服务文件测试失败: {e}")
        return False
    finally:
        if os.path.exists(test_file):
            os.remove(test_file)

def main():
    """运行所有测试"""
    print("V2Ray部署脚本功能测试")
    print("=" * 40)
    
    tests = [
        test_architecture_detection,
        test_config_generation,
        test_service_file_generation,
        test_client_configs,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 40)
    print(f"测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("✓ 所有测试通过！脚本功能正常")
        return True
    else:
        print("✗ 部分测试失败，请检查代码")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)