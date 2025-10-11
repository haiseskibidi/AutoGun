"""
Триггер-бот - автоматическая стрельба при наведении на врага
"""

import time
import random
from loguru import logger

try:
    import win32api
    import win32con
    import win32gui
    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False
    logger.warning("pywin32 не установлен. Установите: pip install pywin32")


class TriggerBot:
    """Триггер-бот для автоматической стрельбы"""
    
    def __init__(self, memory_reader):
        """
        Инициализация триггер-бота
        
        Args:
            memory_reader: Экземпляр MemoryReader
        """
        if not WIN32_AVAILABLE:
            raise ImportError("pywin32 не установлен!")
        
        self.memory_reader = memory_reader
        self.enabled = False
        self.game_hwnd = None  # HWND окна игры
        
        # Настройки
        self.reaction_delay_min = 0.05  # Минимальная задержка реакции (сек)
        self.reaction_delay_max = 0.15  # Максимальная задержка реакции (сек)
        self.shot_duration = 0.05       # Длительность нажатия ЛКМ (сек)
        
        # Состояние
        self.last_state = False  # Был ли враг в прошлом кадре
        self.is_holding = False  # Зажата ли кнопка мыши
        self.first_check = True  # Флаг первой проверки (для debug лога)
        
        logger.info("TriggerBot инициализирован")
    
    def enable(self):
        """Включить триггер-бот"""
        # Ищем окно игры
        self.game_hwnd = win32gui.FindWindow(None, "Pixel Gun 3D")
        
        if not self.game_hwnd:
            # Пробуем альтернативные названия
            self.game_hwnd = win32gui.FindWindow(None, "Pixel Gun 3D - Unity")
        
        if not self.game_hwnd:
            logger.error("❌ Окно игры не найдено!")
            return False
        
        self.enabled = True
        logger.info(f"✅ Триггер-бот ВКЛЮЧЕН (HWND: {self.game_hwnd})")
        return True
    
    def disable(self):
        """Выключить триггер-бот"""
        # Отпускаем кнопку если была зажата
        if self.is_holding:
            self._release_mouse()
        
        self.enabled = False
        logger.info("⏸ Триггер-бот ВЫКЛЮЧЕН")
    
    def set_reaction_delay(self, min_ms: int, max_ms: int):
        """
        Установить задержку реакции
        
        Args:
            min_ms: Минимальная задержка (миллисекунды)
            max_ms: Максимальная задержка (миллисекунды)
        """
        self.reaction_delay_min = min_ms / 1000.0
        self.reaction_delay_max = max_ms / 1000.0
        logger.info(f"Задержка реакции: {min_ms}-{max_ms} мс")
    
    def update(self):
        """Обновление триггер-бота (вызывать в основном цикле)"""
        if not self.enabled:
            return
        
        try:
            # При первой проверке - выводим детальный лог
            debug_mode = self.first_check
            if self.first_check:
                logger.info("[TRIGGER] 🔍 Первая проверка - включаем детальное логирование")
                self.first_check = False
            
            # Проверяем наведён ли прицел на врага
            is_on_enemy = self.memory_reader.read_crosshair_on_enemy(debug_mode=debug_mode)
            
            # Логируем изменения состояния
            if is_on_enemy != self.last_state:
                if is_on_enemy:
                    logger.info(f"[TRIGGER] 🎯 Цель обнаружена - ЗАЖИМАЕМ")
                else:
                    logger.info(f"[TRIGGER] Цель потеряна - отпускаем")
            
            # Зажимаем кнопку если прицел на враге
            if is_on_enemy and not self.is_holding:
                self._press_mouse()
            # Отпускаем если ушли с врага
            elif not is_on_enemy and self.is_holding:
                self._release_mouse()
            
            self.last_state = is_on_enemy
            
        except Exception as e:
            logger.error(f"[TRIGGER] Ошибка: {e}")
    
    def _press_mouse(self):
        """Зажать левую кнопку мыши"""
        try:
            if not self.game_hwnd or not win32gui.IsWindow(self.game_hwnd):
                self.game_hwnd = win32gui.FindWindow(None, "Pixel Gun 3D")
                if not self.game_hwnd:
                    return
            
            # Небольшая задержка реакции
            reaction_delay = random.uniform(self.reaction_delay_min, self.reaction_delay_max)
            time.sleep(reaction_delay)
            
            # Получаем центр окна
            rect = win32gui.GetClientRect(self.game_hwnd)
            center_x = rect[2] // 2
            center_y = rect[3] // 2
            lParam = win32api.MAKELONG(center_x, center_y)
            
            # Зажимаем ЛКМ
            win32api.PostMessage(
                self.game_hwnd,
                win32con.WM_LBUTTONDOWN,
                win32con.MK_LBUTTON,
                lParam
            )
            
            self.is_holding = True
            logger.debug(f"[TRIGGER] Зажали ЛКМ (задержка: {reaction_delay*1000:.0f}мс)")
            
        except Exception as e:
            logger.error(f"[TRIGGER] Ошибка зажатия: {e}")
    
    def _release_mouse(self):
        """Отпустить левую кнопку мыши"""
        try:
            if not self.game_hwnd or not win32gui.IsWindow(self.game_hwnd):
                return
            
            # Получаем центр окна
            rect = win32gui.GetClientRect(self.game_hwnd)
            center_x = rect[2] // 2
            center_y = rect[3] // 2
            lParam = win32api.MAKELONG(center_x, center_y)
            
            # Отпускаем ЛКМ
            win32api.PostMessage(
                self.game_hwnd,
                win32con.WM_LBUTTONUP,
                0,
                lParam
            )
            
            self.is_holding = False
            logger.debug(f"[TRIGGER] Отпустили ЛКМ")
            
        except Exception as e:
            logger.error(f"[TRIGGER] Ошибка отпускания: {e}")
    
    def get_status(self) -> str:
        """Получить статус триггер-бота"""
        if not self.enabled:
            return "Выключен"
        
        return f"Активен (задержка: {self.reaction_delay_min*1000:.0f}-{self.reaction_delay_max*1000:.0f} мс)"
