"""
Модуль чтения памяти Pixel Gun 3D
Чтение патронов и другой игровой информации напрямую из памяти процесса
"""

import time
import struct
from typing import Optional, Dict, List, Tuple
from loguru import logger

try:
    import pymem
    import pymem.process
    PYMEM_AVAILABLE = True
except ImportError:
    PYMEM_AVAILABLE = False
    logger.warning("pymem не установлен. Установите: pip install pymem")


class MemoryReader:
    """
    Класс для чтения памяти игры Pixel Gun 3D
    
    Читает напрямую из памяти процесса:
    - Патроны всех 6 оружий (текущие/максимум)
    - Активное оружие
    - Здоровье, броня (опционально)
    """
    
    def __init__(self, process_name: str = "PixelGun3D.exe"):
        """
        Инициализация memory reader
        
        Args:
            process_name: Имя процесса игры
        """
        if not PYMEM_AVAILABLE:
            raise ImportError("pymem не установлен!")
        
        self.process_name = process_name
        self.pm = None
        self.base_address = None
        self.module_base = None  # База GameAssembly.dll
        
        # Оффсеты (будут найдены через Cheat Engine)
        self.offsets = {
            'weapon_slots_base': None,  # Базовый адрес в модуле
            'pointer_offsets': [],      # Цепочка pointer offsets
            'slot_1_clip': None,        # Оффсет для обоймы
            'slot_1_reserve': None,     # Оффсет для запаса
            'slot_offset': None,        # Размер структуры одного слота
            'active_weapon': None,      # Оффсет активного оружия (1-6)
            # Триггер: Цвет прицела (UISprite.mColor)
            'crosshair_controller': None,  # Базовый адрес AimCrosshairController
            'crosshair_offsets': []        # Цепочка указателей к AimCrosshairController
        }
        
        # Кэш данных
        self.ammo_cache = {}
        self.active_weapon_cache = 1
        self.last_update = 0
        
        # Кэш для триггера (чтобы не спамить логи)
        self.last_target_state = None  # True/False/None
        self.last_target_ptr = None
        
        logger.info("MemoryReader инициализирован")
    
    def connect(self) -> bool:
        """
        Подключение к процессу игры
        
        Returns:
            True если успешно подключились
        """
        try:
            self.pm = pymem.Pymem(self.process_name)
            self.base_address = pymem.process.module_from_name(
                self.pm.process_handle,
                self.process_name
            ).lpBaseOfDll
            
            # Ищем GameAssembly.dll (Unity)
            try:
                game_assembly = pymem.process.module_from_name(
                    self.pm.process_handle,
                    "GameAssembly.dll"
                )
                self.module_base = game_assembly.lpBaseOfDll
                logger.info(f"✅ Найден GameAssembly.dll: 0x{self.module_base:X}")
            except:
                self.module_base = self.base_address
                logger.warning(f"⚠️ GameAssembly.dll не найден, используем базовый адрес")
            
            logger.info(f"✅ Подключено к {self.process_name}")
            logger.info(f"Base address: 0x{self.base_address:X}")
            return True
        
        except pymem.exception.ProcessNotFound:
            logger.error(f"❌ Процесс {self.process_name} не найден!")
            logger.info("Запустите игру Pixel Gun 3D и попробуйте снова")
            return False
        
        except Exception as e:
            logger.error(f"Ошибка подключения: {e}")
            return False
    
    def is_connected(self) -> bool:
        """Проверка подключения к процессу"""
        return self.pm is not None
    
    def set_offsets(self, offsets: Dict[str, int]):
        """
        Установка оффсетов для чтения памяти
        
        Args:
            offsets: Словарь с оффсетами
        """
        self.offsets.update(offsets)
        logger.info(f"Оффсеты установлены: {offsets}")
    
    def read_int32(self, address: int) -> Optional[int]:
        """
        Чтение 32-битного целого числа
        
        Args:
            address: Адрес для чтения
            
        Returns:
            Значение или None при ошибке
        """
        if not self.is_connected():
            return None
        
        try:
            return self.pm.read_int(address)
        except Exception as e:
            logger.debug(f"Ошибка чтения адреса 0x{address:X}: {e}")
            return None
    
    def read_float(self, address: int) -> Optional[float]:
        """
        Чтение float значения
        
        Args:
            address: Адрес для чтения
            
        Returns:
            Значение или None при ошибке
        """
        if not self.is_connected():
            return None
        
        try:
            return self.pm.read_float(address)
        except Exception as e:
            logger.debug(f"Ошибка чтения float адреса 0x{address:X}: {e}")
            return None
    
    def read_pointer(self, address: int) -> Optional[int]:
        """
        Чтение указателя (64-bit адрес)
        
        Args:
            address: Адрес для чтения
            
        Returns:
            Значение указателя или None
        """
        if not self.is_connected():
            return None
        
        try:
            return self.pm.read_longlong(address)
        except Exception as e:
            logger.debug(f"Ошибка чтения указателя 0x{address:X}: {e}")
            return None
    
    def read_byte(self, address: int) -> Optional[int]:
        """
        Чтение 1 байта
        
        Args:
            address: Адрес для чтения
            
        Returns:
            Значение байта (0-255) или None
        """
        if not self.is_connected():
            return None
        
        try:
            return self.pm.read_uchar(address)
        except Exception as e:
            logger.debug(f"Ошибка чтения байта 0x{address:X}: {e}")
            return None
    
    def follow_pointer_chain(self) -> Optional[int]:
        """
        Следование по цепочке указателей
        
        Returns:
            Финальный адрес или None
        """
        if not self.is_connected():
            return None
        
        if self.offsets['weapon_slots_base'] is None:
            return None
        
        try:
            # Начинаем с модуля + базовый оффсет
            address = self.module_base + self.offsets['weapon_slots_base']
            logger.debug(f"Начало: 0x{address:X}")
            
            # Идём по цепочке указателей
            for i, offset in enumerate(self.offsets.get('pointer_offsets', [])):
                # Читаем указатель
                address = self.read_pointer(address)
                if address is None:
                    logger.error(f"Не удалось прочитать указатель на шаге {i}")
                    return None
                
                # Прибавляем оффсет
                address += offset
                logger.debug(f"Шаг {i+1}: 0x{address:X} (+0x{offset:X})")
            
            logger.debug(f"Финал: 0x{address:X}")
            return address
        
        except Exception as e:
            logger.error(f"Ошибка pointer chain: {e}")
            return None
    
    def read_slot_ammo(self, slot_id: int) -> Optional[Tuple[int, int]]:
        """
        Чтение патронов для слота
        
        Args:
            slot_id: ID слота (1-6)
            
        Returns:
            Tuple(clip, reserve) - обойма и запас
        """
        if not self.is_connected():
            return None
        
        if self.offsets['weapon_slots_base'] is None:
            logger.warning("⚠️ Оффсеты не установлены! Используйте set_offsets()")
            return None
        
        try:
            # Следуем по pointer chain
            slots_base = self.follow_pointer_chain()
            if slots_base is None:
                logger.error("Не удалось пройти pointer chain")
                return None
            
            # Вычисляем адрес слота
            slot_offset = self.offsets['slot_offset'] * (slot_id - 1)
            slot_address = slots_base + slot_offset
            
            # Читаем запас (reserve)
            reserve_addr = slot_address + self.offsets['slot_1_reserve']
            reserve = self.read_int32(reserve_addr)
            
            # Читаем обойму (clip)
            clip_addr = slot_address + self.offsets['slot_1_clip']
            clip = self.read_int32(clip_addr)
            
            if clip is not None and reserve is not None:
                logger.debug(f"Слот {slot_id}: {clip}/{reserve} (обойма/запас)")
                return (clip, reserve)
            
            return None
        
        except Exception as e:
            logger.error(f"Ошибка чтения слота {slot_id}: {e}")
            return None
    
    def read_all_ammo(self) -> Dict[int, Tuple[int, int]]:
        """
        Чтение патронов для всех 6 слотов одновременно
        
        Returns:
            Dict {slot_id: (current, max)}
        """
        all_ammo = {}
        
        for slot_id in range(1, 7):
            ammo = self.read_slot_ammo(slot_id)
            if ammo:
                all_ammo[slot_id] = ammo
                self.ammo_cache[slot_id] = ammo
        
        self.last_update = time.time()
        return all_ammo
    
    def read_active_weapon(self) -> Optional[int]:
        """
        Чтение ID активного оружия
        
        Returns:
            ID оружия (1-6) или None
        """
        if not self.is_connected():
            return None
        
        if self.offsets['active_weapon'] is None:
            return None
        
        try:
            addr = self.base_address + self.offsets['active_weapon']
            weapon_id = self.read_int32(addr)
            
            if weapon_id and 1 <= weapon_id <= 6:
                self.active_weapon_cache = weapon_id
                return weapon_id
            
            return None
        
        except Exception as e:
            logger.error(f"Ошибка чтения активного оружия: {e}")
            return None
    
    def get_cached_ammo(self, slot_id: int) -> Optional[Tuple[int, int]]:
        """Получение кэшированных патронов"""
        return self.ammo_cache.get(slot_id)
    
    def read_crosshair_on_enemy(self, debug_mode: bool = False) -> bool:
        """
        Проверить наведён ли прицел на врага через ЦВЕТ прицела
        
        ПУТЬ: GameAssembly → AimCrosshairController → aimCenterSprite (+0x38) → mColor (+0x94)
        Читаем FLOAT зелёного канала (G):
        - Если G ≈ 1.0 → прицел БЕЛЫЙ → мимо
        - Если G ≈ 0.0 → прицел КРАСНЫЙ → на враге
        
        Args:
            debug_mode: Включить детальное логирование цепочки указателей
        
        Returns:
            True если прицел на враге, False иначе
        """
        if not self.is_connected():
            if debug_mode:
                logger.error("[TRIGGER DEBUG] ❌ Не подключено к процессу")
            return False
        
        # Проверяем наличие оффсетов
        if 'crosshair_controller' not in self.offsets or self.offsets['crosshair_controller'] is None:
            if debug_mode:
                logger.error("[TRIGGER DEBUG] ❌ crosshair_controller не установлен в конфиге")
            return False
        
        try:
            # Начинаем с базового адреса
            base_offset = self.offsets['crosshair_controller']
            address = self.module_base + base_offset
            
            if debug_mode:
                logger.info("[TRIGGER DEBUG] ═══════════════════════════════════════════")
                logger.info(f"[TRIGGER DEBUG] 🎨 ПРОВЕРКА ЦВЕТА ПРИЦЕЛА")
                logger.info(f"[TRIGGER DEBUG] GameAssembly.dll база: 0x{self.module_base:X}")
                logger.info(f"[TRIGGER DEBUG] Базовый оффсет: 0x{base_offset:X}")
                logger.info(f"[TRIGGER DEBUG] Шаг 0 (начало): 0x{address:X}")
            
            # Идём по цепочке указателей
            # ВСЕ оффсеты кроме последнего - разыменовываем (читаем указатель)
            # Последний оффсет - просто прибавляем (до Green канала)
            crosshair_offsets = self.offsets.get('crosshair_offsets', [])
            
            for i, offset in enumerate(crosshair_offsets):
                # Читаем указатель
                prev_address = address
                address = self.read_pointer(address)
                
                if debug_mode:
                    if address is None:
                        logger.error(f"[TRIGGER DEBUG] ❌ Шаг {i+1}: не удалось прочитать указатель по 0x{prev_address:X}")
                        return False
                    elif address == 0:
                        logger.error(f"[TRIGGER DEBUG] ❌ Шаг {i+1}: указатель = NULL (0x0)")
                        return False
                    else:
                        logger.info(f"[TRIGGER DEBUG] ✅ Шаг {i+1}: [0x{prev_address:X}] → 0x{address:X}, затем +0x{offset:X}")
                
                if address is None or address == 0:
                    return False
                
                # Прибавляем оффсет
                address += offset
                
                if debug_mode:
                    logger.info(f"[TRIGGER DEBUG]         → Итого: 0x{address:X}")
            
            # Финальный адрес - это UISprite (после всех оффсетов)
            if debug_mode:
                logger.info(f"[TRIGGER DEBUG] ✅ Адрес Green канала: 0x{address:X}")
            
            # Читаем Green канал напрямую
            green_value = self.read_float(address)
            
            if debug_mode:
                if green_value is None:
                    logger.error(f"[TRIGGER DEBUG] ❌ Не удалось прочитать Green по 0x{address:X}")
                else:
                    # Читаем и другие каналы для полной картины
                    r = self.read_float(address - 0x4)  # R на -4 от G
                    g = green_value
                    b = self.read_float(address + 0x4)  # B на +4 от G
                    a = self.read_float(address + 0x8)  # A на +8 от G
                    logger.info(f"[TRIGGER DEBUG] Цвет прицела: R={r:.2f}, G={g:.2f}, B={b:.2f}, A={a:.2f}")
            
            if green_value is None:
                return False
            
            # Если G < 0.5 → красный → на враге
            # Если G > 0.5 → белый → мимо
            is_on_enemy = (green_value < 0.5)
            
            # Логируем только изменения состояния
            if is_on_enemy != self.last_target_state:
                if is_on_enemy:
                    logger.info(f"[TRIGGER] 🎯 Прицел КРАСНЫЙ - враг обнаружен!")
                else:
                    logger.info(f"[TRIGGER] Прицел БЕЛЫЙ - цель потеряна")
                self.last_target_state = is_on_enemy
            
            if debug_mode:
                logger.info(f"[TRIGGER DEBUG] Результат: {'🔴 КРАСНЫЙ (на враге)' if is_on_enemy else '⚪ БЕЛЫЙ (мимо)'}")
                logger.info("[TRIGGER DEBUG] ═══════════════════════════════════════════")
            
            return is_on_enemy
        
        except Exception as e:
            if debug_mode:
                logger.error(f"[TRIGGER DEBUG] ❌ ОШИБКА: {e}")
            else:
                logger.debug(f"[TRIGGER] Ошибка чтения цвета: {e}")
            return False
    
    def update_all(self) -> Dict:
        """
        Обновление всех данных
        
        Returns:
            Словарь с обновлённой информацией
        """
        data = {
            'ammo': self.read_all_ammo(),
            'active_weapon': self.read_active_weapon(),
            'timestamp': time.time()
        }
        
        return data
    
    def disconnect(self):
        """Отключение от процесса"""
        if self.pm:
            self.pm = None
            self.base_address = None
            logger.info("Отключено от процесса")
    
    def get_status(self) -> str:
        """Получение статуса подключения"""
        if not self.is_connected():
            return "❌ Не подключено"
        
        if not any(self.offsets.values()):
            return "⚠️ Подключено (оффсеты не установлены)"
        
        return "✅ Подключено и готово"

