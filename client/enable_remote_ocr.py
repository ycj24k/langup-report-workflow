#!/usr/bin/env python3
"""
启用远程OCR配置脚本
"""

import os
import sys
from pathlib import Path

def enable_remote_ocr():
    """启用远程OCR配置"""
    
    config_file = Path("src/pdf_ocr_module/config.py")
    
    if not config_file.exists():
        print("❌ 配置文件不存在")
        return False
    
    # 读取配置文件
    with open(config_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 修改配置
    old_config = '"enabled": False,  # 是否启用远程OCR'
    new_config = '"enabled": True,  # 是否启用远程OCR'
    
    if old_config in content:
        content = content.replace(old_config, new_config)
        
        # 写回配置文件
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ 远程OCR配置已启用")
        print("📡 服务器地址: http://192.168.3.133:8888")
        print("🔄 回退机制: 远程失败时自动使用本地OCR")
        return True
    else:
        print("❌ 配置文件中未找到远程OCR配置项")
        return False

def disable_remote_ocr():
    """禁用远程OCR配置"""
    
    config_file = Path("src/pdf_ocr_module/config.py")
    
    if not config_file.exists():
        print("❌ 配置文件不存在")
        return False
    
    # 读取配置文件
    with open(config_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 修改配置
    old_config = '"enabled": True,  # 是否启用远程OCR'
    new_config = '"enabled": False,  # 是否启用远程OCR'
    
    if old_config in content:
        content = content.replace(old_config, new_config)
        
        # 写回配置文件
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ 远程OCR配置已禁用，将使用本地OCR")
        return True
    else:
        print("❌ 配置文件中未找到启用的远程OCR配置项")
        return False

def test_remote_connection():
    """测试远程连接"""
    try:
        import requests
        response = requests.get("http://192.168.3.133:8888/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✅ 远程OCR服务器连接成功")
            print(f"📊 服务器状态: {data}")
            return True
        else:
            print(f"❌ 远程OCR服务器响应异常: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 无法连接到远程OCR服务器: {e}")
        return False

if __name__ == "__main__":
    print("=== 远程OCR配置工具 ===")
    print("1. 启用远程OCR")
    print("2. 禁用远程OCR")
    print("3. 测试远程连接")
    print("4. 退出")
    
    while True:
        choice = input("\n请选择操作 (1-4): ").strip()
        
        if choice == "1":
            if enable_remote_ocr():
                print("\n🔍 测试远程连接...")
                test_remote_connection()
            break
        elif choice == "2":
            disable_remote_ocr()
            break
        elif choice == "3":
            test_remote_connection()
        elif choice == "4":
            print("👋 再见！")
            break
        else:
            print("❌ 无效选择，请重新输入")
