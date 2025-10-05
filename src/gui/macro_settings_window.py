"""
Окно настройки макросов - пресеты с правилами свапа
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QListWidget, QComboBox, QLineEdit, QGroupBox,
                             QMessageBox, QListWidgetItem, QWidget, QFrame)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from loguru import logger


class SwapRule(QFrame):
    """Одно правило свапа"""
    
    def __init__(self, rule_data=None, on_delete=None):
        super().__init__()
        self.on_delete = on_delete
        
        self.setStyleSheet("""
            QFrame {
                background-color: #2a2a2a;
                border: 1px solid #444;
                border-radius: 3px;
                padding: 5px;
            }
        """)
        
        layout = QHBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        self.setLayout(layout)
        
        # Условие: Из
        layout.addWidget(QLabel("Из:"))
        
        self.from_weapon = QComboBox()
        self.from_weapon.addItems([
            "1. Основное",
            "2. Пистолет",
            "3. Холодное",
            "4. Специальное",
            "5. Снайперка",
            "6. Тяжёлое"
        ])
        layout.addWidget(self.from_weapon)
        
        # Стрелка
        layout.addWidget(QLabel("→"))
        
        # Действие
        self.to_weapon = QComboBox()
        self.to_weapon.addItems([
            "1. Основное",
            "2. Пистолет",
            "3. Холодное",
            "4. Специальное",
            "5. Снайперка",
            "6. Тяжёлое"
        ])
        layout.addWidget(self.to_weapon)
        
        # Галочка: только если есть патроны
        from PyQt6.QtWidgets import QCheckBox, QSpinBox
        self.check_ammo = QCheckBox("Если есть патроны")
        self.check_ammo.setChecked(True)
        self.check_ammo.setStyleSheet("color: #888; font-size: 10px;")
        layout.addWidget(self.check_ammo)
        
        # Количество повторений
        layout.addWidget(QLabel("Раз:"))
        self.repeat_count = QSpinBox()
        self.repeat_count.setRange(1, 99)
        self.repeat_count.setValue(1)
        self.repeat_count.setFixedWidth(50)
        self.repeat_count.setStyleSheet("padding: 3px; background-color: #1e1e1e; border: 1px solid #444; border-radius: 2px;")
        self.repeat_count.setToolTip("Сколько раз правило сработает перед переключением на следующее")
        layout.addWidget(self.repeat_count)
        
        # Кнопка удалить
        delete_btn = QPushButton("✖")
        delete_btn.setFixedWidth(30)
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                border-radius: 2px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #da190b; }
        """)
        delete_btn.clicked.connect(self._on_delete_clicked)
        layout.addWidget(delete_btn)
        
        # Загрузить данные если есть
        if rule_data:
            self.from_weapon.setCurrentIndex(rule_data['from'] - 1)
            self.to_weapon.setCurrentIndex(rule_data['to'] - 1)
            self.check_ammo.setChecked(rule_data.get('check_ammo', True))
            self.repeat_count.setValue(rule_data.get('repeat_count', 1))
    
    def _on_delete_clicked(self):
        if self.on_delete:
            self.on_delete(self)
    
    def get_rule_data(self):
        """Получить данные правила"""
        return {
            'from': self.from_weapon.currentIndex() + 1,
            'to': self.to_weapon.currentIndex() + 1,
            'check_ammo': self.check_ammo.isChecked(),
            'repeat_count': self.repeat_count.value()
        }


class MacroSettingsWindow(QDialog):
    """Окно настройки макросов"""
    
    def __init__(self, parent=None, config_manager=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.current_preset = None
        self.presets = self._load_presets()
        self.rule_widgets = []
        
        self._init_ui()
        self._load_preset_list()
        
        logger.info("Окно настройки макросов открыто")
    
    def _init_ui(self):
        """Инициализация UI"""
        self.setWindowTitle("Настройка макросов")
        self.setGeometry(200, 200, 700, 500)
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e1e;
                color: #ffffff;
            }
        """)
        
        layout = QHBoxLayout()
        self.setLayout(layout)
        
        # Левая панель - список пресетов
        left_panel = self._create_presets_panel()
        layout.addWidget(left_panel)
        
        # Правая панель - правила свапа
        right_panel = self._create_rules_panel()
        layout.addWidget(right_panel)
    
    def _create_presets_panel(self) -> QWidget:
        """Панель со списком пресетов"""
        widget = QWidget()
        widget.setFixedWidth(200)
        layout = QVBoxLayout()
        widget.setLayout(layout)
        
        # Заголовок
        title = QLabel("Пресеты")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # Список пресетов
        self.presets_list = QListWidget()
        self.presets_list.setStyleSheet("""
            QListWidget {
                background-color: #2a2a2a;
                border: 1px solid #444;
                border-radius: 3px;
            }
            QListWidget::item {
                padding: 8px;
            }
            QListWidget::item:selected {
                background-color: #4CAF50;
            }
        """)
        self.presets_list.itemClicked.connect(self._on_preset_selected)
        layout.addWidget(self.presets_list)
        
        # Кнопки управления пресетами
        btn_layout = QVBoxLayout()
        
        add_btn = QPushButton("➕ Новый пресет")
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 8px;
                border: none;
                border-radius: 3px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #45a049; }
        """)
        add_btn.clicked.connect(self._on_add_preset)
        btn_layout.addWidget(add_btn)
        
        rename_btn = QPushButton("✏️ Переименовать")
        rename_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                padding: 8px;
                border: none;
                border-radius: 3px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #0b7dda; }
        """)
        rename_btn.clicked.connect(self._on_rename_preset)
        btn_layout.addWidget(rename_btn)
        
        delete_btn = QPushButton("🗑️ Удалить")
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                padding: 8px;
                border: none;
                border-radius: 3px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #da190b; }
        """)
        delete_btn.clicked.connect(self._on_delete_preset)
        btn_layout.addWidget(delete_btn)
        
        layout.addLayout(btn_layout)
        
        return widget
    
    def _create_rules_panel(self) -> QWidget:
        """Панель с правилами свапа"""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)
        
        # Заголовок
        title = QLabel("Правила свапа")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        self.preset_name_label = QLabel("Выберите пресет")
        self.preset_name_label.setStyleSheet("color: #888; font-size: 10px;")
        layout.addWidget(self.preset_name_label)
        
        # Контейнер для правил
        self.rules_container = QWidget()
        self.rules_layout = QVBoxLayout()
        self.rules_layout.setSpacing(5)
        self.rules_container.setLayout(self.rules_layout)
        layout.addWidget(self.rules_container)
        
        layout.addStretch()
        
        # Кнопка добавить правило
        add_rule_btn = QPushButton("➕ Добавить правило")
        add_rule_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 10px;
                border: none;
                border-radius: 3px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #45a049; }
        """)
        add_rule_btn.clicked.connect(self._on_add_rule)
        layout.addWidget(add_rule_btn)
        
        # Кнопки сохранить/закрыть
        bottom_layout = QHBoxLayout()
        
        save_btn = QPushButton("💾 Сохранить")
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                padding: 12px;
                border: none;
                border-radius: 3px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #0b7dda; }
        """)
        save_btn.clicked.connect(self._on_save)
        bottom_layout.addWidget(save_btn)
        
        close_btn = QPushButton("Закрыть")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #666;
                color: white;
                padding: 12px;
                border: none;
                border-radius: 3px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #555; }
        """)
        close_btn.clicked.connect(self.close)
        bottom_layout.addWidget(close_btn)
        
        layout.addLayout(bottom_layout)
        
        return widget
    
    def _load_presets(self) -> dict:
        """Загрузить пресеты из конфига"""
        presets = self.config_manager.get('macros.presets', {}) if self.config_manager else {}
        
        # Создать дефолтный пресет если нет
        if not presets:
            presets = {
                'Основной': {
                    'rules': []
                }
            }
        
        return presets
    
    def _save_presets(self):
        """Сохранить пресеты в конфиг"""
        if self.config_manager:
            self.config_manager.set('macros.presets', self.presets)
            self.config_manager.save_user_config()
    
    def _load_preset_list(self):
        """Загрузить список пресетов в UI"""
        self.presets_list.clear()
        for preset_name in self.presets.keys():
            self.presets_list.addItem(preset_name)
    
    def _on_preset_selected(self, item):
        """Выбран пресет"""
        preset_name = item.text()
        self.current_preset = preset_name
        self.preset_name_label.setText(f"Пресет: {preset_name}")
        self._load_rules(preset_name)
    
    def _load_rules(self, preset_name: str):
        """Загрузить правила пресета"""
        # Очистить текущие правила
        for widget in self.rule_widgets:
            widget.deleteLater()
        self.rule_widgets.clear()
        
        # Загрузить правила из пресета
        if preset_name in self.presets:
            rules = self.presets[preset_name].get('rules', [])
            for rule_data in rules:
                self._add_rule_widget(rule_data)
    
    def _add_rule_widget(self, rule_data=None):
        """Добавить виджет правила"""
        rule_widget = SwapRule(rule_data, on_delete=self._on_delete_rule)
        self.rules_layout.addWidget(rule_widget)
        self.rule_widgets.append(rule_widget)
    
    def _on_add_rule(self):
        """Добавить новое правило"""
        if not self.current_preset:
            QMessageBox.warning(self, "Ошибка", "Сначала выберите пресет!")
            return
        
        self._add_rule_widget()
    
    def _on_delete_rule(self, rule_widget):
        """Удалить правило"""
        self.rules_layout.removeWidget(rule_widget)
        self.rule_widgets.remove(rule_widget)
        rule_widget.deleteLater()
    
    def _on_add_preset(self):
        """Добавить новый пресет"""
        from PyQt6.QtWidgets import QInputDialog
        
        name, ok = QInputDialog.getText(self, "Новый пресет", "Название пресета:")
        if ok and name:
            if name in self.presets:
                QMessageBox.warning(self, "Ошибка", "Пресет с таким именем уже существует!")
                return
            
            self.presets[name] = {'rules': []}
            self._load_preset_list()
            logger.info(f"Создан новый пресет: {name}")
    
    def _on_rename_preset(self):
        """Переименовать пресет"""
        if not self.current_preset:
            QMessageBox.warning(self, "Ошибка", "Сначала выберите пресет!")
            return
        
        from PyQt6.QtWidgets import QInputDialog
        
        new_name, ok = QInputDialog.getText(
            self, "Переименовать", "Новое название:", 
            text=self.current_preset
        )
        
        if ok and new_name and new_name != self.current_preset:
            if new_name in self.presets:
                QMessageBox.warning(self, "Ошибка", "Пресет с таким именем уже существует!")
                return
            
            self.presets[new_name] = self.presets.pop(self.current_preset)
            self.current_preset = new_name
            self._load_preset_list()
            logger.info(f"Пресет переименован: {new_name}")
    
    def _on_delete_preset(self):
        """Удалить пресет"""
        if not self.current_preset:
            QMessageBox.warning(self, "Ошибка", "Сначала выберите пресет!")
            return
        
        reply = QMessageBox.question(
            self, "Подтверждение",
            f"Удалить пресет '{self.current_preset}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            del self.presets[self.current_preset]
            self.current_preset = None
            self._load_preset_list()
            
            # Очистить правила
            for widget in self.rule_widgets:
                widget.deleteLater()
            self.rule_widgets.clear()
            
            self.preset_name_label.setText("Выберите пресет")
            logger.info("Пресет удалён")
    
    def _on_save(self):
        """Сохранить изменения"""
        if not self.current_preset:
            QMessageBox.warning(self, "Ошибка", "Сначала выберите пресет!")
            return
        
        # Собрать все правила
        rules = []
        for rule_widget in self.rule_widgets:
            rules.append(rule_widget.get_rule_data())
        
        # Сохранить в пресет
        self.presets[self.current_preset]['rules'] = rules
        self._save_presets()
        
        QMessageBox.information(self, "Успех", "Пресет сохранён!")
        logger.info(f"Пресет '{self.current_preset}' сохранён с {len(rules)} правилами")

