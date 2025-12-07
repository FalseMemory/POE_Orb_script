#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
POE装备洗练工具 - 日志处理模块
用于设置和管理应用程序日志
"""

import os
import logging
import logging.handlers
from datetime import datetime


def setup_logger(log_dir='logs', log_level=logging.INFO, log_name='poe_washer'):
    """
    设置日志系统
    
    参数:
        log_dir (str): 日志文件保存目录
        log_level (int): 日志级别
        log_name (str): 日志名称
        
    返回:
        logging.Logger: 配置好的日志记录器
    """
    # 确保日志目录存在
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
        
    # 创建logger
    logger = logging.getLogger(log_name)
    logger.setLevel(log_level)
    
    # 检查是否已经有handler，避免重复添加
    if not logger.handlers:
        # 创建控制台handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        
        # 创建文件handler，使用TimedRotatingFileHandler实现日志滚动
        log_filename = os.path.join(log_dir, f'{log_name}_{datetime.now().strftime("%Y%m%d")}.log')
        file_handler = logging.handlers.TimedRotatingFileHandler(
            log_filename,
            when='midnight',
            interval=1,
            backupCount=7,
            encoding='utf-8'
        )
        file_handler.setLevel(log_level)
        
        # 设置日志格式
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 应用格式到handlers
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)
        
        # 添加handlers到logger
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)
    
    return logger


def get_debug_logger():
    """
    获取调试模式日志记录器
    
    返回:
        logging.Logger: 调试级别日志记录器
    """
    return setup_logger(log_level=logging.DEBUG)


def log_execution(func):
    """
    装饰器：记录函数执行信息
    
    参数:
        func (callable): 被装饰的函数
        
    返回:
        callable: 装饰后的函数
    """
    logger = logging.getLogger('poe_washer')
    
    def wrapper(*args, **kwargs):
        logger.debug(f"执行函数: {func.__name__}")
        try:
            result = func(*args, **kwargs)
            logger.debug(f"函数 {func.__name__} 执行成功")
            return result
        except Exception as e:
            logger.error(f"函数 {func.__name__} 执行失败: {str(e)}")
            raise
    
    return wrapper


def log_time(func):
    """
    装饰器：记录函数执行时间
    
    参数:
        func (callable): 被装饰的函数
        
    返回:
        callable: 装饰后的函数
    """
    logger = logging.getLogger('poe_washer')
    
    def wrapper(*args, **kwargs):
        start_time = datetime.now()
        result = func(*args, **kwargs)
        end_time = datetime.now()
        logger.info(f"函数 {func.__name__} 执行时间: {(end_time - start_time).total_seconds():.2f} 秒")
        return result
    
    return wrapper