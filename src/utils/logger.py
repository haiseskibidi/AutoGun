"""
Модуль логирования
Настройка и инициализация логгера
"""

import sys
from pathlib import Path
from loguru import logger


def setup_logger(log_level: str = "INFO", log_to_file: bool = True, log_file: str = "logs/ammo_tracker.log"):
    """
    Настройка логгера
    
    Args:
        log_level: Уровень логирования (DEBUG, INFO, WARNING, ERROR)
        log_to_file: Сохранять ли логи в файл
        log_file: Путь к файлу логов
    """
    # Удаляем стандартный обработчик
    logger.remove()
    
    # Добавляем консольный вывод с цветами
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
        level=log_level,
        colorize=True
    )
    
    # Добавляем запись в файл
    if log_to_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.add(
            log_file,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function} - {message}",
            level=log_level,
            rotation="10 MB",  # Ротация при достижении 10MB
            retention="7 days",  # Хранить логи 7 дней
            compression="zip"  # Сжимать старые логи
        )
    
    logger.info(f"Логгер инициализирован с уровнем {log_level}")
    
    return logger


def get_logger():
    """Получить экземпляр логгера"""
    return logger

