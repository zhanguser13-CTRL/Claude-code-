#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Items System for Claude Pet Companion

This module provides the evolution items and inventory management.
"""

from .evolution_items import (
    EvolutionItemType,
    EvolutionItem,
    Inventory,
    get_item_display_name,
    get_item_description,
    get_item_icon,
    get_item_color,
    get_item_rarity,
)

__all__ = [
    'EvolutionItemType',
    'EvolutionItem',
    'Inventory',
    'get_item_display_name',
    'get_item_description',
    'get_item_icon',
    'get_item_color',
    'get_item_rarity',
]
