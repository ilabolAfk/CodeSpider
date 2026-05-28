import sys
import ast
import networkx as nx
import matplotlib.pyplot as plt
from pathlib import Path
from tkinter import filedialog, Tk
import hashlib
import os
import json
from datetime import datetime

# Импорты для PyQt5
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

class CodeSpiderGUI(QMainWindow):
    """Анализатор зависимостей кода"""
    
    def __init__(self):
        super().__init__()
        self.graph = nx.DiGraph()
        self.target_file = None
        self.setup_ui()
        self.check_protection()
    
    def check_protection(self):
        """Проверяет защиту от слива (только в PRO/ULTIMATE версиях)"""
        try:
            # Проверяем наличие скрытой метки (встроена при сборке)
            import protection
            self.buyer_id = protection.BUYER_ID
            self.watermark = protection.WATERMARK
            self.is_protected = True
        except:
            self.is_protected = False
            self.buyer_id = None
    
    def setup_ui(self):
        """Настройка интерфейса"""
        self.setWindowTitle("Code Spider - Анализатор кода")
        self.setGeometry(100, 100, 1200, 800)
        
        # Стили
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
            }
            QLabel {
                color: #d4d4d4;
                font-family: 'Consolas', monospace;
            }
            QPushButton {
                background-color: #0e639c;
                color: white;
                border: none;
                padding: 8px;
                font-size: 12px;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #1177bb;
            }
            QPushButton:disabled {
                background-color: #555555;
            }
            QPushButton#buyBtn {
                background-color: #ff3366;
                color: white;
                border: 2px solid #ff6600;
                font-weight: bold;
            }
            QPushButton#buyBtn:hover {
                background-color: #ff6600;
            }
            QTextEdit {
                background-color: #252526;
                color: #d4d4d4;
                border: 1px solid #3e3e42;
                font-family: 'Consolas', monospace;
                font-size: 11px;
            }
            QListWidget {
                background-color: #252526;
                color: #d4d4d4;
                border: 1px solid #3e3e42;
                font-family: 'Consolas', monospace;
            }
            QListWidget::item:hover {
                background-color: #2a2d2e;
            }
            QListWidget::item:selected {
                background-color: #0e639c;
            }
        """)
        
        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Главный layout
        main_layout = QHBoxLayout(central_widget)
        
        # Левая панель
        left_panel = QWidget()
        left_panel.setMaximumWidth(350)
        left_layout = QVBoxLayout(left_panel)
        
        # Заголовок
        title = QLabel("CODE SPIDER")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #0e639c;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_layout.addWidget(title)
        
        left_layout.addSpacing(20)
        
        # Кнопка выбора файла
        self.file_btn = QPushButton("📂 Выбрать файл")
        self.file_btn.clicked.connect(self.select_file)
        left_layout.addWidget(self.file_btn)
        
        # Информация о файле
        self.file_info = QLabel("Файл не выбран")
        self.file_info.setWordWrap(True)
        self.file_info.setStyleSheet("padding: 10px; background-color: #252526; border-radius: 4px;")
        left_layout.addWidget(self.file_info)
        
        left_layout.addSpacing(20)
        
        # Кнопка анализа
        self.analyze_btn = QPushButton("🔍 Запустить анализ")
        self.analyze_btn.clicked.connect(self.analyze_code)
        self.analyze_btn.setEnabled(False)
        left_layout.addWidget(self.analyze_btn)
        
        left_layout.addSpacing(10)
        
        # Кнопка покупки PRO (только в FREE версии)
        self.buy_btn = QPushButton("💎 КУПИТЬ PRO ВЕРСИЮ (СНЯТЬ ЛИМИТЫ)")
        self.buy_btn.setObjectName("buyBtn")
        self.buy_btn.clicked.connect(self.buy_pro)
        left_layout.addWidget(self.buy_btn)
        
        left_layout.addSpacing(20)
        
        # Статистика
        stats_label = QLabel("Статистика")
        stats_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #0e639c;")
        left_layout.addWidget(stats_label)
        
        self.stats_text = QTextEdit()
        self.stats_text.setMaximumHeight(200)
        self.stats_text.setReadOnly(True)
        left_layout.addWidget(self.stats_text)
        
        left_layout.addSpacing(20)
        
        # Список функций
        func_label = QLabel("Найденные функции")
        func_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #0e639c;")
        left_layout.addWidget(func_label)
        
        self.func_list = QListWidget()
        left_layout.addWidget(self.func_list)
        
        left_layout.addStretch()
        
        # Правая панель с графиком
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        self.figure = Figure(figsize=(8, 6), facecolor='#1e1e1e')
        self.canvas = FigureCanvas(self.figure)
        right_layout.addWidget(self.canvas)
        
        # Статус бар
        self.status_label = QLabel("Готов к работе")
        self.status_label.setStyleSheet("padding: 5px; background-color: #252526; border-radius: 4px;")
        right_layout.addWidget(self.status_label)
        
        # Добавляем панели
        main_layout.addWidget(left_panel)
        main_layout.addWidget(right_panel, stretch=1)
    
    def buy_pro(self):
        """Открывает окно с контактами для покупки"""
        msg = QMessageBox()
        msg.setWindowTitle("💎 Купить PRO версию")
        msg.setText("""
<b>CODE SPIDER PRO</b><br/><br/>
Снимите все ограничения!<br/><br/>
<b>PRO версия включает:</b><br/>
• Анализ файлов до 200 MB<br/>
• 20,000+ символов<br/>
• 2,000+ импортов<br/>
• Экспорт результатов<br/>
• Приоритетная поддержка<br/>
• Без водяных знаков<br/><br/>
<b>💰 Цена: $9 (одноразово)</b><br/><br/>
<b>Свяжитесь со мной для покупки:</b><br/>
📧 Email: ads-on-mail@ro.ru<br/>
        """)
        msg.setInformativeText("После оплаты вы получите PRO версию без ограничений!")
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.setIcon(QMessageBox.Icon.Information)
        
        # Добавляем кнопку копирования контактов
        copy_btn = msg.addButton("📋 Скопировать контакты", QMessageBox.ButtonRole.ActionRole)
        
        if msg.exec() == QMessageBox.StandardButton.Ok:
            pass
        elif msg.clickedButton() == copy_btn:
            clipboard = QApplication.clipboard()
            clipboard.setText("Telegram: @code_spider_bot\nEmail: codespider@proton.me")
            QMessageBox.information(self, "Готово", "Контакты скопированы в буфер обмена!")
    
    def select_file(self):
        """Выбор файла через диалог"""
        root = Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        
        file_path = filedialog.askopenfilename(
            title="Выберите Python файл",
            filetypes=[("Python files", "*.py"), ("All files", "*.*")]
        )
        
        root.destroy()
        
        if file_path:
            self.target_file = file_path
            self.file_info.setText(f"Файл: {Path(file_path).name}\nПуть: {file_path}")
            self.analyze_btn.setEnabled(True)
            self.status_label.setText(f"Выбран файл: {Path(file_path).name}")
    
    def analyze_code(self):
        """Анализ кода"""
        if not self.target_file:
            return
        
        self.analyze_btn.setEnabled(False)
        self.status_label.setText("Анализируем код...")
        
        QTimer.singleShot(100, self.perform_analysis)
    
    def perform_analysis(self):
        """Реальный анализ"""
        try:
            with open(self.target_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            functions = set()
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    functions.add(node.name)
            
            self.graph.clear()
            calls = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                    if node.func.id in functions:
                        parent = None
                        for p in ast.walk(tree):
                            if isinstance(p, (ast.FunctionDef, ast.AsyncFunctionDef)):
                                if hasattr(node, 'lineno') and hasattr(p, 'lineno'):
                                    if p.lineno < node.lineno:
                                        parent = p.name
                        if parent:
                            self.graph.add_edge(parent, node.func.id)
                            calls.append((parent, node.func.id))
            
            stats_text = f"""
📊 Результаты анализа:

📁 Файл: {Path(self.target_file).name}
🔷 Функций найдено: {len(functions)}
🔗 Вызовов обнаружено: {len(self.graph.edges)}
📈 Индекс сложности: {len(self.graph.edges) / max(1, len(functions)):.2f}
            """
            
            if len(self.graph.nodes) > 0:
                most_connected = max(self.graph.nodes, key=lambda n: self.graph.degree(n))
                stats_text += f"\n⭐ Наиболее связанная функция: {most_connected}"
            
            self.stats_text.setText(stats_text)
            
            self.func_list.clear()
            for func in sorted(functions):
                self.func_list.addItem(func)
            
            self.draw_graph()
            
            self.status_label.setText(f"Анализ завершен. Найдено {len(functions)} функций")
            
        except Exception as e:
            self.status_label.setText(f"Ошибка: {str(e)}")
        
        self.analyze_btn.setEnabled(True)
    
    def draw_graph(self):
        """Рисует граф вызовов"""
        self.figure.clear()
        
        if len(self.graph.nodes) == 0:
            ax = self.figure.add_subplot(111)
            ax.set_facecolor('#1e1e1e')
            ax.text(0.5, 0.5, 'Нет связей между функциями', 
                   ha='center', va='center', color='white', fontsize=14)
            ax.axis('off')
            self.canvas.draw()
            return
        
        ax = self.figure.add_subplot(111)
        ax.set_facecolor('#1e1e1e')
        
        pos = nx.spring_layout(self.graph, k=2, iterations=50)
        
        nx.draw_networkx_nodes(self.graph, pos, ax=ax,
                              node_color='#0e639c',
                              node_size=1000,
                              alpha=0.9)
        
        nx.draw_networkx_edges(self.graph, pos, ax=ax,
                              edge_color='#d4d4d4',
                              width=2,
                              alpha=0.6,
                              arrows=True,
                              arrowsize=20)
        
        nx.draw_networkx_labels(self.graph, pos, ax=ax,
                               font_size=10,
                               font_weight='bold',
                               font_color='white')
        
        ax.set_title(f"Граф вызовов функций\n{Path(self.target_file).name}", 
                    color='white', fontsize=12)
        ax.axis('off')
        
        self.canvas.draw()

def main():
    app = QApplication(sys.argv)
    window = CodeSpiderGUI()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()