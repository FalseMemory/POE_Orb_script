#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""POE装备洗练工具 - 用户界面模块"""

import os
import sys
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, simpledialog, messagebox
from src.utils.keyboard_listener import GlobalKeyboardListener
import logging
from ..core.washer_core import PoeClipboardWasher
from ..utils.logger_setup import setup_logger

logger = setup_logger()
import pyautogui


class PoeWasherGUI:
    """POE装备洗练工具图形界面"""

    def __init__(self, root):
        self.root = root
        self.root.title("POE装备洗练工具 - 基于剪贴板分析")
        self.root.geometry("900x700")
        self.root.minsize(800, 500)

        self.washer = PoeClipboardWasher()
        self.washing_thread = None

        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self.tab_control = ttk.Notebook(self.main_frame)
        self.tab_control.pack(fill=tk.BOTH, expand=True)

        self.create_main_tab()
        self.create_target_tab()
        self.create_equipment_tab()
        self.create_sequence_tab()
        self.create_fate_card_tab()
        self.create_config_tab()
        self.create_log_tab()

        self.status_var = tk.StringVar()
        self.status_var.set("就绪 - 等待操作")
        self.status_bar = ttk.Label(root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        self.global_listener = GlobalKeyboardListener()
        self.root.bind('<F10>', self.toggle_washing)
        self.root.bind('<F11>', self.record_equipment_position)
        self.root.bind('<F12>', self.toggle_sequence)
        self.root.bind('<Escape>', self.stop_all_operations)
        self.setup_global_hotkeys()
        self.update_stats()

    def _build_label_grid(self, parent, items, row=0, col=0, sticky=tk.W, padx=2, pady=2):
        """批量创建grid布局的label和variable对"""
        for i, (label_text, var) in enumerate(items):
            ttk.Label(parent, text=label_text).grid(row=row + i, column=col, sticky=sticky, padx=padx, pady=pady)
            ttk.Label(parent, textvariable=var).grid(row=row + i, column=col + 1, sticky=sticky, padx=padx, pady=pady)

    def create_main_tab(self):
        main_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(main_tab, text="主界面")

        desc = (
            "1. 将鼠标放在装备上，按 F11 记录装备位置\n"
            "2. 将鼠标放在通货上，按 F12 记录通货位置\n"
            "3. 在目标词条标签页中设置需要的词条\n"
            "4. 点击'开始洗练'或按 F10 开始自动洗练\n"
            "5. 再次按 F10 停止洗练\n"
            "6. 按 ESC 键可以停止所有操作\n"
            "\n注意：请确保游戏中鼠标悬停在装备上时按Ctrl+C可以复制装备属性。"
        )
        desc_frame = ttk.LabelFrame(main_tab, text="使用说明", padding="10")
        desc_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(desc_frame, text=desc, justify=tk.LEFT).pack(fill=tk.X)

        hint_frame = ttk.Frame(main_tab, padding="10")
        hint_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(hint_frame, text="💡 提示：在任何操作过程中，按 ESC 键可以立即停止所有操作",
                  foreground="blue", font=("Arial", 10, "bold")).pack(fill=tk.X, anchor=tk.CENTER)

        ctrl_frame = ttk.LabelFrame(main_tab, text="洗练控制", padding="10")
        ctrl_frame.pack(fill=tk.X, padx=5, pady=5)
        self.wash_button = ttk.Button(ctrl_frame, text="开始洗练 (F10)", command=self.toggle_washing)
        self.wash_button.pack(side=tk.LEFT, padx=5, pady=5)

        self.status_frame = ttk.Frame(ctrl_frame)
        self.status_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=20)
        self.current_equipment_var = tk.StringVar()
        self.current_currency_var = tk.StringVar()
        self.current_match_mode_var = tk.StringVar()
        self.update_current_info()
        self._build_label_grid(self.status_frame, [
            ("当前装备: ", self.current_equipment_var),
            ("当前通货: ", self.current_currency_var),
            ("匹配模式: ", self.current_match_mode_var),
        ])

        stats_frame = ttk.LabelFrame(main_tab, text="洗练统计", padding="10")
        stats_frame.pack(fill=tk.X, padx=5, pady=5)
        self.click_count_var = tk.StringVar(value="0")
        self.attempt_count_var = tk.StringVar(value="0")
        self.match_count_var = tk.StringVar(value="0")
        self._build_label_grid(stats_frame, [
            ("点击次数: ", self.click_count_var),
            ("尝试次数: ", self.attempt_count_var),
            ("匹配词条: ", self.match_count_var),
        ], col=0)
        ttk.Label(stats_frame, text="匹配词条: ").grid(row=0, column=4, sticky=tk.W, padx=2, pady=2)
        ttk.Label(stats_frame, textvariable=self.match_count_var).grid(row=0, column=5, sticky=tk.W, padx=2, pady=2)

    def create_target_tab(self):
        target_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(target_tab, text="目标词条")

        rule_set_frame = ttk.LabelFrame(target_tab, text="规则集合", padding="10")
        rule_set_frame.pack(fill=tk.X, padx=5, pady=5)

        rule_row1 = ttk.Frame(rule_set_frame)
        rule_row1.pack(fill=tk.X, pady=5)
        ttk.Label(rule_row1, text="当前规则集合:").pack(side=tk.LEFT, padx=5, pady=5)

        self.rule_set_names = list(self.washer.config['rule_sets'].keys())
        self.current_rule_set_var = tk.StringVar(value=self.washer.config['current_rule_set'])
        self.rule_set_combobox = ttk.Combobox(rule_row1, textvariable=self.current_rule_set_var,
                                              values=self.rule_set_names, state="readonly")
        self.rule_set_combobox.pack(side=tk.LEFT, padx=5, pady=5)

        ttk.Button(rule_row1, text="新建规则集", command=self.create_new_rule_set).pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(rule_row1, text="删除规则集", command=self.delete_rule_set).pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(rule_row1, text="重命名规则集", command=self.rename_rule_set).pack(side=tk.LEFT, padx=5, pady=5)

        rule_row2 = ttk.Frame(rule_set_frame)
        rule_row2.pack(fill=tk.X, pady=5)

        self.rule_set_equipment_var = tk.StringVar()
        ttk.Label(rule_row2, text="默认装备:").pack(side=tk.LEFT, padx=5, pady=5)
        self.rule_set_equipment_combobox = ttk.Combobox(rule_row2, textvariable=self.rule_set_equipment_var,
                                                        values=self.washer.get_equipment_list(), state="readonly")
        self.rule_set_equipment_combobox.pack(side=tk.LEFT, padx=5, pady=5)
        self.rule_set_equipment_combobox.bind("<<ComboboxSelected>>", self.on_rule_set_equipment_change)

        self.rule_set_currency_var = tk.StringVar()
        ttk.Label(rule_row2, text="默认通货:").pack(side=tk.LEFT, padx=5, pady=5)
        self.rule_set_currency_combobox = ttk.Combobox(rule_row2, textvariable=self.rule_set_currency_var,
                                                       values=self.washer.get_currency_list(), state="readonly")
        self.rule_set_currency_combobox.pack(side=tk.LEFT, padx=5, pady=5)
        self.rule_set_currency_combobox.bind("<<ComboboxSelected>>", self.on_rule_set_currency_change)

        self.rule_set_combobox.bind("<<ComboboxSelected>>", self.on_rule_set_change)
        ttk.Button(rule_row2, text="应用设置", command=self.apply_rule_set_settings).pack(side=tk.LEFT, padx=5, pady=5)

        list_frame = ttk.LabelFrame(target_tab, text="目标词条列表", padding="10")
        list_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

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
        self.target_tree.bind("<Double-1>", self.on_target_double_click)
        self.target_tree.bind("<Button-1>", self.on_target_tree_click)
        self.target_tree.pack(fill=tk.BOTH, expand=True, side=tk.TOP)

        button_frame = ttk.Frame(target_tab, padding="10")
        button_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)

        ttk.Button(button_frame, text="添加包含词条", command=self.add_include_target).pack(fill=tk.X, pady=5)
        ttk.Button(button_frame, text="添加排除词条", command=self.add_exclude_target).pack(fill=tk.X, pady=5)
        ttk.Button(button_frame, text="移除选中词条", command=self.remove_selected_target).pack(fill=tk.X, pady=5)

        mode_frame = ttk.LabelFrame(button_frame, text="匹配模式", padding="10")
        mode_frame.pack(fill=tk.X, pady=10)

        self.match_mode = tk.StringVar(value=self.washer.config['match_mode'])
        ttk.Radiobutton(mode_frame, text="全匹配 (AND)", variable=self.match_mode, value="AND",
                        command=self.update_match_mode).pack(anchor=tk.W)
        ttk.Radiobutton(mode_frame, text="任一匹配 (OR)", variable=self.match_mode, value="OR",
                        command=self.update_match_mode).pack(anchor=tk.W)

        count_frame = ttk.Frame(mode_frame)
        count_frame.pack(anchor=tk.W, pady=5)
        ttk.Radiobutton(count_frame, text="数量匹配 (COUNT):", variable=self.match_mode, value="COUNT",
                        command=self.update_match_mode).pack(side=tk.LEFT)

        self.match_count_var = tk.StringVar(value=str(self.washer.config.get('match_count', 1)))
        self.match_count_combobox = ttk.Combobox(count_frame, textvariable=self.match_count_var,
                                                 values=["1", "2", "3", "4", "5", "6"], width=3, state="readonly")
        self.match_count_combobox.pack(side=tk.LEFT, padx=5)
        self.match_count_combobox.bind("<<ComboboxSelected>>", lambda e: self.update_match_mode())
        ttk.Label(count_frame, text="条规则满足").pack(side=tk.LEFT)

        self.refresh_target_list()

    def create_equipment_tab(self):
        equipment_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(equipment_tab, text="装备管理")

        equip_frame = ttk.LabelFrame(equipment_tab, text="装备位置", padding="10")
        equip_frame.pack(fill=tk.X, padx=5, pady=5)

        columns = ("name", "position")
        self.equipment_tree = ttk.Treeview(equip_frame, columns=columns, show="headings", height=8)
        self.equipment_tree.heading("name", text="装备名称")
        self.equipment_tree.heading("position", text="位置")
        self.equipment_tree.column("name", width=200, anchor=tk.W)
        self.equipment_tree.column("position", anchor=tk.W)
        self.equipment_tree.pack(fill=tk.X, side=tk.TOP, padx=5, pady=5)

        equip_btn_frame = ttk.Frame(equip_frame)
        equip_btn_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=5)
        ttk.Button(equip_btn_frame, text="记录位置 (截图模式)", command=self.record_equipment_position).pack(side=tk.LEFT, padx=5)
        ttk.Button(equip_btn_frame, text="编辑装备", command=self.edit_equipment_position).pack(side=tk.LEFT, padx=5)
        ttk.Button(equip_btn_frame, text="使用选中装备", command=self.use_selected_equipment).pack(side=tk.LEFT, padx=5)
        ttk.Button(equip_btn_frame, text="移除选中装备", command=self.remove_selected_equipment).pack(side=tk.LEFT, padx=5)

        currency_frame = ttk.LabelFrame(equipment_tab, text="通货位置", padding="10")
        currency_frame.pack(fill=tk.X, padx=5, pady=5)

        self.currency_tree = ttk.Treeview(currency_frame, columns=columns, show="headings", height=8)
        self.currency_tree.heading("name", text="通货名称")
        self.currency_tree.heading("position", text="位置")
        self.currency_tree.column("name", width=200, anchor=tk.W)
        self.currency_tree.column("position", anchor=tk.W)
        self.currency_tree.pack(fill=tk.X, side=tk.TOP, padx=5, pady=5)

        currency_btn_frame = ttk.Frame(currency_frame)
        currency_btn_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=5)
        ttk.Button(currency_btn_frame, text="记录位置 (截图模式)", command=self.record_currency_position).pack(side=tk.LEFT, padx=5)
        ttk.Button(currency_btn_frame, text="编辑通货", command=self.edit_currency_position).pack(side=tk.LEFT, padx=5)
        ttk.Button(currency_btn_frame, text="使用选中通货", command=self.use_selected_currency).pack(side=tk.LEFT, padx=5)
        ttk.Button(currency_btn_frame, text="移除选中通货", command=self.remove_selected_currency).pack(side=tk.LEFT, padx=5)

        self.refresh_equipment_lists()

    def create_config_tab(self):
        config_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(config_tab, text="配置")

        delay_frame = ttk.LabelFrame(config_tab, text="延迟设置", padding="10")
        delay_frame.pack(fill=tk.X, padx=5, pady=5)

        self.click_duration_var = tk.StringVar(value=str(self.washer.config['click_duration']))
        self.operation_delay_var = tk.StringVar(value=str(self.washer.config['operation_delay']))
        self.clipboard_delay_var = tk.StringVar(value=str(self.washer.config['clipboard_check_delay']))
        self.max_attempts_var = tk.StringVar(value=str(self.washer.config['max_attempts']))
        self.stop_key_var = tk.StringVar(value=str(self.washer.config.get('stop_key', 'esc')))

        fields = [
            ("点击持续时间 (秒):", self.click_duration_var),
            ("操作间隔延迟 (秒):", self.operation_delay_var),
            ("剪贴板检查延迟 (秒):", self.clipboard_delay_var),
        ]
        for i, (label, var) in enumerate(fields):
            ttk.Label(delay_frame, text=label).grid(row=i, column=0, sticky=tk.W, padx=5, pady=5)
            ttk.Entry(delay_frame, textvariable=var, width=10).grid(row=i, column=1, sticky=tk.W, padx=5, pady=5)

        other_frame = ttk.LabelFrame(config_tab, text="其他设置", padding="10")
        other_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(other_frame, text="最大尝试次数:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Entry(other_frame, textvariable=self.max_attempts_var, width=10).grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)

        ttk.Label(other_frame, text="停止键:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        stop_opts = ['esc', 'f1', 'f2', 'f3', 'f4', 'f5', 'f6', 'f7', 'f8', 'f9', 'f10', 'f11', 'f12', 'pause', 'insert', 'home', 'pageup', 'pagedown', 'end', 'delete']
        ttk.Combobox(other_frame, textvariable=self.stop_key_var, values=stop_opts, width=10, state="readonly").grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)

        config_btns = ttk.Frame(config_tab, padding="10")
        config_btns.pack(fill=tk.X, padx=5, pady=5)
        ttk.Button(config_btns, text="保存配置", command=self.save_config).pack(side=tk.LEFT, padx=5)
        ttk.Button(config_btns, text="导出配置", command=self.export_config).pack(side=tk.LEFT, padx=5)
        ttk.Button(config_btns, text="导入配置", command=self.import_config).pack(side=tk.LEFT, padx=5)

    def create_sequence_tab(self):
        sequence_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(sequence_tab, text="顺序执行")

        seq_frame = ttk.LabelFrame(sequence_tab, text="执行序列", padding="10")
        seq_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        columns = ("enabled", "index", "equipment", "currency", "rules")
        self.sequence_tree = ttk.Treeview(seq_frame, columns=columns, show="headings", height=15)
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
        self.sequence_tree.bind("<Button-1>", self.on_sequence_tree_click)
        self.sequence_tree.pack(fill=tk.BOTH, expand=True, side=tk.TOP, padx=5, pady=5)

        btn_frame = ttk.Frame(seq_frame, padding="10")
        btn_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=5, pady=5)

        left_btns = ttk.Frame(btn_frame)
        left_btns.pack(side=tk.LEFT)
        ttk.Button(left_btns, text="添加操作", command=self.add_sequence_item).pack(side=tk.LEFT, padx=5)
        ttk.Button(left_btns, text="编辑操作", command=self.edit_sequence_item).pack(side=tk.LEFT, padx=5)
        ttk.Button(left_btns, text="移除操作", command=self.remove_sequence_item).pack(side=tk.LEFT, padx=5)

        right_btns = ttk.Frame(btn_frame)
        right_btns.pack(side=tk.RIGHT)
        ttk.Button(right_btns, text="上移", command=self.move_sequence_item_up).pack(side=tk.LEFT, padx=5)
        ttk.Button(right_btns, text="下移", command=self.move_sequence_item_down).pack(side=tk.LEFT, padx=5)

        exec_frame = ttk.Frame(sequence_tab, padding="10")
        exec_frame.pack(fill=tk.X, padx=5, pady=5)
        self.execute_sequence_button = ttk.Button(exec_frame, text="开始执行序列", command=self.execute_sequence)
        self.execute_sequence_button.pack(side=tk.LEFT, padx=5)
        self.stop_sequence_button = ttk.Button(exec_frame, text="停止执行", command=self.stop_sequence, state=tk.DISABLED)
        self.stop_sequence_button.pack(side=tk.LEFT, padx=5)

        hint_frame = ttk.Frame(sequence_tab, padding="10")
        hint_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(hint_frame, text="💡 提示：在任何操作过程中，按 ESC 键可以立即停止所有操作",
                  foreground="blue", font=("Arial", 10, "bold")).pack(fill=tk.X, anchor=tk.CENTER)

        self.sequence_items = self.washer.config.get('sequence_items', [])
        self.refresh_sequence_list()

    def create_fate_card_tab(self):
        fate_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(fate_tab, text="未知命运卡")

        config_frame = ttk.LabelFrame(fate_tab, text="配置", padding="10")
        config_frame.pack(fill=tk.X, padx=5, pady=5)

        self.unknown_card_pos_var = tk.StringVar(value=f"{self.washer.config.get('unknown_fate_card_position', (0,0))[0]}, {self.washer.config.get('unknown_fate_card_position', (0,0))[1]}")
        self.storage_pos_var = tk.StringVar(value=f"{self.washer.config.get('card_storage_position', (0,0))[0]}, {self.washer.config.get('card_storage_position', (0,0))[1]}")
        self.loop_count_var = tk.StringVar(value=str(self.washer.config.get('fate_card_loop_count', 10)))

        ttk.Label(config_frame, text="未知命运卡位置:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Entry(config_frame, textvariable=self.unknown_card_pos_var, width=20).grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        ttk.Button(config_frame, text="记录位置", command=lambda: self.record_position('unknown_card')).grid(row=0, column=2, padx=5, pady=5)

        ttk.Label(config_frame, text="存放卡片位置:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Entry(config_frame, textvariable=self.storage_pos_var, width=20).grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        ttk.Button(config_frame, text="记录位置", command=lambda: self.record_position('storage')).grid(row=1, column=2, padx=5, pady=5)

        ttk.Label(config_frame, text="循环次数:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Entry(config_frame, textvariable=self.loop_count_var, width=10).grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)

        ttk.Button(config_frame, text="保存配置", command=self.save_fate_card_config).grid(row=3, column=0, columnspan=3, pady=10)

        ctrl_frame = ttk.LabelFrame(fate_tab, text="操作", padding="10")
        ctrl_frame.pack(fill=tk.X, padx=5, pady=5)
        self.start_fate_card_btn = ttk.Button(ctrl_frame, text="开始处理", command=self.start_fate_card_process)
        self.start_fate_card_btn.pack(side=tk.LEFT, padx=5)
        self.stop_fate_card_btn = ttk.Button(ctrl_frame, text="停止处理", command=self.stop_fate_card_process, state=tk.DISABLED)
        self.stop_fate_card_btn.pack(side=tk.LEFT, padx=5)

        hint_frame = ttk.Frame(fate_tab, padding="10")
        hint_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(hint_frame, text="💡 提示：在任何操作过程中，按 ESC 键可以立即停止所有操作",
                  foreground="blue", font=("Arial", 10, "bold")).pack(fill=tk.X, anchor=tk.CENTER)

    def create_log_tab(self):
        log_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(log_tab, text="日志")
        self.log_text = scrolledtext.ScrolledText(log_tab, wrap=tk.WORD, height=25)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.log_text.config(state=tk.DISABLED)
        self.log_handler = TextHandler(self.log_text)
        self.log_handler.setLevel(logging.INFO)
        logger.addHandler(self.log_handler)

    def toggle_washing(self, event=None):
        self.stop_washing() if self.washer.is_running() else self.start_washing()

    def start_washing(self):
        if not self.washer.config['current_equipment']:
            messagebox.showerror("错误", "请先记录并选择装备位置")
            return
        if not self.washer.config['current_currency']:
            messagebox.showerror("错误", "请先记录并选择通货位置")
            return
        if not self.washer.config['conditional_targets']:
            messagebox.showerror("错误", "请添加至少一个目标词条")
            return
        self.wash_button.config(text="停止洗练 (F10)")
        self.status_var.set("洗练中...")
        self.washing_thread = threading.Thread(target=self.run_washing, daemon=True)
        self.washing_thread.start()

    def stop_washing(self):
        self.washer.stop_washing()
        self.wash_button.config(text="开始洗练 (F10)")
        self.status_var.set("已停止洗练")

    def run_washing(self):
        try:
            result = self.washer.wash_equipment()
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
        trigger = "快捷键F11" if event else "按钮点击"
        logging.info(f"{trigger}触发，开始记录装备位置")
        self.root.lift()
        self.root.update_idletasks()
        self.create_overlay_window('equipment', self.handle_position_record)

    def record_currency_position(self, event=None):
        trigger = "快捷键F12" if event else "按钮点击"
        logging.info(f"{trigger}触发，开始记录通货位置")
        self.root.lift()
        self.root.update_idletasks()
        self.create_overlay_window('currency', self.handle_position_record)

    def handle_position_record(self, x, y, position_type):
        if x is None or y is None:
            return
        try:
            dialog = tk.Toplevel(self.root)
            ptype = '装备' if position_type == 'equipment' else '通货'
            dialog.title(f"记录{ptype}名称")
            dialog.geometry("400x150")
            dialog.transient(self.root)
            dialog.grab_set()
            dialog.lift()
            ttk.Label(dialog, text=f"请输入{ptype}名称:").pack(pady=10)
            name_var = tk.StringVar()
            ttk.Entry(dialog, textvariable=name_var, width=30).pack(pady=5)

            confirmed = False

            def on_ok():
                nonlocal confirmed
                confirmed = True
                dialog.destroy()

            btn_frame = ttk.Frame(dialog)
            btn_frame.pack(pady=10)
            ttk.Button(btn_frame, text="确定", command=on_ok).pack(side=tk.LEFT, padx=5)
            ttk.Button(btn_frame, text="取消", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
            dialog.bind('<Return>', lambda e: on_ok())
            dialog.bind('<Escape>', lambda e: dialog.destroy())
            self.root.wait_window(dialog)

            name = name_var.get().strip() if confirmed else ""
            if name:
                logging.info(f"用户输入的{position_type}名称: {name}, 位置: ({x}, {y})")
                if position_type == 'equipment':
                    self.washer.config['equipment_positions'][name] = (x, y)
                    self.washer.config['current_equipment'] = name
                elif position_type == 'currency':
                    self.washer.config['currency_positions'][name] = (x, y)
                    self.washer.config['current_currency'] = name

                from ..utils.config_manager import save_config
                save_config(self.washer.config)
                self.refresh_equipment_lists()
                self.update_current_info()
                msg = f"已成功记录{ptype} '{name}' 的位置 ({x}, {y})"
                self.status_var.set(msg)
                logging.info(msg)
                messagebox.showinfo("成功", msg)
        except Exception as e:
            error_msg = f"保存{position_type}位置时出错: {str(e)}"
            logging.error(error_msg)
            self.status_var.set(error_msg)
            messagebox.showerror("错误", error_msg)

    def create_overlay_window(self, position_type, callback):
        overlay = tk.Toplevel(self.root)
        overlay.attributes('-fullscreen', True)
        overlay.attributes('-topmost', True)
        overlay.overrideredirect(True)
        overlay.attributes('-alpha', 0.7)

        canvas = tk.Canvas(overlay, bg='#333333', highlightthickness=0)
        canvas.pack(fill=tk.BOTH, expand=True)

        position_label = tk.Label(canvas, text="", font=('Microsoft YaHei', 12), bg='#FFFFFF', fg='#000000', relief=tk.SUNKEN)
        ptype = '装备' if position_type == 'equipment' else '通货'
        hint_label = tk.Label(canvas, text=f"点击要记录的{ptype}位置\n按ESC键取消", font=('Microsoft YaHei', 14, 'bold'), bg='#FF0000', fg='#FFFFFF')
        hint_label.place(relx=0.5, rely=0.1, anchor=tk.CENTER)

        def on_mouse_move(event):
            px, py = pyautogui.position()
            position_label.config(text=f"位置: ({px}, {py})")
            lx = event.x_root + 10
            ly = event.y_root - 30
            sw, sh = overlay.winfo_screenwidth(), overlay.winfo_screenheight()
            lw, lh = position_label.winfo_reqwidth(), position_label.winfo_reqheight()
            if lx + lw > sw:
                lx = sw - lw - 10
            if ly < 0:
                ly = 10
            canvas.create_window(lx, ly, window=position_label, anchor=tk.NW)

        def on_mouse_click(event):
            px, py = pyautogui.position()
            logging.info(f"用户点击记录{ptype}位置: ({px}, {py})")
            overlay.destroy()
            callback(px, py, position_type)

        def on_escape(event):
            logging.info(f"用户取消记录{ptype}位置")
            overlay.destroy()
            callback(None, None, position_type)

        canvas.bind('<Motion>', on_mouse_move)
        canvas.bind('<Button-1>', on_mouse_click)
        overlay.bind('<Escape>', on_escape)
        canvas.position_label = position_label
        canvas.hint_label = hint_label
        return overlay

    def add_include_target(self):
        self._show_add_target_dialog("添加包含词条", include=True)

    def add_exclude_target(self):
        self._show_add_target_dialog("添加排除词条", include=False)

    def _show_edit_target_dialog(self, index, current_text, current_min_value, tree_values):
        self._show_target_dialog("编辑词条", tree_values[2] == "包含", tree_values[0] == "✓",
                                 lambda t, mv: self.washer.update_target(index, text=t,
                                        include=(tree_values[2] == "包含"), enabled=(tree_values[0] == "✓"),
                                        min_value=mv),
                                 initial_text=current_text, initial_min_value=current_min_value)

    def _show_add_target_dialog(self, title, include):
        self._show_target_dialog(title, include, True,
                                 lambda t, mv: self.washer.add_target(t, include=include, enabled=True, min_value=mv))

    def _show_target_dialog(self, title, include, enabled, save_callback, initial_text="", initial_min_value=None):
        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.geometry("400x200")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.update_idletasks()
        w, h = dialog.winfo_width(), dialog.winfo_height()
        x = (self.root.winfo_width() // 2) - (w // 2) + self.root.winfo_x()
        y = (self.root.winfo_height() // 2) - (h // 2) + self.root.winfo_y()
        dialog.geometry(f"+{x}+{y}")

        ttk.Label(dialog, text="词条内容:").grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
        text_var = tk.StringVar(value=initial_text)
        ttk.Entry(dialog, textvariable=text_var, width=30).grid(row=0, column=1, padx=10, pady=10)

        ttk.Label(dialog, text="最小数值要求 (可选):").grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)
        min_var = tk.StringVar(value="" if initial_min_value is None else str(initial_min_value))
        ttk.Entry(dialog, textvariable=min_var, width=10).grid(row=1, column=1, padx=10, pady=10, sticky=tk.W)

        def on_ok():
            text = text_var.get().strip()
            if not text:
                messagebox.showerror("错误", "词条内容不能为空")
                return
            min_value = None
            if min_var.get().strip():
                try:
                    min_value = float(min_var.get().strip())
                except ValueError:
                    messagebox.showerror("错误", "请输入有效的数值")
                    return
            save_callback(text, min_value)
            self.refresh_target_list()
            dialog.destroy()

        btn_frame = ttk.Frame(dialog)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=10)
        ttk.Button(btn_frame, text="确定", command=on_ok).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="取消", command=dialog.destroy).pack(side=tk.LEFT)

    def remove_selected_target(self):
        selected = self.target_tree.selection()
        if selected:
            index = int(self.target_tree.item(selected[0], "values")[1]) - 1
            self.washer.remove_target(index)
            self.refresh_target_list()

    def _edit_position_dialog(self, tree, positions_dict, config_key, current_config_key, pos_config_key, label):
        selected = tree.selection()
        if not selected:
            messagebox.showinfo("提示", f"请先选中一个{label}")
            return

        old_name = tree.item(selected[0], "values")[0]
        current_pos = positions_dict.get(old_name, (0, 0))
        pos_str = f"{current_pos[0]}, {current_pos[1]}"

        dialog = tk.Toplevel(self.root)
        dialog.title(f"编辑{label}")
        dialog.geometry("400x250")
        dialog.transient(self.root)
        dialog.grab_set()

        ttk.Label(dialog, text=f"{label}名称:").grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
        name_var = tk.StringVar(value=old_name)
        ttk.Entry(dialog, textvariable=name_var, width=25).grid(row=0, column=1, padx=10, pady=10)

        ttk.Label(dialog, text="位置坐标:").grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)
        pos_var = tk.StringVar(value=pos_str)
        ttk.Entry(dialog, textvariable=pos_var, width=25).grid(row=1, column=1, padx=10, pady=10)

        def on_ok():
            new_name = name_var.get().strip()
            p = pos_var.get().strip()
            if not new_name:
                messagebox.showerror("错误", f"{label}名称不能为空")
                return
            if not p:
                messagebox.showerror("错误", "位置坐标不能为空")
            try:
                x, y = map(int, p.split(','))
                if x < 0 or y < 0:
                    raise ValueError("坐标值不能为负数")

                from ..utils.config_manager import save_config
                if new_name != old_name:
                    if new_name in positions_dict:
                        messagebox.showerror("错误", f"该{label}名称已存在")
                        return
                    del positions_dict[old_name]
                    positions_dict[new_name] = (x, y)
                    if self.washer.config[current_config_key] == old_name:
                        self.washer.config[current_config_key] = new_name
                        self.washer.config[pos_config_key] = (x, y)
                else:
                    positions_dict[new_name] = (x, y)
                    if self.washer.config[current_config_key] == new_name:
                        self.washer.config[pos_config_key] = (x, y)

                save_config(self.washer.config)
                self.refresh_equipment_lists()
                self.update_current_info()
                msg = f"已更新{label} '{new_name}' 的位置为 ({x}, {y})"
                self.status_var.set(msg)
                logger.info(msg)
                messagebox.showinfo("成功", msg)
                dialog.destroy()
            except ValueError as e:
                messagebox.showerror("错误", f"输入格式错误: {str(e)}")

        btn_frame = ttk.Frame(dialog)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=20)
        ttk.Button(btn_frame, text="确定", command=on_ok).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="取消", command=dialog.destroy).pack(side=tk.LEFT)

    def use_selected_equipment(self):
        selected = self.equipment_tree.selection()
        if selected:
            name = self.equipment_tree.item(selected[0], "values")[0]
            if self.washer.set_current_equipment(name):
                self.update_current_info()
                self.status_var.set(f"当前装备已设置为: {name}")

    def remove_selected_equipment(self):
        self._remove_position_item(self.equipment_tree, self.washer.config['equipment_positions'], 'current_equipment', '装备')

    def _remove_position_item(self, tree, positions_dict, current_key, label):
        selected = tree.selection()
        if not selected:
            messagebox.showinfo("提示", f"请先选中一个{label}")
            return
        name = tree.item(selected[0], "values")[0]
        if name in positions_dict:
            del positions_dict[name]
            if self.washer.config[current_key] == name:
                self.washer.config[current_key] = None
            from ..utils.config_manager import save_config
            save_config(self.washer.config)
            self.refresh_equipment_lists()
            self.update_current_info()
            messagebox.showinfo("成功", f"已移除{label}: {name}")
        else:
            messagebox.showerror("错误", f"找不到该{label}")

    def edit_equipment_position(self):
        self._edit_position_dialog(self.equipment_tree, self.washer.config['equipment_positions'],
                                   'equipment_positions', 'current_equipment', 'current_equipment_position', '装备')

    def use_selected_currency(self):
        selected = self.currency_tree.selection()
        if selected:
            name = self.currency_tree.item(selected[0], "values")[0]
            if self.washer.set_current_currency(name):
                self.update_current_info()
                self.status_var.set(f"当前通货已设置为: {name}")

    def remove_selected_currency(self):
        self._remove_position_item(self.currency_tree, self.washer.config['currency_positions'], 'current_currency', '通货')

    def edit_currency_position(self):
        self._edit_position_dialog(self.currency_tree, self.washer.config['currency_positions'],
                                   'currency_positions', 'current_currency', 'currency_position', '通货')

    def update_match_mode(self, value=None):
        mode = self.match_mode.get()
        if mode == "COUNT":
            try:
                count = int(self.match_count_var.get())
                if count < 1 or count > 6:
                    messagebox.showerror("错误", "匹配数量必须在1-6之间")
                    return
                if self.washer.set_match_mode(mode, count):
                    self.update_current_info()
            except Exception as e:
                logger.error(f"更新匹配模式时出错: {str(e)}")
                messagebox.showerror("错误", f"更新匹配模式失败: {str(e)}")
        else:
            self.washer.set_match_mode(mode)
            self.update_current_info()

    def save_config(self):
        try:
            self.washer.set_delay_settings(
                float(self.click_duration_var.get()),
                float(self.operation_delay_var.get()),
                float(self.clipboard_delay_var.get())
            )
            self.washer.config['max_attempts'] = int(self.max_attempts_var.get())
            self.washer.config['stop_key'] = self.stop_key_var.get().lower()
            from ..utils.config_manager import save_config
            save_config(self.washer.config)
            self.setup_global_hotkeys()
            self.status_var.set("配置已保存")
        except ValueError as e:
            messagebox.showerror("错误", f"配置值无效: {e}")

    def export_config(self):
        try:
            from tkinter import filedialog
            from ..utils.config_manager import save_config
            fp = filedialog.asksaveasfilename(defaultextension=".ini", filetypes=[("INI配置文件", "*.ini"), ("所有文件", "*.*")], title="导出配置")
            if fp:
                save_config(self.washer.config, fp)
                self.status_var.set(f"配置已导出到: {fp}")
                logger.info(f"配置已导出到: {fp}")
                messagebox.showinfo("成功", f"配置已导出到: {fp}")
        except Exception as e:
            logger.error(f"导出配置失败: {e}")
            messagebox.showerror("错误", f"导出配置失败: {e}")

    def import_config(self):
        try:
            from tkinter import filedialog
            from ..utils.config_manager import load_config
            fp = filedialog.askopenfilename(defaultextension=".ini", filetypes=[("INI配置文件", "*.ini"), ("所有文件", "*.*")], title="导入配置")
            if fp:
                imported = load_config(fp)
                self.washer.config.update(imported)
                self.update_current_info()
                self.click_duration_var.set(str(self.washer.config['click_duration']))
                self.operation_delay_var.set(str(self.washer.config['operation_delay']))
                self.clipboard_delay_var.set(str(self.washer.config['clipboard_check_delay']))
                self.max_attempts_var.set(str(self.washer.config['max_attempts']))
                self.stop_key_var.set(str(self.washer.config['stop_key']))
                self.refresh_equipment_lists()
                self.refresh_target_list()
                self.rule_set_names = list(self.washer.config['rule_sets'].keys())
                self.rule_set_combobox['values'] = self.rule_set_names
                self.current_rule_set_var.set(self.washer.config['current_rule_set'])
                if hasattr(self, 'rule_set_equipment_var'):
                    rd = self.washer.config['rule_sets'][self.washer.config['current_rule_set']]
                    self.rule_set_equipment_var.set(rd['equipment'])
                    self.rule_set_currency_var.set(rd['currency'])
                self.setup_global_hotkeys()
                self.status_var.set(f"配置已从 {fp} 导入")
                logger.info(f"配置已从 {fp} 导入")
                messagebox.showinfo("成功", f"配置已从 {fp} 导入")
        except Exception as e:
            logger.error(f"导入配置失败: {e}")
            messagebox.showerror("错误", f"导入配置失败: {e}")

    def refresh_target_list(self):
        for item in self.target_tree.get_children():
            self.target_tree.delete(item)
        for i, t in enumerate(self.washer.get_targets()):
            ttype = "包含" if t['include'] else "排除"
            enabled = "✓" if t.get('enabled', True) else ""
            self.target_tree.insert("", tk.END, values=(enabled, i + 1, ttype, t['text']))

    def _sync_rule_set(self):
        current = self.current_rule_set_var.get()
        rd = self.washer.config['rule_sets'][current]
        self.washer.config['current_rule_set'] = current
        self.washer.config['conditional_targets'] = rd['targets']
        self.washer.config['current_equipment'] = rd['equipment']
        self.washer.config['current_currency'] = rd['currency']
        self.update_current_info()
        self.refresh_target_list()
        from ..utils.config_manager import save_config
        save_config(self.washer.config)

    def on_rule_set_change(self, event):
        self._sync_rule_set()

    def on_rule_set_equipment_change(self, event):
        current = self.current_rule_set_var.get()
        self.washer.config['rule_sets'][current]['equipment'] = self.rule_set_equipment_var.get()
        if self.washer.config['current_rule_set'] == current:
            self.washer.config['current_equipment'] = self.rule_set_equipment_var.get()
            self.washer.config['current_equipment_position'] = self.washer.config['equipment_positions'].get(self.rule_set_equipment_var.get(), (0, 0))
        self.update_current_info()
        from ..utils.config_manager import save_config
        save_config(self.washer.config)

    def on_rule_set_currency_change(self, event):
        current = self.current_rule_set_var.get()
        self.washer.config['rule_sets'][current]['currency'] = self.rule_set_currency_var.get()
        if self.washer.config['current_rule_set'] == current:
            self.washer.config['current_currency'] = self.rule_set_currency_var.get()
            self.washer.config['currency_position'] = self.washer.config['currency_positions'].get(self.rule_set_currency_var.get(), (0, 0))
        self.update_current_info()
        from ..utils.config_manager import save_config
        save_config(self.washer.config)

    def apply_rule_set_settings(self):
        self._sync_rule_set()
        msg = f"已应用规则集合 '{self.current_rule_set_var.get()}' 的设置"
        self.status_var.set(msg)
        logger.info(msg)

    def create_new_rule_set(self):
        name = simpledialog.askstring("新建规则集合", "请输入规则集合名称:")
        if not name or not name.strip():
            return
        name = name.strip()
        if name in self.washer.config['rule_sets']:
            messagebox.showerror("错误", "该规则集合名称已存在")
            return
        self.washer.config['rule_sets'][name] = {
            'targets': [],
            'equipment': self.washer.config['current_equipment'],
            'currency': self.washer.config['current_currency']
        }
        self.rule_set_names = list(self.washer.config['rule_sets'].keys())
        self.rule_set_combobox['values'] = self.rule_set_names
        self.current_rule_set_var.set(name)
        self.on_rule_set_change(None)
        logger.info(f"创建了新规则集合: {name}")

    def delete_rule_set(self):
        current = self.current_rule_set_var.get()
        if current == '默认规则':
            messagebox.showerror("错误", "不能删除默认规则集合")
            return
        if messagebox.askyesno("确认删除", f"确定要删除规则集合 '{current}' 吗？"):
            del self.washer.config['rule_sets'][current]
            self.rule_set_names = list(self.washer.config['rule_sets'].keys())
            self.rule_set_combobox['values'] = self.rule_set_names
            self.current_rule_set_var.set('默认规则')
            self.on_rule_set_change(None)
            logger.info(f"删除了规则集合: {current}")

    def rename_rule_set(self):
        current = self.current_rule_set_var.get()
        new_name = simpledialog.askstring("重命名规则集合", "请输入新的规则集合名称:", initialvalue=current)
        if not new_name or not new_name.strip() or new_name.strip() == current:
            return
        new_name = new_name.strip()
        if new_name in self.washer.config['rule_sets']:
            messagebox.showerror("错误", "该规则集合名称已存在")
            return
        self.washer.config['rule_sets'][new_name] = self.washer.config['rule_sets'].pop(current)
        if self.washer.config['current_rule_set'] == current:
            self.washer.config['current_rule_set'] = new_name
        self.rule_set_names = list(self.washer.config['rule_sets'].keys())
        self.rule_set_combobox['values'] = self.rule_set_names
        self.current_rule_set_var.set(new_name)
        self.washer.config['conditional_targets'] = self.washer.config['rule_sets'][new_name]
        self.refresh_target_list()
        from ..utils.config_manager import save_config
        save_config(self.washer.config)
        logger.info(f"将规则集合 '{current}' 重命名为 '{new_name}'")

    def on_target_double_click(self, event):
        item = self.target_tree.identify_row(event.y)
        if not item:
            return
        values = self.target_tree.item(item, "values")
        if len(values) < 4:
            return
        index = int(values[1]) - 1
        targets = self.washer.get_targets()
        if index < len(targets):
            self._show_edit_target_dialog(index, values[3], targets[index].get('min_value', None), values)
        else:
            messagebox.showerror("错误", "无法找到指定的词条")

    def on_target_tree_click(self, event):
        item = self.target_tree.identify_row(event.y)
        if not item:
            return
        if self.target_tree.identify_column(event.x) == '#1':
            values = self.target_tree.item(item, 'values')
            if len(values) >= 4:
                index = int(values[1]) - 1
                include = values[2] == "包含"
                enabled = values[0] == "✓"
                if self.washer.update_target(index, text=values[3], include=include, enabled=not enabled):
                    self.status_var.set(f"词条已{'启用' if not enabled else '禁用'}")
                    self.refresh_target_list()

    def refresh_equipment_lists(self):
        for item in self.equipment_tree.get_children():
            self.equipment_tree.delete(item)
        for name, pos in self.washer.config['equipment_positions'].items():
            self.equipment_tree.insert("", tk.END, values=(name, f"({pos[0]}, {pos[1]})"))

        for item in self.currency_tree.get_children():
            self.currency_tree.delete(item)
        for name, pos in self.washer.config['currency_positions'].items():
            self.currency_tree.insert("", tk.END, values=(name, f"({pos[0]}, {pos[1]})"))

    def update_current_info(self):
        self.current_equipment_var.set(self.washer.config['current_equipment'] or "未选择")
        self.current_currency_var.set(self.washer.config['current_currency'] or "未选择")
        self.current_match_mode_var.set(self.washer.config['match_mode'])
        if hasattr(self, 'match_count_var'):
            mc = self.washer.config.get('match_count', 1)
            if mc is None:
                mc = 1
            self.match_count_var.set(str(max(1, min(6, mc))))

    def update_stats(self):
        stats = self.washer.get_stats()
        self.click_count_var.set(str(stats['click_count']))
        self.attempt_count_var.set(str(stats['current_attempt']))
        self.match_count_var.set(str(stats['last_match_count']))
        self.root.after(100, self.update_stats)

    def setup_global_hotkeys(self):
        try:
            self.global_listener.register_callback('f10', self.toggle_washing)
            self.global_listener.register_callback('f11', self.record_equipment_position)
            self.global_listener.register_callback('f12', self.toggle_sequence)
            stop_key = self.washer.config.get('stop_key', 'esc')
            self.global_listener.register_callback(stop_key, self.stop_all_operations)
            logging.info(f"已注册停止键全局热键: {stop_key}")
            self.global_listener.start()
            logging.info("全局热键已设置完成")
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        except Exception as e:
            logging.error(f"设置全局热键时出错: {str(e)}")
            messagebox.showerror("错误", f"无法设置全局热键: {str(e)}")

    def _get_seq_index(self):
        selected = self.sequence_tree.selection()
        if not selected:
            messagebox.showinfo("提示", "请先选择一个操作")
            return None
        return int(self.sequence_tree.item(selected[0], "values")[1]) - 1

    def _seq_dialog(self, title, item, save_callback):
        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.geometry("400x300")
        dialog.transient(self.root)
        dialog.grab_set()

        eq_names = list(self.washer.config['equipment_positions'].keys())
        cur_names = list(self.washer.config['currency_positions'].keys())
        rs_names = list(self.washer.config['rule_sets'].keys())

        ttk.Label(dialog, text="装备位置:").grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
        eq_var = tk.StringVar(value=item.get('equipment', eq_names[0] if eq_names else ""))
        ttk.Combobox(dialog, textvariable=eq_var, values=eq_names, width=20, state="readonly").grid(row=0, column=1, padx=10, pady=10)

        ttk.Label(dialog, text="通货位置:").grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)
        cur_var = tk.StringVar(value=item.get('currency', cur_names[0] if cur_names else ""))
        ttk.Combobox(dialog, textvariable=cur_var, values=cur_names, width=20, state="readonly").grid(row=1, column=1, padx=10, pady=10)

        ttk.Label(dialog, text="匹配规则:").grid(row=2, column=0, padx=10, pady=10, sticky=tk.W)
        rs_var = tk.StringVar(value=item.get('rules', rs_names[0] if rs_names else ""))
        ttk.Combobox(dialog, textvariable=rs_var, values=rs_names, width=20, state="readonly").grid(row=2, column=1, padx=10, pady=10)

        def on_ok():
            eq, cur, rs = eq_var.get(), cur_var.get(), rs_var.get()
            if not eq or not cur:
                messagebox.showerror("错误", "请选择装备和通货位置")
                return
            save_callback(eq, cur, rs)
            self.refresh_sequence_list()
            dialog.destroy()

        btn_frame = ttk.Frame(dialog)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=20)
        ttk.Button(btn_frame, text="确定", command=on_ok).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="取消", command=dialog.destroy).pack(side=tk.LEFT)

    def add_sequence_item(self):
        self._seq_dialog("添加操作", {}, lambda eq, cur, rs: self._save_seq_item(None, eq, cur, rs))

    def edit_sequence_item(self):
        idx = self._get_seq_index()
        if idx is not None and 0 <= idx < len(self.sequence_items):
            self._seq_dialog("编辑操作", self.sequence_items[idx], lambda eq, cur, rs: self._save_seq_item(idx, eq, cur, rs))

    def _save_seq_item(self, index, eq, cur, rs):
        rs_data = self.washer.config['rule_sets'][rs]
        item = {
            'equipment': eq, 'currency': cur, 'rules': rs,
            'rule_set': rs_data['targets'].copy(),
            'enabled': self.sequence_items[index].get('enabled', True) if index is not None else True
        }
        if index is not None:
            self.sequence_items[index] = item
        else:
            self.sequence_items.append(item)
        self.washer.config['sequence_items'] = self.sequence_items
        from ..utils.config_manager import save_config
        save_config(self.washer.config)

    def remove_sequence_item(self):
        idx = self._get_seq_index()
        if idx is not None and 0 <= idx < len(self.sequence_items):
            del self.sequence_items[idx]
            self.washer.config['sequence_items'] = self.sequence_items
            from ..utils.config_manager import save_config
            save_config(self.washer.config)
            self.refresh_sequence_list()

    def _swap_seq_items(self, idx, other_idx):
        self.sequence_items[idx], self.sequence_items[other_idx] = self.sequence_items[other_idx], self.sequence_items[idx]
        self.washer.config['sequence_items'] = self.sequence_items
        from ..utils.config_manager import save_config
        save_config(self.washer.config)
        self.refresh_sequence_list()

    def move_sequence_item_up(self):
        idx = self._get_seq_index()
        if idx is not None and idx > 0:
            self._swap_seq_items(idx, idx - 1)

    def move_sequence_item_down(self):
        idx = self._get_seq_index()
        if idx is not None and idx < len(self.sequence_items) - 1:
            self._swap_seq_items(idx, idx + 1)

    def refresh_sequence_list(self):
        for item in self.sequence_tree.get_children():
            self.sequence_tree.delete(item)
        for i, it in enumerate(self.sequence_items):
            enabled = "✓" if it.get('enabled', True) else ""
            self.sequence_tree.insert("", tk.END, values=(enabled, i + 1, it['equipment'], it['currency'], it['rules']))

    def on_sequence_tree_click(self, event):
        item = self.sequence_tree.identify_row(event.y)
        if not item:
            return
        if self.sequence_tree.identify_column(event.x) == '#1':
            values = self.sequence_tree.item(item, 'values')
            if len(values) >= 5:
                idx = int(values[1]) - 1
                if 0 <= idx < len(self.sequence_items):
                    new_enabled = not (values[0] == "✓")
                    self.sequence_items[idx]['enabled'] = new_enabled
                    self.washer.config['sequence_items'] = self.sequence_items
                    from ..utils.config_manager import save_config
                    save_config(self.washer.config)
                    self.status_var.set(f"序列项已{'启用' if new_enabled else '禁用'}")
                    self.refresh_sequence_list()

    def execute_sequence(self):
        if not self.sequence_items:
            messagebox.showinfo("提示", "序列为空，请先添加操作")
            return
        self.washer.running = True
        self.execute_sequence_button.config(state=tk.DISABLED)
        self.stop_sequence_button.config(state=tk.NORMAL)
        self.status_var.set("序列执行中...")
        self.sequence_thread = threading.Thread(target=self.run_sequence, daemon=True)
        self.sequence_thread.start()

    def run_sequence(self):
        try:
            original_rules = self.washer.config['conditional_targets'].copy()
            for i, item in enumerate(self.sequence_items):
                if self.washer._manual_stop:
                    logger.info("序列执行已手动停止")
                    break
                if not item.get('enabled', True):
                    logger.info(f"跳过禁用的序列项 {i+1}: 装备={item['equipment']}, 通货={item['currency']}")
                    continue
                logger.info(f"执行序列项 {i+1}/{len(self.sequence_items)}: 装备={item['equipment']}, 通货={item['currency']}")
                self.washer.set_current_equipment(item['equipment'])
                self.washer.set_current_currency(item['currency'])

                rs_name = item['rules']
                if rs_name in self.washer.config['rule_sets']:
                    rd = self.washer.config['rule_sets'][rs_name]
                    self.washer.config['conditional_targets'] = rd['targets'].copy()
                    logger.info(f"使用序列项 {i+1} 的规则集 '{rs_name}'，包含 {len(rd['targets'])} 个规则")
                elif 'rule_set' in item:
                    self.washer.config['conditional_targets'] = item['rule_set'].copy()
                    logger.info(f"使用序列项 {i+1} 的自定义规则集，包含 {len(item['rule_set'])} 个规则")
                else:
                    logger.warning(f"序列项 {i+1} 无法找到对应的规则集 '{rs_name}'")

                result = self.washer.wash_equipment()
                if result:
                    logger.info(f"序列项 {i+1} 执行成功")
                else:
                    logger.info(f"序列项 {i+1} 执行失败或未找到匹配装备")

                if self.washer._manual_stop:
                    logger.info("检测到手动停止信号，准备结束序列执行")
                    break

            self.washer.config['conditional_targets'] = original_rules
            logger.info("序列执行完成，已恢复原始规则集")
            self.root.after(0, lambda: self.execute_sequence_button.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.stop_sequence_button.config(state=tk.DISABLED))
            self.root.after(0, lambda: self.status_var.set("序列执行完成"))
        except Exception as e:
            self.washer.config['conditional_targets'] = original_rules
            logger.error(f"序列执行出错: {e}")
            self.root.after(0, lambda: self.execute_sequence_button.config(state=tk.NORMAL))
            self.root.after(0, lambda: self.stop_sequence_button.config(state=tk.DISABLED))
            self.root.after(0, lambda: self.status_var.set(f"序列执行出错: {str(e)}"))
        finally:
            self.washer.running = False
            self.washer._manual_stop = False

    def toggle_sequence(self, event=None):
        self.stop_sequence() if self.washer.running else self.execute_sequence()

    def stop_sequence(self):
        self.washer.stop_washing()
        self.execute_sequence_button.config(state=tk.NORMAL)
        self.stop_sequence_button.config(state=tk.DISABLED)
        self.status_var.set("序列执行已停止")
        logger.info("序列执行已停止")

    def record_position(self, position_type):
        try:
            self.root.lift()
            self.root.update_idletasks()
            self.create_overlay_window(position_type, self.handle_fate_card_position_record)
        except Exception as e:
            error_msg = f"记录位置时出错: {str(e)}"
            logging.error(error_msg)
            self.status_var.set(error_msg)
            messagebox.showerror("错误", error_msg)

    def handle_fate_card_position_record(self, x, y, position_type):
        if x is None or y is None:
            return
        try:
            if position_type == 'unknown_card':
                self.washer.config['unknown_fate_card_position'] = (x, y)
                self.unknown_card_pos_var.set(f"{x}, {y}")
                msg = f"已成功记录未知命运卡位置 ({x}, {y})"
            elif position_type == 'storage':
                self.washer.config['card_storage_position'] = (x, y)
                self.storage_pos_var.set(f"{x}, {y}")
                msg = f"已成功记录存放卡片位置 ({x}, {y})"
            else:
                return
            from ..utils.config_manager import save_config
            save_config(self.washer.config)
            self.status_var.set(msg)
            logger.info(msg)
            messagebox.showinfo("成功", msg)
        except Exception as e:
            error_msg = f"保存位置时出错: {str(e)}"
            logging.error(error_msg)
            self.status_var.set(error_msg)
            messagebox.showerror("错误", error_msg)

    def save_fate_card_config(self):
        try:
            ux, uy = map(int, self.unknown_card_pos_var.get().strip().split(','))
            sx, sy = map(int, self.storage_pos_var.get().strip().split(','))
            loop = int(self.loop_count_var.get().strip())
            self.washer.config['unknown_fate_card_position'] = (ux, uy)
            self.washer.config['card_storage_position'] = (sx, sy)
            self.washer.config['fate_card_loop_count'] = loop
            from ..utils.config_manager import save_config
            save_config(self.washer.config)
            self.status_var.set("未知命运卡配置已保存")
            logger.info("未知命运卡配置已保存")
            messagebox.showinfo("成功", "未知命运卡配置已保存")
        except ValueError as e:
            messagebox.showerror("错误", f"配置值无效: {e}")

    def start_fate_card_process(self):
        self.start_fate_card_btn.config(state=tk.DISABLED)
        self.stop_fate_card_btn.config(state=tk.NORMAL)
        self.status_var.set("未知命运卡处理中...")
        self.fate_card_thread = threading.Thread(target=self.run_fate_card_process, daemon=True)
        self.fate_card_thread.start()

    def run_fate_card_process(self):
        try:
            result = self.washer.process_fate_cards()
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
        self.washer.stop_washing()
        self.start_fate_card_btn.config(state=tk.NORMAL)
        self.stop_fate_card_btn.config(state=tk.DISABLED)
        self.status_var.set("未知命运卡处理已停止")
        logger.info("未知命运卡处理已停止")

    def stop_all_operations(self, event=None):
        stop_key = self.washer.config.get('stop_key', 'esc')
        logger.info(f"{stop_key.upper()}键被按下，停止所有操作")
        if self.washer.is_running():
            self.washer.stop_washing()
            if hasattr(self, 'wash_button'):
                self.wash_button.config(text="开始洗练 (F10)")
        self.washer.running = False
        self.washer._manual_stop = True
        if hasattr(self, 'execute_sequence_button'):
            self.execute_sequence_button.config(state=tk.NORMAL)
        if hasattr(self, 'stop_sequence_button'):
            self.stop_sequence_button.config(state=tk.DISABLED)
        if hasattr(self, 'start_fate_card_btn'):
            self.start_fate_card_btn.config(state=tk.NORMAL)
        if hasattr(self, 'stop_fate_card_btn'):
            self.stop_fate_card_btn.config(state=tk.DISABLED)
        self.status_var.set("所有操作已停止")
        logger.info("所有操作已停止")

    def on_closing(self):
        try:
            if hasattr(self, 'global_listener') and self.global_listener.is_running():
                self.global_listener.stop()
        except Exception as e:
            logging.error(f"关闭全局监听器时出错: {str(e)}")
        self.root.destroy()


class TextHandler(logging.Handler):
    """将日志输出到Tkinter文本框的处理器"""

    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget
        self.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

    def emit(self, record):
        msg = self.format(record)

        def append_log():
            self.text_widget.config(state=tk.NORMAL)
            self.text_widget.insert(tk.END, msg + "\n")
            self.text_widget.see(tk.END)
            self.text_widget.config(state=tk.DISABLED)

        self.text_widget.after(0, append_log)


def main():
    root = tk.Tk()
    app = PoeWasherGUI(root)
    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("\n程序已通过Ctrl+C停止")
        root.destroy()


if __name__ == "__main__":
    main()
