#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
POE装备洗练工具 - 主程序入口
基于剪贴板分析的Path of Exile装备自动洗练工具
"""

import os
import sys
import logging

# 添加src目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.ui.washer_gui import main
from src.utils.logger_setup import setup_logger


def ensure_directories():
    """
    确保必要的目录存在
    """
    # 确保日志目录存在
    log_dir = os.path.join(os.path.dirname(__file__), 'logs')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # 确保输出目录存在
    output_dir = os.path.join(os.path.dirname(__file__), 'output')
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)


def check_requirements():
    """
    检查必要的依赖包
    
    Returns:
        bool: 是否所有依赖都可用
    """
    required_packages = [
        ('pyautogui', 'pyautogui'),
        ('tkinter', 'tkinter')  # tkinter通常随Python一起安装
    ]
    
    missing_packages = []
    
    for import_name, package_name in required_packages:
        try:
            __import__(import_name)
        except ImportError:
            missing_packages.append(package_name)
    
    if missing_packages:
        print("警告: 缺少以下必要的依赖包:")
        for package in missing_packages:
            print(f"  - {package}")
        print("\n请使用pip安装这些依赖包:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    
    return True


def handle_exceptions(exctype, value, traceback):
    """
    全局异常处理函数
    
    Args:
        exctype: 异常类型
        value: 异常值
        traceback: 回溯信息
    """
    logger = logging.getLogger('poe_washer')
    logger.error("发生未捕获的异常:", exc_info=(exctype, value, traceback))
    
    # 在控制台也打印错误信息
    import traceback as tb
    print("\n发生错误:")
    print(''.join(tb.format_exception(exctype, value, traceback)))
    
    # 对于GUI应用，可以显示一个错误对话框
    try:
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()  # 隐藏主窗口
        messagebox.showerror("应用程序错误", f"发生错误: {str(value)}")
        root.destroy()
    except:
        pass


def main_entry():
    """
    主程序入口
    """
    # 设置全局异常处理器
    sys.excepthook = handle_exceptions
    
    # 确保必要的目录存在
    ensure_directories()
    
    # 设置日志，使用DEBUG级别以便查看更多详细信息
    logger = setup_logger(log_level=logging.DEBUG)
    logger.info("POE装备洗练工具启动")
    logger.debug("日志级别已设置为DEBUG")
    
    # 检查依赖
    if not check_requirements():
        logger.warning("缺少必要的依赖包")
        input("按Enter键继续...")
    
    # 运行主程序
    try:
        main()
    except KeyboardInterrupt:
        logger.info("用户中断程序")
    except Exception as e:
        logger.error(f"程序运行出错: {e}")
        raise
    finally:
        logger.info("POE装备洗练工具关闭")


if __name__ == "__main__":
    main_entry()