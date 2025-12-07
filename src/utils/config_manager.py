#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
POE装备洗练工具 - 配置管理模块
用于加载、保存和管理配置文件
"""

import os
import configparser
import logging

logger = logging.getLogger(__name__)


def load_config(config_file='config.ini'):
    """
    加载配置文件
    
    Args:
        config_file (str): 配置文件路径
        
    Returns:
        dict: 配置字典
    """
    # 基础配置模板
    config = {
        'debug_mode': False,        # 调试模式
        'output_dir': 'output',    # 输出目录
        'max_attempts': 1000,      # 最大尝试次数
        'click_duration': 0.1,     # 点击持续时间
        'operation_delay': 0.3,    # 操作间隔延迟
        'clipboard_check_delay': 0.5,  # 剪贴板检查延迟
        'match_mode': 'OR',        # 匹配模式: AND, OR
        'match_count': 1,          # 当模式为COUNT时，需要满足的规则数量
        'currency_position': (0, 0),  # 当前使用的通货位置
        'equipment_positions': {
            '默认武器': (500, 300),
            '默认护甲': (600, 300),
            '默认首饰': (700, 300)
        },
        'currency_positions': {
            '混沌石': (800, 300),
            '崇高石': (900, 300),
            '改造石': (1000, 300)
        },
        'current_currency': '混沌石', # 当前使用的通货名称
        'current_equipment': '默认武器', # 默认使用的装备名称
        'rule_sets': {             # 规则集合字典，键是规则名称，值是包含词条、装备和通货的字典
            '默认规则': {
                'targets': [],     # 词条列表
                'equipment': '默认武器',  # 默认装备位置
                'currency': '混沌石'       # 默认通货位置
            }         # 默认规则集合
        },
        'current_rule_set': '默认规则', # 当前使用的规则集合名称
        'sequence_items': [],       # 序列执行项列表
        # 未知命运卡相关配置
        'unknown_fate_card_position': (0, 0),  # 未知命运卡位置
        'card_storage_position': (0, 0),        # 存放卡片位置
        'fate_card_loop_count': 10,             # 循环次数
        # 按键配置
        'stop_key': 'esc'           # 停止所有操作的按键
    }
    
    if not os.path.exists(config_file):
        logger.info(f"配置文件 {config_file} 不存在，使用默认配置")
        return config
    
    try:
        parser = configparser.ConfigParser(allow_no_value=True)
        parser.read(config_file, encoding='utf-8')
        
        # 读取通用配置
        if 'General' in parser:
            general = parser['General']
            config['debug_mode'] = general.getboolean('DebugMode', fallback=False)
            config['output_dir'] = general.get('OutputDir', fallback='output')
            config['max_attempts'] = general.getint('maxattempts', fallback=1000)
            config['click_duration'] = general.getfloat('ClickDuration', fallback=0.1)
            config['operation_delay'] = general.getfloat('OperationDelay', fallback=0.3)
            config['clipboard_check_delay'] = general.getfloat('ClipboardCheckDelay', fallback=0.5)
            config['match_mode'] = general.get('MatchMode', fallback='OR')
            config['match_count'] = general.getint('matchcount', fallback=1)
        
        # 读取带条件的词条
        if 'ConditionalTargets' in parser:
            # 兼容旧版本配置，将原有的条件词条加载到默认规则集合的targets字段
            default_rules = []
            for key, value in parser['ConditionalTargets'].items():
                if value and ',' in value:
                    parts = value.strip().split(',', 2)
                    include = parts[0].strip().lower() == 'include'
                    text = parts[1].strip()
                    min_value = None
                    # 检查是否有最小数值要求
                    if len(parts) >= 3:
                        try:
                            min_value = float(parts[2].strip())
                        except ValueError:
                            logger.warning(f"词条 '{key}' 的最小数值要求格式不正确: {parts[2]}")
                    # 创建词条字典，包含启用状态（默认启用）
                    target = {
                        'text': text,
                        'include': include,
                        'enabled': True
                    }
                    if min_value is not None:
                        target['min_value'] = min_value
                    default_rules.append(target)
            # 更新默认规则集
            config['rule_sets']['默认规则']['targets'] = default_rules
        
        # 读取规则集合配置
        rule_sets_section = 'RuleSets'
        if rule_sets_section in parser:
            # 读取规则集合配置
            for key, value in parser[rule_sets_section].items():
                if key.startswith('rule_set_') and value:
                    # 获取规则集合名称
                    rule_set_name = value.strip()
                    # 读取该规则集合的词条
                    rule_set_key = key.replace('rule_set_', 'rules_')
                    if rule_set_key in parser:
                        rule_items = []
                        for rule_key, rule_value in parser[rule_set_key].items():
                            if rule_value and ',' in rule_value:
                                parts = rule_value.strip().split(',', 2)
                                include = parts[0].strip().lower() == 'include'
                                text = parts[1].strip()
                                min_value = None
                                if len(parts) >= 3:
                                    try:
                                        min_value = float(parts[2].strip())
                                    except ValueError:
                                        logger.warning(f"规则集合 '{rule_set_name}' 的词条 '{rule_key}' 最小数值要求格式不正确: {parts[2]}")
                                target = {
                                    'text': text,
                                    'include': include,
                                    'enabled': True
                                }
                                if min_value is not None:
                                    target['min_value'] = min_value
                                rule_items.append(target)
                        
                        # 读取规则集合的装备和通货配置
                        equip_key = key.replace('rule_set_', 'equip_')
                        curr_key = key.replace('rule_set_', 'curr_')
                        
                        equipment = parser[rule_sets_section].get(equip_key, '默认武器').strip()
                        currency = parser[rule_sets_section].get(curr_key, '混沌石').strip()
                        
                        # 更新规则集合
                        config['rule_sets'][rule_set_name] = {
                            'targets': rule_items,
                            'equipment': equipment,
                            'currency': currency
                        }
        
        # 兼容旧代码，保持conditional_targets字段
        config['conditional_targets'] = config['rule_sets'][config['current_rule_set']]['targets']
        
        # 读取装备位置
        if 'EquipmentPositions' in parser:
            for name, pos_str in parser['EquipmentPositions'].items():
                if pos_str:  # 确保值不为空
                    try:
                        x, y = map(int, pos_str.strip().split(','))
                        config['equipment_positions'][name] = (x, y)
                    except (ValueError, IndexError):
                        logger.warning(f"装备位置 '{name}' 格式不正确: {pos_str}")
        
        # 读取通货位置
        if 'CurrencyPositions' in parser:
            for name, pos_str in parser['CurrencyPositions'].items():
                if name.lower() == 'currentcurrency':
                    config['current_currency'] = pos_str.strip()
                elif pos_str:  # 确保值不为空
                    try:
                        x, y = map(int, pos_str.strip().split(','))
                        config['currency_positions'][name] = (x, y)
                    except (ValueError, IndexError):
                        logger.warning(f"通货位置 '{name}' 格式不正确: {pos_str}")
        
        # 读取序列执行项
        if 'SequenceItems' in parser:
            config['sequence_items'] = []
            for key, value in parser['SequenceItems'].items():
                if value:
                    try:
                        parts = value.strip().split(',', 3)
                        if len(parts) >= 3:
                            equipment = parts[0].strip()
                            currency = parts[1].strip()
                            rules = parts[2].strip()
                            enabled = True
                            if len(parts) >= 4:
                                enabled = parts[3].strip().lower() == 'true'
                            
                            # 使用对应的规则集
                            rule_set = []
                            if rules in config['rule_sets']:
                                rule_set = config['rule_sets'][rules]['targets'].copy()
                            
                            config['sequence_items'].append({
                                'equipment': equipment,
                                'currency': currency,
                                'rules': rules,
                                'rule_set': rule_set,
                                'enabled': enabled
                            })
                    except (ValueError, IndexError):
                        logger.warning(f"序列执行项 '{key}' 格式不正确: {value}")
        
        # 读取未知命运卡配置
        if 'FateCard' in parser:
            fate_card = parser['FateCard']
            # 读取未知命运卡位置
            if 'UnknownCardPosition' in fate_card:
                try:
                    pos_str = fate_card['UnknownCardPosition'].strip()
                    x, y = map(int, pos_str.split(','))
                    config['unknown_fate_card_position'] = (x, y)
                except (ValueError, IndexError):
                    logger.warning(f"未知命运卡位置格式不正确: {fate_card.get('UnknownCardPosition', '')}")
            # 读取存放卡片位置
            if 'CardStoragePosition' in fate_card:
                try:
                    pos_str = fate_card['CardStoragePosition'].strip()
                    x, y = map(int, pos_str.split(','))
                    config['card_storage_position'] = (x, y)
                except (ValueError, IndexError):
                    logger.warning(f"存放卡片位置格式不正确: {fate_card.get('CardStoragePosition', '')}")
            # 读取循环次数
            if 'LoopCount' in fate_card:
                try:
                    config['fate_card_loop_count'] = int(fate_card['LoopCount'])
                except ValueError:
                    logger.warning(f"循环次数格式不正确: {fate_card.get('LoopCount', '')}")
        
        # 读取按键配置
        if 'General' in parser:
            general = parser['General']
            if 'StopKey' in general:
                config['stop_key'] = general['StopKey'].strip().lower()
        
    except Exception as e:
        logger.error(f"加载配置文件失败: {e}")
    
    return config


def save_config(config, config_file='config.ini'):
    """
    保存配置到文件
    
    Args:
        config (dict): 配置字典
        config_file (str): 配置文件路径
        
    Returns:
        bool: 操作是否成功
    """
    try:
        # 确保配置文件路径是绝对路径
        if not os.path.isabs(config_file):
            config_file = os.path.abspath(config_file)
        
        logger.debug(f"[save_config] 开始保存配置到文件: {config_file}")
        logger.debug(f"[save_config] 配置内容: {config}")
        
        parser = configparser.ConfigParser(allow_no_value=True)
        
        # 写入通用配置
        parser['General'] = {
            'DebugMode': str(config['debug_mode']),
            'OutputDir': config['output_dir'],
            'maxattempts': str(config['max_attempts']),
            'ClickDuration': str(config['click_duration']),
            'OperationDelay': str(config['operation_delay']),
            'ClipboardCheckDelay': str(config['clipboard_check_delay']),
            'MatchMode': config['match_mode'],
            'StopKey': config['stop_key']
        }
        
        # 无论匹配模式是什么，都写入匹配数量（如果存在）
        if 'match_count' in config:
            parser['General']['matchcount'] = str(config['match_count'])
            logger.debug(f"[save_config] 写入matchcount: {config['match_count']}")
        
        # 写入带条件的词条（兼容旧版本）
        current_rule_data = config['rule_sets'][config['current_rule_set']]
        current_rules = current_rule_data['targets']
        if current_rules:
            parser['ConditionalTargets'] = {}
            for i, target in enumerate(current_rules):
                condition = 'include' if target['include'] else 'exclude'
                # 构建词条字符串，包含条件、文本和最小数值要求（如果存在）
                target_str = f'{condition}, {target["text"]}'
                if 'min_value' in target and target['min_value'] is not None:
                    target_str += f', {target["min_value"]}'
                parser['ConditionalTargets'][f'target_{i+1}'] = target_str
        
        # 写入规则集合配置
        parser['RuleSets'] = {}
        for i, (rule_set_name, rule_data) in enumerate(config['rule_sets'].items()):
            # 写入规则集合名称
            rule_set_key = f'rule_set_{i+1}'
            parser['RuleSets'][rule_set_key] = rule_set_name
            
            # 写入规则集合的装备和通货
            parser['RuleSets'][f'equip_{i+1}'] = rule_data['equipment']
            parser['RuleSets'][f'curr_{i+1}'] = rule_data['currency']
            
            # 写入规则集合的词条
            rule_section_name = f'rules_{i+1}'
            parser[rule_section_name] = {}
            rules = rule_data['targets']
            for j, target in enumerate(rules):
                condition = 'include' if target['include'] else 'exclude'
                target_str = f'{condition}, {target["text"]}'
                if 'min_value' in target and target['min_value'] is not None:
                    target_str += f', {target["min_value"]}'
                parser[rule_section_name][f'rule_{j+1}'] = target_str
        
        # 写入装备位置
        if config['equipment_positions']:
            parser['EquipmentPositions'] = {}
            for name, pos in config['equipment_positions'].items():
                parser['EquipmentPositions'][name] = f'{pos[0]}, {pos[1]}'
        
        # 写入通货位置
        parser['CurrencyPositions'] = {}
        parser['CurrencyPositions']['CurrentCurrency'] = config['current_currency']
        for name, pos in config['currency_positions'].items():
            parser['CurrencyPositions'][name] = f'{pos[0]}, {pos[1]}'
        
        # 写入序列执行项
        if config['sequence_items']:
            parser['SequenceItems'] = {}
            for i, item in enumerate(config['sequence_items']):
                enabled_str = 'True' if item.get('enabled', True) else 'False'
                parser['SequenceItems'][f'sequence_{i+1}'] = f'{item["equipment"]}, {item["currency"]}, {item["rules"]}, {enabled_str}'
        
        # 写入未知命运卡配置
        parser['FateCard'] = {
            'UnknownCardPosition': f'{config["unknown_fate_card_position"][0]}, {config["unknown_fate_card_position"][1]}',
            'CardStoragePosition': f'{config["card_storage_position"][0]}, {config["card_storage_position"][1]}',
            'LoopCount': str(config['fate_card_loop_count'])
        }
        
        # 写入文件
        with open(config_file, 'w', encoding='utf-8') as f:
            parser.write(f)
        
        logger.info(f"配置已保存到 {config_file}")
        
        # 验证配置是否被正确保存
        with open(config_file, 'r', encoding='utf-8') as f:
            content = f.read()
        logger.debug(f"[save_config] 配置文件内容: {content}")
        
        return True
    except Exception as e:
        logger.error(f"保存配置失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def create_default_config(config_file='config.ini'):
    """
    创建默认配置文件
    
    Args:
        config_file (str): 配置文件路径
        
    Returns:
        bool: 操作是否成功
    """
    default_config = {
        'debug_mode': False,
        'output_dir': 'output',
        'max_attempts': 1000,
        'click_duration': 0.1,
        'operation_delay': 0.3,
        'clipboard_check_delay': 0.5,
        'match_mode': 'OR',
        'rule_sets': {
            '默认规则': {
                'targets': [{'text': '弓类攻击发射2支额外箭矢', 'include': True, 'enabled': True}],
                'equipment': '默认武器',
                'currency': '混沌石'
            }
        },
        'current_rule_set': '默认规则',
        # 默认装备位置
        'equipment_positions': {
            '默认武器': (500, 300),
            '默认护甲': (600, 300),
            '默认首饰': (700, 300)
        },
        'currency_positions': {},
        'current_currency': '混沌石',
        'current_equipment': '默认武器'
    }
    return save_config(default_config, config_file)


def ensure_output_dir(output_dir='output'):
    """
    确保输出目录存在
    
    Args:
        output_dir (str): 输出目录路径
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        logger.info(f"创建输出目录: {output_dir}")