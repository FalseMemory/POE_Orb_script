#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""POE装备数据模型"""
from typing import Dict, List, Optional


class EquipmentProperty:
    def __init__(self, name="", value="", is_augmented=False):
        self.name = name; self.value = value; self.is_augmented = is_augmented
    def __str__(self):
        return f"{self.name}: {self.value}{' (augmented)' if self.is_augmented else ''}"
    def to_dict(self):
        return {"name": self.name, "value": self.value, "is_augmented": self.is_augmented}
    @classmethod
    def from_dict(cls, d):
        return cls(d.get("name", ""), d.get("value", ""), d.get("is_augmented", False))


class Affix:
    def __init__(self, text="", is_mutated=False):
        self.text = text; self.is_mutated = is_mutated
    def __str__(self):
        return f"{self.text}{' (mutated)' if self.is_mutated else ''}"
    def to_dict(self):
        return {"text": self.text, "is_mutated": self.is_mutated}
    @classmethod
    def from_dict(cls, d):
        return cls(d.get("text", ""), d.get("is_mutated", False))


class Equipment:
    def __init__(self):
        self.category = ""; self.rarity = ""; self.name = ""; self.base_name = ""
        self.item_level = 0; self.required_level = 0; self.required_attributes = {}
        self.properties = []; self.sockets = ""; self.affixes = []
        self.flavor_text = ""; self.is_identified = True; self.is_corrupted = False
    def get_all_text(self):
        parts = [self.category, self.rarity, self.name, self.base_name]
        for p in self.properties: parts.append(f"{p.name}: {p.value}")
        for a, v in self.required_attributes.items(): parts.append(f"{a}: {v}")
        parts.append(self.sockets)
        for a in self.affixes: parts.append(a.text)
        parts.append(self.flavor_text)
        return " ".join(filter(None, parts))
    def has_stat(self, kw, case_sensitive=False):
        t = self.get_all_text()
        if not case_sensitive: t = t.lower(); kw = kw.lower()
        return kw in t
    def to_dict(self):
        return {"category": self.category, "rarity": self.rarity, "name": self.name,
                "base_name": self.base_name, "item_level": self.item_level,
                "required_level": self.required_level, "required_attributes": self.required_attributes,
                "properties": [p.to_dict() for p in self.properties], "sockets": self.sockets,
                "affixes": [a.to_dict() for a in self.affixes], "flavor_text": self.flavor_text,
                "is_identified": self.is_identified, "is_corrupted": self.is_corrupted}
    @classmethod
    def from_dict(cls, d):
        e = cls()
        e.category = d.get("category", ""); e.rarity = d.get("rarity", "")
        e.name = d.get("name", ""); e.base_name = d.get("base_name", "")
        e.item_level = d.get("item_level", 0); e.required_level = d.get("required_level", 0)
        e.required_attributes = d.get("required_attributes", {})
        for pd in d.get("properties", []): e.properties.append(EquipmentProperty.from_dict(pd))
        e.sockets = d.get("sockets", "")
        for ad in d.get("affixes", []): e.affixes.append(Affix.from_dict(ad))
        e.flavor_text = d.get("flavor_text", "")
        e.is_identified = d.get("is_identified", True); e.is_corrupted = d.get("is_corrupted", False)
        return e


class TargetCondition:
    def __init__(self, text="", include=True):
        self.text = text; self.include = include
    def __str__(self):
        return f"{'[包含]' if self.include else '[排除]'} {self.text}"
    def to_dict(self):
        return {"text": self.text, "include": self.include}
    @classmethod
    def from_dict(cls, d):
        return cls(d.get("text", ""), d.get("include", True))


class MatchResult:
    def __init__(self, attempt=0):
        self.attempt = attempt; self.is_qualified = False
        self.matched_includes = []; self.unmatched_includes = []; self.matched_excludes = []
        self.equipment = None
    def to_dict(self):
        r = {"attempt": self.attempt, "is_qualified": self.is_qualified,
             "matched_includes": self.matched_includes, "unmatched_includes": self.unmatched_includes,
             "matched_excludes": self.matched_excludes}
        if self.equipment: r["equipment"] = self.equipment.to_dict()
        return r
