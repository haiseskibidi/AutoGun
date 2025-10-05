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
            # Новая система для currentTargetMoveC
            'weapon_manager_static': 0x230,  # Статический WeaponManager (из dump.cs)
            'player_movec_offset': 0x48,     # myPlayerMoveC в WeaponManager
            'current_target_offset': 0x1380, # currentTargetMoveC (8-byte pointer)
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
    
    def read_crosshair_on_enemy(self) -> bool:
        """
        Проверить наведён ли прицел на врага через currentTargetMoveC
        
        АЛЬТЕРНАТИВНЫЙ ПУТЬ (через патроны):
        Патроны → WeaponManager → myPlayerMoveC → currentTargetMoveC
        
        Returns:
            True если прицел на враге (указатель != 0), False иначе
        """
        if not self.is_connected():
            logger.debug("[TARGET] ❌ Не подключено к игре")
            return False
        
        try:
            # ПЛАН B: Идём от патронов к WeaponManager!
            # Патроны: GameAssembly+059A58A0 → [B8] → [0] → [38] → [120] → [20]
            # Но [B8] → [0] → [38] это путь к WeaponManager!
            
            # ОТЛАДОЧНЫЙ ПУТЬ - проверяем каждый шаг!
            if self.last_target_state is None:
                logger.info(f"[TARGET] 🔍 === ПРОВЕРКА ПУТИ К WEAPONMANAGER ===")
            
            # Шаг 1: Базовый адрес патронов
            base = self.module_base + self.offsets['weapon_slots_base']
            if self.last_target_state is None:
                logger.info(f"[TARGET] Шаг 1: GameAssembly + 0x{self.offsets['weapon_slots_base']:X} = 0x{base:X}")
            
            # Шаг 2: Читаем первый указатель
            ptr1 = self.read_pointer(base)
            if not ptr1:
                return False
            if self.last_target_state is None:
                logger.info(f"[TARGET] Шаг 2: [0x{base:X}] = 0x{ptr1:X}")
            
            # Шаг 3: ptr1 + 0xB8
            addr_b8 = ptr1 + 0xB8
            ptr2 = self.read_pointer(addr_b8)
            if not ptr2:
                return False
            if self.last_target_state is None:
                logger.info(f"[TARGET] Шаг 3: [0x{ptr1:X} + 0xB8] = [0x{addr_b8:X}] = 0x{ptr2:X}")
            
            # Шаг 4: ptr2 + 0x0 (просто разыменование)
            ptr3 = self.read_pointer(ptr2 + 0x0)
            if not ptr3:
                return False
            if self.last_target_state is None:
                logger.info(f"[TARGET] Шаг 4: [0x{ptr2:X} + 0x0] = 0x{ptr3:X}")
            
            # Шаг 5: ptr3 + 0x38 → МОЖЕТ ТУТ WeaponManager?
            addr_38 = ptr3 + 0x38
            ptr4 = self.read_pointer(addr_38)
            if not ptr4:
                return False
            if self.last_target_state is None:
                logger.info(f"[TARGET] Шаг 5: [0x{ptr3:X} + 0x38] = [0x{addr_38:X}] = 0x{ptr4:X}")
            
            # Попробуем ptr4 как WeaponManager
            weapon_manager_ptr = ptr4
            
            if self.last_target_state is None:
                logger.info(f"[TARGET] === ПРОВЕРКА WEAPONMANAGER ===")
                # Читаем myPlayer (GameObject) на +0x40
                my_player_go_addr = weapon_manager_ptr + 0x40
                my_player_go_ptr = self.read_pointer(my_player_go_addr)
                logger.info(f"[TARGET] myPlayer (GameObject) +0x40 = 0x{my_player_go_ptr:X}" if my_player_go_ptr else "[TARGET] myPlayer (GameObject) = NULL")
            
            # Шаг 6: Читаем myPlayerMoveC (+0x48 от WeaponManager)
            my_player_addr = weapon_manager_ptr + self.offsets['player_movec_offset']
            my_player_ptr = self.read_pointer(my_player_addr)
            
            if not my_player_ptr or my_player_ptr == 0:
                if self.last_target_state is None:
                    logger.warning(f"[TARGET] ⚠️ myPlayerMoveC (+0x48) = NULL!")
                return False
            
            if self.last_target_state is None:
                logger.info(f"[TARGET] myPlayerMoveC (+0x48) = 0x{my_player_ptr:X}")
                logger.info(f"[TARGET] === КОНЕЦ ПРОВЕРКИ ПУТИ ===")
            
            # Шаг 7: Читаем currentTargetMoveC - это УКАЗАТЕЛЬ (8 байт) на +0x1380!
            current_target_offset = 0x1380
            current_target_addr = my_player_ptr + current_target_offset
            
            # Читаем 8-байтовый указатель
            try:
                current_target_ptr = self.read_pointer(current_target_addr)
            except:
                return False
            
            # РАСШИРЕННЫЙ ДАМП - покажем ТОЛЬКО NULL значения (кандидаты)!
            if self.last_target_state is None:
                logger.info(f"[TARGET] 🔍 === ПОИСК NULL УКАЗАТЕЛЕЙ (0x1000-0x1500) ===")
                logger.info(f"[TARGET] myPlayerMoveC: 0x{my_player_ptr:X}")
                logger.info(f"[TARGET] Показываю ТОЛЬКО NULL (они должны стать НЕ-NULL при наведении):")
                
                null_count = 0
                # Показываем ТОЛЬКО NULL значения в РАСШИРЕННОМ диапазоне
                for offset in range(0x1000, 0x1500, 8):
                    try:
                        addr = my_player_ptr + offset
                        ptr_val = self.read_pointer(addr)
                        
                        if ptr_val == 0:
                            logger.info(f"[TARGET]   +0x{offset:04X}: NULL")
                            null_count += 1
                    except:
                        pass
                
                logger.info(f"[TARGET] Найдено {null_count} NULL указателей")
                logger.info(f"[TARGET] === КОНЕЦ ПОИСКА ===")
            
            # Если указатель != NULL, значит прицел на враге!
            is_on_enemy = (current_target_ptr is not None and current_target_ptr != 0)
            
            # ЛОГИРУЕМ ТОЛЬКО ПРИ ИЗМЕНЕНИИ СОСТОЯНИЯ!
            if is_on_enemy != self.last_target_state or current_target_ptr != self.last_target_ptr:
                if is_on_enemy:
                    logger.info(f"[TARGET] 🎯 ✅ ЦЕЛЬ ЗАХВАЧЕНА! currentTargetMoveC = 0x{current_target_ptr:X}")
                else:
                    logger.info(f"[TARGET] ❌ ЦЕЛЬ ПОТЕРЯНА (currentTargetMoveC = NULL)")
                
                # Обновляем кэш
                self.last_target_state = is_on_enemy
                self.last_target_ptr = current_target_ptr
            
            return is_on_enemy
        
        except Exception as e:
            logger.error(f"[TARGET] 💥 Ошибка чтения: {e}", exc_info=True)
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

