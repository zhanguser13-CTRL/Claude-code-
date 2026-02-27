"""
Multi-Pet System for Claude Pet Companion
"""

from .farm import PetFarm, FarmPet, PetState, PetType, PresetFarmPets
from .breeding import BreedingSystem, BreedingResult, Offspring, PetGenetics
from .trading import TradingSystem, TradeOffer, TradeStatus

__all__ = [
    'PetFarm',
    'FarmPet',
    'PetState',
    'PetType',
    'PresetFarmPets',
    'BreedingSystem',
    'BreedingResult',
    'Offspring',
    'PetGenetics',
    'TradingSystem',
    'TradeOffer',
    'TradeStatus',
]
