#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Evolution Items System

Defines the items required for pet evolution and manages the inventory.
"""
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional
import json
from pathlib import Path


class EvolutionItemType(Enum):
    """Types of evolution items."""
    CODE_FRAGMENT = "code_fragment"          # 代码碎片 - 阶段1-3进化
    BUG_SLAYER = "bug_slayer"                # 除虫剑 - 阶段4-6进化
    WISDOM_CRYSTAL = "wisdom_crystal"        # 智慧水晶 - 阶段7-8进化
    ANCIENT_RELIC = "ancient_relic"          # 远古遗物 - 阶段9进化
    FRIENDSHIP_BADGE = "friendship_badge"    # 友谊徽章 - 社交路径进化
    MOONSTONE = "moonstone"                  # 月光石 - 夜猫路径进化
    GOLDEN_APPLE = "golden_apple"            # 金苹果 - 恢复道具
    RAINBOW_FEATHER = "rainbow_feather"      # 彩虹羽毛 - 稀有装饰


@dataclass
class EvolutionItem:
    """进化道具类"""
    item_type: EvolutionItemType
    count: int = 1
    obtained_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        return {
            'item_type': self.item_type.value,
            'count': self.count,
            'obtained_at': self.obtained_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'EvolutionItem':
        return cls(
            item_type=EvolutionItemType(data['item_type']),
            count=data.get('count', 1),
            obtained_at=datetime.fromisoformat(data.get('obtained_at', datetime.now().isoformat()))
        )


# Item display information
ITEM_DISPLAY_INFO = {
    EvolutionItemType.CODE_FRAGMENT: {
        'name': '代码碎片',
        'icon': '🔹',
        'description': '从创建的文件中收集的代码碎片',
        'rarity': 'common',
        'color': '#3b82f6',
        'evolution_stages': [1, 2, 3]
    },
    EvolutionItemType.BUG_SLAYER: {
        'name': '除虫剑',
        'icon': '⚔️',
        'description': '修复错误时获得的荣耀之剑',
        'rarity': 'uncommon',
        'color': '#f97316',
        'evolution_stages': [4, 5, 6]
    },
    EvolutionItemType.WISDOM_CRYSTAL: {
        'name': '智慧水晶',
        'icon': '💎',
        'description': '高生产力时凝结的智慧',
        'rarity': 'rare',
        'color': '#a855f7',
        'evolution_stages': [7, 8]
    },
    EvolutionItemType.ANCIENT_RELIC: {
        'name': '远古遗物',
        'icon': '🏺',
        'description': '收集全部成就后的神秘遗物',
        'rarity': 'legendary',
        'color': '#fbbf24',
        'evolution_stages': [9]
    },
    EvolutionItemType.FRIENDSHIP_BADGE: {
        'name': '友谊徽章',
        'icon': '🎖️',
        'description': '与宠物互动50次获得',
        'rarity': 'uncommon',
        'color': '#ec4899',
        'evolution_stages': []  # 用于社交路径加成
    },
    EvolutionItemType.MOONSTONE: {
        'name': '月光石',
        'icon': '🌙',
        'description': '深夜编程时收集的月光精华',
        'rarity': 'rare',
        'color': '#8b5cf6',
        'evolution_stages': []  # 用于夜猫路径加成
    },
    EvolutionItemType.GOLDEN_APPLE: {
        'name': '金苹果',
        'icon': '🍎',
        'description': '恢复50点饱食度和快乐值',
        'rarity': 'uncommon',
        'color': '#eab308',
        'evolution_stages': []
    },
    EvolutionItemType.RAINBOW_FEATHER: {
        'name': '彩虹羽毛',
        'icon': '🪶',
        'description': '稀有装饰道具，让宠物更加闪耀',
        'rarity': 'epic',
        'color': '#f472b6',
        'evolution_stages': []
    },
}


def get_item_display_name(item_type: EvolutionItemType) -> str:
    """获取道具显示名称"""
    return ITEM_DISPLAY_INFO.get(item_type, {}).get('name', item_type.value.replace('_', ' ').title())


def get_item_description(item_type: EvolutionItemType) -> str:
    """获取道具描述"""
    return ITEM_DISPLAY_INFO.get(item_type, {}).get('description', '')


def get_item_icon(item_type: EvolutionItemType) -> str:
    """获取道具图标"""
    return ITEM_DISPLAY_INFO.get(item_type, {}).get('icon', '📦')


def get_item_color(item_type: EvolutionItemType) -> str:
    """获取道具颜色"""
    return ITEM_DISPLAY_INFO.get(item_type, {}).get('color', '#94a3b8')


def get_item_rarity(item_type: EvolutionItemType) -> str:
    """获取道具稀有度"""
    return ITEM_DISPLAY_INFO.get(item_type, {}).get('rarity', 'common')


class Inventory:
    """物品栏管理"""

    def __init__(self):
        self.items: Dict[EvolutionItemType, int] = {}
        self._save_file = Path.home() / '.claude-pet-companion' / 'inventory.json'
        self.load()

    def add_item(self, item_type: EvolutionItemType, count: int = 1) -> bool:
        """添加道具到物品栏"""
        self.items[item_type] = self.items.get(item_type, 0) + count
        self.save()
        return True

    def has_item(self, item_type: EvolutionItemType, count: int = 1) -> bool:
        """检查是否有足够的道具"""
        return self.items.get(item_type, 0) >= count

    def use_item(self, item_type: EvolutionItemType, count: int = 1) -> bool:
        """使用道具"""
        if self.has_item(item_type, count):
            self.items[item_type] -= count
            if self.items[item_type] <= 0:
                del self.items[item_type]
            self.save()
            return True
        return False

    def get_item_count(self, item_type: EvolutionItemType) -> int:
        """获取道具数量"""
        return self.items.get(item_type, 0)

    def get_all_items(self) -> Dict[EvolutionItemType, int]:
        """获取所有道具"""
        return self.items.copy()

    def get_total_count(self) -> int:
        """获取道具总数"""
        return sum(self.items.values())

    def clear(self):
        """清空物品栏"""
        self.items.clear()
        self.save()

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'items': {k.value: v for k, v in self.items.items()}
        }

    def save(self):
        """保存物品栏"""
        self._save_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self._save_file, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)

    def load(self):
        """加载物品栏"""
        if self._save_file.exists():
            try:
                with open(self._save_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.items = {
                        EvolutionItemType(k): v
                        for k, v in data.get('items', {}).items()
                    }
            except (json.JSONDecodeError, ValueError, KeyError):
                self.items = {}

    def get_evolution_requirements(self, target_stage: int) -> Dict[EvolutionItemType, int]:
        """获取进化到指定阶段所需的道具"""
        requirements = {}

        if 1 <= target_stage <= 3:
            requirements[EvolutionItemType.CODE_FRAGMENT] = target_stage
        elif 4 <= target_stage <= 6:
            requirements[EvolutionItemType.BUG_SLAYER] = target_stage - 3
        elif target_stage in [7, 8]:
            requirements[EvolutionItemType.WISDOM_CRYSTAL] = target_stage - 6
        elif target_stage == 9:
            requirements[EvolutionItemType.ANCIENT_RELIC] = 1

        return requirements

    def can_evolve(self, target_stage: int) -> bool:
        """检查是否可以进化到指定阶段"""
        requirements = self.get_evolution_requirements(target_stage)
        for item_type, count in requirements.items():
            if not self.has_item(item_type, count):
                return False
        return True

    def use_evolution_items(self, target_stage: int) -> bool:
        """使用进化道具"""
        if not self.can_evolve(target_stage):
            return False

        requirements = self.get_evolution_requirements(target_stage)
        for item_type, count in requirements.items():
            self.use_item(item_type, count)
        return True


# Item drop conditions and rates
class ItemDropManager:
    """管理道具掉落"""

    @staticmethod
    def check_file_creation_drop(files_created: int) -> Optional[EvolutionItemType]:
        """检查文件创建是否掉落道具"""
        # 每创建5个文件获得1个代码碎片
        if files_created > 0 and files_created % 5 == 0:
            return EvolutionItemType.CODE_FRAGMENT
        return None

    @staticmethod
    def check_error_fix_drop(errors_fixed: int) -> Optional[EvolutionItemType]:
        """检查修复错误是否掉落道具"""
        # 修复10个错误获得1个除虫剑
        if errors_fixed > 0 and errors_fixed % 10 == 0:
            return EvolutionItemType.BUG_SLAYER
        return None

    @staticmethod
    def check_productivity_drop(productivity: float) -> Optional[EvolutionItemType]:
        """检查生产力是否掉落道具"""
        # 生产力达到90%以上有机会获得智慧水晶
        if productivity >= 90:
            return EvolutionItemType.WISDOM_CRYSTAL
        return None

    @staticmethod
    def check_interaction_drop(interaction_count: int) -> Optional[EvolutionItemType]:
        """检查互动是否掉落道具"""
        # 互动50次获得友谊徽章
        if interaction_count > 0 and interaction_count % 50 == 0:
            return EvolutionItemType.FRIENDSHIP_BADGE
        return None

    @staticmethod
    def check_night_coding_drop(night_hours: int) -> Optional[EvolutionItemType]:
        """检查深夜编程是否掉落道具"""
        # 凌晨编程10小时获得月光石
        if night_hours >= 10:
            return EvolutionItemType.MOONSTONE
        return None


if __name__ == "__main__":
    # 测试道具系统
    inventory = Inventory()

    # 添加道具
    inventory.add_item(EvolutionItemType.CODE_FRAGMENT, 5)
    inventory.add_item(EvolutionItemType.BUG_SLAYER, 2)

    print(f"道具总数: {inventory.get_total_count()}")
    print(f"代码碎片数量: {inventory.get_item_count(EvolutionItemType.CODE_FRAGMENT)}")

    # 检查进化条件
    for stage in range(1, 10):
        can_evolve = inventory.can_evolve(stage)
        print(f"阶段 {stage} 进化要求: {inventory.get_evolution_requirements(stage)} - {'可以' if can_evolve else '不能'}进化")
