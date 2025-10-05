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
    
    def reload_presets(self):
        """Перезагрузить список пресетов"""
        current = self.preset_combo.currentText()
        self.preset_combo.clear()
        
        presets = self.config.get('macros.presets', {})
        for preset_name in presets.keys():
            self.preset_combo.addItem(preset_name)
        
        # Восстановить выбор если возможно
        if current:
            index = self.preset_combo.findText(current)
            if index >= 0:
                self.preset_combo.setCurrentIndex(index)
    
    def _save_settings(self):
        """Сохранить настройки в user_settings"""
        fps = self.fps_spinbox.value()
        macros = self.macros_enabled_checkbox.isChecked()
        preset = self.preset_combo.currentText()
        
        self.config.set('gui.last_update_rate', fps)
        self.config.set('gui.macros_enabled', macros)
        self.config.set('gui.last_preset', preset)
        self.config.save_user_config()
        
        logger.debug(f"Сохранены настройки: FPS={fps}, Макросы={macros}, Пресет={preset}")
    
    def _load_settings(self):
        """Загрузить сохранённые настройки"""
        # FPS
        saved_fps = self.config.get('gui.last_update_rate')
        if saved_fps:
            self.fps_spinbox.blockSignals(True)  # Блокируем сигналы
            self.fps_spinbox.setValue(saved_fps)
            self.fps_spinbox.blockSignals(False)
            logger.info(f"Загружен FPS: {saved_fps}")
        
        # Пресет (загружаем до макросов!)
        last_preset = self.config.get('gui.last_preset')
        if last_preset:
            index = self.preset_combo.findText(last_preset)
            if index >= 0:
                self.preset_combo.blockSignals(True)  # Блокируем сигналы
                self.preset_combo.setCurrentIndex(index)
                self.preset_combo.blockSignals(False)
                logger.info(f"Загружен пресет: {last_preset}")
        
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
