"""
Модуль захвата экрана
Захват определённых областей экрана для анализа
"""

import mss
import numpy as np
from PIL import Image
from typing import Tuple, Optional, Dict
from loguru import logger


class ScreenCapture:
    """Класс для захвата экрана и определённых областей"""
    
    def __init__(self):
        """Инициализация захвата экрана"""
        self.sct = mss.mss()
        self.screen_size = self._get_screen_size()
        logger.info(f"ScreenCapture инициализирован. Разрешение экрана: {self.screen_size}")
    
    def _get_screen_size(self) -> Tuple[int, int]:
        """
        Получение размера экрана
        
        Returns:
            Tuple[width, height]
        """
        monitor = self.sct.monitors[1]  # Основной монитор
        return (monitor['width'], monitor['height'])
    
    def capture_region(self, x: int, y: int, width: int, height: int) -> np.ndarray:
        """
        Захват прямоугольной области экрана
        
        Args:
            x: X координата левого верхнего угла
            y: Y координата левого верхнего угла
            width: Ширина области
            height: Высота области
            
        Returns:
            Numpy array с изображением в формате RGB
        """
        try:
            monitor = {
                "top": y,
                "left": x,
                "width": width,
                "height": height
            }
            
            screenshot = self.sct.grab(monitor)
            img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
            
            return np.array(img)
        
        except Exception as e:
            logger.error(f"Ошибка при захвате области ({x}, {y}, {width}, {height}): {e}")
            return np.array([])
    
    def capture_region_percent(self, x_percent: float, y_percent: float,
                              width_percent: float, height_percent: float) -> np.ndarray:
        """
        Захват области экрана с использованием процентных координат
        Удобно для поддержки разных разрешений
        
        Args:
            x_percent: X координата в процентах (0-100)
            y_percent: Y координата в процентах (0-100)
            width_percent: Ширина в процентах (0-100)
            height_percent: Высота в процентах (0-100)
            
        Returns:
            Numpy array с изображением
        """
        screen_width, screen_height = self.screen_size
        
        x = int((x_percent / 100) * screen_width)
        y = int((y_percent / 100) * screen_height)
        width = int((width_percent / 100) * screen_width)
        height = int((height_percent / 100) * screen_height)
        
        return self.capture_region(x, y, width, height)
    
    def capture_multiple_regions(self, regions: Dict[str, Dict]) -> Dict[str, np.ndarray]:
        """
        Захват нескольких областей одновременно
        
        Args:
            regions: Словарь с регионами {name: {x, y, width, height}}
            
        Returns:
            Словарь {name: image_array}
        """
        captured = {}
        
        for name, region in regions.items():
            if 'x_percent' in region:
                # Используем процентные координаты
                img = self.capture_region_percent(
                    region['x_percent'],
                    region['y_percent'],
                    region['width_percent'],
                    region['height_percent']
                )
            else:
                # Используем абсолютные координаты
                img = self.capture_region(
                    region['x'],
                    region['y'],
                    region['width'],
                    region['height']
                )
            
            if img.size > 0:
                captured[name] = img
        
        return captured
    
    def get_monitor_info(self, monitor_number: int = 1) -> Dict:
        """
        Получение информации о мониторе
        
        Args:
            monitor_number: Номер монитора (1 = основной)
            
        Returns:
            Словарь с информацией о мониторе
        """
        if monitor_number < len(self.sct.monitors):
            return self.sct.monitors[monitor_number]
        else:
            logger.warning(f"Монитор {monitor_number} не найден")
            return {}
    
    def save_screenshot(self, filepath: str, x: int = None, y: int = None,
                       width: int = None, height: int = None):
        """
        Сохранение скриншота в файл
        
        Args:
            filepath: Путь для сохранения
            x, y, width, height: Координаты области (если None - весь экран)
        """
        if x is None:
            # Захватываем весь экран
            monitor = self.sct.monitors[1]
            screenshot = self.sct.grab(monitor)
        else:
            monitor = {"top": y, "left": x, "width": width, "height": height}
            screenshot = self.sct.grab(monitor)
        
        img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
        img.save(filepath)
        logger.info(f"Скриншот сохранён: {filepath}")
    
    def __del__(self):
        """Очистка ресурсов"""
        if hasattr(self, 'sct'):
            self.sct.close()

