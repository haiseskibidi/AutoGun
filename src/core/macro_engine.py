"""
Движок макросов - отслеживание выстрелов и автосвап
"""

import time
from typing import Dict, List, Optional
from loguru import logger
import keyboard


class MacroEngine:
    """Движок макросов для автоматического свапа оружий"""
    
    def __init__(self, config_manager):
        """
        Инициализация движка
        
        Args:
            config_manager: Менеджер конфигурации
        """
        self.config = config_manager
        self.enabled = False
        self.current_preset = None
        self.presets = {}
        
        # Кэш патронов для отслеживания выстрелов
        self.last_ammo = {}
        self.last_weapon_id = 1
        
        # Счётчики повторений для чередования правил
        # Формат: {weapon_id: {'current_rule_idx': 0, 'counter': 0}}
        self.rule_rotation = {}
        
        # Координаты слотов оружия для клика
        self.weapon_keys = {
            1: '1',
            2: '2', 
            3: '3',
            4: '4',
            5: '5',
            6: '6'
        }
        
        logger.info("MacroEngine инициализирован")
    
    def load_presets(self):
        """Загрузить пресеты из конфига"""
        self.presets = self.config.get('macros.presets', {})
        logger.info(f"Загружено {len(self.presets)} пресетов")
    
    def set_active_preset(self, preset_name: str):
        """
        Установить активный пресет
        
        Args:
            preset_name: Название пресета
        """
        if preset_name in self.presets:
            self.current_preset = preset_name
            # Сбросить счётчики при смене пресета
            self.rule_rotation = {}
            logger.info(f"Активный пресет: {preset_name}")
        else:
            logger.warning(f"Пресет '{preset_name}' не найден")
    
    def enable(self):
        """Включить макросы"""
        if not self.current_preset:
            logger.warning("Не выбран активный пресет!")
            return False
        
        if not self.presets.get(self.current_preset, {}).get('rules'):
            logger.warning("В пресете нет правил!")
            return False
        
        self.enabled = True
        logger.info("Макросы включены")
        return True
    
    def disable(self):
        """Выключить макросы"""
        self.enabled = False
        logger.info("Макросы выключены")
    
    def update(self, ammo_data: Dict[int, tuple], current_weapon: Optional[int] = None):
        """
        Обновление состояния - проверка выстрелов и свап
        
        Args:
            ammo_data: Данные о патронах {weapon_id: (clip, reserve)}
            current_weapon: ID текущего оружия (опционально)
        """
        if not self.enabled or not self.current_preset:
            return
        
        # Определяем текущее оружие
        if current_weapon is None:
            # Если не передано, пытаемся определить по изменению патронов
            current_weapon = self._detect_current_weapon(ammo_data)
        
        if current_weapon is None:
            return
        
        # Проверяем был ли выстрел
        if self._was_shot_fired(current_weapon, ammo_data):
            logger.debug(f"Выстрел из оружия {current_weapon}")
            self._handle_shot(current_weapon)
        
        # Обновляем кэш
        self.last_ammo = ammo_data.copy()
        self.last_weapon_id = current_weapon
    
    def _detect_current_weapon(self, ammo_data: Dict[int, tuple]) -> Optional[int]:
        """
        Определить текущее оружие по изменению патронов
        
        Args:
            ammo_data: Данные о патронах
            
        Returns:
            ID оружия или None
        """
        # Проверяем у какого оружия изменилась обойма
        for weapon_id, (clip, reserve) in ammo_data.items():
            if weapon_id in self.last_ammo:
                old_clip, old_reserve = self.last_ammo[weapon_id]
                if clip < old_clip:  # Уменьшилась обойма = стреляли
                    return weapon_id
        
        return self.last_weapon_id
    
    def _was_shot_fired(self, weapon_id: int, ammo_data: Dict[int, tuple]) -> bool:
        """
        Проверить был ли выстрел
        
        Args:
            weapon_id: ID оружия
            ammo_data: Данные о патронах
            
        Returns:
            True если был выстрел
        """
        if weapon_id not in ammo_data or weapon_id not in self.last_ammo:
            return False
        
        current_clip, _ = ammo_data[weapon_id]
        old_clip, _ = self.last_ammo[weapon_id]
        
        # Выстрел = уменьшилась обойма
        return current_clip < old_clip
    
    def _handle_shot(self, from_weapon: int):
        """
        Обработать выстрел - выполнить свап если есть правило
        
        Args:
            from_weapon: ID оружия из которого стреляли
        """
        if not self.current_preset or self.current_preset not in self.presets:
            return
        
        # Получаем правила текущего пресета
        rules = self.presets[self.current_preset].get('rules', [])
        
        # Фильтруем правила для текущего оружия
        matching_rules = [rule for rule in rules if rule['from'] == from_weapon]
        
        if not matching_rules:
            return
        
        # Инициализация счётчика для оружия если нужно
        if from_weapon not in self.rule_rotation:
            self.rule_rotation[from_weapon] = {
                'current_rule_idx': 0,
                'counter': 0
            }
        
        rotation = self.rule_rotation[from_weapon]
        
        # Получаем текущее правило для чередования
        current_rule = matching_rules[rotation['current_rule_idx']]
        to_weapon = current_rule['to']
        check_ammo = current_rule.get('check_ammo', True)
        repeat_count = current_rule.get('repeat_count', 1)
        
        # Проверяем патроны если нужно
        if check_ammo and not self._has_ammo(to_weapon):
            logger.debug(f"Свап отменён: у оружия {to_weapon} нет патронов")
            # Пропускаем это правило и переходим к следующему
            rotation['counter'] = 0
            rotation['current_rule_idx'] = (rotation['current_rule_idx'] + 1) % len(matching_rules)
            return
        
        # Выполняем свап
        logger.info(f"Свап: {from_weapon} → {to_weapon} (правило {rotation['current_rule_idx'] + 1}/{len(matching_rules)}, выстрел {rotation['counter'] + 1}/{repeat_count})")
        self._switch_weapon(to_weapon)
        
        # Увеличиваем счётчик
        rotation['counter'] += 1
        
        # Если достигли лимита повторений, переключаемся на следующее правило
        if rotation['counter'] >= repeat_count:
            rotation['counter'] = 0
            rotation['current_rule_idx'] = (rotation['current_rule_idx'] + 1) % len(matching_rules)
    
    def _has_ammo(self, weapon_id: int) -> bool:
        """
        Проверить есть ли патроны у оружия (в обойме)
        
        Args:
            weapon_id: ID оружия
            
        Returns:
            True если есть патроны в обойме
        """
        if weapon_id not in self.last_ammo:
            return False
        
        clip, reserve = self.last_ammo[weapon_id]
        # Проверяем ТОЛЬКО обойму (не запас!)
        return clip > 0
    
    def _switch_weapon(self, weapon_id: int):
        """
        Переключить оружие
        
        Args:
            weapon_id: ID оружия (1-6)
        """
        if weapon_id not in self.weapon_keys:
            logger.warning(f"Некорректный ID оружия: {weapon_id}")
            return
        
        try:
            # Нажимаем клавишу оружия быстрым методом
            key = self.weapon_keys[weapon_id]
            
            # Используем send вместо press_and_release для мгновенной отправки
            keyboard.send(key)
            logger.debug(f"Нажата клавиша: {key}")
            
            # Задержка убрана чтобы не блокировать управление
            
        except Exception as e:
            logger.error(f"Ошибка переключения оружия: {e}")
    
    def get_status(self) -> str:
        """Получить статус макросов"""
        if not self.enabled:
            return "Выключено"
        
        if not self.current_preset:
            return "Не выбран пресет"
        
        rules_count = len(self.presets.get(self.current_preset, {}).get('rules', []))
        return f"Активно: {self.current_preset} ({rules_count} правил)"
    
    def get_available_presets(self) -> List[str]:
        """Получить список доступных пресетов"""
        return list(self.presets.keys())
