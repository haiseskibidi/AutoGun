"""
Менеджер конфигурации
Загрузка и сохранение настроек программы
"""

import yaml
from pathlib import Path
from typing import Any, Dict
from loguru import logger


class ConfigManager:
    """Управление конфигурационными файлами"""
    
    def __init__(self, default_config_path: str = "config/default_config.yaml",
                 user_config_path: str = "config/user_settings.yaml"):
        """
        Инициализация менеджера конфигурации
        
        Args:
            default_config_path: Путь к конфигу по умолчанию
            user_config_path: Путь к пользовательскому конфигу
        """
        self.default_config_path = Path(default_config_path)
        self.user_config_path = Path(user_config_path)
        self.config: Dict[str, Any] = {}
        
        self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """
        Загрузка конфигурации
        Сначала загружается дефолтный конфиг, затем перезаписывается пользовательским
        
        Returns:
            Словарь с конфигурацией
        """
        # Загружаем дефолтный конфиг
        if self.default_config_path.exists():
            with open(self.default_config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
                logger.info(f"Загружен дефолтный конфиг из {self.default_config_path}")
        else:
            logger.warning(f"Дефолтный конфиг не найден: {self.default_config_path}")
            self.config = {}
        
        # Загружаем пользовательский конфиг (если есть)
        if self.user_config_path.exists():
            with open(self.user_config_path, 'r', encoding='utf-8') as f:
                user_config = yaml.safe_load(f)
                self._merge_configs(self.config, user_config)
                logger.info(f"Загружен пользовательский конфиг из {self.user_config_path}")
        else:
            logger.info("Пользовательский конфиг не найден, используются настройки по умолчанию")
        
        return self.config
    
    def save_user_config(self, config: Dict[str, Any] = None):
        """
        Сохранение пользовательских настроек
        
        Args:
            config: Конфиг для сохранения (если None, сохраняется текущий)
        """
        if config is not None:
            self.config = config
        
        # Создаём директорию если нужно
        self.user_config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(self.user_config_path, 'w', encoding='utf-8') as f:
            yaml.dump(self.config, f, default_flow_style=False, allow_unicode=True)
        
        logger.info(f"Пользовательский конфиг сохранён в {self.user_config_path}")
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Получение значения из конфига по пути
        
        Args:
            key_path: Путь к значению через точку (например, 'screen_capture.update_rate')
            default: Значение по умолчанию
            
        Returns:
            Значение из конфига или default
        """
        keys = key_path.split('.')
        value = self.config
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            logger.warning(f"Ключ '{key_path}' не найден в конфиге, используется значение по умолчанию: {default}")
            return default
    
    def set(self, key_path: str, value: Any):
        """
        Установка значения в конфиге по пути
        
        Args:
            key_path: Путь к значению через точку
            value: Новое значение
        """
        keys = key_path.split('.')
        config = self.config
        
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        
        config[keys[-1]] = value
        logger.debug(f"Установлено значение '{key_path}' = {value}")
    
    def _merge_configs(self, base: Dict, update: Dict):
        """
        Рекурсивное слияние конфигов
        
        Args:
            base: Базовый конфиг (изменяется)
            update: Конфиг с обновлениями
        """
        for key, value in update.items():
            if isinstance(value, dict) and key in base and isinstance(base[key], dict):
                self._merge_configs(base[key], value)
            else:
                base[key] = value
    
    def reload(self):
        """Перезагрузка конфигурации из файлов"""
        self.load_config()
        logger.info("Конфигурация перезагружена")

