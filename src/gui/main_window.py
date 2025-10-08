"""
Главное окно приложения - минималистичный дизайн
"""

from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QSpinBox, QCheckBox, QTextEdit, QFrame, QComboBox)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from loguru import logger


class WeaponRow(QWidget):
    """Строка с информацией об оружии"""
    
    def __init__(self, weapon_id: int, weapon_name: str, color: str):
        super().__init__()
        self.weapon_id = weapon_id
        self.color = color
        
        layout = QHBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        self.setLayout(layout)
        
        # Цветная метка
        marker = QLabel("●")
        marker.setStyleSheet(f"color: {color}; font-size: 14px;")
        marker.setFixedWidth(20)
        layout.addWidget(marker)
        
        # Название
        name_label = QLabel(weapon_name)
        name_label.setFixedWidth(120)
        name_label.setStyleSheet(f"color: {color};")
        layout.addWidget(name_label)
        
        # Обойма
        self.clip_label = QLabel("--")
        clip_font = QFont()
        clip_font.setPointSize(14)
        clip_font.setBold(True)
        self.clip_label.setFont(clip_font)
        self.clip_label.setStyleSheet("color: #4CAF50;")
        self.clip_label.setFixedWidth(50)
        self.clip_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(self.clip_label)
        
        # Разделитель
        sep = QLabel("/")
        sep.setStyleSheet("color: #666;")
        layout.addWidget(sep)
        
        # Запас
        self.reserve_label = QLabel("--")
        reserve_font = QFont()
        reserve_font.setPointSize(14)
        reserve_font.setBold(True)
        self.reserve_label.setFont(reserve_font)
        self.reserve_label.setStyleSheet("color: #2196F3;")
        self.reserve_label.setFixedWidth(50)
        layout.addWidget(self.reserve_label)
        
        layout.addStretch()
    
    def update_ammo(self, clip: int, reserve: int):
        """Обновление патронов"""
        if self.weapon_id == 3:  # Холодное
            self.clip_label.setText("--")
            self.reserve_label.setText("--")
            return
        
        self.clip_label.setText(str(clip))
        self.reserve_label.setText(str(reserve))
        
        # Цвет обоймы
        if clip + reserve == 0:
            self.clip_label.setStyleSheet("color: #f44336;")
        elif clip == 0:
            self.clip_label.setStyleSheet("color: #FF9800;")
        else:
            self.clip_label.setStyleSheet("color: #4CAF50;")


class MainWindow(QMainWindow):
    """Главное окно"""
    
    tracking_started = pyqtSignal()
    tracking_stopped = pyqtSignal()
    reconnect_requested = pyqtSignal()
    macros_toggled = pyqtSignal(bool)
    preset_changed = pyqtSignal(str)
    trigger_toggled = pyqtSignal(bool)
    auto_jump_toggled = pyqtSignal(bool)
    auto_jump_settings_changed = pyqtSignal(int, int)  # (repeat_count, delay_ms)
    
    def __init__(self, config_manager):
        super().__init__()
        self.config = config_manager
        self.is_tracking = False
        self.weapon_rows = {}
        
        self._init_ui()
        
        logger.info("Главное окно инициализировано")
    
    def load_saved_settings(self):
        """Загрузить сохранённые настройки (вызывается после инициализации всего)"""
        self._load_settings()
    
    def _init_ui(self):
        """Инициализация UI"""
        self.setWindowTitle("AutoGun - PG3D Ammo Tracker")
        self.setGeometry(100, 100, 450, 500)
        
        central = QWidget()
        self.setCentralWidget(central)
        
        layout = QVBoxLayout()
        layout.setSpacing(10)
        central.setLayout(layout)
        
        # Заголовок
        title = QLabel("AutoGun")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #4CAF50; padding: 5px;")
        layout.addWidget(title)
        
        # Статус
        status_frame = QFrame()
        status_frame.setStyleSheet("background-color: #252525; border-radius: 3px;")
        status_layout = QHBoxLayout()
        status_layout.setContentsMargins(10, 5, 10, 5)
        status_frame.setLayout(status_layout)
        
        self.status_indicator = QLabel("●")
        self.status_indicator.setStyleSheet("color: #666; font-size: 12px;")
        status_layout.addWidget(self.status_indicator)
        
        self.status_label = QLabel("Остановлено")
        status_layout.addWidget(self.status_label)
        
        status_layout.addStretch()
        
        self.connection_label = QLabel("Не подключено")
        self.connection_label.setStyleSheet("color: #888; font-size: 10px;")
        status_layout.addWidget(self.connection_label)
        
        self.fps_label = QLabel("FPS: 0")
        self.fps_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
        status_layout.addWidget(self.fps_label)
        
        layout.addWidget(status_frame)
        
        # Оружия
        weapons_widget = QWidget()
        weapons_layout = QVBoxLayout()
        weapons_layout.setSpacing(2)
        weapons_layout.setContentsMargins(0, 0, 0, 0)
        weapons_widget.setLayout(weapons_layout)
        
        weapons = [
            (1, "Основное", "#4CAF50"),
            (2, "Пистолет", "#2196F3"),
            (3, "Холодное", "#FF9800"),
            (4, "Специальное", "#9C27B0"),
            (5, "Снайперка", "#00BCD4"),
            (6, "Тяжёлое", "#F44336")
        ]
        
        for wid, name, color in weapons:
            row = WeaponRow(wid, name, color)
            self.weapon_rows[wid] = row
            weapons_layout.addWidget(row)
        
        layout.addWidget(weapons_widget)
        
        # Кнопки
        buttons_frame = QFrame()
        buttons_frame.setStyleSheet("background-color: #252525; border-radius: 3px;")
        buttons_layout = QHBoxLayout()
        buttons_layout.setContentsMargins(10, 8, 10, 8)
        buttons_frame.setLayout(buttons_layout)
        
        self.start_button = QPushButton("▶ Начать")
        self.start_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 8px 15px;
                border: none;
                border-radius: 3px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #45a049; }
        """)
        self.start_button.clicked.connect(self._on_start)
        buttons_layout.addWidget(self.start_button)
        
        self.stop_button = QPushButton("⏸ Стоп")
        self.stop_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                padding: 8px 15px;
                border: none;
                border-radius: 3px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #da190b; }
        """)
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self._on_stop)
        buttons_layout.addWidget(self.stop_button)
        
        self.reconnect_button = QPushButton("🔌")
        self.reconnect_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                padding: 8px 12px;
                border: none;
                border-radius: 3px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #0b7dda; }
        """)
        self.reconnect_button.clicked.connect(self._on_reconnect)
        buttons_layout.addWidget(self.reconnect_button)
        
        # Кнопка настройки макросов
        self.macros_button = QPushButton("⚙️")
        self.macros_button.setToolTip("Настройка макросов")
        self.macros_button.setStyleSheet("""
            QPushButton {
                background-color: #9C27B0;
                color: white;
                padding: 8px 12px;
                border: none;
                border-radius: 3px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #7B1FA2; }
        """)
        self.macros_button.clicked.connect(self._on_macros_settings)
        buttons_layout.addWidget(self.macros_button)
        
        # Кнопка настройки клавиш
        self.keybindings_button = QPushButton("⌨️")
        self.keybindings_button.setToolTip("Настройка клавиш оружия")
        self.keybindings_button.setStyleSheet("""
            QPushButton {
                background-color: #00BCD4;
                color: white;
                padding: 8px 12px;
                border: none;
                border-radius: 3px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #0097A7; }
        """)
        self.keybindings_button.clicked.connect(self._on_keybindings_settings)
        buttons_layout.addWidget(self.keybindings_button)
        
        buttons_layout.addStretch()
        
        buttons_layout.addWidget(QLabel("FPS:"))
        self.fps_spinbox = QSpinBox()
        self.fps_spinbox.setRange(10, 120)
        # Берём из gui.last_update_rate или memory_reading.update_rate
        default_fps = self.config.get('gui.last_update_rate') or self.config.get('memory_reading.update_rate', 120)
        self.fps_spinbox.setValue(default_fps)
        self.fps_spinbox.setFixedWidth(60)
        self.fps_spinbox.setStyleSheet("padding: 3px; background-color: #2a2a2a; border: 1px solid #444; border-radius: 2px;")
        self.fps_spinbox.valueChanged.connect(lambda: self._save_settings())
        buttons_layout.addWidget(self.fps_spinbox)
        
        self.debug_checkbox = QCheckBox("Debug")
        self.debug_checkbox.setChecked(self.config.get('gui.show_debug_info', False))
        buttons_layout.addWidget(self.debug_checkbox)
        
        layout.addWidget(buttons_frame)
        
        # Панель макросов
        macros_frame = QFrame()
        macros_frame.setStyleSheet("background-color: #252525; border-radius: 3px;")
        macros_layout = QHBoxLayout()
        macros_layout.setContentsMargins(10, 5, 10, 5)
        macros_frame.setLayout(macros_layout)
        
        macros_layout.addWidget(QLabel("Макросы:"))
        
        # Переключатель вкл/выкл
        self.macros_enabled_checkbox = QCheckBox("Вкл")
        default_macros_enabled = self.config.get('macros.enabled', True)
        self.macros_enabled_checkbox.setChecked(default_macros_enabled)
        self.macros_enabled_checkbox.stateChanged.connect(self._on_macros_toggled)
        macros_layout.addWidget(self.macros_enabled_checkbox)
        
        # Выбор пресета
        macros_layout.addWidget(QLabel("Пресет:"))
        self.preset_combo = QComboBox()
        self.preset_combo.setStyleSheet("padding: 3px; background-color: #2a2a2a; border: 1px solid #444; border-radius: 2px;")
        self.preset_combo.currentTextChanged.connect(self._on_preset_changed)
        macros_layout.addWidget(self.preset_combo)
        
        # Статус макросов
        self.macros_status_label = QLabel("Выключено")
        self.macros_status_label.setStyleSheet("color: #888; font-size: 10px;")
        macros_layout.addWidget(self.macros_status_label)
        
        macros_layout.addStretch()
        
        layout.addWidget(macros_frame)
        
        # Панель триггер-бота
        trigger_frame = QFrame()
        trigger_frame.setStyleSheet("background-color: #252525; border-radius: 3px;")
        trigger_layout = QHBoxLayout()
        trigger_layout.setContentsMargins(10, 5, 10, 5)
        trigger_frame.setLayout(trigger_layout)
        
        trigger_layout.addWidget(QLabel("Триггер-бот:"))
        
        # Переключатель вкл/выкл
        self.trigger_enabled_checkbox = QCheckBox("Вкл")
        # Устанавливаем дефолтное значение из конфига ДО подключения сигнала
        default_trigger_enabled = self.config.get('trigger.enabled', False)
        self.trigger_enabled_checkbox.setChecked(default_trigger_enabled)
        self.trigger_enabled_checkbox.stateChanged.connect(self._on_trigger_toggled)
        trigger_layout.addWidget(self.trigger_enabled_checkbox)
        
        # Статус триггера
        self.trigger_status_label = QLabel("Выключено")
        self.trigger_status_label.setStyleSheet("color: #888; font-size: 10px;")
        trigger_layout.addWidget(self.trigger_status_label)
        
        # Предупреждение
        warning_label = QLabel("⚠️ Используйте осторожно")
        warning_label.setStyleSheet("color: #FF9800; font-size: 9px;")
        trigger_layout.addWidget(warning_label)
        
        # Настройки триггера
        trigger_layout.addWidget(QLabel("Задержка:"))
        self.trigger_delay_spinbox = QSpinBox()
        self.trigger_delay_spinbox.setRange(10, 300)
        self.trigger_delay_spinbox.setValue(100)  # По умолчанию
        self.trigger_delay_spinbox.setSuffix(" мс")
        self.trigger_delay_spinbox.setFixedWidth(80)
        self.trigger_delay_spinbox.setStyleSheet("padding: 3px; background-color: #2a2a2a; border: 1px solid #444; border-radius: 2px;")
        self.trigger_delay_spinbox.setToolTip("Средняя задержка реакции")
        trigger_layout.addWidget(self.trigger_delay_spinbox)
        
        trigger_layout.addStretch()
        
        layout.addWidget(trigger_frame)
        
        # Панель Auto Jump (BunnyHop)
        auto_jump_frame = QFrame()
        auto_jump_frame.setStyleSheet("background-color: #252525; border-radius: 3px;")
        auto_jump_layout = QHBoxLayout()
        auto_jump_layout.setContentsMargins(10, 5, 10, 5)
        auto_jump_frame.setLayout(auto_jump_layout)
        
        auto_jump_layout.addWidget(QLabel("Auto Jump:"))
        
        # Переключатель вкл/выкл
        self.auto_jump_enabled_checkbox = QCheckBox("Вкл")
        default_auto_jump_enabled = self.config.get('auto_jump.enabled', False)
        self.auto_jump_enabled_checkbox.setChecked(default_auto_jump_enabled)
        self.auto_jump_enabled_checkbox.stateChanged.connect(self._on_auto_jump_toggled)
        auto_jump_layout.addWidget(self.auto_jump_enabled_checkbox)
        
        # Статус
        self.auto_jump_status_label = QLabel("Выключено")
        self.auto_jump_status_label.setStyleSheet("color: #888; font-size: 10px;")
        auto_jump_layout.addWidget(self.auto_jump_status_label)
        
        # Иконка
        jump_icon = QLabel("🦘")
        jump_icon.setStyleSheet("font-size: 14px;")
        auto_jump_layout.addWidget(jump_icon)
        
        # Количество повторов
        auto_jump_layout.addWidget(QLabel("Повторов:"))
        self.auto_jump_repeat_spinbox = QSpinBox()
        self.auto_jump_repeat_spinbox.setRange(1, 10)
        self.auto_jump_repeat_spinbox.setValue(self.config.get('auto_jump.repeat_count', 2))
        self.auto_jump_repeat_spinbox.setFixedWidth(50)
        self.auto_jump_repeat_spinbox.setStyleSheet("padding: 3px; background-color: #2a2a2a; border: 1px solid #444; border-radius: 2px;")
        self.auto_jump_repeat_spinbox.setToolTip("Количество повторных прыжков")
        self.auto_jump_repeat_spinbox.valueChanged.connect(self._on_auto_jump_settings_changed)
        auto_jump_layout.addWidget(self.auto_jump_repeat_spinbox)
        
        # Задержка
        auto_jump_layout.addWidget(QLabel("Задержка:"))
        self.auto_jump_delay_spinbox = QSpinBox()
        self.auto_jump_delay_spinbox.setRange(10, 2000)
        self.auto_jump_delay_spinbox.setValue(self.config.get('auto_jump.delay_ms', 100))
        self.auto_jump_delay_spinbox.setSuffix(" мс")
        self.auto_jump_delay_spinbox.setFixedWidth(90)
        self.auto_jump_delay_spinbox.setStyleSheet("padding: 3px; background-color: #2a2a2a; border: 1px solid #444; border-radius: 2px;")
        self.auto_jump_delay_spinbox.setToolTip("Задержка между прыжками")
        self.auto_jump_delay_spinbox.valueChanged.connect(self._on_auto_jump_settings_changed)
        auto_jump_layout.addWidget(self.auto_jump_delay_spinbox)
        
        auto_jump_layout.addStretch()
        
        layout.addWidget(auto_jump_frame)
        
        # Лог
        log_label = QLabel("Логи:")
        log_label.setStyleSheet("font-size: 9px; color: #666;")
        layout.addWidget(log_label)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMinimumHeight(60)  # Минимальная высота
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #1a1a1a;
                border: 1px solid #333;
                border-radius: 2px;
                padding: 3px;
                font-family: 'Consolas', monospace;
                font-size: 8px;
                color: #888;
            }
        """)
        layout.addWidget(self.log_text, 1)  # stretch factor = 1 (будет растягиваться)
        
        # Тема
        self.setStyleSheet("""
                QMainWindow, QWidget {
                    background-color: #1e1e1e;
                    color: #ffffff;
                }
        """)
    
    def _on_start(self):
        self.is_tracking = True
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.status_indicator.setStyleSheet("color: #4CAF50; font-size: 12px;")
        self.status_label.setText("Работает")
        self.tracking_started.emit()
        self.add_log("✅ Начато")
        self._save_settings()
    
    def _on_stop(self):
        self.is_tracking = False
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.status_indicator.setStyleSheet("color: #666; font-size: 12px;")
        self.status_label.setText("Остановлено")
        self.tracking_stopped.emit()
        self.add_log("⏸ Остановлено")
    
    def _on_reconnect(self):
        self.reconnect_requested.emit()
        self.add_log("🔄 Переподключение...")
    
    def _on_macros_settings(self):
        """Открыть окно настройки макросов"""
        from src.gui.macro_settings_window import MacroSettingsWindow
        dialog = MacroSettingsWindow(self, self.config)
        dialog.exec()
        # Обновить список пресетов после закрытия окна
        self.reload_presets()
    
    def _on_keybindings_settings(self):
        """Открыть окно настройки клавиш оружия"""
        from src.gui.keybindings_window import KeybindingsWindow
        dialog = KeybindingsWindow(self, self.config)
        dialog.exec()
    
    def _on_macros_toggled(self, state):
        """Переключение макросов"""
        enabled = (state == 2)  # Qt.CheckState.Checked
        self.macros_toggled.emit(enabled)
        
        if enabled:
            self.macros_status_label.setText("Включено")
            self.macros_status_label.setStyleSheet("color: #4CAF50; font-size: 10px;")
            self.add_log("✅ Макросы включены")
        else:
            self.macros_status_label.setText("Выключено")
            self.macros_status_label.setStyleSheet("color: #888; font-size: 10px;")
            self.add_log("⏸ Макросы выключены")
        
        self._save_settings()
    
    def _on_preset_changed(self, preset_name):
        """Изменение пресета"""
        if preset_name:
            self.preset_changed.emit(preset_name)
            self.add_log(f"Пресет: {preset_name}")
            self._save_settings()
    
    def _on_trigger_toggled(self, state):
        """Переключение триггер-бота"""
        enabled = (state == 2)  # Qt.CheckState.Checked
        self.trigger_toggled.emit(enabled)
        
        if enabled:
            self.trigger_status_label.setText("АКТИВЕН")
            self.trigger_status_label.setStyleSheet("color: #f44336; font-size: 10px; font-weight: bold;")
            self.add_log("🎯 Триггер-бот включен")
        else:
            self.trigger_status_label.setText("Выключено")
            self.trigger_status_label.setStyleSheet("color: #888; font-size: 10px;")
            self.add_log("⏸ Триггер-бот выключен")
        
        self._save_settings()
    
    def _on_auto_jump_toggled(self, state):
        """Переключение Auto Jump"""
        enabled = (state == 2)  # Qt.CheckState.Checked
        self.auto_jump_toggled.emit(enabled)
        
        if enabled:
            self.auto_jump_status_label.setText("АКТИВЕН")
            self.auto_jump_status_label.setStyleSheet("color: #4CAF50; font-size: 10px; font-weight: bold;")
            self.add_log("🦘 Auto Jump включен")
        else:
            self.auto_jump_status_label.setText("Выключено")
            self.auto_jump_status_label.setStyleSheet("color: #888; font-size: 10px;")
            self.add_log("⏸ Auto Jump выключен")
        
        self._save_settings()
    
    def _on_auto_jump_settings_changed(self):
        """Изменение настроек Auto Jump"""
        repeat_count = self.auto_jump_repeat_spinbox.value()
        delay_ms = self.auto_jump_delay_spinbox.value()
        
        # Сохраняем в конфиг
        self.config.set('auto_jump.repeat_count', repeat_count)
        self.config.set('auto_jump.delay_ms', delay_ms)
        self._save_settings()
        
        # Эмитируем сигнал для обновления в реальном времени
        self.auto_jump_settings_changed.emit(repeat_count, delay_ms)
    
    def reload_presets(self):
        """Перезагрузить список пресетов"""
        current = self.preset_combo.currentText()
        
        # Блокируем сигналы чтобы не вызывался _on_preset_changed при заполнении
        self.preset_combo.blockSignals(True)
        self.preset_combo.clear()
        
        presets = self.config.get('macros.presets', {})
        for preset_name in presets.keys():
            self.preset_combo.addItem(preset_name)
        
        # Восстановить выбор
        # Сначала пробуем текущий выбранный
        preset_to_select = current
        
        # Если пусто (первый запуск) - берём последний сохранённый
        if not preset_to_select:
            preset_to_select = self.config.get('gui.last_preset')
        
        # Устанавливаем если нашли
        if preset_to_select:
            index = self.preset_combo.findText(preset_to_select)
            if index >= 0:
                self.preset_combo.setCurrentIndex(index)
                logger.info(f"Пресет восстановлен: {preset_to_select}")
        
        # Разблокируем сигналы
        self.preset_combo.blockSignals(False)
        
        # ВАЖНО: После разблокировки вручную эмитируем сигнал 
        # чтобы macro_engine знал какой пресет выбран
        current_preset = self.preset_combo.currentText()
        if current_preset:
            self.preset_changed.emit(current_preset)
    
    def _save_settings(self):
        """Сохранить настройки в user_settings"""
        fps = self.fps_spinbox.value()
        macros = self.macros_enabled_checkbox.isChecked()
        trigger = self.trigger_enabled_checkbox.isChecked()
        auto_jump = self.auto_jump_enabled_checkbox.isChecked()
        preset = self.preset_combo.currentText()
        
        self.config.set('gui.last_update_rate', fps)
        self.config.set('gui.macros_enabled', macros)
        self.config.set('gui.trigger_enabled', trigger)
        self.config.set('gui.auto_jump_enabled', auto_jump)
        self.config.set('gui.last_preset', preset)
        self.config.save_user_config()
        
        logger.debug(f"Сохранены настройки: FPS={fps}, Макросы={macros}, Триггер={trigger}, AutoJump={auto_jump}, Пресет={preset}")
    
    def _load_settings(self):
        """Загрузить сохранённые настройки"""
        # FPS
        saved_fps = self.config.get('gui.last_update_rate')
        if saved_fps:
            self.fps_spinbox.blockSignals(True)  # Блокируем сигналы
            self.fps_spinbox.setValue(saved_fps)
            self.fps_spinbox.blockSignals(False)
            logger.info(f"Загружен FPS: {saved_fps}")
        
        # Пресет уже загружен в reload_presets(), не дублируем
        
        macros_enabled = self.config.get('gui.macros_enabled')
        if macros_enabled is None:
            macros_enabled = self.config.get('macros.enabled', True)
        
        self.macros_enabled_checkbox.blockSignals(True)  # Блокируем сигналы
        self.macros_enabled_checkbox.setChecked(macros_enabled)
        self.macros_enabled_checkbox.blockSignals(False)
        
        # Обновляем визуальный статус
        if macros_enabled:
            self.macros_status_label.setText("Включено")
            self.macros_status_label.setStyleSheet("color: #4CAF50; font-size: 10px;")
        else:
            self.macros_status_label.setText("Выключено")
            self.macros_status_label.setStyleSheet("color: #888; font-size: 10px;")
        
        logger.info(f"Загружено состояние макросов: {macros_enabled}")
        
        # Эмитируем сигнал для применения настроек макросов
        self.macros_toggled.emit(macros_enabled)
        
        # Триггер-бот (загружаем последним!)
        trigger_enabled = self.config.get('gui.trigger_enabled')
        if trigger_enabled is None:
            trigger_enabled = self.config.get('trigger.enabled', False)
        
        self.trigger_enabled_checkbox.blockSignals(True)
        self.trigger_enabled_checkbox.setChecked(trigger_enabled)
        self.trigger_enabled_checkbox.blockSignals(False)
        
        # Обновляем визуальный статус
        if trigger_enabled:
            self.trigger_status_label.setText("АКТИВЕН")
            self.trigger_status_label.setStyleSheet("color: #f44336; font-size: 10px; font-weight: bold;")
        else:
            self.trigger_status_label.setText("Выключено")
            self.trigger_status_label.setStyleSheet("color: #888; font-size: 10px;")
        
        logger.info(f"Загружено состояние триггера: {trigger_enabled}")
        
        # Эмитируем сигнал для применения настроек триггера
        self.trigger_toggled.emit(trigger_enabled)
        
        # Auto Jump
        auto_jump_enabled = self.config.get('gui.auto_jump_enabled')
        if auto_jump_enabled is None:
            auto_jump_enabled = self.config.get('auto_jump.enabled', False)
        
        self.auto_jump_enabled_checkbox.blockSignals(True)
        self.auto_jump_enabled_checkbox.setChecked(auto_jump_enabled)
        self.auto_jump_enabled_checkbox.blockSignals(False)
        
        # Обновляем визуальный статус
        if auto_jump_enabled:
            self.auto_jump_status_label.setText("АКТИВЕН")
            self.auto_jump_status_label.setStyleSheet("color: #4CAF50; font-size: 10px; font-weight: bold;")
        else:
            self.auto_jump_status_label.setText("Выключено")
            self.auto_jump_status_label.setStyleSheet("color: #888; font-size: 10px;")
        
        logger.info(f"Загружено состояние Auto Jump: {auto_jump_enabled}")
        
        # Эмитируем сигнал для применения настроек Auto Jump
        self.auto_jump_toggled.emit(auto_jump_enabled)
    
    def update_weapon_ammo(self, weapon_id: int, clip: int, reserve: int):
        if weapon_id in self.weapon_rows:
            self.weapon_rows[weapon_id].update_ammo(clip, reserve)
    
    def update_all_weapons(self, ammo_data: dict):
        for wid in range(1, 7):
            if wid in ammo_data:
                clip, reserve = ammo_data[wid]
                self.update_weapon_ammo(wid, clip, reserve)
    
    def update_fps(self, fps: float):
        self.fps_label.setText(f"FPS: {fps:.1f}")
        
        if fps >= 50:
            self.fps_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
        elif fps >= 30:
            self.fps_label.setStyleSheet("color: #FF9800; font-weight: bold;")
        else:
            self.fps_label.setStyleSheet("color: #f44336; font-weight: bold;")
    
    def add_log(self, message: str):
        self.log_text.append(message)
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def get_update_rate(self) -> int:
        return self.fps_spinbox.value()
    
    def update_connection_status(self, status: str, color: str = "green"):
        color_map = {
            "green": "#4CAF50",
            "orange": "#FF9800",
            "red": "#f44336"
        }
        self.connection_label.setText(status)
        self.connection_label.setStyleSheet(f"color: {color_map.get(color, '#888')}; font-size: 10px;")
    
    def is_debug_mode(self) -> bool:
        return self.debug_checkbox.isChecked()
    
    # Совместимость
    def update_ammo_count(self, current: int, maximum: int):
        pass
    
    def get_current_category(self):
        return 1
