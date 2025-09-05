#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
启动脚本 - 设置Python路径并运行主程序
"""
import sys
import os

# 添加src目录到Python路径
src_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src')
sys.path.insert(0, src_path)

# 运行主程序
if __name__ == "__main__":
    try:
        from main import ResearchFileManager
        app = ResearchFileManager()
        app.initialize()
        app.gui.root.mainloop()
    except Exception as e:
        print(f"启动失败: {e}")
        import traceback
        traceback.print_exc()
        input("按回车键退出...")

