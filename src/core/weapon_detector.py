"""
Модуль определения оружия
Определение текущего оружия по иконке и сопоставление с базой данных
"""

import cv2
import json
import numpy as np
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from loguru import logger


class WeaponDetector:
    """Класс для определения текущего оружия"""
    
    def __init__(self, templates_folder: str = "data/weapon_templates",
                 match_threshold: float = 0.7):
        """
        Инициализация детектора оружия
        
        Args:
            templates_folder: Папка с шаблонами иконок оружия
            match_threshold: Минимальная схожесть для определения (0-1)
        """
        self.templates_folder = Path(templates_folder)
        self.match_threshold = match_threshold
        self.weapon_categories = {}
        self.weapons_db = {}
        self.templates = {}
        
        # Создаём папку если её нет
        self.templates_folder.mkdir(parents=True, exist_ok=True)
        
        # Загружаем базу данных оружия
        self._load_weapons_database()
        
        # Загружаем шаблоны
        self._load_templates()
        
        logger.info(f"WeaponDetector инициализирован. Категорий: {len(self.weapon_categories)}, Шаблонов: {len(self.templates)}")
    
    def _load_weapons_database(self):
        """Загрузка базы данных оружия из JSON"""
        db_path = self.templates_folder / "weapons_db.json"
        
        if db_path.exists():
            with open(db_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.weapon_categories = data.get('weapon_categories', {})
                self.weapons_db = data.get('weapons', {})
            logger.info(f"Загружено категорий: {len(self.weapon_categories)}, оружий: {len(self.weapons_db)}")
        else:
            logger.warning("База данных не найдена, будет создана новая")
            self.weapon_categories = {}
            self.weapons_db = {}
            self._save_weapons_database()
    
    def _save_weapons_database(self):
        """Сохранение базы данных оружия"""
        db_path = self.templates_folder / "weapons_db.json"
        data = {
            'weapon_categories': self.weapon_categories,
            'weapons': self.weapons_db
        }
        with open(db_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.debug("База данных оружия сохранена")
    
    def _load_templates(self):
        """Загрузка шаблонов иконок оружия"""
        for weapon_id, weapon_data in self.weapons_db.items():
            template_file = weapon_data.get('template_file')
            if template_file:
                template_path = self.templates_folder / template_file
                if template_path.exists():
                    template = cv2.imread(str(template_path))
                    if template is not None:
                        self.templates[weapon_id] = template
                        logger.debug(f"Загружен шаблон для {weapon_id}")
    
    def detect_weapon(self, icon_image: np.ndarray) -> Optional[Dict]:
        """
        Определение оружия по иконке
        
        Args:
            icon_image: Изображение иконки оружия
            
        Returns:
            Словарь с информацией об оружии или None
        """
        if len(self.templates) == 0:
            logger.warning("Нет загруженных шаблонов для определения оружия")
            return None
        
        best_match = None
        best_score = 0.0
        
        # Конвертируем в BGR если нужно (для OpenCV)
        if len(icon_image.shape) == 3 and icon_image.shape[2] == 3:
            icon_bgr = cv2.cvtColor(icon_image, cv2.COLOR_RGB2BGR)
        else:
            icon_bgr = icon_image
        
        # Сравниваем со всеми шаблонами
        for weapon_id, template in self.templates.items():
            score = self._compare_images(icon_bgr, template)
            
            if score > best_score:
                best_score = score
                best_match = weapon_id
        
        # Проверяем порог
        if best_score >= self.match_threshold:
            weapon_info = self.weapons_db[best_match].copy()
            weapon_info['id'] = best_match
            weapon_info['match_score'] = best_score
            logger.debug(f"Определено оружие: {weapon_info['name']} (score: {best_score:.2f})")
            return weapon_info
        else:
            logger.debug(f"Оружие не определено (лучший score: {best_score:.2f})")
            return None
    
    def _compare_images(self, img1: np.ndarray, img2: np.ndarray) -> float:
        """
        Сравнение двух изображений методом Template Matching
        
        Args:
            img1: Первое изображение
            img2: Второе изображение (шаблон)
            
        Returns:
            Коэффициент схожести (0-1)
        """
        try:
            # Приводим к одному размеру
            h, w = img2.shape[:2]
            img1_resized = cv2.resize(img1, (w, h))
            
            # Используем несколько методов сравнения
            methods = [
                cv2.TM_CCOEFF_NORMED,
                cv2.TM_CCORR_NORMED,
            ]
            
            scores = []
            for method in methods:
                result = cv2.matchTemplate(img1_resized, img2, method)
                _, max_val, _, _ = cv2.minMaxLoc(result)
                scores.append(max_val)
            
            # Возвращаем среднее значение
            return sum(scores) / len(scores)
        
        except Exception as e:
            logger.error(f"Ошибка при сравнении изображений: {e}")
            return 0.0
    
    def add_weapon(self, weapon_id: str, name: str, category: int,
                   max_ammo: int, magazine_size: int, icon_image: np.ndarray = None):
        """
        Добавление нового оружия в базу данных
        
        Args:
            weapon_id: Уникальный ID оружия
            name: Название оружия
            category: Категория (1-6: основное, пистолет, ближнего боя, специальное, снайперка, тяжёлое)
            max_ammo: Максимум патронов
            magazine_size: Размер магазина
            icon_image: Изображение иконки (опционально)
        """
        template_file = f"{weapon_id}.png"
        
        weapon_data = {
            "name": name,
            "category": category,
            "max_ammo": max_ammo,
            "magazine_size": magazine_size,
            "template_file": template_file
        }
        
        self.weapons_db[weapon_id] = weapon_data
        
        # Сохраняем иконку если предоставлена
        if icon_image is not None:
            template_path = self.templates_folder / template_file
            if len(icon_image.shape) == 3:
                icon_bgr = cv2.cvtColor(icon_image, cv2.COLOR_RGB2BGR)
            else:
                icon_bgr = icon_image
            cv2.imwrite(str(template_path), icon_bgr)
            self.templates[weapon_id] = icon_bgr
        
        self._save_weapons_database()
        logger.info(f"Добавлено новое оружие: {name} (ID: {weapon_id}, категория: {category})")
    
    def get_weapon_info(self, weapon_id: str) -> Optional[Dict]:
        """
        Получение информации об оружии по ID
        
        Args:
            weapon_id: ID оружия
            
        Returns:
            Словарь с информацией или None
        """
        return self.weapons_db.get(weapon_id)
    
    def list_weapons(self) -> List[Dict]:
        """
        Получение списка всех оружий
        
        Returns:
            Список словарей с информацией об оружии
        """
        weapons_list = []
        for weapon_id, weapon_data in self.weapons_db.items():
            weapon_info = weapon_data.copy()
            weapon_info['id'] = weapon_id
            weapons_list.append(weapon_info)
        return weapons_list
    
    def get_category_name(self, category_id: int) -> str:
        """
        Получение названия категории по ID
        
        Args:
            category_id: ID категории (1-6)
            
        Returns:
            Название категории
        """
        category = self.weapon_categories.get(str(category_id))
        if category:
            return category.get('name', 'Неизвестно')
        return 'Неизвестно'
    
    def get_category_info(self, category_id: int) -> Optional[Dict]:
        """
        Получение полной информации о категории
        
        Args:
            category_id: ID категории (1-6)
            
        Returns:
            Словарь с информацией о категории или None
        """
        return self.weapon_categories.get(str(category_id))
    
    def save_icon_for_calibration(self, icon_image: np.ndarray, weapon_id: str):
        """
        Сохранение иконки оружия для калибровки
        
        Args:
            icon_image: Изображение иконки
            weapon_id: ID оружия
        """
        filepath = self.templates_folder / f"{weapon_id}_calibration.png"
        if len(icon_image.shape) == 3:
            icon_bgr = cv2.cvtColor(icon_image, cv2.COLOR_RGB2BGR)
        else:
            icon_bgr = icon_image
        cv2.imwrite(str(filepath), icon_bgr)
        logger.info(f"Иконка сохранена для калибровки: {filepath}")

