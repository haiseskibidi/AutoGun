"""
Окно настройки клавиш для смены оружия
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFrame, QLineEdit, QMessageBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QKeyEvent
from loguru import logger


class KeyBindingEdit(QLineEdit):
    """Поле ввода для клавиши (перехватывает нажатия)"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("""
            QLineEdit {
                background-color: #2a2a2a;
                border: 2px solid #444;
                border-radius: 3px;
                padding: 5px;
                color: #4CAF50;
                font-weight: bold;
                font-size: 12px;
            }
            QLineEdit:focus {
                border: 2px solid #4CAF50;
            }
        """)
        self.setPlaceholderText("Нажмите клавишу...")
        self.setFixedWidth(100)
    
    def keyPressEvent(self, event: QKeyEvent):
        """Перехватываем нажатие клавиши"""
        key = event.key()
        
        # Игнорируем служебные клавиши
        if key in (Qt.Key.Key_Escape, Qt.Key.Key_Tab, Qt.Key.Key_Backtab):
            super().keyPressEvent(event)
            return
        
        # Получаем текстовое представление клавиши
        key_text = event.text()
        
        # Для специальных клавиш используем их имена
        if not key_text or key_text.isprintable() == False:
            key_name = {
                Qt.Key.Key_Space: 'space',
                Qt.Key.Key_Return: 'enter',
                Qt.Key.Key_Backspace: 'backspace',
                Qt.Key.Key_Delete: 'delete',
                Qt.Key.Key_Insert: 'insert',
                Qt.Key.Key_Home: 'home',
                Qt.Key.Key_End: 'end',
                Qt.Key.Key_PageUp: 'page up',
                Qt.Key.Key_PageDown: 'page down',
                Qt.Key.Key_Up: 'up',
                Qt.Key.Key_Down: 'down',
                Qt.Key.Key_Left: 'left',
                Qt.Key.Key_Right: 'right',
                Qt.Key.Key_F1: 'f1',
                Qt.Key.Key_F2: 'f2',
                Qt.Key.Key_F3: 'f3',
                Qt.Key.Key_F4: 'f4',
                Qt.Key.Key_F5: 'f5',
                Qt.Key.Key_F6: 'f6',
                Qt.Key.Key_F7: 'f7',
                Qt.Key.Key_F8: 'f8',
                Qt.Key.Key_F9: 'f9',
                Qt.Key.Key_F10: 'f10',
                Qt.Key.Key_F11: 'f11',
                Qt.Key.Key_F12: 'f12',
                Qt.Key.Key_Shift: 'shift',
                Qt.Key.Key_Control: 'ctrl',
                Qt.Key.Key_Alt: 'alt',
            }.get(key, None)
            
            if key_name:
                key_text = key_name
            else:
                return
        
        # Устанавливаем текст клавиши
        self.setText(key_text.lower())
        logger.debug(f"Установлена клавиша: {key_text}")


class KeybindingsWindow(QDialog):
    """Окно настройки клавиш смены оружия"""
    
    def __init__(self, parent, config_manager):
        super().__init__(parent)
        self.config = config_manager
        self.key_edits = {}  # {slot_id: KeyBindingEdit}
        
        self._init_ui()
        self._load_keybindings()
        
        logger.info("Окно настройки клавиш открыто")
    
    def _init_ui(self):
        """Инициализация UI"""
        self.setWindowTitle("⌨️ Настройка клавиш оружия")
        self.setModal(True)
        self.setFixedWidth(400)
        
        layout = QVBoxLayout()
        layout.setSpacing(10)
        self.setLayout(layout)
        
        # Заголовок
        title = QLabel("⌨️ Клавиши смены оружия")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #4CAF50; padding: 10px;")
        layout.addWidget(title)
        
        # Инструкция
        instruction = QLabel("Кликните на поле и нажмите нужную клавишу")
        instruction.setStyleSheet("color: #888; font-size: 10px;")
        instruction.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(instruction)
        
        # Фрейм с клавишами
        keys_frame = QFrame()
        keys_frame.setStyleSheet("background-color: #252525; border-radius: 5px;")
        keys_layout = QVBoxLayout()
        keys_layout.setSpacing(8)
        keys_layout.setContentsMargins(15, 15, 15, 15)
        keys_frame.setLayout(keys_layout)
        
        # Слоты оружия
        weapons = [
            (1, "1. Основное", "#4CAF50"),
            (2, "2. Пистолет", "#2196F3"),
            (3, "3. Холодное (нож)", "#FF9800"),
            (4, "4. Специальное", "#9C27B0"),
            (5, "5. Снайперка", "#00BCD4"),
            (6, "6. Тяжёлое", "#F44336")
        ]
        
        for slot_id, name, color in weapons:
            row = QHBoxLayout()
            row.setSpacing(10)
            
            # Название слота
            label = QLabel(name)
            label.setStyleSheet(f"color: {color}; font-weight: bold;")
            label.setFixedWidth(150)
            row.addWidget(label)
            
            # Поле ввода клавиши
            key_edit = KeyBindingEdit()
            self.key_edits[slot_id] = key_edit
            row.addWidget(key_edit)
            
            row.addStretch()
            
            keys_layout.addLayout(row)
        
        layout.addWidget(keys_frame)
        
        # Кнопки внизу
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)
        
        # Кнопка сброса
        reset_button = QPushButton("🔄 Сбросить по умолчанию")
        reset_button.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                padding: 8px 15px;
                border: none;
                border-radius: 3px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #F57C00; }
        """)
        reset_button.clicked.connect(self._reset_to_defaults)
        buttons_layout.addWidget(reset_button)
        
        buttons_layout.addStretch()
        
        # Кнопка отмены
        cancel_button = QPushButton("✖ Отмена")
        cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #666;
                color: white;
                padding: 8px 15px;
                border: none;
                border-radius: 3px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #555; }
        """)
        cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_button)
        
        # Кнопка сохранения
        save_button = QPushButton("✔ Сохранить")
        save_button.setStyleSheet("""
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
        save_button.clicked.connect(self._save_keybindings)
        buttons_layout.addWidget(save_button)
        
        layout.addLayout(buttons_layout)
        
        # Тёмная тема
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e1e;
                color: #ffffff;
            }
        """)
    
    def _load_keybindings(self):
        """Загрузить текущие клавиши из конфига"""
        for slot_id in range(1, 7):
            key = self.config.get(f'keybindings.weapon_slot_{slot_id}', str(slot_id))
            self.key_edits[slot_id].setText(key)
            logger.debug(f"Загружена клавиша для слота {slot_id}: {key}")
    
    def _save_keybindings(self):
        """Сохранить клавиши в конфиг"""
        # Проверяем на дубликаты
        keys = {}
        for slot_id, edit in self.key_edits.items():
            key = edit.text().strip()
            if not key:
                QMessageBox.warning(self, "Ошибка", f"Не указана клавиша для слота {slot_id}!")
                return
            
            # Проверка дубликатов
            if key in keys.values():
                QMessageBox.warning(self, "Ошибка", f"Клавиша '{key}' уже используется!")
                return
            
            keys[slot_id] = key
        
        # Сохраняем в конфиг
        for slot_id, key in keys.items():
            self.config.set(f'keybindings.weapon_slot_{slot_id}', key)
            logger.info(f"Слот {slot_id}: клавиша установлена на '{key}'")
        
        # Сохраняем конфиг в файл
        self.config.save_user_config()
        
        QMessageBox.information(self, "Успех", "Клавиши сохранены!")
        self.accept()
    
    def _reset_to_defaults(self):
        """Сбросить клавиши к значениям по умолчанию"""
        reply = QMessageBox.question(
            self,
            "Подтверждение",
            "Вернуть клавиши к значениям по умолчанию (1-6)?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            for slot_id in range(1, 7):
                self.key_edits[slot_id].setText(str(slot_id))
            logger.info("Клавиши сброшены к значениям по умолчанию")

