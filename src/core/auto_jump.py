"""
Автоматические повторные прыжки
"""

import time
import threading
import keyboard
from loguru import logger

try:
    import win32api
    import win32con
    import win32gui
    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False
    logger.warning("pywin32 не установлен. Установите: pip install pywin32")


class AutoJump:
    """Автоматические повторные прыжки при нажатии пробела"""
    
    def __init__(self, config_manager):
        """
        Инициализация
        
        Args:
            config_manager: Менеджер конфигурации
        """
        if not WIN32_AVAILABLE:
            raise ImportError("pywin32 не установлен!")
        
        self.config = config_manager
        self.enabled = False
        self.game_hwnd = None  # HWND окна игры
        
        # Настройки из конфига
        self.jump_key = self.config.get('auto_jump.jump_key', 'space')
        self.repeat_count = self.config.get('auto_jump.repeat_count', 2)  # Сколько раз прыгать
        self.delay_ms = self.config.get('auto_jump.delay_ms', 100)  # Задержка между прыжками
        
        # Состояние пробела (для отслеживания нажатия/отпускания)
        self.was_pressed = False
        
        # Флаг выполнения автопрыжков
        self.is_jumping = False
        
        logger.info("AutoJump инициализирован")
    
    def enable(self):
        """Включить функцию"""
        # Ищем окно игры
        self.game_hwnd = win32gui.FindWindow(None, "Pixel Gun 3D")
        
        if not self.game_hwnd:
            # Пробуем альтернативные названия
            self.game_hwnd = win32gui.FindWindow(None, "Pixel Gun 3D - Unity")
        
        if not self.game_hwnd:
            logger.error("❌ Окно игры не найдено!")
            return False
        
        # Перезагружаем настройки из конфига
        self.jump_key = self.config.get('auto_jump.jump_key', 'space')
        self.repeat_count = self.config.get('auto_jump.repeat_count', 2)
        self.delay_ms = self.config.get('auto_jump.delay_ms', 100)
        
        self.enabled = True
        self.was_pressed = False
        self.is_jumping = False
        logger.info(f"✅ AutoJump ВКЛЮЧЕН (HWND: {self.game_hwnd}, повторов: {self.repeat_count}, задержка: {self.delay_ms}мс)")
        return True
    
    def disable(self):
        """Выключить функцию"""
        self.enabled = False
        self.was_pressed = False
        self.is_jumping = False
        logger.info("⏸ AutoJump ВЫКЛЮЧЕН")
    
    def update(self):
        """Обновление (вызывается в основном цикле)"""
        if not self.enabled:
            return
        
        try:
            # Проверяем состояние пробела через GetAsyncKeyState
            # VK_SPACE = 0x20
            space_state = win32api.GetAsyncKeyState(0x20)
            is_pressed = (space_state & 0x8000) != 0
            
            # Обрабатываем только момент нажатия (переход из False в True)
            if is_pressed and not self.was_pressed:
                # Проверяем что не выполняются другие прыжки
                if not self.is_jumping:
                    # Проверяем что окно игры активно
                    if self._is_game_window_active():
                        # Запускаем автопрыжки в отдельном потоке
                        self.is_jumping = True
                        jump_thread = threading.Thread(target=self._perform_auto_jumps, daemon=True)
                        jump_thread.start()
            
            # Сохраняем состояние для следующего кадра
            self.was_pressed = is_pressed
            
        except Exception as e:
            logger.error(f"[AUTO_JUMP] Ошибка в update: {e}")
    
    def _is_game_window_active(self):
        """
        Проверить что окно игры активно (в фокусе)
        
        Returns:
            True если окно игры активно
        """
        try:
            if not self.game_hwnd or not win32gui.IsWindow(self.game_hwnd):
                # Пытаемся найти окно заново
                self.game_hwnd = win32gui.FindWindow(None, "Pixel Gun 3D")
                if not self.game_hwnd:
                    return False
            
            # Получаем активное окно
            active_hwnd = win32gui.GetForegroundWindow()
            
            # Проверяем что активное окно = окно игры
            return active_hwnd == self.game_hwnd
            
        except Exception as e:
            logger.error(f"[AUTO_JUMP] Ошибка проверки окна: {e}")
            return False
    
    def _perform_auto_jumps(self):
        """Выполнить серию автоматических прыжков (в отдельном потоке)"""
        try:
            logger.info(f"[AUTO_JUMP] 🦘 Начало автопрыжков (x{self.repeat_count})")
            
            # Небольшая задержка перед первым повторным прыжком
            # (чтобы не конфликтовать с оригинальным нажатием пользователя)
            time.sleep(self.delay_ms / 1000.0)
            
            # Выполняем повторные прыжки
            for i in range(self.repeat_count):
                if not self.enabled:
                    # Если функция выключилась во время выполнения - прерываем
                    break
                
                # Симулируем нажатие пробела
                keyboard.press(self.jump_key)
                time.sleep(0.05)  # Короткое нажатие (50мс)
                keyboard.release(self.jump_key)
                
                logger.debug(f"[AUTO_JUMP] Прыжок {i+1}/{self.repeat_count}")
                
                # Задержка перед следующим прыжком (кроме последнего)
                if i < self.repeat_count - 1:
                    time.sleep(self.delay_ms / 1000.0)
            
            logger.info(f"[AUTO_JUMP] ✅ Автопрыжки завершены")
            
        except Exception as e:
            logger.error(f"[AUTO_JUMP] Ошибка выполнения: {e}")
        
        finally:
            self.is_jumping = False
    
    def set_repeat_count(self, count: int):
        """
        Установить количество повторений
        
        Args:
            count: Количество повторных прыжков (1-10)
        """
        self.repeat_count = max(1, min(10, count))
        logger.info(f"AutoJump: повторов установлено = {self.repeat_count}")
    
    def set_delay(self, delay_ms: int):
        """
        Установить задержку между прыжками
        
        Args:
            delay_ms: Задержка в миллисекундах (10-2000)
        """
        self.delay_ms = max(10, min(2000, delay_ms))
        logger.info(f"AutoJump: задержка установлена = {self.delay_ms}мс")
    
    def get_status(self) -> str:
        """Получить статус"""
        if not self.enabled:
            return "Выключен"
        
        return f"Активен (x{self.repeat_count}, {self.delay_ms}мс)"

