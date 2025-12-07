#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
POE装备洗练工具 - 洗练核心模块
基于剪贴板分析实现装备洗练的核心逻辑
"""

import time
import random
import pyautogui
import logging
from typing import Dict, List, Tuple, Optional

from ..utils.clipboard_handler import ClipboardHandler
from ..utils.config_manager import load_config, save_config
from ..utils.logger_setup import setup_logger

logger = setup_logger()


class PoeClipboardWasher:
    """
    基于剪贴板的POE装备洗练器
    """
    
    def __init__(self, config_file='config.ini'):
        """
        初始化洗练器
        
        参数:
            config_file (str): 配置文件路径
        """
        print("[DEBUG] PoeClipboardWasher类初始化")
        logger.info("初始化POE装备洗练器")
        self.config = load_config(config_file)
        self.clipboard = ClipboardHandler()
        self.running = False
        self.click_count = 0
        self.current_attempt = 0
        self.last_match_count = 0  # 上次匹配的词条数量
        
        # 为现有词条添加enabled字段（向后兼容）
        if 'conditional_targets' not in self.config:
            self.config['conditional_targets'] = []
        for target in self.config['conditional_targets']:
            if 'enabled' not in target:
                target['enabled'] = True
    
    def save_position(self, position_name: str, position_type: str = 'equipment') -> bool:
        """
        保存当前鼠标位置
        
        参数:
            position_name (str): 位置名称
            position_type (str): 位置类型 ('equipment' 或 'currency')
            
        返回:
            bool: 保存是否成功
        """
        try:
            # 获取鼠标当前位置
            x, y = pyautogui.position()
            logger.info(f"获取当前鼠标位置: ({x}, {y})")
            
            # 验证名称
            if not position_name or not position_name.strip():
                logger.error(f"无效的名称: {position_name}")
                return False
            
            position_name = position_name.strip()
            
            # 保存位置
            if position_type == 'equipment':
                self.config['equipment_positions'][position_name] = (x, y)
                self.config['current_equipment'] = position_name
                logger.info(f"已设置当前装备: {position_name}")
            elif position_type == 'currency':
                self.config['currency_positions'][position_name] = (x, y)
                self.config['current_currency'] = position_name
                logger.info(f"已设置当前通货: {position_name}")
            else:
                logger.error(f"无效的位置类型: {position_type}")
                return False
            
            # 保存配置
            save_config(self.config)
            logger.info(f"成功保存{position_type}位置: {position_name} at ({x}, {y})")
            return True
            
        except Exception as e:
            logger.error(f"保存{position_type}位置失败: {str(e)}")
            return False
    
    def get_position(self, position_name: str, position_type: str = 'equipment') -> Optional[Tuple[int, int]]:
        """
        获取保存的位置
        
        参数:
            position_name (str): 位置名称
            position_type (str): 位置类型 ('equipment' 或 'currency')
            
        返回:
            Optional[Tuple[int, int]]: 位置坐标，如果不存在则返回None
        """
        if position_type == 'equipment':
            return self.config['equipment_positions'].get(position_name)
        elif position_type == 'currency':
            return self.config['currency_positions'].get(position_name)
        return None
    
    def copy_equipment_properties(self) -> Optional[str]:
        """
        复制装备属性到剪贴板
        
        返回:
            Optional[str]: 剪贴板内容，如果失败则返回None
        """
        print("[DEBUG] 复制装备属性方法被调用")
        logger.info("开始复制装备属性")
        
        # 先获取当前剪贴板内容作为参考
        initial_clipboard = self.clipboard.get_clipboard_text()
        print(f"[DEBUG] 复制前剪贴板初始内容: {initial_clipboard[:50] if initial_clipboard else '空'}")
        logger.debug(f"复制前剪贴板初始内容: {initial_clipboard[:50] if initial_clipboard else '空'}")
        
        # 使用pyautogui模拟Ctrl+C复制装备属性
        print("[DEBUG] 使用pyautogui按下Ctrl+C")
        logger.info("使用pyautogui按下Ctrl+C复制当前悬停的装备属性")
        try:
            # 添加小延迟确保操作稳定
            time.sleep(0.1)
            pyautogui.hotkey('ctrl', 'c')
            print("[DEBUG] Ctrl+C组合键模拟成功")
            logger.info("Ctrl+C组合键模拟成功")
        except Exception as e:
            print(f"[DEBUG] 模拟复制操作失败: {e}")
            logger.error(f"模拟复制操作失败: {e}")
            return None
        
        # 增加等待时间以确保剪贴板完全更新，特别是对于多行文本
        # 调整为1秒延迟，加快处理速度
        delay = 1.0  # 调整为1秒延迟
        print(f"[DEBUG] 等待剪贴板更新，使用固定延迟时间: {delay:.2f}秒")
        logger.info(f"等待剪贴板更新，使用固定延迟时间: {delay:.2f}秒")
        time.sleep(delay)  # 等待剪贴板更新
        
        # 尝试多次获取剪贴板内容，增加到5次尝试
        print("[DEBUG] 开始多次尝试获取剪贴板内容")
        max_attempts = 5
        for attempt in range(max_attempts):
            clipboard_content = self.clipboard.get_clipboard_text()
            print(f"[DEBUG] 尝试 {attempt+1}/{max_attempts} 获取剪贴板内容")
            
            # 检查剪贴板内容是否发生变化
            if clipboard_content and clipboard_content != initial_clipboard:
                # 记录剪贴板内容的前200个字符，并记录总行数，以便更好地调试
                line_count = clipboard_content.count('\n') + 1
                preview = clipboard_content[:200] + ('...' if len(clipboard_content) > 200 else '')
                print(f"[DEBUG] [尝试{attempt+1}/{max_attempts}] 成功获取装备属性: {preview}")
                print(f"[DEBUG] [尝试{attempt+1}/{max_attempts}] 剪贴板内容总行数: {line_count}")
                logger.info(f"[尝试{attempt+1}/{max_attempts}] 成功从剪贴板获取装备属性，内容预览: {preview}")
                logger.info(f"[尝试{attempt+1}/{max_attempts}] 剪贴板内容总行数: {line_count}")
                return clipboard_content
            elif clipboard_content == initial_clipboard and initial_clipboard:
                print(f"[DEBUG] [尝试{attempt+1}/{max_attempts}] 剪贴板内容未变化")
                logger.warning(f"[尝试{attempt+1}/{max_attempts}] 剪贴板内容未变化，可能复制失败")
                # 每次尝试增加等待时间
                wait_time = 0.5 + attempt * 0.2  # 递增等待时间
                time.sleep(wait_time)
            else:
                print(f"[DEBUG] [尝试{attempt+1}/{max_attempts}] 剪贴板为空")
                logger.warning(f"[尝试{attempt+1}/{max_attempts}] 剪贴板为空")
                # 每次尝试增加等待时间
                wait_time = 0.5 + attempt * 0.2
                time.sleep(wait_time)
        
        print("[DEBUG] 所有尝试均未能获取装备属性")
        logger.warning("所有尝试均未能从剪贴板获取新的装备属性，请确保鼠标悬停在装备上")
        return None
    
    def check_equipment_properties(self) -> Tuple[bool, int, Dict]:
        """
        【属性检查函数】检查装备属性是否符合目标条件
        负责获取、解析装备属性并判断是否符合目标条件
        
        返回:
            Tuple[bool, int, Dict]: (是否符合条件, 匹配的词条数量, 装备数据)
        """
        logger.info("===== 开始检查装备属性 =====")
        
        # 获取装备属性
        clipboard_content = self.copy_equipment_properties()
        if not clipboard_content:
            logger.warning("获取装备属性失败，跳过检查")
            # 复制失败5次，设置running为False，停止洗练循环
            self.running = False
            logger.info("连续5次复制失败，自动停止洗练操作")
            return False, 0, {}
        
        # 解析装备数据
        logger.info("开始解析装备数据")
        equipment_data = self.clipboard.parse_equipment_data(clipboard_content)
        
        if not equipment_data:
            logger.warning("无法解析装备数据，请检查剪贴板内容格式")
            return False, 0, {}
        
        # 记录装备基本信息
        item_name = equipment_data.get('name', '未知装备')
        item_type = equipment_data.get('type', '未知类型')
        logger.info(f"装备信息: {item_name} [{item_type}]")
        
        # 记录装备属性数量
        total_properties = len(equipment_data.get('base_properties', [])) + \
                          len(equipment_data.get('implicit_mods', [])) + \
                          len(equipment_data.get('explicit_mods', []))
        logger.info(f"解析到的装备属性数量: {total_properties}条")
        
        # 记录装备完整信息
        logger.info(f"=== 装备完整信息 ===")
        logger.info(f"稀有度: {equipment_data.get('rarity', '未知')}")
        logger.info(f"装备名称: {equipment_data.get('name', '未知')}")
        logger.info(f"装备类型: {equipment_data.get('type', '未知')}")
        logger.info(f"物品等级: {equipment_data.get('item_level', '未知')}")
        
        # 记录基底属性
        base_props = equipment_data.get('base_properties', [])
        if base_props:
            logger.info(f"基底属性 ({len(base_props)}条):")
            for prop in base_props:
                logger.info(f"  {prop}")
        
        # 记录隐性词缀
        implicit_mods = equipment_data.get('implicit_mods', [])
        if implicit_mods:
            logger.info(f"隐性词缀 ({len(implicit_mods)}条):")
            for mod in implicit_mods:
                logger.info(f"  {mod}")
        
        # 记录显性词缀
        explicit_mods = equipment_data.get('explicit_mods', [])
        if explicit_mods:
            logger.info(f"显性词缀 ({len(explicit_mods)}条):")
            for mod in explicit_mods:
                logger.info(f"  {mod}")
        
        # 检查目标词条
        logger.info("开始检查目标词条匹配情况")
        matches = self.check_targets(equipment_data)
        
        # 更新上次匹配计数
        self.last_match_count = matches
        
        # 根据匹配模式判断是否符合条件
        match_mode = self.config['match_mode'].upper()
        enabled_include_targets = [t for t in self.config['conditional_targets'] if t.get('include', True) and t.get('enabled', True)]
        targets_count = len(enabled_include_targets)
        
        # 判断是否符合条件
        is_match = False
        if match_mode == 'AND' and matches > 0 and matches == targets_count:
            is_match = True
            logger.info(f"匹配模式: {match_mode}，启用的目标词条数: {targets_count}，匹配成功数: {matches}")
            logger.info("✅ 装备符合所有目标条件 (AND模式)")
        elif match_mode == 'OR' and matches > 0:
            is_match = True
            logger.info(f"匹配模式: {match_mode}，启用的目标词条数: {targets_count}，匹配成功数: {matches}")
            logger.info(f"✅ 装备符合至少一个目标条件 (OR模式)，匹配数: {matches}")
        elif match_mode == 'COUNT' and 'match_count' in self.config:
            required_count = self.config['match_count']
            logger.info(f"匹配模式: {match_mode}，需要满足的规则数量: {required_count}，匹配成功数: {matches}")
            if matches >= required_count:
                is_match = True
                logger.info(f"✅ 装备符合{matches}条目标条件，满足最低要求{required_count}条 (COUNT模式)")
            else:
                logger.info(f"❌ 装备仅符合{matches}条目标条件，未达到最低要求{required_count}条 (COUNT模式)")
        else:
            logger.info(f"匹配模式: {match_mode}，启用的目标词条数: {targets_count}，匹配成功数: {matches}")
            logger.info(f"❌ 装备不符合目标条件")
        
        logger.info("===== 装备属性检查完成 =====")
        return is_match, matches, equipment_data
    
    def check_targets(self, equipment_data: Dict) -> int:
        """
        【词条匹配函数】检查装备是否包含目标词条
        使用现有的数值匹配逻辑进行匹配
        
        参数:
            equipment_data (Dict): 装备数据字典
            
        返回:
            int: 匹配的目标词条数量
        """
        logger.info("开始进行词条匹配检查")
        
        # 确保equipment_data有效
        if not equipment_data:
            logger.error("错误：equipment_data为空")
            return 0
        
        # 获取词缀属性（只使用词缀，不使用基底属性）
        explicit_mods = equipment_data.get("explicit_mods", [])
        implicit_mods = equipment_data.get("implicit_mods", [])
        
        # 合并词缀列表用于匹配
        all_mods = explicit_mods + implicit_mods
        
        matched_count = 0
        
        # 遍历所有目标词条
        for target in self.config['conditional_targets']:
            if not target.get("enabled", True):
                logger.info(f"跳过禁用的词条条件: {target['text']}")
                continue
            
            if target["include"]:
                # 包含条件，检查装备是否包含该词条
                text = target["text"]
                min_value = target.get("min_value")
                if self._check_text_in_properties(text, all_mods, min_value):
                    matched_count += 1
                    logger.info(f"✅ 条件匹配成功: '{text}'")
                else:
                    logger.info(f"❌ 条件匹配失败: '{text}'")
        
        logger.info(f"词条匹配检查完成，匹配成功的包含条件数量: {matched_count}")
        
        return matched_count
    
    def _check_text_in_properties(self, text: str, properties: List[str], min_value: float = None) -> bool:
        """
        检查文本是否在装备属性中
        使用更健壮的匹配逻辑，确保关键词能被正确识别
        
        参数:
            text (str): 要检查的文本
            properties (List[str]): 装备属性列表
            min_value (float, optional): 最小数值要求，用于数值比较
            
        返回:
            bool: 是否匹配
        """
        # 对匹配文本进行处理，去除首尾空格
        text_lower = text.strip().lower()
        logger.debug(f"检查关键词 '{text_lower}' 是否存在于装备属性中")
        
        # 为了更好的匹配效果，创建一个处理过的关键词列表
        keywords = text_lower.split()
        
        # 定义需要特殊处理的通用关键词列表
        general_keywords = ['元素', '抗性', '护甲', '闪避', '暴击', '生命', '魔力', '诅咒']
        
        # 遍历所有装备属性进行匹配
        for i, prop in enumerate(properties):
            # 去除属性文本的首尾空格并转为小写
            prop_lower = prop.strip().lower()
            
            # 记录当前检查的属性，用于调试
            logger.debug(f"检查属性 {i+1}: '{prop_lower}'")
            
            # 检查是否匹配（不立即返回，先收集匹配信息）
            is_match = False
            
            # 1. 首先尝试完整文本包含匹配
            if text_lower in prop_lower:
                logger.debug(f"✅ 完整文本匹配成功: '{text_lower}' 在 '{prop}'")
                is_match = True
            
            # 2. 改进的关键词匹配逻辑
            # 对于通用关键词如"元素"、"抗性"等，使用更宽松的匹配规则
            elif any(general_keyword == text_lower and general_keyword in prop_lower 
                    for general_keyword in general_keywords):
                logger.debug(f"✅ 通用关键词匹配成功: '{text_lower}' 在 '{prop}' 中找到")
                is_match = True
            
            # 3. 对于复合关键词的部分匹配
            elif ' ' in text_lower and any(keyword in prop_lower for keyword in keywords):
                matched_keywords = [k for k in keywords if k in prop_lower]
                if matched_keywords:
                    logger.debug(f"✅ 关键词部分匹配成功: '{text_lower}' 的关键词 {matched_keywords} 在 '{prop}' 中找到")
                    # 对于重要关键词，即使只匹配部分也视为成功
                    if any(important_key in text_lower for important_key in 
                           ['暴击率', '暴击伤害', '效果提高', '额外伤害', '元素抗性', '护甲', '闪避']):
                        is_match = True
            
            # 4. 针对特殊情况的额外匹配逻辑
            elif text_lower == '暴击率' and '暴击率' in prop_lower:
                logger.debug(f"✅ 特殊关键词'暴击率'匹配成功: '{prop}'")
                is_match = True
            
            # 5. 特别处理元素抗性相关的匹配
            elif text_lower in ['元素', '抗性'] and any(res_type in prop_lower for res_type in 
                                                      ['元素抗性', '火焰抗性', '冰冷抗性', '闪电抗性']):
                logger.debug(f"✅ 元素抗性相关匹配成功: '{text_lower}' 在 '{prop}' 中找到")
                is_match = True
            
            # 如果匹配成功，处理数值要求
            if is_match:
                # 如果有数值要求，需要提取并比较数值
                if min_value is not None:
                    if self._extract_and_compare_value(prop, min_value):
                        logger.debug(f"✅ 满足数值要求: {prop} >= {min_value}")
                        return True
                    else:
                        logger.debug(f"❌ 不满足数值要求: {prop} < {min_value}")
                        # 继续检查其他属性
                else:
                    # 没有数值要求，直接返回成功
                    logger.debug(f"✅ 匹配成功，无数值要求: '{prop}'")
                    return True
        
        # 如果未找到匹配，记录所有属性用于调试
        if properties:
            logger.debug(f"❌ 未找到匹配的属性。关键词: '{text_lower}'")
            logger.debug(f"装备属性数量: {len(properties)}")
            # 详细输出每个属性，帮助诊断问题
            for i, prop in enumerate(properties):
                logger.debug(f"属性 {i+1}: '{prop.strip().lower()}'")
        else:
            logger.debug("❌ 未找到匹配的属性。装备属性列表为空")
        
        return False
    
    def _extract_and_compare_value(self, text: str, min_value: float) -> bool:
        """
        从文本中提取数值并与最小要求进行比较
        
        参数:
            text (str): 包含数值的文本
            min_value (float): 最小数值要求
            
        返回:
            bool: 提取的数值是否大于等于最小要求
        """
        import re
        # 尝试提取文本中的数值
        # 匹配正数、负数、小数
        matches = re.findall(r'[-+]?\d*\.?\d+', text)
        
        if matches:
            # 取最后一个找到的数值（通常是主要数值）
            try:
                value = float(matches[-1])
                logger.debug(f"提取到数值: {value}，最小要求: {min_value}")
                return value >= min_value
            except ValueError:
                logger.debug(f"无法将提取的内容转换为数值: {matches[-1]}")
        
        logger.debug(f"在文本'{text}'中未找到可比较的数值")
        return False
    
    def click_position(self, position: Tuple[int, int], duration: float = None, button='left') -> bool:
        """
        【点击操作函数】点击指定位置
        执行鼠标点击操作，是洗练过程中模拟用户操作的关键函数
        
        参数:
            position (Tuple[int, int]): 坐标位置
            duration (float): 点击持续时间
            button (str): 按钮类型 ('left' 或 'right')
            
        返回:
            bool: 操作是否成功
        """
        try:
            if duration is None:
                duration = self.config['click_duration']
            
            # 获取当前鼠标位置
            current_x, current_y = pyautogui.position()
            logger.info(f"当前鼠标位置: ({current_x}, {current_y})")
            
            # 平滑移动鼠标到目标位置
            # 移动时间为随机值，模拟人类操作
            move_duration = random.uniform(0.05, 0.15)
            logger.info(f"平滑移动鼠标到: ({position[0]}, {position[1]})，持续时间: {move_duration:.2f}秒")
            pyautogui.moveTo(position[0], position[1], duration=move_duration, tween=pyautogui.easeOutQuad)
            
            # 添加短暂停顿，模拟人类操作节奏
            time.sleep(random.uniform(0.02, 0.08))
            
            # 执行点击操作
            logger.info(f"{button}键点击位置: ({position[0]}, {position[1]}), 点击持续时间: {duration:.2f}秒")
            pyautogui.click(position[0], position[1], duration=duration, button=button)
            self.click_count += 1
            return True
        except Exception as e:
            logger.error(f"点击操作失败: {e}")
            return False
    
    def wash_equipment(self) -> bool:
        """
        【核心洗练函数】执行装备洗练操作
        此函数是整个洗练流程的主要入口，控制洗练过程的完整逻辑
        
        返回:
            bool: 是否成功找到符合条件的装备
        """
        # 获取装备和通货位置
        equipment_name = self.config['current_equipment']
        currency_name = self.config['current_currency']
        
        if not equipment_name:
            logger.error("未选择装备")
            return False
        
        if not currency_name:
            logger.error("未选择通货")
            return False
        
        equipment_pos = self.get_position(equipment_name, 'equipment')
        currency_pos = self.get_position(currency_name, 'currency')
        
        if not equipment_pos:
            logger.error(f"未找到装备位置: {equipment_name}")
            return False
        
        if not currency_pos:
            logger.error(f"未找到通货位置: {currency_name}")
            return False
        
        logger.info(f"开始洗练装备: {equipment_name}, 使用通货: {currency_name}")
        
        # 重置计数器
        self.running = True
        self.click_count = 0
        self.current_attempt = 0
        
        try:
            while self.running and self.current_attempt < self.config['max_attempts']:
                self.current_attempt += 1
                logger.info(f"尝试次数: {self.current_attempt}/{self.config['max_attempts']}")
                
                # 先右键点击通货
                # 添加前置随机延迟
                random_delay_before = random.uniform(0.05, 0.15)
                logger.info(f"[操作前] 准备右键点击通货: {currency_name} 在位置 {currency_pos}, 等待随机延迟: {random_delay_before:.2f}秒")
                time.sleep(random_delay_before)
                
                # 执行右键点击通货
                logger.info(f"[执行中] 正在右键点击通货: {currency_name} 在坐标 {currency_pos[0]},{currency_pos[1]}")
                if not self.click_position(currency_pos, button='right'):
                    logger.warning("[操作失败] 右键点击通货失败，跳过当前循环")
                    continue
                logger.info(f"[操作成功] 右键点击通货 {currency_name} 完成")
                
                # 添加后置随机延迟
                random_delay_after = random.uniform(self.config['operation_delay'] * 0.4, self.config['operation_delay'] * 0.6)
                logger.info(f"[操作后] 右键点击完成，等待随机延迟: {random_delay_after:.2f}秒")
                time.sleep(random_delay_after)
                
                # 然后左键点击装备
                # 添加前置随机延迟
                random_delay_before = random.uniform(0.05, 0.15)
                logger.info(f"[操作前] 准备左键点击装备: {equipment_name} 在位置 {equipment_pos}, 等待随机延迟: {random_delay_before:.2f}秒")
                time.sleep(random_delay_before)
                
                # 执行左键点击装备
                logger.info(f"[执行中] 正在左键点击装备: {equipment_name} 在坐标 {equipment_pos[0]},{equipment_pos[1]}")
                if not self.click_position(equipment_pos, button='left'):
                    logger.warning("[操作失败] 左键点击装备失败，跳过当前循环")
                    continue
                logger.info(f"[操作成功] 左键点击装备 {equipment_name} 完成")
                
                # 添加后置随机延迟
                random_delay_after = random.uniform(self.config['operation_delay'] * 0.8, self.config['operation_delay'] * 1.2)
                logger.info(f"[操作后] 左键点击完成，等待随机延迟: {random_delay_after:.2f}秒")
                time.sleep(random_delay_after)
                
                # 检查装备属性
                matched, match_count, equipment_data = self.check_equipment_properties()
                
                if matched:
                    logger.info(f"找到符合条件的装备！匹配词条数: {match_count}")
                    logger.info(f"装备名称: {equipment_data.get('name')}")
                    logger.info(f"稀有度: {equipment_data.get('rarity')}")
                    return True
                
                if match_count > 0:
                    logger.info(f"部分匹配！当前匹配词条数: {match_count}")
        
        except Exception as e:
            logger.error(f"洗练过程中出错: {e}")
        
        finally:
            self.running = False
            logger.info(f"洗练结束，总点击次数: {self.click_count}")
        
        return False
    
    def stop_washing(self) -> None:
        """
        停止洗练操作
        """
        logger.info("正在停止洗练操作...")
        self.running = False
    
    def add_target(self, text: str, include: bool = True, enabled: bool = True, min_value: float = None) -> None:
        """
        添加目标词条
        
        参数:
            text (str): 词条文本
            include (bool): 是否包含此词条（True）或排除此词条（False）
            enabled (bool): 是否启用此词条（True）或禁用此词条（False）
            min_value (float, optional): 最小数值要求，用于数值比较
        """
        target_data = {'text': text, 'include': include, 'enabled': enabled}
        if min_value is not None:
            target_data['min_value'] = min_value
        
        # 获取当前规则集合
        current_rule_set = self.config['current_rule_set']
        self.config['rule_sets'][current_rule_set]['targets'].append(target_data)
        
        # 更新conditional_targets引用，兼容旧代码
        self.config['conditional_targets'] = self.config['rule_sets'][current_rule_set]['targets']
        
        logger.info(f"添加目标词条到规则集合 '{current_rule_set}': {'包含' if include else '排除'} '{text}' (启用: {enabled}{', 最小数值要求: ' + str(min_value) if min_value is not None else ''})")
        save_config(self.config)
    
    def remove_target(self, index: int) -> bool:
        """
        移除目标词条
        
        参数:
            index (int): 词条索引
            
        返回:
            bool: 操作是否成功
        """
        # 获取当前规则集合
        current_rule_set = self.config['current_rule_set']
        rule_data = self.config['rule_sets'][current_rule_set]
        rules = rule_data['targets']
        
        if 0 <= index < len(rules):
            removed = rules.pop(index)
            logger.info(f"从规则集合 '{current_rule_set}' 移除目标词条: {'包含' if removed['include'] else '排除'} '{removed['text']}' (启用: {removed.get('enabled', True)})")
            
            # 更新conditional_targets引用，兼容旧代码
            self.config['conditional_targets'] = rule_data['targets']
            
            save_config(self.config)
            return True
        return False
    
    def get_targets(self) -> List[Dict]:
        """
        获取所有目标词条
        
        返回:
            List[Dict]: 目标词条列表
        """
        # 获取当前规则集合
        current_rule_set = self.config['current_rule_set']
        return self.config['rule_sets'][current_rule_set]['targets']
    
    def get_equipment_list(self) -> List[str]:
        """
        获取已保存的装备列表
        
        返回:
            List[str]: 装备名称列表
        """
        return list(self.config['equipment_positions'].keys())
    
    def get_currency_list(self) -> List[str]:
        """
        获取已保存的通货列表
        
        返回:
            List[str]: 通货名称列表
        """
        return list(self.config['currency_positions'].keys())
    
    def update_target(self, index: int, text: str = None, include: bool = None, enabled: bool = None, min_value: float = None) -> bool:
        """
        更新目标词条
        
        参数:
            index (int): 词条索引
            text (str, optional): 词条文本
            include (bool, optional): 是否包含此词条
            enabled (bool, optional): 是否启用此词条
            min_value (float, optional): 最小数值要求，用于数值比较
            
        返回:
            bool: 操作是否成功
        """
        # 获取当前规则集合
        current_rule_set = self.config['current_rule_set']
        rule_data = self.config['rule_sets'][current_rule_set]
        rules = rule_data['targets']
        
        if 0 <= index < len(rules):
            target = rules[index]
            
            if text is not None:
                old_text = target['text']
                target['text'] = text
                logger.info(f"更新规则集合 '{current_rule_set}' 的词条文本: 从 '{old_text}' 到 '{text}'")
            
            if include is not None:
                old_include = target['include']
                target['include'] = include
                logger.info(f"更新规则集合 '{current_rule_set}' 的词条类型: 从 {'包含' if old_include else '排除'} 到 {'包含' if include else '排除'}")
            
            if enabled is not None:
                old_enabled = target.get('enabled', True)
                target['enabled'] = enabled
                logger.info(f"更新规则集合 '{current_rule_set}' 的词条状态: 从 {'启用' if old_enabled else '禁用'} 到 {'启用' if enabled else '禁用'}")
            
            if min_value is not None:
                old_min_value = target.get('min_value', None)
                target['min_value'] = min_value
                logger.info(f"更新规则集合 '{current_rule_set}' 的词条数值要求: 从 {old_min_value} 到 {min_value}")
            
            # 更新conditional_targets引用，兼容旧代码
            self.config['conditional_targets'] = rule_data['targets']
            
            save_config(self.config)
            return True
        return False
    
    def set_current_equipment(self, equipment_name: str) -> bool:
        """
        设置当前使用的装备
        
        参数:
            equipment_name (str): 装备名称
            
        返回:
            bool: 操作是否成功
        """
        if equipment_name in self.config['equipment_positions']:
            self.config['current_equipment'] = equipment_name
            save_config(self.config)
            logger.info(f"设置当前装备: {equipment_name}")
            return True
        return False
    
    def set_current_currency(self, currency_name: str) -> bool:
        """
        设置当前使用的通货
        
        参数:
            currency_name (str): 通货名称
            
        返回:
            bool: 操作是否成功
        """
        if currency_name in self.config['currency_positions']:
            self.config['current_currency'] = currency_name
            save_config(self.config)
            logger.info(f"设置当前通货: {currency_name}")
            return True
        return False
    
    def set_match_mode(self, mode: str, count: int = None) -> bool:
        """
        设置匹配模式
        
        参数:
            mode (str): 匹配模式 ('AND', 'OR' 或 'COUNT')
            count (int): 当模式为COUNT时，需要满足的规则数量
            
        返回:
            bool: 操作是否成功
        """
        mode_upper = mode.upper()
        logger.debug(f"[set_match_mode] 开始设置匹配模式: mode={mode_upper}, count={count}")
        
        if mode_upper in ['AND', 'OR']:
            self.config['match_mode'] = mode_upper
            # 如果切换到非COUNT模式，清除匹配数量
            if 'match_count' in self.config:
                del self.config['match_count']
            logger.debug(f"[set_match_mode] 保存配置前: {self.config}")
            # 使用绝对路径保存配置，确保保存到正确的文件
            save_config(self.config, 'config.ini')
            logger.debug(f"[set_match_mode] 保存配置后")
            logger.info(f"设置匹配模式: {self.config['match_mode']}")
            return True
        elif mode_upper == 'COUNT' and count is not None and count > 0:
            self.config['match_mode'] = mode_upper
            self.config['match_count'] = count
            logger.debug(f"[set_match_mode] 保存配置前: {self.config}")
            # 使用绝对路径保存配置，确保保存到正确的文件
            save_config(self.config, 'config.ini')
            logger.debug(f"[set_match_mode] 保存配置后")
            logger.info(f"设置匹配模式: COUNT，需要满足{count}条规则")
            return True
        logger.debug(f"[set_match_mode] 无效的参数: mode={mode_upper}, count={count}")
        return False
    
    def set_delay_settings(self, click_duration: float = None, operation_delay: float = None, 
                         clipboard_check_delay: float = None) -> None:
        """
        设置延迟参数
        
        参数:
            click_duration (float): 点击持续时间
            operation_delay (float): 操作间隔延迟
            clipboard_check_delay (float): 剪贴板检查延迟
        """
        if click_duration is not None:
            self.config['click_duration'] = click_duration
        if operation_delay is not None:
            self.config['operation_delay'] = operation_delay
        if clipboard_check_delay is not None:
            self.config['clipboard_check_delay'] = clipboard_check_delay
            
        save_config(self.config)
        logger.info(f"更新延迟设置: 点击持续时间={self.config['click_duration']}, "
                  f"操作间隔={self.config['operation_delay']}, "
                  f"剪贴板检查={self.config['clipboard_check_delay']}")
    
    def is_running(self) -> bool:
        """
        获取洗练器运行状态
        
        返回:
            bool: 是否正在运行
        """
        return self.running
    
    def get_stats(self) -> Dict[str, int]:
        """
        获取统计信息
        
        返回:
            Dict[str, int]: 统计数据
        """
        return {
            'click_count': self.click_count,
            'current_attempt': self.current_attempt,
            'last_match_count': self.last_match_count
        }
    
    def process_fate_cards(self) -> bool:
        """
        处理未知命运卡
        点击逻辑：右键点击未知命运卡位置，然后左键点击存放卡片位置，最后在存放卡片位置按下"ctrl + 鼠标左键"
        
        返回:
            bool: 操作是否成功
        """
        logger.info("===== 开始处理未知命运卡 =====")
        
        # 获取配置
        unknown_card_pos = self.config.get('unknown_fate_card_position', (0, 0))
        storage_pos = self.config.get('card_storage_position', (0, 0))
        loop_count = self.config.get('fate_card_loop_count', 10)
        
        # 验证配置
        if unknown_card_pos == (0, 0) or storage_pos == (0, 0):
            logger.error("未知命运卡位置或存放卡片位置未设置")
            return False
        
        # 设置运行状态
        self.running = True
        
        try:
            for i in range(loop_count):
                if not self.running:
                    logger.info("命运卡处理已停止")
                    break
                
                logger.info(f"处理未知命运卡，循环 {i+1}/{loop_count}")
                
                # 1. 右键点击未知命运卡位置
                logger.info(f"右键点击未知命运卡位置: {unknown_card_pos}")
                if not self.click_position(unknown_card_pos, button='right'):
                    logger.warning("右键点击未知命运卡位置失败")
                    continue
                
                # 添加操作间隔延迟
                time.sleep(self.config['operation_delay'])
                
                # 2. 左键点击存放卡片位置
                logger.info(f"左键点击存放卡片位置: {storage_pos}")
                if not self.click_position(storage_pos, button='left'):
                    logger.warning("左键点击存放卡片位置失败")
                    continue
                
                # 添加操作间隔延迟
                time.sleep(self.config['operation_delay'])
                
                # 3. 在存放卡片位置按下"ctrl + 鼠标左键"
                logger.info(f"在存放卡片位置按下ctrl + 鼠标左键: {storage_pos}")
                
                # 移动鼠标到存放卡片位置
                pyautogui.moveTo(storage_pos[0], storage_pos[1], duration=random.uniform(0.05, 0.15))
                
                # 按下ctrl键
                pyautogui.keyDown('ctrl')
                
                # 左键点击
                pyautogui.click(storage_pos[0], storage_pos[1], button='left')
                
                # 释放ctrl键
                pyautogui.keyUp('ctrl')
                
                # 增加点击计数
                self.click_count += 1
                
                # 添加操作间隔延迟
                time.sleep(self.config['operation_delay'])
            
            logger.info("===== 未知命运卡处理完成 =====")
            return True
        except Exception as e:
            logger.error(f"处理未知命运卡时出错: {e}")
            return False
        finally:
            self.running = False