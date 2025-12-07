#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
POE装备洗练工具 - 剪贴板处理模块
用于从剪贴板获取和解析装备属性信息（简化版本）
"""

import pyperclip
import re
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class ClipboardHandler:
    """剪贴板处理器，用于获取和解析装备信息"""
    
    @staticmethod
    def get_clipboard_text():
        """
        获取剪贴板文本内容
        
        返回:
            str: 剪贴板中的文本内容，如果获取失败则返回空字符串
        """
        try:
            return pyperclip.paste()
        except Exception as e:
            logger.error(f"获取剪贴板内容失败: {e}")
            return ""
    
    @staticmethod
    def copy_to_clipboard(text):
        """
        将文本复制到剪贴板
        
        参数:
            text (str): 要复制到剪贴板的文本
            
        返回:
            bool: 操作是否成功
        """
        try:
            pyperclip.copy(text)
            return True
        except Exception as e:
            logger.error(f"复制到剪贴板失败: {e}")
            return False
    
    @staticmethod
    def parse_equipment_data(text=None):
        """
        改进版解析装备数据
        将基底属性和词缀属性分开存储
        
        Args:
            text (str, optional): 装备文本内容，如果为None则从剪贴板获取
            
        Returns:
            dict: 包含基底属性和词缀属性分离的装备数据字典，如果无法识别则返回None
        """
        # 如果未提供文本，从剪贴板获取
        if text is None:
            text = ClipboardHandler.get_clipboard_text()
            if not text:
                logger.warning("剪贴板为空，无法解析装备数据")
                return None
                
        if not text or not isinstance(text, str):
            return None
        
        # 增强的装备关键词检查，添加更多药剂相关关键词
        equipment_keywords = [
            "稀有度:", "物品类别:", "药剂", "生命药剂", "魔力药剂", "物品等级:",
            "持续 ", "充能次数", "目前有", "效果提高", "暴击率提高", "护甲", "闪避", "诅咒", "元素",
            "黄玉药剂", "蓝玉药剂", "红玉药剂", "翡翠药剂", "紫晶药剂", "坚岩药剂"
        ]
        
        # 检查是否包含任何关键词
        if not any(keyword in text for keyword in equipment_keywords):
            logger.debug(f"未检测到装备相关关键词，文本: {text[:100]}...")
            return None
        
        # 提取所有非空行
        all_lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        # 分离基底属性和词缀属性
        base_properties = []  # 基底属性
        explicit_mods = []    # 词缀属性（显性）
        implicit_mods = []    # 词缀属性（隐性）- 药剂可能没有
        
        # 识别装备类型
        equipment_type = ClipboardHandler._identify_equipment_type(text)
        
        # 特殊处理功能药剂
        if equipment_type == "功能药剂":
            logger.info("已识别为功能药剂，使用特殊解析逻辑")
            
            # 识别分隔线位置
            separator_indices = []
            for i, line in enumerate(all_lines):
                if '--------' in line:
                    separator_indices.append(i)
            
            # 词缀通常在第4个分隔线后，直到第5个分隔线或结束
            base_start = 0
            affix_start = len(all_lines)  # 默认在末尾（找不到则没有词缀）
            affix_end = len(all_lines)
            
            if len(separator_indices) >= 4:
                # 词缀通常在第4个分隔线后
                affix_start = separator_indices[3] + 1
            
            if len(separator_indices) >= 5:
                # 如果有第5个分隔线，则词缀在第4和第5个分隔线之间
                affix_end = separator_indices[4]
            
            # 收集基底属性（所有内容直到词缀开始之前，但排除分隔线）
            for i in range(base_start, affix_start):
                if '--------' not in all_lines[i]:
                    base_properties.append(all_lines[i])
            
            # 收集词缀属性，跳过需求和使用提示等行
            for i in range(affix_start, affix_end):
                line = all_lines[i]
                if line and not any(skip in line for skip in ["需求", "等级:", "物品等级:", "点击右键", "--------"]):
                    # 进一步确认是否为词缀行，功能药剂的词缀通常包含关键词
                    if any(keyword in line for keyword in ["生效期间", "增加", "提高", "转化", "获得", "减少", "额外", "生命", "魔力", "持续时间", "充能", "恢复", "暴击", "伤害", "移动速度"]):
                        explicit_mods.append(line)
        else:
            # 非功能药剂的处理逻辑
            # 识别分隔线位置
            separator_indices = []
            for i, line in enumerate(all_lines):
                if '--------' in line:
                    separator_indices.append(i)
            
            # 根据分隔线位置区分不同部分
            if len(separator_indices) >= 4:
                # 装备通常有多个分隔线，结构为：
                # 0: 装备名称和稀有度
                # 1: 需求信息
                # 2: 物品等级
                # 3: 隐性词缀
                # 4: 显性词缀
                # 5: 特殊标签（分裂、塑界者等）
                
                # 隐性词缀：在第3和第4个分隔线之间
                implicit_start = separator_indices[3] + 1
                implicit_end = separator_indices[4] if len(separator_indices) > 4 else len(all_lines)
                for i in range(implicit_start, implicit_end):
                    line = all_lines[i]
                    if line and '--------' not in line:
                        implicit_mods.append(line)
                
                # 显性词缀：在第4和第5个分隔线之间
                explicit_start = separator_indices[4] + 1 if len(separator_indices) > 4 else separator_indices[-1] + 1
                explicit_end = separator_indices[5] if len(separator_indices) > 5 else len(all_lines)
                for i in range(explicit_start, explicit_end):
                    line = all_lines[i]
                    if line and '--------' not in line:
                        explicit_mods.append(line)
                
                # 基底属性：只包含名称、稀有度和隐性词缀前的部分
                base_properties = []
                # 添加名称和稀有度
                for line in all_lines[:separator_indices[0]]:
                    if line and '--------' not in line:
                        base_properties.append(line)
                # 添加隐性词缀
                for mod in implicit_mods:
                    base_properties.append(mod)
            elif separator_indices:
                # 简单处理：词缀在最后一个分隔线之后
                for i, line in enumerate(all_lines):
                    if '--------' in line:
                        continue
                    # 跳过需求信息
                    if '需求:' in line or '等级:' in line:
                        continue
                    # 区分词缀和基底属性
                    if i < separator_indices[-1]:
                        base_properties.append(line)
                    else:
                        explicit_mods.append(line)
            else:
                # 没有分隔线的情况，默认所有行都是基底属性
                base_properties = all_lines
        
        # 提取装备名称（单独处理以提高准确性）
        equipment_name = ClipboardHandler._extract_equipment_name(text)
        
        # 提取额外的装备信息
        rarity = "未知"
        item_level = "未知"
        
        # 从所有行中提取稀有度和物品等级
        for line in all_lines:
            if "稀有度:" in line:
                rarity = line.split("稀有度:")[-1].strip()
            elif "物品等级:" in line:
                item_level = line.split("物品等级:")[-1].strip()
        
        # 构建装备数据结构
        equipment_data = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "raw_text": text,
            "name": equipment_name,
            "all_text_lines": all_lines,
            "type": equipment_type,
            "rarity": rarity,
            "item_level": item_level,
            "base_properties": base_properties,  # 基底属性
            "explicit_mods": explicit_mods,      # 显性词缀（实际词缀属性）
            "implicit_mods": implicit_mods       # 隐性词缀（通常药剂没有）
        }
        
        # 记录详细的日志，包括分离后的属性数量
        preview = text[:200] + ('...' if len(text) > 200 else '')
        logger.info(f"成功解析装备数据，文本总行数: {len(all_lines)}")
        logger.info(f"装备信息: {equipment_name} [{equipment_type}]")
        logger.info(f"解析到的基底属性数量: {len(base_properties)}条")
        logger.info(f"解析到的词缀属性数量: {len(explicit_mods)}条")
        logger.debug(f"装备文本预览: {preview}")
        
        # 记录具体的词缀内容
        if explicit_mods:
            logger.info("识别到的词缀内容:")
            for i, mod in enumerate(explicit_mods[:3]):  # 只显示前3个词缀
                logger.info(f"  词缀{i+1}: {mod}")
            if len(explicit_mods) > 3:
                logger.info(f"  ... 等{len(explicit_mods)}个词缀")
        
        return equipment_data
    
    @staticmethod
    def _identify_equipment_type(text):
        """
        简单识别装备类型
        
        Args:
            text (str): 装备文本
            
        Returns:
            str: 装备类型描述
        """
        if any(keyword in text for keyword in ["药剂", "生命药剂", "魔力药剂", "黄玉药剂", "蓝玉药剂", 
                                              "红玉药剂", "翡翠药剂", "紫晶药剂", "坚岩药剂"]):
            return "功能药剂"
        elif "物品类别:" in text:
            return "装备"
        else:
            return "未知类型"
    
    @staticmethod
    def _extract_equipment_name(text):
        """
        简单提取装备名称
        
        Args:
            text (str): 装备文本
            
        Returns:
            str: 装备名称或None
        """
        # 直接返回第一行非空行作为名称
        lines = text.split('\n')
        for line in lines:
            stripped_line = line.strip()
            if stripped_line and "----" not in stripped_line and "稀有度:" not in stripped_line:
                return stripped_line
        
        return None
    
    @staticmethod
    def check_mods_match(equipment_data, target_mods, match_mode="OR", match_count=None):
        """
        增强版检查装备是否匹配目标规则
        只在词缀属性（explicit_mods和implicit_mods）中进行匹配，避免匹配到基底属性
        
        Args:
            equipment_data (dict): 装备数据字典
            target_mods (list): 目标词缀列表，每个元素为 {"text": "词缀文本", "include": True/False}
            match_mode (str): 匹配模式，"AND", "OR" 或 "COUNT"
            match_count (int, optional): COUNT模式下需要匹配的词缀数量
            
        Returns:
            tuple: (是否匹配, 匹配信息字典)
        """
        if not equipment_data:
            return False, {}
        
        # 如果没有提供匹配规则，直接返回匹配失败
        if not target_mods or not isinstance(target_mods, list):
            logger.warning("未提供有效的匹配规则，返回匹配失败")
            return False, {}
        
        matched_includes = []
        matched_excludes = []
        unmatched_includes = []
        
        # 获取词缀属性（只使用词缀，不使用基底属性）
        explicit_mods = equipment_data.get("explicit_mods", [])
        implicit_mods = equipment_data.get("implicit_mods", [])
        
        # 合并词缀列表用于匹配
        all_mods = explicit_mods + implicit_mods
        
        logger.info(f"开始检查目标词条匹配情况")
        logger.info(f"用于匹配的词缀属性数量: {len(all_mods)} 条")
        
        # 记录可用的词缀内容
        if all_mods:
            logger.info("词缀属性内容:")
            for i, mod in enumerate(all_mods[:5]):  # 最多显示5个词缀
                logger.info(f"  词缀{i+1}: {mod}")
        else:
            logger.warning("警告: 未找到词缀属性，可能导致匹配失败")
        
        # 分别处理包含和排除的词条
        for target in target_mods:
            if not target.get("enabled", True):
                logger.info(f"跳过禁用的词条条件: {target['text']}")
                continue
                
            # 对目标词条进行规范化处理
            target_text = target["text"].lower().replace('　', ' ')
            target_text = re.sub(r'\s+', ' ', target_text)
            
            logger.info(f"检查{'' if target['include'] else '排除'}条件: '{target['text']}'")
            
            # 只在词缀属性中进行匹配
            final_matched = False
            matched_mod = None
            
            for mod in all_mods:
                # 对词缀行也进行规范化处理
                norm_mod = mod.lower().replace('　', ' ')
                norm_mod = re.sub(r'\s+', ' ', norm_mod)
                
                if target_text in norm_mod:
                    final_matched = True
                    matched_mod = mod
                    break
            
            if target["include"]:
                if final_matched:
                    matched_includes.append({"text": target["text"], "matched_mod": matched_mod})
                    logger.info(f"✅ 条件匹配成功: '{target['text']}' 在词缀 '{matched_mod}' 中找到")
                else:
                    unmatched_includes.append(target["text"])
                    logger.info(f"❌ 条件匹配失败: '{target['text']}' 未在装备词缀中找到")
            else:
                if final_matched:
                    matched_excludes.append({"text": target["text"], "matched_mod": matched_mod})
                    logger.info(f"⚠️  匹配到排除词条: '{target['text']}' 在词缀 '{matched_mod}' 中找到")
        
        # 判断是否合格
        # 1. 如果有任何排除词条匹配，则不合格
        if matched_excludes:
            is_qualified = False
        elif match_mode == "AND":
            # AND模式：所有包含词条都必须匹配
            is_qualified = len(unmatched_includes) == 0
        elif match_mode == "COUNT" and match_count is not None:
            # COUNT模式：匹配的包含词条数量需要达到指定数量
            is_qualified = len(matched_includes) >= match_count
        else:
            # 默认OR模式：至少有一个包含词条匹配
            is_qualified = len(matched_includes) > 0
        
        # 确保在没有任何规则或没有成功匹配时不返回误报
        enabled_rules = [rule for rule in target_mods if rule.get("enabled", True)]
        if not enabled_rules and is_qualified:
            logger.warning("所有规则都被禁用，但匹配结果为成功，强制返回失败")
            is_qualified = False
        
        match_info = {
            "matched_includes": matched_includes,
            "matched_excludes": matched_excludes,
            "unmatched_includes": unmatched_includes,
            "equipment_name": equipment_data.get("name", "未知装备"),
            "equipment_type": equipment_data.get("type", "未知类型"),
            "mod_count": len(all_mods),
            "match_count": len(matched_includes)
        }
        
        return is_qualified, match_info
    

    
    @staticmethod
    def extract_all_mods(text):
        """
        简化版提取所有可能的词缀行
        
        Args:
            text (str): 装备文本
            
        Returns:
            list: 所有非空行的列表（简化处理）
        """
        if not text:
            return []
            
        # 简单返回所有非空行
        return [line.strip() for line in text.split('\n') if line.strip()]
