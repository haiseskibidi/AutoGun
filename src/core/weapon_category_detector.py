"""
Модуль определения категории оружия
Упрощённая система - определяет только класс оружия (1-6), а не конкретную модель
"""

import cv2
import numpy as np
from typing import Optional, Dict
from loguru import logger


class WeaponCategoryDetector:
    """
    Класс для определения категории активного оружия
    
    Категории оружия в Pixel Gun 3D:
    1 - Основное
    2 - Пистолет
    3 - Ближнего боя
    4 - Специальное
    5 - Снайперка
    6 - Тяжёлое
    """
    
    # Информация о категориях
    CATEGORIES = {
        1: {"name": "Основное", "name_en": "primary", "color": "#4CAF50", "has_ammo": True},
        2: {"name": "Пистолет", "name_en": "pistol", "color": "#2196F3", "has_ammo": True},
        3: {"name": "Ближнего боя", "name_en": "melee", "color": "#FF9800", "has_ammo": False},
        4: {"name": "Специальное", "name_en": "special", "color": "#9C27B0", "has_ammo": True},
        5: {"name": "Снайперка", "name_en": "sniper", "color": "#00BCD4", "has_ammo": True},
        6: {"name": "Тяжёлое", "name_en": "heavy", "color": "#F44336", "has_ammo": True}
    }
    
    def __init__(self):
        """Инициализация детектора категорий"""
        self.current_category = None
        self.category_templates = {}
        logger.info("WeaponCategoryDetector инициализирован")
    
    def get_category_info(self, category_id: int) -> Optional[Dict]:
        """
        Получение информации о категории
        
        Args:
            category_id: ID категории (1-6)
            
        Returns:
            Словарь с информацией о категории
        """
        return self.CATEGORIES.get(category_id)
    
    def get_category_name(self, category_id: int) -> str:
        """
        Получение названия категории
        
        Args:
            category_id: ID категории (1-6)
            
        Returns:
            Название категории
        """
        category = self.CATEGORIES.get(category_id)
        if category:
            return category['name']
        return "Неизвестно"
    
    def has_ammo(self, category_id: int) -> bool:
        """
        Проверка, есть ли у категории патроны
        
        Args:
            category_id: ID категории (1-6)
            
        Returns:
            True если есть патроны, False если нет (например, для холодного оружия)
        """
        category = self.CATEGORIES.get(category_id)
        if category:
            return category.get('has_ammo', True)
        return True
    
    def detect_category_by_template(self, weapon_slot_image: np.ndarray) -> Optional[int]:
        """
        Определение активной категории по изображению слота оружия
        
        В Pixel Gun 3D обычно есть индикатор активного слота (подсвечивается рамкой или цветом).
        Можно анализировать либо позицию подсветки, либо цветовые маркеры.
        
        Args:
            weapon_slot_image: Изображение области со слотами оружия
            
        Returns:
            ID категории (1-6) или None
        """
        # Этот метод нужно будет настроить под конкретный интерфейс игры
        # Пока возвращаем None - требуется калибровка
        logger.warning("Определение категории по шаблону требует калибровки")
        return None
    
    def detect_category_by_color(self, indicator_image: np.ndarray) -> Optional[int]:
        """
        Определение категории по цветному индикатору
        
        Если в игре есть цветной индикатор текущего оружия
        
        Args:
            indicator_image: Изображение индикатора
            
        Returns:
            ID категории (1-6) или None
        """
        # Конвертируем в HSV для анализа цвета
        if len(indicator_image.shape) == 3:
            hsv = cv2.cvtColor(indicator_image, cv2.COLOR_RGB2HSV)
            
            # Находим доминирующий цвет
            dominant_color = self._get_dominant_color(indicator_image)
            
            # Сопоставляем с категориями (это упрощённый пример)
            # В реальности нужно будет настроить цветовые диапазоны
            logger.debug(f"Доминирующий цвет: {dominant_color}")
        
        return None
    
    def _get_dominant_color(self, image: np.ndarray) -> tuple:
        """
        Определение доминирующего цвета в изображении
        
        Args:
            image: Изображение
            
        Returns:
            RGB tuple доминирующего цвета
        """
        # Изменяем размер для ускорения
        small_image = cv2.resize(image, (50, 50))
        
        # Преобразуем в массив пикселей
        pixels = small_image.reshape(-1, 3)
        pixels = pixels.astype(float)
        
        # Находим средний цвет
        avg_color = pixels.mean(axis=0)
        
        return tuple(map(int, avg_color))
    
    def set_category_manually(self, category_id: int):
        """
        Ручная установка текущей категории
        
        Args:
            category_id: ID категории (1-6)
        """
        if category_id in self.CATEGORIES:
            self.current_category = category_id
            logger.info(f"Категория установлена вручную: {self.get_category_name(category_id)}")
        else:
            logger.warning(f"Некорректная категория: {category_id}")
    
    def get_current_category(self) -> Optional[int]:
        """
        Получение текущей активной категории
        
        Returns:
            ID текущей категории или None
        """
        return self.current_category
    
    def detect_category_by_position(self, slot_positions: list, highlighted_position: tuple) -> Optional[int]:
        """
        Определение категории по позиции подсвеченного слота
        
        Если известны позиции всех 6 слотов оружия и позиция активного,
        можно определить категорию
        
        Args:
            slot_positions: Список позиций слотов [(x1,y1), (x2,y2), ...]
            highlighted_position: Позиция активного слота (x, y)
            
        Returns:
            ID категории (1-6) или None
        """
        if len(slot_positions) != 6:
            logger.warning("Должно быть ровно 6 позиций слотов")
            return None
        
        # Находим ближайший слот к подсвеченной позиции
        min_distance = float('inf')
        closest_index = None
        
        for i, (sx, sy) in enumerate(slot_positions):
            hx, hy = highlighted_position
            distance = ((sx - hx) ** 2 + (sy - hy) ** 2) ** 0.5
            
            if distance < min_distance:
                min_distance = distance
                closest_index = i
        
        if closest_index is not None:
            category_id = closest_index + 1  # Индексы 0-5, категории 1-6
            logger.debug(f"Определена категория {category_id} по позиции")
            return category_id
        
        return None
    
    def list_categories(self) -> list:
        """
        Получение списка всех категорий
        
        Returns:
            Список словарей с информацией о категориях
        """
        return [
            {
                'id': cat_id,
                'name': cat_info['name'],
                'name_en': cat_info['name_en'],
                'color': cat_info['color'],
                'has_ammo': cat_info['has_ammo']
            }
            for cat_id, cat_info in sorted(self.CATEGORIES.items())
        ]

