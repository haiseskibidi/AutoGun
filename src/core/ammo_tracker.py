"""
Модуль отслеживания патронов для всех 6 слотов оружия
"""

from typing import Dict, Optional, Tuple
import numpy as np
from loguru import logger


class AmmoTracker:
    """
    Класс для отслеживания патронов всех 6 категорий оружия одновременно
    """
    
    def __init__(self):
        """Инициализация трекера патронов"""
        # Состояние патронов для каждого слота
        self.ammo_state = {
            1: {"current": 0, "max": 0, "last_update": 0},
            2: {"current": 0, "max": 0, "last_update": 0},
            3: {"current": 0, "max": 0, "last_update": 0},  # Холодное - всегда 0
            4: {"current": 0, "max": 0, "last_update": 0},
            5: {"current": 0, "max": 0, "last_update": 0},
            6: {"current": 0, "max": 0, "last_update": 0},
        }
        
        # История изменений
        self.history = []
        
        logger.info("AmmoTracker инициализирован")
    
    def update_slot(self, slot_id: int, current: int, maximum: int):
        """
        Обновление информации о патронах для слота
        
        Args:
            slot_id: ID слота (1-6)
            current: Текущее количество патронов
            maximum: Максимальное количество патронов
        """
        if slot_id not in self.ammo_state:
            logger.warning(f"Некорректный slot_id: {slot_id}")
            return
        
        import time
        
        # Обновляем состояние
        old_current = self.ammo_state[slot_id]["current"]
        self.ammo_state[slot_id]["current"] = current
        self.ammo_state[slot_id]["max"] = maximum
        self.ammo_state[slot_id]["last_update"] = time.time()
        
        # Логируем изменения
        if old_current != current:
            logger.debug(f"Слот {slot_id}: {current}/{maximum}")
            self.history.append({
                "slot": slot_id,
                "current": current,
                "max": maximum,
                "timestamp": time.time()
            })
    
    def get_slot_ammo(self, slot_id: int) -> Tuple[int, int]:
        """
        Получение информации о патронах для слота
        
        Args:
            slot_id: ID слота (1-6)
            
        Returns:
            Tuple(current, max)
        """
        if slot_id not in self.ammo_state:
            return (0, 0)
        
        state = self.ammo_state[slot_id]
        return (state["current"], state["max"])
    
    def get_all_ammo(self) -> Dict[int, Tuple[int, int]]:
        """
        Получение информации о патронах для всех слотов
        
        Returns:
            Dict {slot_id: (current, max)}
        """
        return {
            slot_id: (state["current"], state["max"])
            for slot_id, state in self.ammo_state.items()
        }
    
    def has_ammo(self, slot_id: int, min_amount: int = 1) -> bool:
        """
        Проверка наличия патронов в слоте
        
        Args:
            slot_id: ID слота
            min_amount: Минимальное количество патронов
            
        Returns:
            True если патронов >= min_amount
        """
        current, _ = self.get_slot_ammo(slot_id)
        return current >= min_amount
    
    def get_ammo_percent(self, slot_id: int) -> float:
        """
        Получение процента заполненности патронов
        
        Args:
            slot_id: ID слота
            
        Returns:
            Процент (0-100)
        """
        current, maximum = self.get_slot_ammo(slot_id)
        if maximum == 0:
            return 0.0
        return (current / maximum) * 100.0
    
    def get_best_weapon(self, slot_ids: list) -> Optional[int]:
        """
        Получение лучшего оружия из списка (с наибольшим % патронов)
        
        Args:
            slot_ids: Список ID слотов для проверки
            
        Returns:
            ID слота с наибольшим количеством патронов или None
        """
        best_slot = None
        best_percent = -1
        
        for slot_id in slot_ids:
            if slot_id == 3:  # Пропускаем холодное
                continue
            
            percent = self.get_ammo_percent(slot_id)
            if percent > best_percent:
                best_percent = percent
                best_slot = slot_id
        
        return best_slot
    
    def reset(self):
        """Сброс всех данных"""
        for slot_id in self.ammo_state:
            self.ammo_state[slot_id] = {"current": 0, "max": 0, "last_update": 0}
        self.history.clear()
        logger.info("AmmoTracker сброшен")
    
    def get_summary(self) -> str:
        """
        Получение текстовой сводки по патронам
        
        Returns:
            Строка с информацией
        """
        lines = ["Патроны:"]
        for slot_id in sorted(self.ammo_state.keys()):
            current, maximum = self.get_slot_ammo(slot_id)
            if slot_id == 3:
                lines.append(f"  {slot_id}: Холодное оружие")
            else:
                percent = self.get_ammo_percent(slot_id)
                lines.append(f"  {slot_id}: {current}/{maximum} ({percent:.0f}%)")
        return "\n".join(lines)

