import sys
import json
import os
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                             QCheckBox, QLabel, QTabWidget, QListWidget, QListWidgetItem,
                             QPushButton, QDialog, QTextEdit, QLineEdit, QDateEdit, QMessageBox)
from PyQt6.QtCore import Qt, QDate

DATA_FILE = "tasks.json"

class MemoDialog(QDialog):
    """세부 메모를 수정하고 저장하는 팝업 창"""
    def __init__(self, task_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("세부 메모")
        self.resize(300, 250)
        self.task_data = task_data

        layout = QVBoxLayout(self)
        
        self.memo_edit = QTextEdit()
        self.memo_edit.setText(self.task_data.get("memo", ""))
        layout.addWidget(self.memo_edit)

        save_btn = QPushButton("저장")
        save_btn.clicked.connect(self.save_memo)
        layout.addWidget(save_btn)

    def save_memo(self):
        self.task_data["memo"] = self.memo_edit.toPlainText()
        self.accept()

class TaskWidget(QWidget):
    """리스트에 들어갈 개별 할 일 위젯"""
    def __init__(self, task_data, main_window):
        super().__init__()
        self.task_data = task_data
        self.main_window = main_window
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # 체크박스
        self.checkbox = QCheckBox()
        self.checkbox.setChecked(self.task_data["is_completed"])
        self.checkbox.toggled.connect(self.on_checked)
        layout.addWidget(self.checkbox)

        # 할 일 제목 (클릭 시 메모 창 열림)
        self.title_label = QLabel(self.task_data["title"])
        self.title_label.mousePressEvent = self.open_memo
        self.title_label.setStyleSheet("color: gray;" if self.task_data["is_completed"] else "color: black;")
        layout.addWidget(self.title_label, stretch=1)

        # D-Day 계산 및 표시
        self.dday_label = QLabel(self.calculate_dday(self.task_data["deadline"]))
        self.dday_label.setStyleSheet("color: red; font-weight: bold;")
        layout.addWidget(self.dday_label)

    def calculate_dday(self, deadline_str):
        deadline = datetime.strptime(deadline_str, "%Y-%m-%d").date()
        today = datetime.now().date()
        delta = (deadline - today).days
        
        if delta > 0:
            return f"D-{delta}"
        elif delta == 0:
            return "D-DAY"
        else:
            return f"D+{abs(delta)}"

    def on_checked(self, checked):
        self.task_data["is_completed"] = checked
        self.main_window.save_data()
        self.main_window.refresh_lists()

    def open_memo(self, event):
        dialog = MemoDialog(self.task_data, self)
        if dialog.exec():
            self.main_window.save_data()

class ChecklistApp(QWidget):
    """메인 애플리케이션 창"""
    def __init__(self):
        super().__init__()
        self.tasks = []
        # jsy03137님의 환경에 맞춘 기본 창 설정
        self.init_ui()
        self.load_data()
        self.refresh_lists()

    def init_ui(self):
        # 바탕화면 고정 및 테두리 없는 창 설정 (리소스 최소화)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnBottomHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(350, 500)
        
        # 메인 레이아웃 (반투명 배경 적용)
        self.main_layout = QVBoxLayout(self)
        
        bg_widget = QWidget()
        bg_widget.setStyleSheet("background-color: rgba(255, 255, 255, 230); border-radius: 10px;")
        bg_layout = QVBoxLayout(bg_widget)
        self.main_layout.addWidget(bg_widget)

        # 탭 위젯 (미완료 / 완료 분리)
        self.tabs = QTabWidget()
        self.todo_list = QListWidget()
        self.done_list = QListWidget()
        self.tabs.addTab(self.todo_list, "진행 중")
        self.tabs.addTab(self.done_list, "완료된 일")
        bg_layout.addWidget(self.tabs)

        # 새 할 일 추가 영역
        add_layout = QHBoxLayout()
        self.new_task_input = QLineEdit()
        self.new_task_input.setPlaceholderText("새 할 일 입력...")
        
        self.date_picker = QDateEdit()
        self.date_picker.setDate(QDate.currentDate())
        self.date_picker.setCalendarPopup(True)
        
        add_btn = QPushButton("추가")
        add_btn.clicked.connect(self.add_task)
        
        add_layout.addWidget(self.new_task_input)
        add_layout.addWidget(self.date_picker)
        add_layout.addWidget(add_btn)
        bg_layout.addLayout(add_layout)

        # 앱 종료 버튼 (테두리가 없으므로 필수)
        exit_btn = QPushButton("앱 종료")
        exit_btn.clicked.connect(self.close)
        bg_layout.addWidget(exit_btn)

    def load_data(self):
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                self.tasks = json.load(f)
        else:
            self.tasks = []

    def save_data(self):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(self.tasks, f, ensure_ascii=False, indent=4)

    def add_task(self):
        title = self.new_task_input.text().strip()
        if not title:
            return
            
        deadline = self.date_picker.date().toString("yyyy-MM-dd")
        new_task = {
            "title": title,
            "deadline": deadline,
            "memo": "",
            "is_completed": False
        }
        self.tasks.append(new_task)
        self.new_task_input.clear()
        self.save_data()
        self.refresh_lists()

    def refresh_lists(self):
        self.todo_list.clear()
        self.done_list.clear()

        for task in self.tasks:
            item = QListWidgetItem()
            widget = TaskWidget(task, self)
            item.setSizeHint(widget.sizeHint())
            
            if task["is_completed"]:
                self.done_list.addItem(item)
                self.done_list.setItemWidget(item, widget)
            else:
                self.todo_list.addItem(item)
                self.todo_list.setItemWidget(item, widget)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ChecklistApp()
    window.show()
    sys.exit(app.exec())