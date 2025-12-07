#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
装备数据模型模块
用于定义和管理Path of Exile装备的数据结构
"""

from typing import Dict, List, Optional


class EquipmentProperty:
    """
    装备属性类
    表示装备上的单个属性，如伤害、暴击率等
    """
    def __init__(self, name: str, value: str, is_augmented: bool = False):
        """
        初始化装备属性
        
        Args:
            name: 属性名称
            value: 属性值
            is_augmented: 是否是被强化过的值
        """
        self.name = name
        self.value = value
        self.is_augmented = is_augmented
    
    def __str__(self) -> str:
        suffix = " (augmented)" if self.is_augmented else ""
        return f"{self.name}: {self.value}{suffix}"
    
    def __repr__(self) -> str:
        return f"EquipmentProperty(name='{self.name}', value='{self.value}', is_augmented={self.is_augmented})"
    
    def to_dict(self) -> Dict:
        """
        转换为字典格式
        
        Returns:
            包含属性信息的字典
        """
        return {
            "name": self.name,
            "value": self.value,
            "is_augmented": self.is_augmented
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'EquipmentProperty':
        """
        从字典创建实例
        
        Args:
            data: 包含属性信息的字典
            
        Returns:
            EquipmentProperty实例
        """
        return cls(
            name=data.get("name", ""),
            value=data.get("value", ""),
            is_augmented=data.get("is_augmented", False)
        )


class Affix:
    """
    装备词缀类
    表示装备上的一条词缀
    """
    def __init__(self, text: str, is_mutated: bool = False):
        """
        初始化词缀
        
        Args:
            text: 词缀文本内容
            is_mutated: 是否是变异词缀
        """
        self.text = text
        self.is_mutated = is_mutated
    
    def __str__(self) -> str:
        suffix = " (mutated)" if self.is_mutated else ""
        return f"{self.text}{suffix}"
    
    def __repr__(self) -> str:
        return f"Affix(text='{self.text}', is_mutated={self.is_mutated})"
    
    def to_dict(self) -> Dict:
        """
        转换为字典格式
        
        Returns:
            包含词缀信息的字典
        """
        return {
            "text": self.text,
            "is_mutated": self.is_mutated
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Affix':
        """
        从字典创建实例
        
        Args:
            data: 包含词缀信息的字典
            
        Returns:
            Affix实例
        """
        return cls(
            text=data.get("text", ""),
            is_mutated=data.get("is_mutated", False)
        )


class Equipment:
    """
    装备类
    表示一个完整的Path of Exile装备
    """
    def __init__(self):
        """
        初始化装备对象
        """
        # 基本信息
        self.category: str = ""
        self.rarity: str = ""
        self.name: str = ""
        self.base_name: str = ""
        self.item_level: int = 0
        
        # 需求
        self.required_level: int = 0
        self.required_attributes: Dict[str, int] = {}
        
        # 属性列表
        self.properties: List[EquipmentProperty] = []
        
        # 插槽
        self.sockets: str = ""
        
        # 词缀列表
        self.affixes: List[Affix] = []
        
        # 描述文本
        self.flavor_text: str = ""
        
        # 其他信息
        self.is_identified: bool = True
        self.is_corrupted: bool = False
    
    def __str__(self) -> str:
        lines = []
        lines.append(f"物品类别: {self.category}")
        lines.append(f"稀 有 度: {self.rarity}")
        lines.append(f"{self.name}")
        if self.base_name and self.base_name != self.name:
            lines.append(f"{self.base_name}")
        lines.append("--------")
        
        for prop in self.properties:
            lines.append(str(prop))
        
        if self.required_level > 0 or self.required_attributes:
            lines.append("--------")
            lines.append("需求:")
            if self.required_level > 0:
                lines.append(f"等级: {self.required_level}")
            for attr, value in self.required_attributes.items():
                lines.append(f"{attr}: {value}")
        
        if self.sockets:
            lines.append("--------")
            lines.append(f"插槽: {self.sockets}")
        
        if self.item_level > 0:
            lines.append("--------")
            lines.append(f"物品等级: {self.item_level}")
        
        if self.affixes:
            lines.append("--------")
            for affix in self.affixes:
                lines.append(str(affix))
        
        if self.flavor_text:
            lines.append("--------")
            lines.append(self.flavor_text)
        
        return "\n".join(lines)
    
    def __repr__(self) -> str:
        return f"Equipment(category='{self.category}', rarity='{self.rarity}', name='{self.name}')"
    
    def get_all_text(self) -> str:
        """
        获取装备的所有文本内容，用于匹配搜索
        
        Returns:
            所有文本内容的组合字符串
        """
        text_parts = []
        text_parts.append(self.category)
        text_parts.append(self.rarity)
        text_parts.append(self.name)
        text_parts.append(self.base_name)
        
        for prop in self.properties:
            text_parts.append(f"{prop.name}: {prop.value}")
        
        for attr, value in self.required_attributes.items():
            text_parts.append(f"{attr}: {value}")
        
        text_parts.append(self.sockets)
        
        for affix in self.affixes:
            text_parts.append(affix.text)
        
        text_parts.append(self.flavor_text)
        
        return " ".join(filter(None, text_parts))
    
    def has_stat(self, keyword: str, case_sensitive: bool = False) -> bool:
        """
        检查装备是否包含特定的属性或词缀
        
        Args:
            keyword: 要搜索的关键词
            case_sensitive: 是否区分大小写
            
        Returns:
            是否包含指定关键词
        """
        all_text = self.get_all_text()
        if not case_sensitive:
            all_text = all_text.lower()
            keyword = keyword.lower()
        
        return keyword in all_text
    
    def to_dict(self) -> Dict:
        """
        转换为字典格式
        
        Returns:
            包含装备信息的字典
        """
        return {
            "category": self.category,
            "rarity": self.rarity,
            "name": self.name,
            "base_name": self.base_name,
            "item_level": self.item_level,
            "required_level": self.required_level,
            "required_attributes": self.required_attributes,
            "properties": [prop.to_dict() for prop in self.properties],
            "sockets": self.sockets,
            "affixes": [affix.to_dict() for affix in self.affixes],
            "flavor_text": self.flavor_text,
            "is_identified": self.is_identified,
            "is_corrupted": self.is_corrupted
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Equipment':
        """
        从字典创建实例
        
        Args:
            data: 包含装备信息的字典
            
        Returns:
            Equipment实例
        """
        equipment = cls()
        equipment.category = data.get("category", "")
        equipment.rarity = data.get("rarity", "")
        equipment.name = data.get("name", "")
        equipment.base_name = data.get("base_name", "")
        equipment.item_level = data.get("item_level", 0)
        equipment.required_level = data.get("required_level", 0)
        equipment.required_attributes = data.get("required_attributes", {})
        
        # 转换属性列表
        for prop_data in data.get("properties", []):
            equipment.properties.append(EquipmentProperty.from_dict(prop_data))
        
        equipment.sockets = data.get("sockets", "")
        
        # 转换词缀列表
        for affix_data in data.get("affixes", []):
            equipment.affixes.append(Affix.from_dict(affix_data))
        
        equipment.flavor_text = data.get("flavor_text", "")
        equipment.is_identified = data.get("is_identified", True)
        equipment.is_corrupted = data.get("is_corrupted", False)
        
        return equipment


class TargetCondition:
    """
    目标洗练条件类
    表示用户设置的需要匹配的词条条件
    """
    def __init__(self, text: str, include: bool = True):
        """
        初始化洗练条件
        
        Args:
            text: 要匹配的文本
            include: 是否是包含条件（True）或排除条件（False）
        """
        self.text = text
        self.include = include
    
    def __str__(self) -> str:
        prefix = "[包含]" if self.include else "[排除]"
        return f"{prefix} {self.text}"
    
    def __repr__(self) -> str:
        return f"TargetCondition(text='{self.text}', include={self.include})"
    
    def to_dict(self) -> Dict:
        """
        转换为字典格式
        
        Returns:
            包含条件信息的字典
        """
        return {
            "text": self.text,
            "include": self.include
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'TargetCondition':
        """
        从字典创建实例
        
        Args:
            data: 包含条件信息的字典
            
        Returns:
            TargetCondition实例
        """
        return cls(
            text=data.get("text", ""),
            include=data.get("include", True)
        )


class MatchResult:
    """
    匹配结果类
    表示一次装备词缀匹配的结果
    """
    def __init__(self, attempt: int = 0):
        """
        初始化匹配结果
        
        Args:
            attempt: 尝试次数
        """
        self.attempt = attempt
        self.is_qualified = False
        self.matched_includes: List[str] = []
        self.unmatched_includes: List[str] = []
        self.matched_excludes: List[str] = []
        self.equipment: Optional[Equipment] = None
    
    def __str__(self) -> str:
        status = "✓ 成功" if self.is_qualified else "✗ 失败"
        result = f"第{self.attempt}次尝试 - {status}"
        
        if self.matched_includes:
            result += f"\n  匹配到的包含词条: {', '.join(self.matched_includes)}"
        if self.unmatched_includes:
            result += f"\n  未匹配的包含词条: {', '.join(self.unmatched_includes)}"
        if self.matched_excludes:
            result += f"\n  匹配到的排除词条: {', '.join(self.matched_excludes)}"
        
        return result
    
    def __repr__(self) -> str:
        return f"MatchResult(attempt={self.attempt}, is_qualified={self.is_qualified})"
    
    def to_dict(self) -> Dict:
        """
        转换为字典格式
        
        Returns:
            包含匹配结果信息的字典
        """
        result = {
            "attempt": self.attempt,
            "is_qualified": self.is_qualified,
            "matched_includes": self.matched_includes,
            "unmatched_includes": self.unmatched_includes,
            "matched_excludes": self.matched_excludes
        }
        
        if self.equipment:
            result["equipment"] = self.equipment.to_dict()
        
        return result