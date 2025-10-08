"""
AutoGun - PG3D Ammo Tracker
Точка входа в приложение
"""

import sys
import time
import argparse

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

from src.utils.logger import setup_logger
from src.utils.config_manager import ConfigManager
from src.core.memory_reader import MemoryReader
from src.core.weapon_category_detector import WeaponCategoryDetector
from src.core.macro_engine import MacroEngine
from src.core.trigger_bot import TriggerBot
from src.core.auto_jump import AutoJump
from src.gui.main_window import MainWindow


class AmmoTracker:
    """Главный класс приложения"""
    
    def __init__(self, config_path: str = "config/default_config.yaml"):
        """
        Инициализация трекера патронов
        
        Args:
            config_path: Путь к файлу конфигурации
        """
        # Загрузка конфигурации
        self.config = ConfigManager(config_path)
        
        # Настройка логгера
        log_level = self.config.get('logging.level', 'INFO')
        log_to_file = self.config.get('logging.save_to_file', True)
        log_file = self.config.get('logging.log_file', 'logs/ammo_tracker.log')
        self.logger = setup_logger(log_level, log_to_file, log_file)
        
        self.logger.info("=" * 50)
        self.logger.info("Запуск AutoGun - PG3D Ammo Tracker")
        self.logger.info("=" * 50)
        
        # Инициализация компонентов
        process_name = self.config.get('memory_reading.process_name', 'PixelGun3D.exe')
        self.memory_reader = MemoryReader(process_name)
        self.weapon_detector = WeaponCategoryDetector()
        self.macro_engine = MacroEngine(self.config)
        self.trigger_bot = TriggerBot(self.memory_reader)
        self.auto_jump = AutoJump(self.config)
        
        # Загрузка оффсетов из конфига
        offsets = self.config.get('memory_reading.offsets', {})
        if any(offsets.values()):
            self.memory_reader.set_offsets(offsets)
            self.logger.info("Оффсеты загружены из конфига")
        else:
            self.logger.warning("⚠️ Оффсеты не установлены! См. MEMORY_OFFSETS_GUIDE.md")
        
        # Переменные состояния
        self.is_tracking = False
        self.all_ammo = {}  # Патроны всех 6 слотов
        self.fps_counter = 0
        self.fps_last_time = time.time()
        self.current_fps = 0.0
        
        # Для режима отладки
        self.debug_last_time = time.time()
        self.debug_interval = 10  # Вывод каждые 10 секунд
        
        # GUI
        self.main_window = None
        self.update_timer = None
    
    def setup_gui(self, app):
        """
        Настройка GUI
        
        Args:
            app: QApplication instance
        """
        self.main_window = MainWindow(self.config)
        
        # Подключение сигналов
        self.main_window.tracking_started.connect(self.start_tracking)
        self.main_window.tracking_stopped.connect(self.stop_tracking)
        self.main_window.reconnect_requested.connect(self.reconnect_to_game)
        self.main_window.macros_toggled.connect(self.on_macros_toggled)
        self.main_window.preset_changed.connect(self.on_preset_changed)
        self.main_window.trigger_toggled.connect(self.on_trigger_toggled)
        self.main_window.auto_jump_toggled.connect(self.on_auto_jump_toggled)
        self.main_window.auto_jump_settings_changed.connect(self.on_auto_jump_settings_changed)
        
        # Таймер обновления
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_tracking)
        
        # Показываем окно
        self.main_window.show()
        
        # Автоматическое подключение к игре
        self.reconnect_to_game()
        
        # Загрузка пресетов макросов
        self.macro_engine.load_presets()
        self.main_window.reload_presets()
        
        # Загрузка сохранённых настроек
        self.main_window.load_saved_settings()
        
        self.logger.info("GUI инициализирован")
    
    def reconnect_to_game(self):
        """Переподключение к процессу игры"""
        self.logger.info("Попытка подключения к игре...")
        self.main_window.update_connection_status("Подключение...", "orange")
        
        if self.memory_reader.connect():
            status = self.memory_reader.get_status()
            self.main_window.update_connection_status(status.replace("✅", "").replace("⚠️", "").strip(), "green")
            self.main_window.add_log("✅ Подключено к игре!")
            
            if not any(self.config.get('memory_reading.offsets', {}).values()):
                self.main_window.add_log("⚠️ Оффсеты не установлены! См. MEMORY_OFFSETS_GUIDE.md")
        else:
            self.main_window.update_connection_status("Не подключено", "red")
            self.main_window.add_log("❌ Не удалось подключиться к игре")
            self.main_window.add_log("Убедитесь что Pixel Gun 3D запущен")
    
    def start_tracking(self):
        """Запуск отслеживания"""
        if not self.memory_reader.is_connected():
            self.logger.warning("Не подключено к игре!")
            self.main_window.add_log("⚠️ Сначала подключитесь к игре!")
            return
        
        self.is_tracking = True
        
        # Получаем частоту обновления из GUI
        update_rate = self.main_window.get_update_rate()
        interval = int(1000 / update_rate)  # Конвертируем в миллисекунды
        
        self.update_timer.start(interval)
        self.logger.info(f"Отслеживание запущено (обновление: {update_rate} Hz)")
    
    def stop_tracking(self):
        """Остановка отслеживания"""
        self.is_tracking = False
        self.update_timer.stop()
        self.logger.info("Отслеживание остановлено")
    
    
    def update_tracking(self):
        """Обновление отслеживания (вызывается таймером)"""
        if not self.is_tracking:
            return
        
        try:
            # Проверяем подключение
            if not self.memory_reader.is_connected():
                self.logger.warning("Потеряно подключение к игре")
                if self.config.get('memory_reading.auto_reconnect', True):
                    self.reconnect_to_game()
                return
            
            # Читаем патроны всех 6 слотов
            self.all_ammo = self.memory_reader.read_all_ammo()
            
            # Обновляем GUI для ВСЕХ оружий сразу
            self.main_window.update_all_weapons(self.all_ammo)
            
            # Обновляем движок макросов
            self.macro_engine.update(self.all_ammo)
            
            # Обновляем триггер-бот
            self.trigger_bot.update()
            
            # Обновляем Auto Jump
            self.auto_jump.update()
            
            # Обновление FPS
            self.fps_counter += 1
            current_time = time.time()
            if current_time - self.fps_last_time >= 1.0:
                self.current_fps = self.fps_counter / (current_time - self.fps_last_time)
                self.main_window.update_fps(self.current_fps)
                self.fps_counter = 0
                self.fps_last_time = current_time
            
            # Режим отладки - вывод всех патронов каждые 10 секунд
            if self.main_window.is_debug_mode():
                if current_time - self.debug_last_time >= self.debug_interval:
                    self._debug_print_all_ammo()
                    self.debug_last_time = current_time
        
        except Exception as e:
            self.logger.error(f"Ошибка в update_tracking: {e}", exc_info=True)
    
    def _debug_print_all_ammo(self):
        """Вывод патронов всех категорий в режиме отладки"""
        debug_msg = "=== ОТЛАДКА: Патроны всех оружий ==="
        self.main_window.add_log(debug_msg)
        
        category_names = {
            1: "Основное",
            2: "Пистолет",
            3: "Холодное",
            4: "Специальное",
            5: "Снайперка",
            6: "Тяжёлое"
        }
        
        for cat_id in range(1, 7):
            if cat_id in self.all_ammo:
                clip, reserve = self.all_ammo[cat_id]
                total = clip + reserve
                msg = f"  [{cat_id}] {category_names[cat_id]}: {clip}/{reserve} (всего: {total}) ✓"
            elif cat_id == 3:
                msg = f"  [{cat_id}] {category_names[cat_id]}: -- (холодное)"
            else:
                msg = f"  [{cat_id}] {category_names[cat_id]}: -- (нет данных)"
            
            self.main_window.add_log(msg)
        
        self.main_window.add_log("=" * 40)
    
    def on_macros_toggled(self, enabled: bool):
        """Обработчик вкл/выкл макросов"""
        if enabled:
            if self.macro_engine.enable():
                self.logger.info(f"Макросы включены: {self.macro_engine.get_status()}")
            else:
                self.main_window.add_log("❌ Не удалось включить макросы")
                self.main_window.macros_enabled_checkbox.setChecked(False)
        else:
            self.macro_engine.disable()
            self.logger.info("Макросы выключены")
    
    def on_preset_changed(self, preset_name: str):
        """Обработчик смены пресета"""
        self.macro_engine.set_active_preset(preset_name)
        self.logger.info(f"Выбран пресет: {preset_name}")
    
    def on_trigger_toggled(self, enabled: bool):
        """Обработчик вкл/выкл триггер-бота"""
        if enabled:
            # Применяем настройки задержки из GUI
            delay = self.main_window.trigger_delay_spinbox.value()
            min_delay = max(10, delay - 50)
            max_delay = delay + 50
            self.trigger_bot.set_reaction_delay(min_delay, max_delay)
            
            if self.trigger_bot.enable():
                self.logger.info(f"Триггер-бот включен: {self.trigger_bot.get_status()}")
                self.main_window.add_log("🎯 Триггер-бот активирован (зажатие)")
            else:
                self.main_window.add_log("❌ Не удалось найти окно игры")
                self.main_window.trigger_enabled_checkbox.setChecked(False)
        else:
            self.trigger_bot.disable()
            self.logger.info("Триггер-бот выключен")
    
    def on_auto_jump_toggled(self, enabled: bool):
        """Обработчик вкл/выкл Auto Jump"""
        if enabled:
            if self.auto_jump.enable():
                self.logger.info(f"Auto Jump включен: {self.auto_jump.get_status()}")
                self.main_window.add_log("🦘 Auto Jump активирован")
            else:
                self.main_window.add_log("❌ Не удалось найти окно игры")
                self.main_window.auto_jump_enabled_checkbox.setChecked(False)
        else:
            self.auto_jump.disable()
            self.logger.info("Auto Jump выключен")
    
    def on_auto_jump_settings_changed(self, repeat_count: int, delay_ms: int):
        """Обработчик изменения настроек Auto Jump"""
        self.auto_jump.set_repeat_count(repeat_count)
        self.auto_jump.set_delay(delay_ms)
        self.logger.info(f"Auto Jump настройки обновлены: x{repeat_count}, {delay_ms}мс")
    
    def run(self):
        """Запуск приложения"""
        app = QApplication(sys.argv)
        app.setApplicationName("AutoGun")
        
        self.setup_gui(app)
        
        self.logger.info("Приложение запущено")
        sys.exit(app.exec())


def main():
    """Точка входа"""
    parser = argparse.ArgumentParser(description="AutoGun - PG3D Ammo Tracker")
    parser.add_argument('--debug', action='store_true', help='Режим отладки')
    parser.add_argument('--config', type=str, default='config/default_config.yaml',
                       help='Путь к файлу конфигурации')
    
    args = parser.parse_args()
    
    # Создаём и запускаем трекер
    tracker = AmmoTracker(config_path=args.config)
    tracker.run()


if __name__ == "__main__":
    main()
