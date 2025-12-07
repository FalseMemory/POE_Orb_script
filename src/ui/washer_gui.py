#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
POE装备洗练工具 - 用户界面模块
基于剪贴板分析的POE装备洗练工具界面
"""

import os
import sys
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, simpledialog, messagebox
from src.utils.keyboard_listener import GlobalKeyboardListener
import logging

from ..core.washer_core import PoeClipboardWasher
from ..utils.logger_setup import setup_logger

# 设置日志
logger = setup_logger()


class PoeWasherGUI:
    """
    POE装备洗练工具图形界面
    """
    
    def __init__(self, root):
        """
        初始化GUI
        
        参数:
            root: Tkinter根窗口
        """
        self.root = root
        self.root.title("POE装备洗练工具 - 基于剪贴板分析")
        self.root.geometry("900x700")
        self.root.minsize(800, 500)
        
        # 确保中文显示正常
        if sys.platform == 'win32':
            # Windows系统默认字体应该能正确显示中文
            pass
        
        # 初始化洗练核心
        self.washer = PoeClipboardWasher()
        self.washing_thread = None
        
        # 创建主框架
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建标签页
        self.tab_control = ttk.Notebook(self.main_frame)
        self.tab_control.pack(fill=tk.BOTH, expand=True)
        
        # 创建各个标签页
        self.create_main_tab()
        self.create_target_tab()
        self.create_equipment_tab()
        self.create_sequence_tab()
        self.create_fate_card_tab()
        self.create_config_tab()
        self.create_log_tab()
        
        # 设置状态栏
        self.status_var = tk.StringVar()
        self.status_var.set("就绪 - 等待操作")
        self.status_bar = ttk.Label(root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # 初始化全局键盘监听器
        self.global_listener = GlobalKeyboardListener()
        
        # 设置快捷键
        self.root.bind('<F10>', self.toggle_washing)
        self.root.bind('<F11>', self.record_equipment_position)
        self.root.bind('<F12>', self.toggle_sequence)
        self.root.bind('<Escape>', self.stop_all_operations)
        
        # 注册全局热键
        self.setup_global_hotkeys()
        
        # 启动定时更新
        self.update_stats()
    
    def create_main_tab(self):
        """
        创建主标签页
        """
        main_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(main_tab, text="主界面")
        
        # 创建说明文本
        description_frame = ttk.LabelFrame(main_tab, text="使用说明", padding="10")
        description_frame.pack(fill=tk.X, padx=5, pady=5)
        
        description_text = (
            "1. 将鼠标放在装备上，按 F11 记录装备位置\n"
            "2. 将鼠标放在通货上，按 F12 记录通货位置\n"
            "3. 在目标词条标签页中设置需要的词条\n"
            "4. 点击'开始洗练'或按 F10 开始自动洗练\n"
            "5. 再次按 F10 停止洗练\n"
            "6. 按 ESC 键可以停止所有操作\n"
            "\n注意：请确保游戏中鼠标悬停在装备上时按Ctrl+C可以复制装备属性。"
        )
        
        description_label = ttk.Label(description_frame, text=description_text, justify=tk.LEFT)
        description_label.pack(fill=tk.X)
        
        # 添加退出按键提示
        exit_hint_frame = ttk.Frame(main_tab, padding="10")
        exit_hint_frame.pack(fill=tk.X, padx=5, pady=5)
        
        exit_hint_label = ttk.Label(exit_hint_frame, text="💡 提示：在任何操作过程中，按 ESC 键可以立即停止所有操作", foreground="blue", font=("Arial", 10, "bold"))
        exit_hint_label.pack(fill=tk.X, anchor=tk.CENTER)
        
        # 创建洗练控制区域
        control_frame = ttk.LabelFrame(main_tab, text="洗练控制", padding="10")
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 洗练按钮
        self.wash_button = ttk.Button(control_frame, text="开始洗练 (F10)", command=self.toggle_washing)
        self.wash_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        # 当前状态显示
        self.status_frame = ttk.Frame(control_frame)
        self.status_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=20)
        
        self.current_equipment_var = tk.StringVar()
        self.current_currency_var = tk.StringVar()
        self.current_match_mode_var = tk.StringVar()
        
        self.update_current_info()
        
        ttk.Label(self.status_frame, text="当前装备: ").grid(row=0, column=0, sticky=tk.W, padx=2, pady=2)
        ttk.Label(self.status_frame, textvariable=self.current_equipment_var).grid(row=0, column=1, sticky=tk.W, padx=2, pady=2)
        
        ttk.Label(self.status_frame, text="当前通货: ").grid(row=1, column=0, sticky=tk.W, padx=2, pady=2)
        ttk.Label(self.status_frame, textvariable=self.current_currency_var).grid(row=1, column=1, sticky=tk.W, padx=2, pady=2)
        
        ttk.Label(self.status_frame, text="匹配模式: ").grid(row=2, column=0, sticky=tk.W, padx=2, pady=2)
        ttk.Label(self.status_frame, textvariable=self.current_match_mode_var).grid(row=2, column=1, sticky=tk.W, padx=2, pady=2)
        
        # 统计信息区域
        stats_frame = ttk.LabelFrame(main_tab, text="洗练统计", padding="10")
        stats_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.click_count_var = tk.StringVar(value="0")
        self.attempt_count_var = tk.StringVar(value="0")
        self.match_count_var = tk.StringVar(value="0")
        
        ttk.Label(stats_frame, text="点击次数: ").grid(row=0, column=0, sticky=tk.W, padx=2, pady=2)
        ttk.Label(stats_frame, textvariable=self.click_count_var).grid(row=0, column=1, sticky=tk.W, padx=2, pady=2)
        
        ttk.Label(stats_frame, text="尝试次数: ").grid(row=0, column=2, sticky=tk.W, padx=2, pady=2)
        ttk.Label(stats_frame, textvariable=self.attempt_count_var).grid(row=0, column=3, sticky=tk.W, padx=2, pady=2)
        
        ttk.Label(stats_frame, text="匹配词条: ").grid(row=0, column=4, sticky=tk.W, padx=2, pady=2)
        ttk.Label(stats_frame, textvariable=self.match_count_var).grid(row=0, column=5, sticky=tk.W, padx=2, pady=2)
    
    def create_target_tab(self):
        """
        创建目标词条标签页
        """
        target_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(target_tab, text="目标词条")
        
        # 规则集合选择区域
        rule_set_frame = ttk.LabelFrame(target_tab, text="规则集合", padding="10")
        rule_set_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 第一行：规则集合选择和管理
        rule_row1 = ttk.Frame(rule_set_frame)
        rule_row1.pack(fill=tk.X, pady=5)
        
        # 规则集合选择
        ttk.Label(rule_row1, text="当前规则集合:").pack(side=tk.LEFT, padx=5, pady=5)
        
        # 获取规则集合名称列表
        self.rule_set_names = list(self.washer.config['rule_sets'].keys())
        self.current_rule_set_var = tk.StringVar(value=self.washer.config['current_rule_set'])
        
        # 创建规则集合下拉菜单
        self.rule_set_combobox = ttk.Combobox(rule_row1, textvariable=self.current_rule_set_var, 
                                              values=self.rule_set_names, state="readonly")
        self.rule_set_combobox.pack(side=tk.LEFT, padx=5, pady=5)
        
        # 规则集合管理按钮
        ttk.Button(rule_row1, text="新建规则集", command=self.create_new_rule_set).pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(rule_row1, text="删除规则集", command=self.delete_rule_set).pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(rule_row1, text="重命名规则集", command=self.rename_rule_set).pack(side=tk.LEFT, padx=5, pady=5)
        
        # 第二行：规则集合的默认装备和通货
        rule_row2 = ttk.Frame(rule_set_frame)
        rule_row2.pack(fill=tk.X, pady=5)
        
        # 默认装备选择
        ttk.Label(rule_row2, text="默认装备:").pack(side=tk.LEFT, padx=5, pady=5)
        
        self.rule_set_equipment_var = tk.StringVar()
        # 获取装备列表
        equipment_list = self.washer.get_equipment_list()
        self.rule_set_equipment_combobox = ttk.Combobox(rule_row2, textvariable=self.rule_set_equipment_var, 
                                                       values=equipment_list, state="readonly")
        self.rule_set_equipment_combobox.pack(side=tk.LEFT, padx=5, pady=5)
        
        # 绑定装备选择事件
        self.rule_set_equipment_combobox.bind("<<ComboboxSelected>>", self.on_rule_set_equipment_change)
        
        # 默认通货选择
        ttk.Label(rule_row2, text="默认通货:").pack(side=tk.LEFT, padx=5, pady=5)
        
        self.rule_set_currency_var = tk.StringVar()
        # 获取通货列表
        currency_list = self.washer.get_currency_list()
        self.rule_set_currency_combobox = ttk.Combobox(rule_row2, textvariable=self.rule_set_currency_var, 
                                                     values=currency_list, state="readonly")
        self.rule_set_currency_combobox.pack(side=tk.LEFT, padx=5, pady=5)
        
        # 绑定通货选择事件
        self.rule_set_currency_combobox.bind("<<ComboboxSelected>>", self.on_rule_set_currency_change)
        
        # 绑定规则集合切换事件
        self.rule_set_combobox.bind("<<ComboboxSelected>>", self.on_rule_set_change)
        
        # 添加应用设置按钮
        ttk.Button(rule_row2, text="应用设置", command=self.apply_rule_set_settings).pack(side=tk.LEFT, padx=5, pady=5)
        
        # 左侧：词条列表
        list_frame = ttk.LabelFrame(target_tab, text="目标词条列表", padding="10")
        list_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 创建词条列表 - 添加启用列
        columns = ("enabled", "index", "type", "content")
        self.target_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=15)
        
        self.target_tree.heading("enabled", text="启用")
        self.target_tree.heading("index", text="序号")
        self.target_tree.heading("type", text="类型")
        self.target_tree.heading("content", text="内容")
        
        self.target_tree.column("enabled", width=50, anchor=tk.CENTER)
        self.target_tree.column("index", width=50, anchor=tk.CENTER)
        self.target_tree.column("type", width=80, anchor=tk.CENTER)
        self.target_tree.column("content", anchor=tk.W)
        
        # 绑定双击编辑事件
        self.target_tree.bind("<Double-1>", self.on_target_double_click)
        
        # 绑定点击启用列切换状态
        self.target_tree.bind("<Button-1>", self.on_target_tree_click)
        
        self.target_tree.pack(fill=tk.BOTH, expand=True, side=tk.TOP)
        
        # 右侧：词条操作按钮
        button_frame = ttk.Frame(target_tab, padding="10")
        button_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)
        
        self.add_include_button = ttk.Button(button_frame, text="添加包含词条", command=self.add_include_target)
        self.add_include_button.pack(fill=tk.X, pady=5)
        
        self.add_exclude_button = ttk.Button(button_frame, text="添加排除词条", command=self.add_exclude_target)
        self.add_exclude_button.pack(fill=tk.X, pady=5)
        
        self.remove_button = ttk.Button(button_frame, text="移除选中词条", command=self.remove_selected_target)
        self.remove_button.pack(fill=tk.X, pady=5)
        
        # 匹配模式选择
        mode_frame = ttk.LabelFrame(button_frame, text="匹配模式", padding="10")
        mode_frame.pack(fill=tk.X, pady=10)
        
        self.match_mode = tk.StringVar(value=self.washer.config['match_mode'])
        
        ttk.Radiobutton(mode_frame, text="全匹配 (AND)", variable=self.match_mode, value="AND", command=self.update_match_mode).pack(anchor=tk.W)
        ttk.Radiobutton(mode_frame, text="任一匹配 (OR)", variable=self.match_mode, value="OR", command=self.update_match_mode).pack(anchor=tk.W)
        
        # 添加数量匹配模式
        count_frame = ttk.Frame(mode_frame)
        count_frame.pack(anchor=tk.W, pady=5)
        
        ttk.Radiobutton(count_frame, text="数量匹配 (COUNT):", variable=self.match_mode, value="COUNT", command=self.update_match_mode).pack(side=tk.LEFT)
        
        # 使用下拉菜单替代拖动条，范围1-6
        self.match_count_var = tk.StringVar(value=str(self.washer.config.get('match_count', 1)))
        
        # 创建下拉菜单
        self.match_count_combobox = ttk.Combobox(count_frame, textvariable=self.match_count_var, 
                                                values=["1", "2", "3", "4", "5", "6"], 
                                                width=3, state="readonly")
        self.match_count_combobox.pack(side=tk.LEFT, padx=5)
        
        # 绑定下拉菜单的选择事件
        self.match_count_combobox.bind("<<ComboboxSelected>>", lambda event: self.update_match_mode())
        
        ttk.Label(count_frame, text="条规则满足").pack(side=tk.LEFT)
        
        # 刷新词条列表
        self.refresh_target_list()
    
    def create_equipment_tab(self):
        """
        创建装备管理标签页
        """
        equipment_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(equipment_tab, text="装备管理")
        
        # 装备部分
        equip_frame = ttk.LabelFrame(equipment_tab, text="装备位置", padding="10")
        equip_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 装备列表
        columns = ("name", "position")
        self.equipment_tree = ttk.Treeview(equip_frame, columns=columns, show="headings", height=8)
        
        self.equipment_tree.heading("name", text="装备名称")
        self.equipment_tree.heading("position", text="位置")
        
        self.equipment_tree.column("name", width=200, anchor=tk.W)
        self.equipment_tree.column("position", anchor=tk.W)
        
        self.equipment_tree.pack(fill=tk.X, side=tk.TOP, padx=5, pady=5)
        
        # 装备操作按钮
        equip_button_frame = ttk.Frame(equip_frame)
        equip_button_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=5)
        
        self.record_equipment_btn = ttk.Button(equip_button_frame, text="记录位置 (截图模式)", command=self.record_equipment_position)
        self.record_equipment_btn.pack(side=tk.LEFT, padx=5)
        
        self.edit_equipment_btn = ttk.Button(equip_button_frame, text="编辑装备", command=self.edit_equipment_position)
        self.edit_equipment_btn.pack(side=tk.LEFT, padx=5)
        
        self.use_equipment_btn = ttk.Button(equip_button_frame, text="使用选中装备", command=self.use_selected_equipment)
        self.use_equipment_btn.pack(side=tk.LEFT, padx=5)
        
        self.remove_equipment_btn = ttk.Button(equip_button_frame, text="移除选中装备", command=self.remove_selected_equipment)
        self.remove_equipment_btn.pack(side=tk.LEFT, padx=5)
        
        # 通货部分
        currency_frame = ttk.LabelFrame(equipment_tab, text="通货位置", padding="10")
        currency_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 通货列表
        self.currency_tree = ttk.Treeview(currency_frame, columns=columns, show="headings", height=8)
        
        self.currency_tree.heading("name", text="通货名称")
        self.currency_tree.heading("position", text="位置")
        
        self.currency_tree.column("name", width=200, anchor=tk.W)
        self.currency_tree.column("position", anchor=tk.W)
        
        self.currency_tree.pack(fill=tk.X, side=tk.TOP, padx=5, pady=5)
        
        # 通货操作按钮
        currency_button_frame = ttk.Frame(currency_frame)
        currency_button_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=5)
        
        self.record_currency_btn = ttk.Button(currency_button_frame, text="记录位置 (截图模式)", command=self.record_currency_position)
        self.record_currency_btn.pack(side=tk.LEFT, padx=5)
        
        self.edit_currency_btn = ttk.Button(currency_button_frame, text="编辑通货", command=self.edit_currency_position)
        self.edit_currency_btn.pack(side=tk.LEFT, padx=5)
        
        self.use_currency_btn = ttk.Button(currency_button_frame, text="使用选中通货", command=self.use_selected_currency)
        self.use_currency_btn.pack(side=tk.LEFT, padx=5)
        
        self.remove_currency_btn = ttk.Button(currency_button_frame, text="移除选中通货", command=self.remove_selected_currency)
        self.remove_currency_btn.pack(side=tk.LEFT, padx=5)
        
        # 刷新列表
        self.refresh_equipment_lists()
    
    def create_config_tab(self):
        """
        创建配置标签页
        """
        config_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(config_tab, text="配置")
        
        # 延迟设置
        delay_frame = ttk.LabelFrame(config_tab, text="延迟设置", padding="10")
        delay_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 点击持续时间
        ttk.Label(delay_frame, text="点击持续时间 (秒):").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.click_duration_var = tk.StringVar(value=str(self.washer.config['click_duration']))
        click_duration_entry = ttk.Entry(delay_frame, textvariable=self.click_duration_var, width=10)
        click_duration_entry.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        # 操作间隔延迟
        ttk.Label(delay_frame, text="操作间隔延迟 (秒):").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.operation_delay_var = tk.StringVar(value=str(self.washer.config['operation_delay']))
        operation_delay_entry = ttk.Entry(delay_frame, textvariable=self.operation_delay_var, width=10)
        operation_delay_entry.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        
        # 剪贴板检查延迟
        ttk.Label(delay_frame, text="剪贴板检查延迟 (秒):").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.clipboard_delay_var = tk.StringVar(value=str(self.washer.config['clipboard_check_delay']))
        clipboard_delay_entry = ttk.Entry(delay_frame, textvariable=self.clipboard_delay_var, width=10)
        clipboard_delay_entry.grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)
        
        # 其他设置
        other_frame = ttk.LabelFrame(config_tab, text="其他设置", padding="10")
        other_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 最大尝试次数
        ttk.Label(other_frame, text="最大尝试次数:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.max_attempts_var = tk.StringVar(value=str(self.washer.config['max_attempts']))
        max_attempts_entry = ttk.Entry(other_frame, textvariable=self.max_attempts_var, width=10)
        max_attempts_entry.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        # 停止键设置
        ttk.Label(other_frame, text="停止键:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.stop_key_var = tk.StringVar(value=str(self.washer.config.get('stop_key', 'esc')))
        # 常用按键选项
        stop_key_options = ['esc', 'f1', 'f2', 'f3', 'f4', 'f5', 'f6', 'f7', 'f8', 'f9', 'f10', 'f11', 'f12', 'pause', 'insert', 'home', 'pageup', 'pagedown', 'end', 'delete']
        stop_key_combo = ttk.Combobox(other_frame, textvariable=self.stop_key_var, values=stop_key_options, width=10, state="readonly")
        stop_key_combo.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        
        # 配置管理按钮
        config_buttons_frame = ttk.Frame(config_tab, padding="10")
        config_buttons_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 保存按钮
        save_button = ttk.Button(config_buttons_frame, text="保存配置", command=self.save_config)
        save_button.pack(side=tk.LEFT, padx=5)
        
        # 导出配置按钮
        export_button = ttk.Button(config_buttons_frame, text="导出配置", command=self.export_config)
        export_button.pack(side=tk.LEFT, padx=5)
        
        # 导入配置按钮
        import_button = ttk.Button(config_buttons_frame, text="导入配置", command=self.import_config)
        import_button.pack(side=tk.LEFT, padx=5)
    
    def create_sequence_tab(self):
        """
        创建顺序执行标签页
        """
        sequence_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(sequence_tab, text="顺序执行")
        
        # 创建序列列表
        sequence_frame = ttk.LabelFrame(sequence_tab, text="执行序列", padding="10")
        sequence_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 创建序列树视图，添加启用列
        columns = ("enabled", "index", "equipment", "currency", "rules")
        self.sequence_tree = ttk.Treeview(sequence_frame, columns=columns, show="headings", height=15)
        
        self.sequence_tree.heading("enabled", text="启用")
        self.sequence_tree.heading("index", text="序号")
        self.sequence_tree.heading("equipment", text="装备位置")
        self.sequence_tree.heading("currency", text="通货位置")
        self.sequence_tree.heading("rules", text="匹配规则")
        
        self.sequence_tree.column("enabled", width=50, anchor=tk.CENTER)
        self.sequence_tree.column("index", width=50, anchor=tk.CENTER)
        self.sequence_tree.column("equipment", width=150, anchor=tk.W)
        self.sequence_tree.column("currency", width=150, anchor=tk.W)
        self.sequence_tree.column("rules", anchor=tk.W)
        
        # 绑定点击启用列切换状态
        self.sequence_tree.bind("<Button-1>", self.on_sequence_tree_click)
        
        self.sequence_tree.pack(fill=tk.BOTH, expand=True, side=tk.TOP, padx=5, pady=5)
        
        # 创建操作按钮
        button_frame = ttk.Frame(sequence_frame, padding="10")
        button_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=5, pady=5)
        
        # 左侧按钮组
        left_buttons = ttk.Frame(button_frame)
        left_buttons.pack(side=tk.LEFT)
        
        self.add_sequence_button = ttk.Button(left_buttons, text="添加操作", command=self.add_sequence_item)
        self.add_sequence_button.pack(side=tk.LEFT, padx=5)
        
        self.edit_sequence_button = ttk.Button(left_buttons, text="编辑操作", command=self.edit_sequence_item)
        self.edit_sequence_button.pack(side=tk.LEFT, padx=5)
        
        self.remove_sequence_button = ttk.Button(left_buttons, text="移除操作", command=self.remove_sequence_item)
        self.remove_sequence_button.pack(side=tk.LEFT, padx=5)
        
        # 右侧按钮组
        right_buttons = ttk.Frame(button_frame)
        right_buttons.pack(side=tk.RIGHT)
        
        self.move_up_button = ttk.Button(right_buttons, text="上移", command=self.move_sequence_item_up)
        self.move_up_button.pack(side=tk.LEFT, padx=5)
        
        self.move_down_button = ttk.Button(right_buttons, text="下移", command=self.move_sequence_item_down)
        self.move_down_button.pack(side=tk.LEFT, padx=5)
        
        # 执行按钮
        execute_frame = ttk.Frame(sequence_tab, padding="10")
        execute_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.execute_sequence_button = ttk.Button(execute_frame, text="开始执行序列", command=self.execute_sequence)
        self.execute_sequence_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_sequence_button = ttk.Button(execute_frame, text="停止执行", command=self.stop_sequence, state=tk.DISABLED)
        self.stop_sequence_button.pack(side=tk.LEFT, padx=5)
        
        # 添加退出按键提示
        exit_hint_frame = ttk.Frame(sequence_tab, padding="10")
        exit_hint_frame.pack(fill=tk.X, padx=5, pady=5)
        
        exit_hint_label = ttk.Label(exit_hint_frame, text="💡 提示：在任何操作过程中，按 ESC 键可以立即停止所有操作", foreground="blue", font=("Arial", 10, "bold"))
        exit_hint_label.pack(fill=tk.X, anchor=tk.CENTER)
        
        # 从配置中加载序列列表
        self.sequence_items = self.washer.config.get('sequence_items', [])
        self.refresh_sequence_list()
    
    def create_fate_card_tab(self):
        """
        创建未知命运卡标签页
        """
        fate_card_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(fate_card_tab, text="未知命运卡")
        
        # 配置区域
        config_frame = ttk.LabelFrame(fate_card_tab, text="配置", padding="10")
        config_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 未知命运卡位置
        ttk.Label(config_frame, text="未知命运卡位置:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.unknown_card_pos_var = tk.StringVar(value=f"{self.washer.config.get('unknown_fate_card_position', (0, 0))[0]}, {self.washer.config.get('unknown_fate_card_position', (0, 0))[1]}")
        unknown_card_pos_entry = ttk.Entry(config_frame, textvariable=self.unknown_card_pos_var, width=20)
        unknown_card_pos_entry.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        # 记录未知命运卡位置按钮
        self.record_unknown_card_btn = ttk.Button(config_frame, text="记录未知命运卡位置", command=lambda: self.record_position('unknown_card'))
        self.record_unknown_card_btn.grid(row=0, column=2, padx=5, pady=5)
        
        # 存放卡片位置
        ttk.Label(config_frame, text="存放卡片位置:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.storage_pos_var = tk.StringVar(value=f"{self.washer.config.get('card_storage_position', (0, 0))[0]}, {self.washer.config.get('card_storage_position', (0, 0))[1]}")
        storage_pos_entry = ttk.Entry(config_frame, textvariable=self.storage_pos_var, width=20)
        storage_pos_entry.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        
        # 记录存放卡片位置按钮
        self.record_storage_btn = ttk.Button(config_frame, text="记录存放卡片位置", command=lambda: self.record_position('storage'))
        self.record_storage_btn.grid(row=1, column=2, padx=5, pady=5)
        
        # 循环次数
        ttk.Label(config_frame, text="循环次数:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.loop_count_var = tk.StringVar(value=str(self.washer.config.get('fate_card_loop_count', 10)))
        loop_count_entry = ttk.Entry(config_frame, textvariable=self.loop_count_var, width=10)
        loop_count_entry.grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)
        
        # 保存配置按钮
        save_btn = ttk.Button(config_frame, text="保存配置", command=self.save_fate_card_config)
        save_btn.grid(row=3, column=0, columnspan=3, pady=10)
        
        # 操作区域
        control_frame = ttk.LabelFrame(fate_card_tab, text="操作", padding="10")
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 开始按钮
        self.start_fate_card_btn = ttk.Button(control_frame, text="开始处理", command=self.start_fate_card_process)
        self.start_fate_card_btn.pack(side=tk.LEFT, padx=5)
        
        # 停止按钮
        self.stop_fate_card_btn = ttk.Button(control_frame, text="停止处理", command=self.stop_fate_card_process, state=tk.DISABLED)
        self.stop_fate_card_btn.pack(side=tk.LEFT, padx=5)
        
        # 添加退出按键提示
        exit_hint_frame = ttk.Frame(fate_card_tab, padding="10")
        exit_hint_frame.pack(fill=tk.X, padx=5, pady=5)
        
        exit_hint_label = ttk.Label(exit_hint_frame, text="💡 提示：在任何操作过程中，按 ESC 键可以立即停止所有操作", foreground="blue", font=("Arial", 10, "bold"))
        exit_hint_label.pack(fill=tk.X, anchor=tk.CENTER)
    
    def create_log_tab(self):
        """
        创建日志标签页
        """
        log_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(log_tab, text="日志")
        
        # 创建日志文本框
        self.log_text = scrolledtext.ScrolledText(log_tab, wrap=tk.WORD, height=25)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.log_text.config(state=tk.DISABLED)
        
        # 添加自定义日志处理器
        self.log_handler = TextHandler(self.log_text)
        self.log_handler.setLevel(logging.INFO)
        logger.addHandler(self.log_handler)
    
    def toggle_washing(self, event=None):
        """
        切换洗练状态
        
        参数:
            event: 键盘事件
        """
        if self.washer.is_running():
            self.stop_washing()
        else:
            self.start_washing()
    
    def start_washing(self):
        """
        开始洗练
        """
        # 检查是否有选中的装备和通货
        if not self.washer.config['current_equipment']:
            messagebox.showerror("错误", "请先记录并选择装备位置")
            return
        
        if not self.washer.config['current_currency']:
            messagebox.showerror("错误", "请先记录并选择通货位置")
            return
        
        if not self.washer.config['conditional_targets']:
            messagebox.showerror("错误", "请添加至少一个目标词条")
            return
        
        # 更新UI状态
        self.wash_button.config(text="停止洗练 (F10)")
        self.status_var.set("洗练中...")
        
        # 在新线程中运行洗练
        self.washing_thread = threading.Thread(target=self.run_washing)
        self.washing_thread.daemon = True
        self.washing_thread.start()
    
    def stop_washing(self):
        """
        停止洗练
        """
        self.washer.stop_washing()
        self.wash_button.config(text="开始洗练 (F10)")
        self.status_var.set("已停止洗练")
    
    def run_washing(self):
        """
        在新线程中运行洗练
        """
        try:
            result = self.washer.wash_equipment()
            
            # 更新UI状态
            self.root.after(0, lambda: self.wash_button.config(text="开始洗练 (F10)"))
            
            if result:
                self.root.after(0, lambda: self.status_var.set("成功找到符合条件的装备！"))
                logger.info("成功找到符合条件的装备！")
            else:
                self.root.after(0, lambda: self.status_var.set("未找到符合条件的装备或已停止"))
        except Exception as e:
            logger.error(f"洗练过程出错: {e}")
            self.root.after(0, lambda: self.status_var.set("洗练过程中发生错误"))
    
    def record_equipment_position(self, event=None):
        """
        记录装备位置 - 新的截图式记录功能
        
        Args:
            event: 键盘事件（可选）
        """
        try:
            # 检查是否通过快捷键触发
            trigger_source = "快捷键F11" if event else "按钮点击"
            logging.info(f"{trigger_source}触发，开始记录装备位置")
            
            # 确保主窗口在前台
            self.root.lift()
            self.root.update_idletasks()
            
            # 创建覆盖层窗口进行位置记录
            self.create_overlay_window('equipment', self.handle_position_record)
        except Exception as e:
            error_msg = f"记录装备位置时出错: {str(e)}"
            logging.error(error_msg)
            self.status_var.set(error_msg)
            messagebox.showerror("错误", error_msg)
    
    def handle_position_record(self, x, y, position_type):
        """
        处理位置记录的回调函数
        
        Args:
            x: 记录的X坐标
            y: 记录的Y坐标
            position_type: 位置类型 ('equipment' 或 'currency')
        """
        # 如果取消或坐标无效，直接返回
        if x is None or y is None:
            return
        
        try:
            # 创建名称输入对话框
            dialog = tk.Toplevel(self.root)
            dialog.title(f"记录{position_type == 'equipment' and '装备' or '通货'}名称")
            dialog.geometry("400x150")
            dialog.transient(self.root)
            dialog.grab_set()  # 模态对话框
            dialog.lift()
            
            # 创建对话框内容
            ttk.Label(dialog, text=f"请输入{position_type == 'equipment' and '装备' or '通货'}名称:").pack(pady=10)
            
            # 创建输入框
            name_var = tk.StringVar()
            entry = ttk.Entry(dialog, textvariable=name_var, width=30)
            entry.pack(pady=5)
            entry.focus()  # 自动聚焦到输入框
            
            # 确认和取消按钮的变量
            confirmed = False
            
            def on_ok():
                nonlocal confirmed
                confirmed = True
                dialog.destroy()
            
            def on_cancel():
                dialog.destroy()
            
            # 创建按钮
            button_frame = ttk.Frame(dialog)
            button_frame.pack(pady=10)
            ttk.Button(button_frame, text="确定", command=on_ok).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="取消", command=on_cancel).pack(side=tk.LEFT, padx=5)
            
            # 绑定Enter键确认
            dialog.bind('<Return>', lambda e: on_ok())
            # 绑定Escape键取消
            dialog.bind('<Escape>', lambda e: on_cancel())
            
            # 等待对话框关闭
            self.root.wait_window(dialog)
            
            # 获取输入的名称
            name = name_var.get() if confirmed else ""
            
            if name and name.strip():
                name = name.strip()
                logging.info(f"用户输入的{position_type}名称: {name}, 位置: ({x}, {y})")
                
                # 直接保存指定位置
                if position_type == 'equipment':
                    self.washer.config['equipment_positions'][name] = (x, y)
                    self.washer.config['current_equipment'] = name
                elif position_type == 'currency':
                    self.washer.config['currency_positions'][name] = (x, y)
                    self.washer.config['current_currency'] = name
                
                # 保存配置
                from ..utils.config_manager import save_config
                save_config(self.washer.config)
                
                # 刷新列表
                self.refresh_equipment_lists()
                self.update_current_info()
                
                message = f"已成功记录{position_type == 'equipment' and '装备' or '通货'} '{name}' 的位置 ({x}, {y})"
                self.status_var.set(message)
                logging.info(message)
                messagebox.showinfo("成功", message)
            else:
                logging.info(f"用户取消输入{position_type}名称")
        except Exception as e:
            error_msg = f"保存{position_type}位置时出错: {str(e)}"
            logging.error(error_msg)
            self.status_var.set(error_msg)
            messagebox.showerror("错误", error_msg)
    
    def create_overlay_window(self, position_type, callback):
        """
        创建屏幕变灰覆盖层窗口并实现鼠标位置实时显示和点击记录
        
        Args:
            position_type: 位置类型 ('equipment' 或 'currency')
            callback: 位置确认后的回调函数
            
        Returns:
            Toplevel: 覆盖层窗口
        """
        import pyautogui
        
        # 创建全屏覆盖层窗口
        overlay = tk.Toplevel(self.root)
        overlay.attributes('-fullscreen', True)
        overlay.attributes('-topmost', True)
        overlay.overrideredirect(True)  # 无边框窗口
        overlay.attributes('-alpha', 0.7)  # 半透明效果
        
        # 创建灰色背景画布
        canvas = tk.Canvas(overlay, bg='#333333', highlightthickness=0)
        canvas.pack(fill=tk.BOTH, expand=True)
        
        # 创建位置文本标签
        position_label = tk.Label(
            canvas,
            text="",
            font=('Microsoft YaHei', 12),
            bg='#FFFFFF',
            fg='#000000',
            relief=tk.SUNKEN
        )
        
        # 创建提示文本
        hint_text = f"点击要记录的{'装备' if position_type == 'equipment' else '通货'}位置\n按ESC键取消"
        hint_label = tk.Label(
            canvas,
            text=hint_text,
            font=('Microsoft YaHei', 14, 'bold'),
            bg='#FF0000',
            fg='#FFFFFF'
        )
        hint_label.place(relx=0.5, rely=0.1, anchor=tk.CENTER)
        
        # 鼠标移动事件处理函数
        def on_mouse_move(event):
            # 获取当前鼠标位置
            x, y = pyautogui.position()
            # 更新位置标签文本
            position_label.config(text=f"位置: ({x}, {y})")
            # 将标签放在鼠标右上方，偏移10像素
            label_x = event.x_root + 10
            label_y = event.y_root - 30
            # 确保标签不会超出屏幕
            screen_width = overlay.winfo_screenwidth()
            screen_height = overlay.winfo_screenheight()
            label_width = position_label.winfo_reqwidth()
            label_height = position_label.winfo_reqheight()
            
            if label_x + label_width > screen_width:
                label_x = screen_width - label_width - 10
            if label_y < 0:
                label_y = 10
            
            # 在画布上显示标签
            canvas.create_window(label_x, label_y, window=position_label, anchor=tk.NW)
        
        # 鼠标点击事件处理函数
        def on_mouse_click(event):
            # 获取点击位置
            x, y = pyautogui.position()
            logging.info(f"用户点击记录{'装备' if position_type == 'equipment' else '通货'}位置: ({x}, {y})")
            # 关闭覆盖层
            overlay.destroy()
            # 调用回调函数，传递位置和类型
            callback(x, y, position_type)
        
        # ESC键取消函数
        def on_escape(event):
            logging.info(f"用户取消记录{'装备' if position_type == 'equipment' else '通货'}位置")
            overlay.destroy()
            callback(None, None, position_type)  # 传递None表示取消
        
        # 绑定事件
        canvas.bind('<Motion>', on_mouse_move)
        canvas.bind('<Button-1>', on_mouse_click)  # 左键点击
        overlay.bind('<Escape>', on_escape)  # ESC键取消
        
        # 存储需要的引用
        canvas.position_label = position_label
        canvas.hint_label = hint_label
        canvas.position_type = position_type
        
        return overlay
    
    def record_currency_position(self, event=None):
        """
        记录通货位置 - 新的截图式记录功能
        
        Args:
            event: 键盘事件（可选）
        """
        try:
            # 检查是否通过快捷键触发
            trigger_source = "快捷键F12" if event else "按钮点击"
            logging.info(f"{trigger_source}触发，开始记录通货位置")
            
            # 确保主窗口在前台
            self.root.lift()
            self.root.update_idletasks()
            
            # 创建覆盖层窗口进行位置记录
            self.create_overlay_window('currency', self.handle_position_record)
        except Exception as e:
            error_msg = f"记录通货位置时出错: {str(e)}"
            logging.error(error_msg)
            self.status_var.set(error_msg)
            messagebox.showerror("错误", error_msg)
            
            # 创建输入框
            name_var = tk.StringVar()
            entry = ttk.Entry(dialog, textvariable=name_var, width=30)
            entry.pack(pady=5)
            entry.focus()  # 自动聚焦到输入框
            
            # 添加提示信息
            ttk.Label(dialog, text="提示：\n- 使用F12前请确保程序窗口在前台\n- 也可以直接编辑坐标值", 
                     justify=tk.LEFT).pack(pady=5, padx=10, anchor=tk.W)
            
            # 创建按钮
            button_frame = ttk.Frame(dialog)
            button_frame.pack(pady=10)
            
            # 确认和取消按钮的变量
            confirmed = False
            
            def on_ok():
                nonlocal confirmed
                confirmed = True
                dialog.destroy()
            
            def on_cancel():
                dialog.destroy()
            
            ttk.Button(button_frame, text="确定", command=on_ok).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="取消", command=on_cancel).pack(side=tk.LEFT, padx=5)
            
            # 绑定Enter键确认
            dialog.bind('<Return>', lambda e: on_ok())
            # 绑定Escape键取消
            dialog.bind('<Escape>', lambda e: on_cancel())
            
            # 等待对话框关闭
            self.root.wait_window(dialog)
            
            # 获取输入的名称
            name = name_var.get() if confirmed else ""
            
            if name and name.strip():
                name = name.strip()
                logging.info(f"用户输入的通货名称: {name}")
                
                try:
                    # 保存位置
                    success = self.washer.save_position(name, 'currency')
                    
                    if success:
                        # 刷新通货列表
                        self.refresh_equipment_lists()
                        self.update_current_info()
                        message = f"已成功记录通货 '{name}' 的位置"
                        self.status_var.set(message)
                        logging.info(message)
                        
                        # 显示成功提示对话框
                        messagebox.showinfo("成功", message)
                    else:
                        error_msg = f"记录通货 '{name}' 位置失败"
                        self.status_var.set(error_msg)
                        logging.error(error_msg)
                        messagebox.showerror("错误", error_msg)
                except Exception as inner_e:
                    # 捕获保存位置时的错误
                    error_msg = f"获取或保存位置时出错: {str(inner_e)}"
                    self.status_var.set(error_msg)
                    logging.error(error_msg)
                    messagebox.showerror(
                        "错误", 
                        "无法获取当前鼠标位置\n\n提示：如果游戏窗口在前台，程序可能无法获取鼠标位置\n请尝试使用'编辑通货位置'手动输入坐标"
                    )
            else:
                logging.info("用户取消输入或输入为空")
        except Exception as e:
            error_msg = f"记录通货位置时出错: {str(e)}"
            logging.error(error_msg)
            self.status_var.set(error_msg)
            messagebox.showerror("错误", error_msg)
    
    def add_include_target(self):
        """
        添加包含词条
        """
        self._show_add_target_dialog("添加包含词条", include=True)
    
    def add_exclude_target(self):
        """
        添加排除词条
        """
        self._show_add_target_dialog("添加排除词条", include=False)
    
    def _show_edit_target_dialog(self, index, current_text, current_min_value, tree_values):
        """
        显示编辑词条对话框，支持修改数值要求
        """
        # 创建自定义对话框
        dialog = tk.Toplevel(self.root)
        dialog.title("编辑词条")
        dialog.geometry("400x200")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # 设置对话框居中
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = (self.root.winfo_width() // 2) - (width // 2) + self.root.winfo_x()
        y = (self.root.winfo_height() // 2) - (height // 2) + self.root.winfo_y()
        dialog.geometry(f"+{x}+{y}")
        
        # 创建词条文本输入
        ttk.Label(dialog, text="词条内容:").grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
        text_var = tk.StringVar(value=current_text)
        ttk.Entry(dialog, textvariable=text_var, width=30).grid(row=0, column=1, padx=10, pady=10)
        
        # 创建数值要求输入
        ttk.Label(dialog, text="最小数值要求 (可选):").grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)
        min_value_var = tk.StringVar(value="" if current_min_value is None else str(current_min_value))
        ttk.Entry(dialog, textvariable=min_value_var, width=10).grid(row=1, column=1, padx=10, pady=10, sticky=tk.W)
        
        def on_ok():
            text = text_var.get().strip()
            if not text:
                messagebox.showerror("错误", "词条内容不能为空")
                return
            
            min_value = None
            if min_value_var.get().strip():
                try:
                    min_value = float(min_value_var.get().strip())
                except ValueError:
                    messagebox.showerror("错误", "请输入有效的数值")
                    return
            
            # 确定词条类型和启用状态
            include = True if tree_values[2] == "包含" else False
            enabled = True if tree_values[0] == "✓" else False
            
            # 更新词条
            if self.washer.update_target(index, text=text, include=include, enabled=enabled, min_value=min_value):
                self.status_var.set(f"词条已更新: {text}")
                self.refresh_target_list()
                dialog.destroy()
            else:
                messagebox.showerror("错误", "更新词条失败")
        
        # 创建按钮
        button_frame = ttk.Frame(dialog)
        button_frame.grid(row=2, column=0, columnspan=2, pady=10)
        
        ttk.Button(button_frame, text="确定", command=on_ok).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="取消", command=dialog.destroy).pack(side=tk.LEFT)
    
    def _show_add_target_dialog(self, title, include):
        """
        显示添加词条对话框，支持设置数值要求
        """
        # 创建自定义对话框
        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.geometry("400x200")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # 设置对话框居中
        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = (self.root.winfo_width() // 2) - (width // 2) + self.root.winfo_x()
        y = (self.root.winfo_height() // 2) - (height // 2) + self.root.winfo_y()
        dialog.geometry(f"+{x}+{y}")
        
        # 创建词条文本输入
        ttk.Label(dialog, text="词条内容:").grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
        text_var = tk.StringVar()
        ttk.Entry(dialog, textvariable=text_var, width=30).grid(row=0, column=1, padx=10, pady=10)
        
        # 创建数值要求输入
        ttk.Label(dialog, text="最小数值要求 (可选):").grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)
        min_value_var = tk.StringVar()
        ttk.Entry(dialog, textvariable=min_value_var, width=10).grid(row=1, column=1, padx=10, pady=10, sticky=tk.W)
        
        def on_ok():
            text = text_var.get().strip()
            if not text:
                messagebox.showerror("错误", "词条内容不能为空")
                return
            
            min_value = None
            if min_value_var.get().strip():
                try:
                    min_value = float(min_value_var.get().strip())
                except ValueError:
                    messagebox.showerror("错误", "请输入有效的数值")
                    return
            
            self.washer.add_target(text, include=include, enabled=True, min_value=min_value)
            self.refresh_target_list()
            dialog.destroy()
        
        # 创建按钮
        button_frame = ttk.Frame(dialog)
        button_frame.grid(row=2, column=0, columnspan=2, pady=10)
        
        ttk.Button(button_frame, text="确定", command=on_ok).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="取消", command=dialog.destroy).pack(side=tk.LEFT)
    
    def add_exclude_target(self):
        """
        添加排除词条
        """
        text = simpledialog.askstring("添加排除词条", "请输入要排除的词条:")
        if text and text.strip():
            self.washer.add_target(text.strip(), include=False, enabled=True)
            self.refresh_target_list()
    
    def remove_selected_target(self):
        """
        移除选中的词条
        """
        selected = self.target_tree.selection()
        if selected:
            item = selected[0]
            values = self.target_tree.item(item, "values")
            # 索引值在第二列（values[1]），第一列是启用状态（✓）
            index = int(values[1]) - 1
            if self.washer.remove_target(index):
                self.refresh_target_list()
    
    def use_selected_equipment(self):
        """
        使用选中的装备
        """
        selected = self.equipment_tree.selection()
        if selected:
            item = selected[0]
            name = self.equipment_tree.item(item, "values")[0]
            if self.washer.set_current_equipment(name):
                self.update_current_info()
                self.status_var.set(f"当前装备已设置为: {name}")
    
    def remove_selected_equipment(self):
        """
        移除选中的装备
        """
        selected_item = self.equipment_tree.selection()
        if not selected_item:
            messagebox.showinfo("提示", "请先选中一个装备")
            return
        
        item = selected_item[0]
        name = self.equipment_tree.item(item, "values")[0]
        
        if name in self.washer.config['equipment_positions']:
            del self.washer.config['equipment_positions'][name]
            if self.washer.config['current_equipment'] == name:
                self.washer.config['current_equipment'] = None
            # 导入配置保存函数
            from ..utils.config_manager import save_config
            save_config(self.washer.config)
            self.refresh_equipment_lists()
            self.update_current_info()
            messagebox.showinfo("成功", f"已移除装备: {name}")
        else:
            messagebox.showerror("错误", "找不到该装备")
    
    def edit_equipment_position(self):
        """
        编辑装备 - 可以修改名称和位置
        """
        selected_item = self.equipment_tree.selection()
        if not selected_item:
            messagebox.showinfo("提示", "请先选中一个装备")
            return
        
        item = selected_item[0]
        old_name = self.equipment_tree.item(item, "values")[0]
        
        # 获取当前位置
        current_pos = self.washer.config['equipment_positions'].get(old_name, (0, 0))
        current_pos_str = f"{current_pos[0]}, {current_pos[1]}"
        
        # 创建自定义对话框
        dialog = tk.Toplevel(self.root)
        dialog.title("编辑装备")
        dialog.geometry("400x250")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # 名称输入
        ttk.Label(dialog, text="装备名称:").grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
        name_var = tk.StringVar(value=old_name)
        name_entry = ttk.Entry(dialog, textvariable=name_var, width=25)
        name_entry.grid(row=0, column=1, padx=10, pady=10)
        
        # 位置输入
        ttk.Label(dialog, text="位置坐标:").grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)
        pos_var = tk.StringVar(value=current_pos_str)
        pos_entry = ttk.Entry(dialog, textvariable=pos_var, width=25)
        pos_entry.grid(row=1, column=1, padx=10, pady=10)
        
        def on_ok():
            new_name = name_var.get().strip()
            pos_str = pos_var.get().strip()
            
            if not new_name:
                messagebox.showerror("错误", "装备名称不能为空")
                return
            
            if not pos_str:
                messagebox.showerror("错误", "位置坐标不能为空")
                return
            
            try:
                # 解析坐标
                x, y = map(int, pos_str.split(','))
                
                # 验证坐标是否合理
                if x < 0 or y < 0:
                    raise ValueError("坐标值不能为负数")
                
                # 保存配置
                from ..utils.config_manager import save_config
                
                # 如果名称改变，需要处理旧名称的删除和新名称的添加
                if new_name != old_name:
                    # 检查新名称是否已存在
                    if new_name in self.washer.config['equipment_positions']:
                        messagebox.showerror("错误", "该装备名称已存在")
                        return
                    
                    # 删除旧名称
                    del self.washer.config['equipment_positions'][old_name]
                    
                    # 添加新名称和位置
                    self.washer.config['equipment_positions'][new_name] = (x, y)
                    
                    # 如果是当前使用的装备，更新当前装备名称
                    if self.washer.config['current_equipment'] == old_name:
                        self.washer.config['current_equipment'] = new_name
                        self.washer.config['current_equipment_position'] = (x, y)
                else:
                    # 名称不变，只更新位置
                    self.washer.config['equipment_positions'][new_name] = (x, y)
                    
                    # 如果是当前使用的装备，更新当前装备位置
                    if self.washer.config['current_equipment'] == new_name:
                        self.washer.config['current_equipment_position'] = (x, y)
                
                # 保存配置
                save_config(self.washer.config)
                
                # 刷新列表
                self.refresh_equipment_lists()
                
                # 更新当前信息显示
                self.update_current_info()
                
                message = f"已更新装备 '{new_name}' 的位置为 ({x}, {y})"
                self.status_var.set(message)
                logger.info(message)
                messagebox.showinfo("成功", message)
                
                dialog.destroy()
                
            except ValueError as e:
                error_msg = f"输入格式错误: {str(e)}"
                self.status_var.set(error_msg)
                logger.error(error_msg)
                messagebox.showerror("错误", error_msg)
            except Exception as e:
                error_msg = f"更新装备失败: {str(e)}"
                self.status_var.set(error_msg)
                logger.error(error_msg)
                messagebox.showerror("错误", error_msg)
        
        # 按钮
        button_frame = ttk.Frame(dialog)
        button_frame.grid(row=2, column=0, columnspan=2, pady=20)
        
        ttk.Button(button_frame, text="确定", command=on_ok).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="取消", command=dialog.destroy).pack(side=tk.LEFT)
    
    def use_selected_currency(self):
        """
        使用选中的通货
        """
        selected = self.currency_tree.selection()
        if selected:
            item = selected[0]
            name = self.currency_tree.item(item, "values")[0]
            if self.washer.set_current_currency(name):
                self.update_current_info()
                self.status_var.set(f"当前通货已设置为: {name}")
    
    def remove_selected_currency(self):
        """
        移除选中的通货
        """
        selected_item = self.currency_tree.selection()
        if not selected_item:
            messagebox.showinfo("提示", "请先选中一个通货")
            return
        
        item = selected_item[0]
        name = self.currency_tree.item(item, "values")[0]
        
        if name in self.washer.config['currency_positions']:
            del self.washer.config['currency_positions'][name]
            if self.washer.config['current_currency'] == name:
                self.washer.config['current_currency'] = None
            # 导入配置保存函数
            from ..utils.config_manager import save_config
            save_config(self.washer.config)
            self.refresh_equipment_lists()
            self.update_current_info()
            messagebox.showinfo("成功", f"已移除通货: {name}")
        else:
            messagebox.showerror("错误", "找不到该通货")
    
    def edit_currency_position(self):
        """
        编辑通货 - 可以修改名称和位置
        """
        selected_item = self.currency_tree.selection()
        if not selected_item:
            messagebox.showinfo("提示", "请先选中一个通货")
            return
        
        item = selected_item[0]
        old_name = self.currency_tree.item(item, "values")[0]
        
        # 获取当前位置
        current_pos = self.washer.config['currency_positions'].get(old_name, (0, 0))
        current_pos_str = f"{current_pos[0]}, {current_pos[1]}"
        
        # 创建自定义对话框
        dialog = tk.Toplevel(self.root)
        dialog.title("编辑通货")
        dialog.geometry("400x250")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # 名称输入
        ttk.Label(dialog, text="通货名称:").grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
        name_var = tk.StringVar(value=old_name)
        name_entry = ttk.Entry(dialog, textvariable=name_var, width=25)
        name_entry.grid(row=0, column=1, padx=10, pady=10)
        
        # 位置输入
        ttk.Label(dialog, text="位置坐标:").grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)
        pos_var = tk.StringVar(value=current_pos_str)
        pos_entry = ttk.Entry(dialog, textvariable=pos_var, width=25)
        pos_entry.grid(row=1, column=1, padx=10, pady=10)
        
        def on_ok():
            new_name = name_var.get().strip()
            pos_str = pos_var.get().strip()
            
            if not new_name:
                messagebox.showerror("错误", "通货名称不能为空")
                return
            
            if not pos_str:
                messagebox.showerror("错误", "位置坐标不能为空")
                return
            
            try:
                # 解析坐标
                x, y = map(int, pos_str.split(','))
                
                # 验证坐标是否合理
                if x < 0 or y < 0:
                    raise ValueError("坐标值不能为负数")
                
                # 保存配置
                from ..utils.config_manager import save_config
                
                # 如果名称改变，需要处理旧名称的删除和新名称的添加
                if new_name != old_name:
                    # 检查新名称是否已存在
                    if new_name in self.washer.config['currency_positions']:
                        messagebox.showerror("错误", "该通货名称已存在")
                        return
                    
                    # 删除旧名称
                    del self.washer.config['currency_positions'][old_name]
                    
                    # 添加新名称和位置
                    self.washer.config['currency_positions'][new_name] = (x, y)
                    
                    # 如果是当前使用的通货，更新当前通货名称
                    if self.washer.config['current_currency'] == old_name:
                        self.washer.config['current_currency'] = new_name
                        self.washer.config['currency_position'] = (x, y)
                else:
                    # 名称不变，只更新位置
                    self.washer.config['currency_positions'][new_name] = (x, y)
                    
                    # 如果是当前使用的通货，更新当前通货位置
                    if self.washer.config['current_currency'] == new_name:
                        self.washer.config['currency_position'] = (x, y)
                
                # 保存配置
                save_config(self.washer.config)
                
                # 刷新列表
                self.refresh_equipment_lists()
                
                # 更新当前信息显示
                self.update_current_info()
                
                message = f"已更新通货 '{new_name}' 的位置为 ({x}, {y})"
                self.status_var.set(message)
                logger.info(message)
                messagebox.showinfo("成功", message)
                
                dialog.destroy()
                
            except ValueError as e:
                error_msg = f"输入格式错误: {str(e)}"
                self.status_var.set(error_msg)
                logger.error(error_msg)
                messagebox.showerror("错误", error_msg)
            except Exception as e:
                error_msg = f"更新通货失败: {str(e)}"
                self.status_var.set(error_msg)
                logger.error(error_msg)
                messagebox.showerror("错误", error_msg)
        
        # 按钮
        button_frame = ttk.Frame(dialog)
        button_frame.grid(row=2, column=0, columnspan=2, pady=20)
        
        ttk.Button(button_frame, text="确定", command=on_ok).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="取消", command=dialog.destroy).pack(side=tk.LEFT)
    
    def update_match_mode(self, value=None):
        """
        更新匹配模式
        
        参数:
            value: 拖动条传递的值（可选）
        """
        mode = self.match_mode.get()
        logger.debug(f"[update_match_mode] 开始更新匹配模式: mode={mode}")
        
        if mode == "COUNT":
            try:
                # 获取下拉菜单值并转换为整数
                count_str = self.match_count_var.get()
                logger.debug(f"[update_match_mode] 下拉菜单值: {count_str}")
                
                count = int(count_str)
                logger.debug(f"[update_match_mode] 转换为整数: {count}")
                
                # 下拉菜单已经限制了范围1-6，这里再加一层检查确保安全性
                if count < 1 or count > 6:
                    logger.error(f"[update_match_mode] 匹配数量超出范围: {count}")
                    messagebox.showerror("错误", "匹配数量必须在1-6之间")
                    return
                
                # 保存输入的值到配置
                logger.debug(f"[update_match_mode] 调用set_match_mode: mode={mode}, count={count}")
                result = self.washer.set_match_mode(mode, count)
                logger.debug(f"[update_match_mode] set_match_mode返回: {result}")
                
                if result:
                    logger.debug(f"[update_match_mode] 调用update_current_info")
                    self.update_current_info()
                else:
                    logger.error(f"[update_match_mode] set_match_mode失败")
            except Exception as e:
                # 处理任何可能的异常
                logger.error(f"[update_match_mode] 更新匹配模式时出错: {str(e)}")
                messagebox.showerror("错误", f"更新匹配模式失败: {str(e)}")
        else:
            logger.debug(f"[update_match_mode] 调用set_match_mode: mode={mode}")
            self.washer.set_match_mode(mode)
            logger.debug(f"[update_match_mode] 调用update_current_info")
            self.update_current_info()
    
    def save_config(self):
        """
        保存配置
        """
        try:
            # 更新延迟设置
            click_duration = float(self.click_duration_var.get())
            operation_delay = float(self.operation_delay_var.get())
            clipboard_delay = float(self.clipboard_delay_var.get())
            self.washer.set_delay_settings(click_duration, operation_delay, clipboard_delay)
            
            # 更新最大尝试次数
            self.washer.config['max_attempts'] = int(self.max_attempts_var.get())
            
            # 更新停止键设置
            self.washer.config['stop_key'] = self.stop_key_var.get().lower()
            
            from ..utils.config_manager import save_config
            save_config(self.washer.config)
            
            # 重新设置全局热键
            self.setup_global_hotkeys()
            
            self.status_var.set("配置已保存")
        except ValueError as e:
            messagebox.showerror("错误", f"配置值无效: {e}")
    
    def export_config(self):
        """
        导出配置
        将当前配置导出到用户选择的文件
        """
        try:
            from tkinter import filedialog
            from ..utils.config_manager import save_config
            
            # 打开文件对话框，让用户选择保存位置和文件名
            file_path = filedialog.asksaveasfilename(
                defaultextension=".ini",
                filetypes=[("INI配置文件", "*.ini"), ("所有文件", "*.*")],
                title="导出配置"
            )
            
            if file_path:
                # 保存配置到选定的文件
                save_config(self.washer.config, file_path)
                self.status_var.set(f"配置已导出到: {file_path}")
                logger.info(f"配置已导出到: {file_path}")
                messagebox.showinfo("成功", f"配置已导出到: {file_path}")
        except Exception as e:
            logger.error(f"导出配置失败: {e}")
            messagebox.showerror("错误", f"导出配置失败: {e}")
    
    def import_config(self):
        """
        导入配置
        从用户选择的文件导入配置
        """
        try:
            from tkinter import filedialog
            from ..utils.config_manager import load_config
            
            # 打开文件对话框，让用户选择配置文件
            file_path = filedialog.askopenfilename(
                defaultextension=".ini",
                filetypes=[("INI配置文件", "*.ini"), ("所有文件", "*.*")],
                title="导入配置"
            )
            
            if file_path:
                # 读取配置文件
                imported_config = load_config(file_path)
                
                # 更新当前配置
                self.washer.config.update(imported_config)
                
                # 更新界面显示
                self.update_current_info()
                
                # 更新配置页面的输入框
                self.click_duration_var.set(str(self.washer.config['click_duration']))
                self.operation_delay_var.set(str(self.washer.config['operation_delay']))
                self.clipboard_delay_var.set(str(self.washer.config['clipboard_check_delay']))
                self.max_attempts_var.set(str(self.washer.config['max_attempts']))
                self.stop_key_var.set(str(self.washer.config['stop_key']))
                
                # 更新装备和通货列表
                self.refresh_equipment_lists()
                
                # 更新目标词条列表
                self.refresh_target_list()
                
                # 更新规则集合相关UI
                self.rule_set_names = list(self.washer.config['rule_sets'].keys())
                self.rule_set_combobox['values'] = self.rule_set_names
                self.current_rule_set_var.set(self.washer.config['current_rule_set'])
                
                # 如果存在rule_set_equipment_var和rule_set_currency_var，更新它们
                if hasattr(self, 'rule_set_equipment_var') and hasattr(self, 'rule_set_equipment_combobox'):
                    current_rule_set = self.washer.config['current_rule_set']
                    rule_data = self.washer.config['rule_sets'][current_rule_set]
                    self.rule_set_equipment_var.set(rule_data['equipment'])
                    self.rule_set_currency_var.set(rule_data['currency'])
                
                # 重新设置全局热键
                self.setup_global_hotkeys()
                
                self.status_var.set(f"配置已从 {file_path} 导入")
                logger.info(f"配置已从 {file_path} 导入")
                messagebox.showinfo("成功", f"配置已从 {file_path} 导入")
        except Exception as e:
            logger.error(f"导入配置失败: {e}")
            messagebox.showerror("错误", f"导入配置失败: {e}")
    
    def refresh_target_list(self):
        """
        刷新词条列表
        """
        # 清空列表
        for item in self.target_tree.get_children():
            self.target_tree.delete(item)
        
        # 添加词条
        for i, target in enumerate(self.washer.get_targets()):
            target_type = "包含" if target['include'] else "排除"
            enabled_status = "✓" if target.get('enabled', True) else ""
            self.target_tree.insert("", tk.END, values=(enabled_status, i+1, target_type, target['text']))
    
    def on_rule_set_change(self, event):
        """
        处理规则集合切换事件
        """
        new_rule_set = self.current_rule_set_var.get()
        logger.info(f"切换到规则集合: {new_rule_set}")
        
        # 获取当前规则集合数据
        rule_data = self.washer.config['rule_sets'][new_rule_set]
        
        # 更新当前规则集合
        self.washer.config['current_rule_set'] = new_rule_set
        
        # 更新conditional_targets引用，兼容旧代码
        self.washer.config['conditional_targets'] = rule_data['targets']
        
        # 更新默认装备选择
        self.rule_set_equipment_var.set(rule_data['equipment'])
        
        # 更新默认通货选择
        self.rule_set_currency_var.set(rule_data['currency'])
        
        # 将规则集合的默认装备和通货设置为主配置的当前值
        self.washer.config['current_equipment'] = rule_data['equipment']
        self.washer.config['current_currency'] = rule_data['currency']
        
        # 更新当前信息显示
        self.update_current_info()
        
        # 刷新词条列表
        self.refresh_target_list()
        
        # 保存配置
        from ..utils.config_manager import save_config
        save_config(self.washer.config)
    
    def on_rule_set_equipment_change(self, event):
        """
        处理规则集合默认装备变更事件
        """
        current_rule_set = self.current_rule_set_var.get()
        new_equipment = self.rule_set_equipment_var.get()
        
        # 更新规则集合的默认装备
        self.washer.config['rule_sets'][current_rule_set]['equipment'] = new_equipment
        
        # 如果当前使用的规则集合就是这个，同步更新主配置中的当前装备
        if self.washer.config['current_rule_set'] == current_rule_set:
            self.washer.config['current_equipment'] = new_equipment
            # 更新当前装备位置
            self.washer.config['current_equipment_position'] = self.washer.config['equipment_positions'].get(new_equipment, (0, 0))
        
        # 更新主页面显示
        self.update_current_info()
        
        # 保存配置
        from ..utils.config_manager import save_config
        save_config(self.washer.config)
        
        logger.info(f"更新规则集合 '{current_rule_set}' 的默认装备为: {new_equipment}")
    
    def on_rule_set_currency_change(self, event):
        """
        处理规则集合默认通货变更事件
        """
        current_rule_set = self.current_rule_set_var.get()
        new_currency = self.rule_set_currency_var.get()
        
        # 更新规则集合的默认通货
        self.washer.config['rule_sets'][current_rule_set]['currency'] = new_currency
        
        # 如果当前使用的规则集合就是这个，同步更新主配置中的当前通货
        if self.washer.config['current_rule_set'] == current_rule_set:
            self.washer.config['current_currency'] = new_currency
            # 更新当前通货位置
            self.washer.config['currency_position'] = self.washer.config['currency_positions'].get(new_currency, (0, 0))
        
        # 更新主页面显示
        self.update_current_info()
        
        # 保存配置
        from ..utils.config_manager import save_config
        save_config(self.washer.config)
        
        logger.info(f"更新规则集合 '{current_rule_set}' 的默认通货为: {new_currency}")
    
    def apply_rule_set_settings(self):
        """
        应用当前规则集合的设置到主配置
        将当前规则集合的默认装备和通货设置到主配置中，刷新主页面显示
        """
        current_rule_set = self.current_rule_set_var.get()
        
        # 获取当前规则集合的默认装备和通货
        rule_data = self.washer.config['rule_sets'][current_rule_set]
        equipment = rule_data['equipment']
        currency = rule_data['currency']
        
        # 更新主配置中的当前装备
        self.washer.config['current_equipment'] = equipment
        self.washer.config['current_equipment_position'] = self.washer.config['equipment_positions'].get(equipment, (0, 0))
        
        # 更新主配置中的当前通货
        self.washer.config['current_currency'] = currency
        self.washer.config['currency_position'] = self.washer.config['currency_positions'].get(currency, (0, 0))
        
        # 更新当前规则集合
        self.washer.config['current_rule_set'] = current_rule_set
        
        # 更新conditional_targets引用，兼容旧代码
        self.washer.config['conditional_targets'] = rule_data['targets']
        
        # 更新主页面显示
        self.update_current_info()
        
        # 保存配置
        from ..utils.config_manager import save_config
        save_config(self.washer.config)
        
        # 显示状态信息
        message = f"已应用规则集合 '{current_rule_set}' 的设置，当前装备: {equipment}，当前通货: {currency}"
        self.status_var.set(message)
        logger.info(message)
    
    def create_new_rule_set(self):
        """
        创建新的规则集合
        """
        name = simpledialog.askstring("新建规则集合", "请输入规则集合名称:")
        if not name or not name.strip():
            return
        
        name = name.strip()
        if name in self.washer.config['rule_sets']:
            messagebox.showerror("错误", "该规则集合名称已存在")
            return
        
        # 获取当前装备和通货作为默认值
        default_equipment = self.washer.config['current_equipment']
        default_currency = self.washer.config['current_currency']
        
        # 创建新的规则集合，包含默认装备和通货
        self.washer.config['rule_sets'][name] = {
            'targets': [],
            'equipment': default_equipment,
            'currency': default_currency
        }
        
        # 更新规则集合名称列表
        self.rule_set_names = list(self.washer.config['rule_sets'].keys())
        self.rule_set_combobox['values'] = self.rule_set_names
        
        # 更新装备列表（如果有新装备）
        self.rule_set_equipment_combobox['values'] = self.washer.get_equipment_list()
        
        # 更新通货列表（如果有新通货）
        self.rule_set_currency_combobox['values'] = self.washer.get_currency_list()
        
        # 切换到新创建的规则集合
        self.current_rule_set_var.set(name)
        self.on_rule_set_change(None)
        
        logger.info(f"创建了新规则集合: {name}")
    
    def delete_rule_set(self):
        """
        删除当前规则集合
        """
        current = self.current_rule_set_var.get()
        
        # 不能删除默认规则集合
        if current == '默认规则':
            messagebox.showerror("错误", "不能删除默认规则集合")
            return
        
        if messagebox.askyesno("确认删除", f"确定要删除规则集合 '{current}' 吗？"):
            # 删除规则集合
            del self.washer.config['rule_sets'][current]
            
            # 更新规则集合名称列表
            self.rule_set_names = list(self.washer.config['rule_sets'].keys())
            self.rule_set_combobox['values'] = self.rule_set_names
            
            # 切换到默认规则集合
            self.current_rule_set_var.set('默认规则')
            self.on_rule_set_change(None)
            
            logger.info(f"删除了规则集合: {current}")
    
    def rename_rule_set(self):
        """
        重命名当前规则集合
        """
        current = self.current_rule_set_var.get()
        new_name = simpledialog.askstring("重命名规则集合", f"请输入新的规则集合名称:", initialvalue=current)
        
        if not new_name or not new_name.strip():
            return
        
        new_name = new_name.strip()
        if new_name == current:
            return
        
        if new_name in self.washer.config['rule_sets']:
            messagebox.showerror("错误", "该规则集合名称已存在")
            return
        
        # 重命名规则集合
        self.washer.config['rule_sets'][new_name] = self.washer.config['rule_sets'].pop(current)
        
        # 更新当前规则集合名称
        if self.washer.config['current_rule_set'] == current:
            self.washer.config['current_rule_set'] = new_name
        
        # 更新规则集合名称列表
        self.rule_set_names = list(self.washer.config['rule_sets'].keys())
        self.rule_set_combobox['values'] = self.rule_set_names
        self.current_rule_set_var.set(new_name)
        
        # 更新conditional_targets引用
        self.washer.config['conditional_targets'] = self.washer.config['rule_sets'][new_name]
        
        # 刷新词条列表
        self.refresh_target_list()
        
        # 保存配置
        from ..utils.config_manager import save_config
        save_config(self.washer.config)
        
        logger.info(f"将规则集合 '{current}' 重命名为 '{new_name}'")
    
    def on_target_double_click(self, event):
        """
        处理词条双击事件 - 编辑词条内容
        """
        item = self.target_tree.identify_row(event.y)
        if not item:
            return
        
        # 获取词条信息
        values = self.target_tree.item(item, "values")
        if len(values) < 4:  # 确保有足够的列数据：启用状态、序号、类型、内容
            return
        
        index = int(values[1]) - 1  # 序号减1得到实际索引
        current_text = values[3]  # 内容在第4列
        
        # 获取词条的数值要求
        targets = self.washer.get_targets()
        if index < len(targets):
            current_min_value = targets[index].get('min_value', None)
            # 显示编辑对话框
            self._show_edit_target_dialog(index, current_text, current_min_value, values)
        else:
            messagebox.showerror("错误", "无法找到指定的词条")
    
    def on_target_tree_click(self, event):
        """
        点击启用列切换状态
        """
        item = self.target_tree.identify_row(event.y)
        if not item:
            return
        
        # 检查是否点击了启用列
        col = self.target_tree.identify_column(event.x)
        if col == '#1':  # 启用列
            values = self.target_tree.item(item, 'values')
            if len(values) >= 4:
                # 切换启用状态
                index = int(values[1]) - 1  # 序号减1得到实际索引
                include = True if values[2] == "包含" else False
                current_enabled = True if values[0] == "✓" else False
                new_enabled = not current_enabled
                
                # 使用update_target方法更新启用状态
                if self.washer.update_target(index, text=values[3], include=include, enabled=new_enabled):
                    status_text = "启用" if new_enabled else "禁用"
                    self.status_var.set(f"词条已{status_text}")
                    self.refresh_target_list()
    
    def refresh_equipment_lists(self):
        """
        刷新装备和通货列表
        """
        # 清空装备列表
        for item in self.equipment_tree.get_children():
            self.equipment_tree.delete(item)
        
        # 添加装备
        for name, pos in self.washer.config['equipment_positions'].items():
            pos_text = f"({pos[0]}, {pos[1]})"
            self.equipment_tree.insert("", tk.END, values=(name, pos_text))
        
        # 清空通货列表
        for item in self.currency_tree.get_children():
            self.currency_tree.delete(item)
        
        # 添加通货
        for name, pos in self.washer.config['currency_positions'].items():
            pos_text = f"({pos[0]}, {pos[1]})"
            self.currency_tree.insert("", tk.END, values=(name, pos_text))
    
    def update_current_info(self):
        """
        更新当前信息显示
        """
        logger.debug(f"[update_current_info] 开始更新当前信息")
        
        self.current_equipment_var.set(self.washer.config['current_equipment'] or "未选择")
        self.current_currency_var.set(self.washer.config['current_currency'] or "未选择")
        self.current_match_mode_var.set(self.washer.config['match_mode'])
        
        # 确保下拉菜单显示正确的值，无论当前匹配模式是什么
        if hasattr(self, 'match_count_var'):
            # 获取match_count值，确保它是一个有效的整数
            # print( self.washer.config)
            match_count = self.washer.config.get('match_count')
            # 如果match_count不存在或为None，使用默认值1
            if match_count is None:
                match_count = 1
            # 确保match_count在1-6之间
            match_count = max(1, min(6, match_count))
            # 转换为字符串
            match_count_str = str(match_count)
            logger.debug(f"[update_current_info] 更新下拉菜单值: {match_count_str}")
            self.match_count_var.set(match_count_str)           
    
    def update_stats(self):
        """
        更新统计信息
        """
        stats = self.washer.get_stats()
        self.click_count_var.set(str(stats['click_count']))
        self.attempt_count_var.set(str(stats['current_attempt']))
        self.match_count_var.set(str(stats['last_match_count']))
        
        # 每100毫秒更新一次
        self.root.after(100, self.update_stats)
    
    def setup_global_hotkeys(self):
        """
        设置全局热键
        """
        try:
            # 注册F10、F11和F12的全局热键回调
            self.global_listener.register_callback('f10', self.toggle_washing)
            self.global_listener.register_callback('f11', self.record_equipment_position)
            self.global_listener.register_callback('f12', self.toggle_sequence)
            
            # 注册停止键的全局热键回调
            stop_key = self.washer.config.get('stop_key', 'esc')
            self.global_listener.register_callback(stop_key, self.stop_all_operations)
            logging.info(f"已注册停止键全局热键: {stop_key}")
            
            # 启动全局监听器
            self.global_listener.start()
            # 使用全局logging
            logging.info("全局热键已设置完成")
            
            # 在窗口关闭时停止监听器
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        except Exception as e:
            # 使用全局logging
            logging.error(f"设置全局热键时出错: {str(e)}")
            messagebox.showerror("错误", f"无法设置全局热键: {str(e)}")
    
    def add_sequence_item(self):
        """
        添加序列项
        """
        # 创建对话框
        dialog = tk.Toplevel(self.root)
        dialog.title("添加操作")
        dialog.geometry("400x300")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # 装备选择
        ttk.Label(dialog, text="装备位置:").grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
        equipment_names = list(self.washer.config['equipment_positions'].keys())
        equipment_var = tk.StringVar(value=equipment_names[0] if equipment_names else "")
        equipment_combo = ttk.Combobox(dialog, textvariable=equipment_var, values=equipment_names, width=20, state="readonly")
        equipment_combo.grid(row=0, column=1, padx=10, pady=10)
        
        # 通货选择
        ttk.Label(dialog, text="通货位置:").grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)
        currency_names = list(self.washer.config['currency_positions'].keys())
        currency_var = tk.StringVar(value=currency_names[0] if currency_names else "")
        currency_combo = ttk.Combobox(dialog, textvariable=currency_var, values=currency_names, width=20, state="readonly")
        currency_combo.grid(row=1, column=1, padx=10, pady=10)
        
        # 匹配规则选择 - 从规则集合中选择
        ttk.Label(dialog, text="匹配规则:").grid(row=2, column=0, padx=10, pady=10, sticky=tk.W)
        # 获取所有规则集合名称
        rule_set_names = list(self.washer.config['rule_sets'].keys())
        rules_var = tk.StringVar(value=rule_set_names[0] if rule_set_names else "")
        rules_combo = ttk.Combobox(dialog, textvariable=rules_var, values=rule_set_names, width=20, state="readonly")
        rules_combo.grid(row=2, column=1, padx=10, pady=10)
        
        def on_ok():
            equipment = equipment_var.get()
            currency = currency_var.get()
            rules = rules_var.get()
            
            if not equipment or not currency:
                messagebox.showerror("错误", "请选择装备和通货位置")
                return
            
            # 添加到序列 - 使用选择的规则集合
            selected_rule_set = self.washer.config['rule_sets'][rules]
            self.sequence_items.append({
                'equipment': equipment,
                'currency': currency,
                'rules': rules,
                'rule_set': selected_rule_set['targets'].copy(),  # 保存选择的规则集合的副本
                'enabled': True  # 默认启用
            })
            
            # 保存到配置
            self.washer.config['sequence_items'] = self.sequence_items
            from ..utils.config_manager import save_config
            save_config(self.washer.config)
            
            self.refresh_sequence_list()
            dialog.destroy()
        
        # 按钮
        button_frame = ttk.Frame(dialog)
        button_frame.grid(row=3, column=0, columnspan=2, pady=20)
        
        ttk.Button(button_frame, text="确定", command=on_ok).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="取消", command=dialog.destroy).pack(side=tk.LEFT)
    
    def edit_sequence_item(self):
        """
        编辑序列项
        """
        selected = self.sequence_tree.selection()
        if not selected:
            messagebox.showinfo("提示", "请先选择一个操作")
            return
        
        item = selected[0]
        values = self.sequence_tree.item(item, "values")
        index = int(values[1]) - 1
        
        if 0 <= index < len(self.sequence_items):
            current_item = self.sequence_items[index]
            
            # 创建对话框
            dialog = tk.Toplevel(self.root)
            dialog.title("编辑操作")
            dialog.geometry("400x300")
            dialog.transient(self.root)
            dialog.grab_set()
            
            # 装备选择
            ttk.Label(dialog, text="装备位置:").grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
            equipment_names = list(self.washer.config['equipment_positions'].keys())
            equipment_var = tk.StringVar(value=current_item['equipment'])
            equipment_combo = ttk.Combobox(dialog, textvariable=equipment_var, values=equipment_names, width=20, state="readonly")
            equipment_combo.grid(row=0, column=1, padx=10, pady=10)
            
            # 通货选择
            ttk.Label(dialog, text="通货位置:").grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)
            currency_names = list(self.washer.config['currency_positions'].keys())
            currency_var = tk.StringVar(value=current_item['currency'])
            currency_combo = ttk.Combobox(dialog, textvariable=currency_var, values=currency_names, width=20, state="readonly")
            currency_combo.grid(row=1, column=1, padx=10, pady=10)
            
            # 匹配规则选择 - 从规则集合中选择
            ttk.Label(dialog, text="匹配规则:").grid(row=2, column=0, padx=10, pady=10, sticky=tk.W)
            # 获取所有规则集合名称
            rule_set_names = list(self.washer.config['rule_sets'].keys())
            # 设置默认值为当前规则名称
            rules_var = tk.StringVar(value=current_item['rules'] if current_item['rules'] in rule_set_names else rule_set_names[0] if rule_set_names else "")
            rules_combo = ttk.Combobox(dialog, textvariable=rules_var, values=rule_set_names, width=20, state="readonly")
            rules_combo.grid(row=2, column=1, padx=10, pady=10)
            
            def on_ok():
                equipment = equipment_var.get()
                currency = currency_var.get()
                rules = rules_var.get()
                
                if not equipment or not currency:
                    messagebox.showerror("错误", "请选择装备和通货位置")
                    return
                
                # 更新序列项 - 使用选择的规则集合
                selected_rule_set = self.washer.config['rule_sets'][rules]
                self.sequence_items[index] = {
                    'equipment': equipment,
                    'currency': currency,
                    'rules': rules,
                    'rule_set': selected_rule_set['targets'].copy(),  # 使用选择的规则集合
                    'enabled': self.sequence_items[index].get('enabled', True)  # 保留原有启用状态
                }
                
                # 保存到配置
                self.washer.config['sequence_items'] = self.sequence_items
                from ..utils.config_manager import save_config
                save_config(self.washer.config)
                
                self.refresh_sequence_list()
                dialog.destroy()
            
            # 按钮
            button_frame = ttk.Frame(dialog)
            button_frame.grid(row=3, column=0, columnspan=2, pady=20)
            
            ttk.Button(button_frame, text="确定", command=on_ok).pack(side=tk.LEFT, padx=10)
            ttk.Button(button_frame, text="取消", command=dialog.destroy).pack(side=tk.LEFT)
    
    def remove_sequence_item(self):
        """
        移除序列项
        """
        selected = self.sequence_tree.selection()
        if not selected:
            messagebox.showinfo("提示", "请先选择一个操作")
            return
        
        item = selected[0]
        values = self.sequence_tree.item(item, "values")
        index = int(values[1]) - 1
        
        if 0 <= index < len(self.sequence_items):
            del self.sequence_items[index]
            
            # 保存到配置
            self.washer.config['sequence_items'] = self.sequence_items
            from ..utils.config_manager import save_config
            save_config(self.washer.config)
            
            self.refresh_sequence_list()
    
    def move_sequence_item_up(self):
        """
        上移序列项
        """
        selected = self.sequence_tree.selection()
        if not selected:
            messagebox.showinfo("提示", "请先选择一个操作")
            return
        
        item = selected[0]
        values = self.sequence_tree.item(item, "values")
        index = int(values[1]) - 1
        
        if index > 0:
            # 交换位置
            self.sequence_items[index], self.sequence_items[index-1] = self.sequence_items[index-1], self.sequence_items[index]
            
            # 保存到配置
            self.washer.config['sequence_items'] = self.sequence_items
            from ..utils.config_manager import save_config
            save_config(self.washer.config)
            
            self.refresh_sequence_list()
    
    def move_sequence_item_down(self):
        """
        下移序列项
        """
        selected = self.sequence_tree.selection()
        if not selected:
            messagebox.showinfo("提示", "请先选择一个操作")
            return
        
        item = selected[0]
        values = self.sequence_tree.item(item, "values")
        index = int(values[1]) - 1
        
        if index < len(self.sequence_items) - 1:
            # 交换位置
            self.sequence_items[index], self.sequence_items[index+1] = self.sequence_items[index+1], self.sequence_items[index]
            
            # 保存到配置
            self.washer.config['sequence_items'] = self.sequence_items
            from ..utils.config_manager import save_config
            save_config(self.washer.config)
            
            self.refresh_sequence_list()
    
    def refresh_sequence_list(self):
        """
        刷新序列列表
        """
        # 清空列表
        for item in self.sequence_tree.get_children():
            self.sequence_tree.delete(item)
        
        # 添加序列项
        for i, item in enumerate(self.sequence_items):
            enabled = "✓" if item.get('enabled', True) else ""
            self.sequence_tree.insert("", tk.END, values=(enabled, i+1, item['equipment'], item['currency'], item['rules']))
    
    def on_sequence_tree_click(self, event):
        """
        点击序列树启用列切换状态
        """
        item = self.sequence_tree.identify_row(event.y)
        if not item:
            return
        
        # 检查是否点击了启用列
        col = self.sequence_tree.identify_column(event.x)
        if col == '#1':  # 启用列
            values = self.sequence_tree.item(item, 'values')
            if len(values) >= 5:
                # 切换启用状态
                index = int(values[1]) - 1  # 序号减1得到实际索引
                current_enabled = True if values[0] == "✓" else False
                new_enabled = not current_enabled
                
                # 更新序列项的启用状态
                if 0 <= index < len(self.sequence_items):
                    self.sequence_items[index]['enabled'] = new_enabled
                    
                    # 保存配置
                    self.washer.config['sequence_items'] = self.sequence_items
                    from ..utils.config_manager import save_config
                    save_config(self.washer.config)
                    
                    status_text = "启用" if new_enabled else "禁用"
                    self.status_var.set(f"序列项已{status_text}")
                    self.refresh_sequence_list()
    
    def execute_sequence(self):
        """
        执行序列
        """
        if not self.sequence_items:
            messagebox.showinfo("提示", "序列为空，请先添加操作")
            return
        
        # 设置序列运行标志
        self.washer.running = True
        
        # 更新UI状态
        self.execute_sequence_button.config(state=tk.DISABLED)
        self.stop_sequence_button.config(state=tk.NORMAL)
        self.status_var.set("序列执行中...")
        
        # 在新线程中运行序列执行
        self.sequence_thread = threading.Thread(target=self.run_sequence)
        self.sequence_thread.daemon = True
        self.sequence_thread.start()
    
    def run_sequence(self):
        """
        运行序列执行逻辑
        """
        try:
            # 保存原始规则集，以便执行完成后恢复
            original_rules = self.washer.config['conditional_targets'].copy()
            
            for i, item in enumerate(self.sequence_items):
                # 检查序列是否被手动停止
                if not self.washer.running:
                    logger.info("序列执行已停止")
                    break
                
                # 检查序列项是否启用
                if not item.get('enabled', True):
                    logger.info(f"跳过禁用的序列项 {i+1}: 装备={item['equipment']}, 通货={item['currency']}")
                    continue
                
                logger.info(f"执行序列项 {i+1}/{len(self.sequence_items)}: 装备={item['equipment']}, 通货={item['currency']}")
                
                # 设置当前装备和通货
                self.washer.set_current_equipment(item['equipment'])
                self.washer.set_current_currency(item['currency'])
                
                # 使用该序列项对应的规则集
                ruleset_name = item['rules']
                if ruleset_name in self.washer.config['rule_sets']:
                    # 获取规则集数据
                    rule_data = self.washer.config['rule_sets'][ruleset_name]
                    # 使用规则集的目标词条
                    self.washer.config['conditional_targets'] = rule_data['targets'].copy()
                    logger.info(f"使用序列项 {i+1} 的规则集 '{ruleset_name}'，包含 {len(rule_data['targets'])} 个规则")
                elif 'rule_set' in item:
                    # 兼容旧格式，直接使用保存的规则集
                    self.washer.config['conditional_targets'] = item['rule_set'].copy()
                    logger.info(f"使用序列项 {i+1} 的自定义规则集，包含 {len(item['rule_set'])} 个规则")
                else:
                    logger.warning(f"序列项 {i+1} 无法找到对应的规则集 '{ruleset_name}'")
                
                # 执行洗练 - wash_equipment会在检测到running=False时提前结束，或在正常完成时设置running=False
                result = self.washer.wash_equipment()
                
                if result:
                    logger.info(f"序列项 {i+1} 执行成功")
                else:
                    logger.info(f"序列项 {i+1} 执行失败或未找到匹配装备")
                
                # 检查序列是否被手动停止（可能在洗练过程中被停止）
                if not self.washer.running:
                    logger.info("检测到停止信号，准备结束序列执行")
                    break
                
                # 如果是最后一个序列项，不需要继续执行，直接结束
                if i == len(self.sequence_items) - 1:
                    break
            
            # 恢复原始规则集
            self.washer.config['conditional_targets'] = original_rules
            logger.info("序列执行完成，已恢复原始规则集")
            
            # 更新UI状态
            self.root.after(0, lambda: self.execute_sequence_button.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.stop_sequence_button.config(state=tk.DISABLED))
            self.root.after(0, lambda: self.status_var.set("序列执行完成"))
        except Exception as e:
            # 确保恢复原始规则集
            self.washer.config['conditional_targets'] = original_rules
            logger.error(f"序列执行出错: {e}")
            self.root.after(0, lambda: self.execute_sequence_button.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.stop_sequence_button.config(state=tk.DISABLED))
            self.root.after(0, lambda: self.status_var.set(f"序列执行出错: {str(e)}"))
        finally:
            # 确保运行状态被重置
            self.washer.running = False
    
    def toggle_sequence(self, event=None):
        """
        切换序列执行状态（F12快捷键）
        """
        if self.washer.running:
            self.stop_sequence()
        else:
            self.execute_sequence()
    
    def stop_sequence(self):
        """
        停止序列执行
        """
        self.washer.stop_washing()
        self.execute_sequence_button.config(state=tk.NORMAL)
        self.stop_sequence_button.config(state=tk.DISABLED)
        self.status_var.set("序列执行已停止")
        logger.info("序列执行已停止")
    
    def record_position(self, position_type):
        """
        记录位置
        
        参数:
            position_type (str): 位置类型 ('unknown_card' 或 'storage')
        """
        try:
            # 确保主窗口在前台
            self.root.lift()
            self.root.update_idletasks()
            
            # 创建覆盖层窗口进行位置记录
            self.create_overlay_window(position_type, self.handle_fate_card_position_record)
        except Exception as e:
            error_msg = f"记录位置时出错: {str(e)}"
            logging.error(error_msg)
            self.status_var.set(error_msg)
            messagebox.showerror("错误", error_msg)
    
    def handle_fate_card_position_record(self, x, y, position_type):
        """
        处理命运卡位置记录的回调函数
        
        参数:
            x: 记录的X坐标
            y: 记录的Y坐标
            position_type: 位置类型 ('unknown_card' 或 'storage')
        """
        # 如果取消或坐标无效，直接返回
        if x is None or y is None:
            return
        
        try:
            # 更新配置
            if position_type == 'unknown_card':
                self.washer.config['unknown_fate_card_position'] = (x, y)
                self.unknown_card_pos_var.set(f"{x}, {y}")
                message = f"已成功记录未知命运卡位置 ({x}, {y})"
            elif position_type == 'storage':
                self.washer.config['card_storage_position'] = (x, y)
                self.storage_pos_var.set(f"{x}, {y}")
                message = f"已成功记录存放卡片位置 ({x}, {y})"
            else:
                return
            
            # 保存配置
            from ..utils.config_manager import save_config
            save_config(self.washer.config)
            
            self.status_var.set(message)
            logger.info(message)
            messagebox.showinfo("成功", message)
        except Exception as e:
            error_msg = f"保存位置时出错: {str(e)}"
            logging.error(error_msg)
            self.status_var.set(error_msg)
            messagebox.showerror("错误", error_msg)
    
    def save_fate_card_config(self):
        """
        保存未知命运卡配置
        """
        try:
            # 解析未知命运卡位置
            unknown_pos_str = self.unknown_card_pos_var.get().strip()
            unknown_x, unknown_y = map(int, unknown_pos_str.split(','))
            
            # 解析存放卡片位置
            storage_pos_str = self.storage_pos_var.get().strip()
            storage_x, storage_y = map(int, storage_pos_str.split(','))
            
            # 解析循环次数
            loop_count = int(self.loop_count_var.get().strip())
            
            # 更新配置
            self.washer.config['unknown_fate_card_position'] = (unknown_x, unknown_y)
            self.washer.config['card_storage_position'] = (storage_x, storage_y)
            self.washer.config['fate_card_loop_count'] = loop_count
            
            # 保存配置
            from ..utils.config_manager import save_config
            save_config(self.washer.config)
            
            self.status_var.set("未知命运卡配置已保存")
            logger.info("未知命运卡配置已保存")
            messagebox.showinfo("成功", "未知命运卡配置已保存")
        except ValueError as e:
            error_msg = f"配置值无效: {e}"
            self.status_var.set(error_msg)
            logger.error(error_msg)
            messagebox.showerror("错误", error_msg)
    
    def start_fate_card_process(self):
        """
        开始处理未知命运卡
        """
        # 更新UI状态
        self.start_fate_card_btn.config(state=tk.DISABLED)
        self.stop_fate_card_btn.config(state=tk.NORMAL)
        self.status_var.set("未知命运卡处理中...")
        
        # 在新线程中运行处理逻辑
        self.fate_card_thread = threading.Thread(target=self.run_fate_card_process)
        self.fate_card_thread.daemon = True
        self.fate_card_thread.start()
    
    def run_fate_card_process(self):
        """
        运行未知命运卡处理逻辑
        """
        try:
            result = self.washer.process_fate_cards()
            
            # 更新UI状态
            self.root.after(0, lambda: self.start_fate_card_btn.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.stop_fate_card_btn.config(state=tk.DISABLED))
            
            if result:
                self.root.after(0, lambda: self.status_var.set("未知命运卡处理完成"))
                logger.info("未知命运卡处理完成")
            else:
                self.root.after(0, lambda: self.status_var.set("未知命运卡处理失败"))
        except Exception as e:
            logger.error(f"处理未知命运卡时出错: {e}")
            self.root.after(0, lambda: self.start_fate_card_btn.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.stop_fate_card_btn.config(state=tk.DISABLED))
            self.root.after(0, lambda: self.status_var.set(f"处理未知命运卡时出错: {str(e)}"))
    
    def stop_fate_card_process(self):
        """
        停止处理未知命运卡
        """
        self.washer.stop_washing()
        self.start_fate_card_btn.config(state=tk.NORMAL)
        self.stop_fate_card_btn.config(state=tk.DISABLED)
        self.status_var.set("未知命运卡处理已停止")
        logger.info("未知命运卡处理已停止")
    
    def stop_all_operations(self, event=None):
        """
        停止所有操作（停止键）
        """
        stop_key = self.washer.config.get('stop_key', 'esc')
        logger.info(f"{stop_key.upper()}键被按下，停止所有操作")
        
        # 停止洗练
        if self.washer.is_running():
            self.washer.stop_washing()
            if hasattr(self, 'wash_button'):
                self.wash_button.config(text="开始洗练 (F10)")
        
        # 停止序列执行
        self.washer.running = False
        if hasattr(self, 'execute_sequence_button'):
            self.execute_sequence_button.config(state=tk.NORMAL)
        if hasattr(self, 'stop_sequence_button'):
            self.stop_sequence_button.config(state=tk.DISABLED)
        
        # 停止命运卡处理
        if hasattr(self, 'start_fate_card_btn'):
            self.start_fate_card_btn.config(state=tk.NORMAL)
        if hasattr(self, 'stop_fate_card_btn'):
            self.stop_fate_card_btn.config(state=tk.DISABLED)
        
        self.status_var.set("所有操作已停止")
        logger.info("所有操作已停止")
    
    def on_closing(self):
        """
        窗口关闭事件处理
        """
        try:
            # 停止全局键盘监听器
            if hasattr(self, 'global_listener') and self.global_listener.is_running():
                self.global_listener.stop()
        except Exception as e:
            # 使用全局logger
            logging.error(f"关闭全局监听器时出错: {str(e)}")
        
        # 关闭窗口
        self.root.destroy()


class TextHandler(logging.Handler):
    """
    将日志输出到Tkinter文本框的处理器
    """
    
    def __init__(self, text_widget):
        """
        初始化文本处理器
        
        参数:
            text_widget: Tkinter文本控件
        """
        logging.Handler.__init__(self)
        self.text_widget = text_widget
        # 设置formatter并应用到handler
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        self.setFormatter(formatter)
        
    def emit(self, record):
        """
        输出日志到文本框
        
        参数:
            record: 日志记录
        """
        msg = self.format(record)
        
        def append_log():
            self.text_widget.config(state=tk.NORMAL)
            self.text_widget.insert(tk.END, msg + "\n")
            self.text_widget.see(tk.END)
            self.text_widget.config(state=tk.DISABLED)
        
        self.text_widget.after(0, append_log)


def main():
    """
    主函数
    """
    # 创建根窗口
    root = tk.Tk()
    
    # 创建并运行GUI
    app = PoeWasherGUI(root)
    
    # 运行主循环，添加异常处理以捕获KeyboardInterrupt
    try:
        root.mainloop()
    except KeyboardInterrupt:
        # 捕获Ctrl+C，优雅退出
        print("\n程序已通过Ctrl+C停止")
        root.destroy()


if __name__ == "__main__":
    main()