import logging
from pynput import keyboard
import threading

class GlobalKeyboardListener:
    """
    全局键盘监听器类，用于在游戏窗口获得焦点时也能监听键盘事件
    使用pynput库实现全局热键功能
    """
    
    def __init__(self):
        """
        初始化全局键盘监听器
        """
        self.listener = None
        self.listener_thread = None
        self.callbacks = {}
        self.running = False
        self.logger = logging.getLogger(__name__)
        self.logger.info("全局键盘监听器已初始化")
    
    def register_callback(self, key, callback):
        """
        注册按键回调函数
        
        参数:
            key: 按键，例如 'f11', 'f12'
            callback: 回调函数
        """
        self.callbacks[key.lower()] = callback
        self.logger.info(f"已注册按键 {key} 的回调函数")
    
    def on_press(self, key):
        """
        按键按下事件处理
        
        参数:
            key: 按下的键
        """
        try:
            # 处理特殊功能键
            if hasattr(key, 'name'):
                key_name = key.name.lower()
                self.logger.debug(f"检测到按键: {key_name}")
                
                # 检查是否有对应的回调函数
                if key_name in self.callbacks:
                    try:
                        self.logger.info(f"触发按键 {key_name} 的回调函数")
                        # 在新线程中执行回调，避免阻塞监听器
                        threading.Thread(target=self.callbacks[key_name]).start()
                    except Exception as e:
                        self.logger.error(f"执行按键 {key_name} 回调函数时出错: {str(e)}")
        except Exception as e:
            self.logger.error(f"处理按键事件时出错: {str(e)}")
    
    def on_release(self, key):
        """
        按键释放事件处理
        
        参数:
            key: 释放的键
        
        返回:
            False: 如果按下esc键，停止监听
        """
        try:
            # 这里可以根据需要添加按键释放事件的处理
            pass
        except Exception as e:
            self.logger.error(f"处理按键释放事件时出错: {str(e)}")
        
        # 始终返回True，保持监听状态
        return True
    
    def start(self):
        """
        启动全局键盘监听器
        
        返回:
            bool: 是否成功启动
        """
        if self.running:
            self.logger.warning("键盘监听器已经在运行中")
            return
        
        try:
            # 创建监听器
            self.listener = keyboard.Listener(
                on_press=self.on_press,
                on_release=self.on_release
            )
            
            # 在后台线程中启动监听器
            self.listener_thread = threading.Thread(target=self._start_listener)
            self.listener_thread.daemon = True
            self.listener_thread.start()
            
            self.running = True
            self.logger.info("全局键盘监听器已启动")
        except Exception as e:
            self.logger.error(f"启动键盘监听器时出错: {str(e)}")
    
    def _start_listener(self):
        """
        在单独线程中运行监听器的方法
        """
        try:
            with self.listener:
                self.listener.join()
        except Exception as e:
            self.logger.error(f"监听器运行时出错: {str(e)}")
            self.running = False
    
    def stop(self):
        """
        停止全局键盘监听器
        
        返回:
            bool: 是否成功停止
        """
        if not self.running:
            self.logger.warning("键盘监听器未在运行")
            return
        
        try:
            if self.listener:
                self.listener.stop()
            
            if self.listener_thread and self.listener_thread.is_alive():
                self.listener_thread.join(timeout=2.0)
            
            self.running = False
            self.logger.info("全局键盘监听器已停止")
        except Exception as e:
            self.logger.error(f"停止键盘监听器时出错: {str(e)}")
    
    def is_running(self):
        """
        检查监听器是否正在运行
        
        返回:
            bool: 如果监听器正在运行，返回True
        """
        return self.running