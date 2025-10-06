"""
Окно настройки макросов - пресеты с правилами свапа
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QListWidget, QComboBox, QLineEdit, QGroupBox,
                             QMessageBox, QListWidgetItem, QWidget, QFrame, QCheckBox, QSpinBox)
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
        self.check_ammo = QCheckBox("Если есть патроны")
        self.check_ammo.setChecked(True)
        self.check_ammo.setStyleSheet("color: #888; font-size: 10px;")
        self.check_ammo.toggled.connect(self._on_check_ammo_toggled)
        layout.addWidget(self.check_ammo)
        
        # Fallback оружие (показывается только если check_ammo включено)
        self.fallback_label = QLabel("→ иначе:")
        self.fallback_label.setStyleSheet("color: #888; font-size: 9px;")
        layout.addWidget(self.fallback_label)
        
        self.fallback_weapon = QComboBox()
        self.fallback_weapon.addItems([
            "—",  # Нет fallback
            "1. Основное",
            "2. Пистолет",
            "3. Холодное",
            "4. Специальное",
            "5. Снайперка",
            "6. Тяжёлое"
        ])
        self.fallback_weapon.setStyleSheet("font-size: 9px; padding: 2px;")
        self.fallback_weapon.setToolTip("Запасное оружие, если в целевом нет патронов")
        self.fallback_weapon.setFixedWidth(100)
        layout.addWidget(self.fallback_weapon)
        
        # Галочка: Quick Switch (отмена анимации через нож)
        self.quick_switch = QCheckBox("🔪 Quick Switch")
        self.quick_switch.setChecked(False)
        self.quick_switch.setStyleSheet("color: #4CAF50; font-size: 10px; font-weight: bold;")
        self.quick_switch.setToolTip("Переключение через нож для отмены анимации доставания оружия")
        layout.addWidget(self.quick_switch)
        
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
            self.quick_switch.setChecked(rule_data.get('quick_switch', False))
            self.repeat_count.setValue(rule_data.get('repeat_count', 1))
            
            # Fallback оружие (0 = нет fallback)
            fallback_to = rule_data.get('fallback_to', 0)
            self.fallback_weapon.setCurrentIndex(fallback_to)
        
        # Обновить видимость fallback при инициализации
        self._on_check_ammo_toggled(self.check_ammo.isChecked())
    
    def _on_delete_clicked(self):
        if self.on_delete:
            self.on_delete(self)
    
    def _on_check_ammo_toggled(self, checked):
        """Показать/скрыть fallback в зависимости от check_ammo"""
        self.fallback_label.setVisible(checked)
        self.fallback_weapon.setVisible(checked)
    
    def get_rule_data(self):
        """Получить данные правила"""
        rule = {
            'from': self.from_weapon.currentIndex() + 1,
            'to': self.to_weapon.currentIndex() + 1,
            'check_ammo': self.check_ammo.isChecked(),
            'quick_switch': self.quick_switch.isChecked(),
            'repeat_count': self.repeat_count.value()
        }
        
        # Добавить fallback только если он выбран (не "—")
        fallback_idx = self.fallback_weapon.currentIndex()
        if fallback_idx > 0:  # 0 = "—" (нет fallback)
            rule['fallback_to'] = fallback_idx
        
        return rule


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
        self._load_quick_switch_settings()
        
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
    
    def _create_quick_switch_panel(self) -> QGroupBox:
        """Панель глобальных настроек Quick Switch"""
        group = QGroupBox("🔪 Quick Switch - глобальные настройки")
        group.setStyleSheet("""
            QGroupBox {
                background-color: #2a2a2a;
                border: 2px solid #4CAF50;
                border-radius: 5px;
                margin-top: 10px;
                padding: 10px;
                font-weight: bold;
            }
            QGroupBox::title {
                color: #4CAF50;
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        
        layout = QVBoxLayout()
        group.setLayout(layout)
        
        # Описание
        desc = QLabel("💡 Настройки применяются ко всем правилам с галочкой \"🔪 Quick Switch\"")
        desc.setStyleSheet("color: #888; font-size: 9px; font-style: italic; margin-bottom: 5px;")
        desc.setWordWrap(True)
        layout.addWidget(desc)
        
        # Настройки
        settings_layout = QHBoxLayout()
        
        # Слот ножа
        settings_layout.addWidget(QLabel("Слот ножа:"))
        self.qs_knife_slot = QSpinBox()
        self.qs_knife_slot.setRange(1, 6)
        self.qs_knife_slot.setValue(3)
        self.qs_knife_slot.setFixedWidth(60)
        self.qs_knife_slot.setStyleSheet("padding: 3px; background-color: #1e1e1e; border: 1px solid #444; border-radius: 2px;")
        self.qs_knife_slot.setToolTip("На каком слоте находится нож (обычно 3)")
        settings_layout.addWidget(self.qs_knife_slot)
        
        settings_layout.addSpacing(20)
        
        # Задержка
        settings_layout.addWidget(QLabel("Задержка (мс):"))
        self.qs_delay = QSpinBox()
        self.qs_delay.setRange(30, 1000)
        # Значение устанавливается в _load_quick_switch_settings() из конфига
        self.qs_delay.setSingleStep(10)
        self.qs_delay.setFixedWidth(80)
        self.qs_delay.setStyleSheet("padding: 3px; background-color: #1e1e1e; border: 1px solid #444; border-radius: 2px;")
        self.qs_delay.setToolTip("Время удержания ножа перед переключением на целевое оружие (50-100 мс оптимально, до 1000 мс если нужно)")
        settings_layout.addWidget(self.qs_delay)
        
        settings_layout.addStretch()
        layout.addLayout(settings_layout)
        
        return group
    
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
        
        # Блок Quick Switch
        qs_group = self._create_quick_switch_panel()
        layout.addWidget(qs_group)
        
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
    
    def _load_quick_switch_settings(self):
        """Загрузить настройки Quick Switch из конфига"""
        if self.config_manager:
            # Читаем из конфига (fallback на дефолтные значения из default_config.yaml)
            knife_slot = self.config_manager.get('macros.knife_slot')
            delay_ms = self.config_manager.get('macros.quick_switch_delay')
            
            # Устанавливаем значения в GUI (если None, оставляем как есть)
            if knife_slot is not None:
                self.qs_knife_slot.setValue(knife_slot)
            if delay_ms is not None:
                self.qs_delay.setValue(delay_ms)
    
    def _save_quick_switch_settings(self):
        """Сохранить настройки Quick Switch в конфиг"""
        if self.config_manager:
            self.config_manager.set('macros.knife_slot', self.qs_knife_slot.value())
            self.config_manager.set('macros.quick_switch_delay', self.qs_delay.value())
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
        # Сохранить Quick Switch настройки (всегда)
        self._save_quick_switch_settings()
        
        # Сохранить правила текущего пресета (если выбран)
        if self.current_preset:
            # Собрать все правила
            rules = []
            for rule_widget in self.rule_widgets:
                rules.append(rule_widget.get_rule_data())
            
            # Сохранить в пресет
            self.presets[self.current_preset]['rules'] = rules
            self._save_presets()
            
            # Подсчитываем правила с Quick Switch
            qs_count = sum(1 for r in rules if r.get('quick_switch', False))
            msg = f"Пресет '{self.current_preset}' сохранён ({len(rules)} правил"
            if qs_count > 0:
                msg += f", {qs_count} с Quick Switch"
            msg += ")!"
            
            QMessageBox.information(self, "Успех", msg)
            logger.info(f"Пресет '{self.current_preset}' сохранён: {len(rules)} правил, {qs_count} с Quick Switch")
        else:
            QMessageBox.information(self, "Успех", "Глобальные настройки Quick Switch сохранены!")
            logger.info("Глобальные настройки Quick Switch сохранены")

