import sys
import json
import os
from datetime import datetime, timedelta, timezone
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                             QCheckBox, QLabel, QListWidget, QListWidgetItem,
                             QPushButton, QDialog, QTextEdit, QLineEdit, QDateEdit, 
                             QColorDialog, QSizeGrip, QCalendarWidget, QComboBox, QMessageBox)
from PyQt6.QtCore import Qt, QDate, QPoint, QTimer
from PyQt6.QtGui import QFont

# Google Calendar API imports
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATA_FILE = os.path.join(BASE_DIR, "tasks.json")
SETTINGS_FILE = os.path.join(BASE_DIR, "settings.json")
CREDENTIALS_FILE = os.path.join(BASE_DIR, "credentials.json")
TOKEN_FILE = os.path.join(BASE_DIR, "token.json")

SCOPES = ['https://www.googleapis.com/auth/calendar']

CATEGORY_COLORS = {
    "과제": "#D9EAF7",  
    "약속": "#D4EFDF",  
    "미팅": "#E8DAEF",  
    "중요": "#FADBD8",  
}

CALENDAR_STYLE = """
    QCalendarWidget QAbstractItemView { background-color: white; color: black; selection-background-color: #d9534f; selection-color: white; }
"""

DIALOG_BUTTON_STYLE = """
    QPushButton { background-color: #f0f0f0; color: black; border: 1px solid #ccc; padding: 5px 15px; border-radius: 3px; }
    QPushButton:hover { background-color: #e0e0e0; }
"""

COMBO_STYLE = """
    QComboBox { background-color: white; color: black; border: 1px solid #ccc; padding: 2px 5px; border-radius: 3px; }
    QComboBox QAbstractItemView { background-color: white; color: black; selection-background-color: #d9534f; selection-color: white; }
"""

# ==========================================
# Google Calendar 매니저 클래스
# ==========================================
class GoogleCalendarManager:
    def __init__(self):
        self.creds = None
        self.service = None
        self.authenticate()

    def authenticate(self):
        try:
            if os.path.exists(TOKEN_FILE):
                self.creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
            if not self.creds or not self.creds.valid:
                if self.creds and self.creds.expired and self.creds.refresh_token:
                    self.creds.refresh(Request())
                else:
                    if not os.path.exists(CREDENTIALS_FILE):
                        print("credentials.json 파일이 없습니다. 구글 캘린더 연동이 비활성화됩니다.")
                        return
                    flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
                    self.creds = flow.run_local_server(port=0)
                with open(TOKEN_FILE, 'w') as token:
                    token.write(self.creds.to_json())
            
            self.service = build('calendar', 'v3', credentials=self.creds)
        except Exception as e:
            print(f"구글 캘린더 인증 오류: {e}")

    def get_upcoming_events(self, days=30):
        if not self.service: return []
        try:
            today_start = datetime.now().astimezone().replace(hour=0, minute=0, second=0, microsecond=0)
            time_min = today_start.astimezone(timezone.utc).isoformat().replace('+00:00', 'Z')
            
            events_result = self.service.events().list(
                calendarId='primary', timeMin=time_min,
                maxResults=200, singleEvents=True,
                orderBy='startTime').execute()
            return events_result.get('items', [])
        except HttpError as error:
            print(f"이벤트 가져오기 오류: {error}")
            return []

    def create_event(self, title, date_str, description=""):
        if not self.service: return None
        try:
            event = {
                'summary': title,
                'description': description,
                'start': {'date': date_str, 'timeZone': 'Asia/Seoul'},
                'end': {'date': date_str, 'timeZone': 'Asia/Seoul'},
            }
            event = self.service.events().insert(calendarId='primary', body=event).execute()
            return event.get('id')
        except HttpError as error:
            print(f"이벤트 생성 오류: {error}")
            return None

# ==========================================
# UI 클래스들
# ==========================================
class DropdownCalendarWidget(QCalendarWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setNavigationBarVisible(False)

        self.nav_bar = QWidget(self)
        self.nav_bar.setStyleSheet("background-color: #f0f0f0; border-radius: 3px;")
        nav_layout = QHBoxLayout(self.nav_bar)
        nav_layout.setContentsMargins(5, 5, 5, 5)

        self.prev_btn = QPushButton("◀")
        self.next_btn = QPushButton("▶")
        for btn in [self.prev_btn, self.next_btn]:
            btn.setFixedSize(25, 25)
            btn.setStyleSheet("QPushButton { border: none; font-weight: bold; background-color: transparent; color: black; } QPushButton:hover { background-color: #e0e0e0; border-radius: 3px; }")

        self.year_combo = QComboBox()
        self.year_combo.addItems([str(y) for y in range(2000, 2051)])
        self.year_combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
        self.year_combo.setMinimumWidth(70)
        self.year_combo.setStyleSheet(COMBO_STYLE)

        self.month_combo = QComboBox()
        self.month_combo.addItems([f"{m}월" for m in range(1, 13)])
        self.month_combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
        self.month_combo.setMinimumWidth(60)
        self.month_combo.setStyleSheet(COMBO_STYLE)

        nav_layout.addWidget(self.prev_btn)
        nav_layout.addStretch()
        nav_layout.addWidget(self.year_combo)
        nav_layout.addWidget(self.month_combo)
        nav_layout.addStretch()
        nav_layout.addWidget(self.next_btn)

        layout = self.layout()
        if layout:
            layout.insertWidget(0, self.nav_bar)

        self.prev_btn.clicked.connect(self.showPreviousMonth)
        self.next_btn.clicked.connect(self.showNextMonth)
        self.year_combo.currentTextChanged.connect(self.sync_date)
        self.month_combo.currentIndexChanged.connect(self.sync_date)
        self.currentPageChanged.connect(self.update_combos)

        self.update_combos(self.yearShown(), self.monthShown())

    def sync_date(self):
        year = int(self.year_combo.currentText())
        month = self.month_combo.currentIndex() + 1
        self.setCurrentPage(year, month)

    def update_combos(self, year, month):
        self.year_combo.blockSignals(True)
        self.month_combo.blockSignals(True)
        self.year_combo.setCurrentText(str(year))
        self.month_combo.setCurrentIndex(month - 1)
        self.year_combo.blockSignals(False)
        self.month_combo.blockSignals(False)

class DateEditDialog(QDialog):
    def __init__(self, current_date_str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("마감일 수정")
        self.resize(320, 300) 
        self.setStyleSheet("background-color: white; color: black;") 
        
        layout = QVBoxLayout(self)
        self.calendar = DropdownCalendarWidget()
        self.calendar.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)
        self.calendar.setStyleSheet(CALENDAR_STYLE)
        
        if current_date_str:
            curr_date = QDate.fromString(current_date_str, "yyyy-MM-dd")
            self.calendar.setSelectedDate(curr_date)
            
        layout.addWidget(self.calendar)

        btn_layout = QHBoxLayout()
        save_btn = QPushButton("확인")
        save_btn.setStyleSheet(DIALOG_BUTTON_STYLE)
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("취소")
        cancel_btn.setStyleSheet(DIALOG_BUTTON_STYLE)
        cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def get_date(self):
        return self.calendar.selectedDate().toString("yyyy-MM-dd")

class MemoDialog(QDialog):
    def __init__(self, task_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("상세 정보 수정")
        self.resize(350, 350)
        self.setStyleSheet("background-color: white; color: black;")
        self.task_data = task_data

        layout = QVBoxLayout(self)
        
        title_layout = QHBoxLayout()
        title_label = QLabel("할 일:")
        title_label.setFixedWidth(60)
        self.title_edit = QLineEdit(self.task_data["title"])
        self.title_edit.setStyleSheet("border: 1px solid #ccc; padding: 3px; border-radius: 3px;")
        title_layout.addWidget(title_label)
        title_layout.addWidget(self.title_edit)
        layout.addLayout(title_layout)

        cat_layout = QHBoxLayout()
        cat_label = QLabel("카테고리:")
        cat_label.setFixedWidth(60)
        self.cat_combo = QComboBox()
        self.cat_combo.addItems(["기타", "과제", "약속", "미팅", "중요"])
        self.cat_combo.setEditable(True) 
        self.cat_combo.setStyleSheet(COMBO_STYLE)
        
        current_cat = self.task_data.get("category", "기타")
        self.cat_combo.setCurrentText(current_cat)
        
        cat_layout.addWidget(cat_label)
        cat_layout.addWidget(self.cat_combo)
        layout.addLayout(cat_layout)

        self.memo_edit = QTextEdit()
        self.memo_edit.setText(self.task_data.get("memo", ""))
        self.memo_edit.setPlaceholderText("여기에 세부 메모를 작성하세요...")
        self.memo_edit.setStyleSheet("border: 1px solid #ccc; margin-top: 10px;")
        layout.addWidget(self.memo_edit)

        btn_layout = QHBoxLayout()
        save_btn = QPushButton("저장")
        save_btn.setStyleSheet(DIALOG_BUTTON_STYLE)
        save_btn.clicked.connect(self.save_memo)
        cancel_btn = QPushButton("취소")
        cancel_btn.setStyleSheet(DIALOG_BUTTON_STYLE)
        cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def save_memo(self):
        self.task_data["title"] = self.title_edit.text().strip()
        self.task_data["category"] = self.cat_combo.currentText().strip()
        self.task_data["memo"] = self.memo_edit.toPlainText()
        self.accept()

class DeleteDialog(QDialog):
    def __init__(self, tasks, parent=None):
        super().__init__(parent)
        self.setWindowTitle("할 일 삭제")
        self.resize(380, 450)
        self.setStyleSheet("background-color: white; color: black;")
        self.tasks = tasks

        layout = QVBoxLayout(self)
        
        label = QLabel("삭제할 항목을 체크한 후 '삭제 확인'을 누르세요:")
        label.setStyleSheet("margin-bottom: 5px;")
        layout.addWidget(label)

        cb_layout = QHBoxLayout()
        self.select_todo_cb = QCheckBox("진행 중")
        self.select_todo_cb.stateChanged.connect(lambda state: self.toggle_group(state, "todo"))
        
        self.select_remember_cb = QCheckBox("기억할 일")
        self.select_remember_cb.stateChanged.connect(lambda state: self.toggle_group(state, "remember"))
        
        self.select_done_cb = QCheckBox("완료된 일")
        self.select_done_cb.stateChanged.connect(lambda state: self.toggle_group(state, "done"))
        
        cb_layout.addWidget(self.select_todo_cb)
        cb_layout.addWidget(self.select_remember_cb)
        cb_layout.addWidget(self.select_done_cb)
        layout.addLayout(cb_layout)

        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet("border: 1px solid #ccc; border-radius: 3px;")
        
        for task in self.tasks:
            is_done = task["is_completed"]
            has_date = bool(task.get("deadline"))
            
            if is_done: task_type = "done"
            elif has_date: task_type = "todo"
            else: task_type = "remember"
                
            status = "✅" if is_done else ("📌" if has_date else "💡")
            deadline_str = f" ({task['deadline']})" if has_date else ""
            item_text = f"[{task.get('category', '기타')}] {task['title']}{deadline_str}"
            item = QListWidgetItem(f"{status} {item_text}")
            
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Unchecked)
            item.setData(Qt.ItemDataRole.UserRole, task_type) 
            self.list_widget.addItem(item)
            
        layout.addWidget(self.list_widget)

        btn_layout = QHBoxLayout()
        delete_btn = QPushButton("삭제 확인")
        delete_btn.setStyleSheet("background-color: #ffcccc; color: black; border: 1px solid #ccc; padding: 5px 15px; border-radius: 3px;")
        delete_btn.clicked.connect(self.accept)
        
        cancel_btn = QPushButton("취소")
        cancel_btn.setStyleSheet(DIALOG_BUTTON_STYLE)
        cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(delete_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def toggle_group(self, state, target_type):
        check_state = Qt.CheckState.Checked if state == 2 else Qt.CheckState.Unchecked
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == target_type:
                item.setCheckState(check_state)

    def get_indices_to_delete(self):
        indices = []
        for i in range(self.list_widget.count()):
            if self.list_widget.item(i).checkState() == Qt.CheckState.Checked:
                indices.append(i)
        return indices

class TaskWidget(QWidget):
    def __init__(self, task_data, main_window):
        super().__init__()
        self.task_data = task_data
        self.main_window = main_window
        
        cat = self.task_data.get("category", "기타")
        bg_color = CATEGORY_COLORS.get(cat, "transparent")
        
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(f"TaskWidget {{ background-color: {bg_color}; border-radius: 5px; }}")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        self.checkbox = QCheckBox()
        self.checkbox.setChecked(self.task_data["is_completed"])
        self.checkbox.toggled.connect(self.on_checked)
        layout.addWidget(self.checkbox)

        self.title_label = QLabel(self.task_data["title"])
        self.title_label.mousePressEvent = self.open_memo
        self.title_label.setCursor(Qt.CursorShape.PointingHandCursor)
        font = self.title_label.font()
        font.setPointSize(11)
        self.title_label.setFont(font)
        self.title_label.setStyleSheet("color: gray; text-decoration: line-through;" if self.task_data["is_completed"] else "color: black;")
        layout.addWidget(self.title_label, stretch=1)

        if self.task_data.get("deadline"):
            dday_str, is_overdue = self.calculate_dday(self.task_data["deadline"])
            
            self.dday_label = QLabel(dday_str)
            self.dday_label.mousePressEvent = self.edit_date
            self.dday_label.setCursor(Qt.CursorShape.PointingHandCursor)
            self.dday_label.setMinimumWidth(65)
            self.dday_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            
            if is_overdue and not self.task_data["is_completed"]:
                self.dday_label.setStyleSheet("color: #0275d8; font-weight: bold;") 
            else:
                self.dday_label.setStyleSheet("color: #d9534f; font-weight: bold;") 
            layout.addWidget(self.dday_label)

    def calculate_dday(self, deadline_str):
        deadline = datetime.strptime(deadline_str, "%Y-%m-%d").date()
        today = datetime.now().date()
        delta = (deadline - today).days
        
        is_overdue = delta < 0 
        
        if delta > 0: return f"D-{delta}", is_overdue
        elif delta == 0: return "D-DAY", is_overdue
        else: return f"D+{abs(delta)}", is_overdue

    def on_checked(self, checked):
        self.task_data["is_completed"] = checked
        self.main_window.save_data()
        self.main_window.refresh_lists()

    def open_memo(self, event):
        dialog = MemoDialog(self.task_data, self)
        if dialog.exec():
            self.main_window.save_data()
            self.main_window.refresh_lists()

    def edit_date(self, event):
        dialog = DateEditDialog(self.task_data.get("deadline", ""), self)
        if dialog.exec():
            new_date = dialog.get_date()
            self.task_data["deadline"] = new_date
            self.main_window.save_data()
            self.main_window.refresh_lists()

# ==========================================
# 메인 앱 클래스
# ==========================================
class ChecklistApp(QWidget):
    def __init__(self):
        super().__init__()
        self.tasks = []
        self.bg_color = "rgba(253, 243, 169, 230)" 
        self.win_x = None
        self.win_y = None
        self.win_w = 850
        self.win_h = 500
        self.oldPos = None

        self.gcal_manager = GoogleCalendarManager()

        self.load_settings()
        self.load_data()
        self.init_ui()
        
        self.sync_all()

        self.current_date = datetime.now().date()
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.timer_routine)
        self.refresh_timer.start(60000)

    def timer_routine(self):
        today = datetime.now().date()
        if today != self.current_date:
            self.current_date = today
            self.sync_all()

    def sync_all(self):
        self.sync_app_to_google_calendar()
        self.sync_google_calendar_to_app()
        self.refresh_lists()

    def sync_app_to_google_calendar(self):
        new_updates = False
        for task in self.tasks:
            if not task.get("is_completed") and task.get("deadline") and "gcal_id" not in task:
                event_id = self.gcal_manager.create_event(task["title"], task["deadline"], task.get("memo", ""))
                if event_id:
                    task["gcal_id"] = event_id
                    new_updates = True
        if new_updates:
            self.save_data()

    def sync_google_calendar_to_app(self):
        events = self.gcal_manager.get_upcoming_events()
        fetched_gcal_ids = {event['id'] for event in events}
        
        today = datetime.now().date()
        tasks_to_keep = []
        sync_modified = False
        
        for task in self.tasks:
            keep = True
            if "gcal_id" in task and not task["is_completed"]:
                base_gcal_id = task["gcal_id"].replace("_start", "").replace("_end", "")
                try:
                    task_date = datetime.strptime(task["deadline"], "%Y-%m-%d").date()
                    if task_date >= today and base_gcal_id not in fetched_gcal_ids:
                        keep = False
                        sync_modified = True
                except ValueError:
                    pass
            
            if keep:
                tasks_to_keep.append(task)
                
        if sync_modified:
            self.tasks = tasks_to_keep

        existing_gcal_ids = [t.get("gcal_id") for t in self.tasks if "gcal_id" in t]
        
        for event in events:
            event_id = event['id']
            start_raw = event['start'].get('dateTime', event['start'].get('date'))
            end_raw = event['end'].get('dateTime', event['end'].get('date'))
            is_all_day = 'date' in event['start']
            
            try:
                start_date_str = start_raw.split('T')[0]
                end_date_str = end_raw.split('T')[0]
                
                start_dt = datetime.strptime(start_date_str, "%Y-%m-%d").date()
                end_dt = datetime.strptime(end_date_str, "%Y-%m-%d").date()
                
                if is_all_day:
                    actual_end_dt = end_dt - timedelta(days=1)
                    time_memo_single = ""
                    time_memo_start = ""
                    time_memo_end = ""
                else:
                    actual_end_dt = end_dt
                    s_time_obj = datetime.fromisoformat(start_raw.replace('Z', '+00:00')).astimezone()
                    e_time_obj = datetime.fromisoformat(end_raw.replace('Z', '+00:00')).astimezone()
                    s_time = s_time_obj.strftime('%H:%M')
                    e_time = e_time_obj.strftime('%H:%M')
                    
                    time_memo_single = f"[시간: {s_time} ~ {e_time}]\n"
                    time_memo_start = f"[시작 시간: {s_time}]\n"
                    time_memo_end = f"[종료 시간: {e_time}]\n"
                    
                summary = event.get('summary', '제목 없는 일정')
                desc = event.get('description', '')

                if actual_end_dt > start_dt: 
                    id_start = f"{event_id}_start"
                    id_end = f"{event_id}_end"
                    
                    if id_start not in existing_gcal_ids:
                        self.tasks.append({
                            "title": f"{summary} 시작",
                            "deadline": start_date_str,
                            "memo": f"{time_memo_start}{desc}".strip(), 
                            "category": "기타", "is_completed": False, "gcal_id": id_start
                        })
                        sync_modified = True
                    if id_end not in existing_gcal_ids:
                        self.tasks.append({
                            "title": f"{summary} 끝",
                            "deadline": actual_end_dt.strftime("%Y-%m-%d"),
                            "memo": f"{time_memo_end}{desc}".strip(), 
                            "category": "기타", "is_completed": False, "gcal_id": id_end
                        })
                        sync_modified = True
                else: 
                    if event_id not in existing_gcal_ids:
                        self.tasks.append({
                            "title": summary,
                            "deadline": start_date_str,
                            "memo": f"{time_memo_single}{desc}".strip(), 
                            "category": "기타", "is_completed": False, "gcal_id": event_id
                        })
                        sync_modified = True
            except Exception as e:
                print(f"이벤트 파싱 오류: {e}")
                
        if sync_modified:
            self.save_data()

    def init_ui(self):
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnBottomHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.resize(self.win_w, self.win_h)
        
        if self.win_x is not None and self.win_y is not None:
            self.move(self.win_x, self.win_y)
        else:
            screen_geometry = QApplication.primaryScreen().availableGeometry()
            self.move(screen_geometry.width() - self.width() - 30, 30)
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        
        self.bg_widget = QWidget()
        self.update_bg_color()
        bg_layout = QVBoxLayout(self.bg_widget)
        self.main_layout.addWidget(self.bg_widget)

        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 할 일, 메모, 날짜(예: 03-23) 검색...")
        self.search_input.setStyleSheet("background-color: white; color: black; padding: 5px; border-radius: 3px; border: 1px solid #ccc;")
        self.search_input.textChanged.connect(self.refresh_lists) 
        search_layout.addWidget(self.search_input)
        
        sync_btn = QPushButton("🔄 수동 동기화")
        sync_btn.setStyleSheet("background-color: white; color: black; padding: 5px 15px; border-radius: 3px; border: 1px solid #ccc;")
        sync_btn.clicked.connect(self.sync_all)
        search_layout.addWidget(sync_btn)
        
        bg_layout.addLayout(search_layout)

        lists_layout = QHBoxLayout()

        todo_layout = QVBoxLayout()
        todo_label = QLabel("📌 진행 중")
        todo_label.setStyleSheet("font-weight: bold; font-size: 14px; margin-bottom: 5px;")
        self.todo_list = QListWidget()
        self.todo_list.setStyleSheet("background-color: transparent; border: 1px solid rgba(0,0,0,30); border-radius: 5px;")
        todo_layout.addWidget(todo_label)
        todo_layout.addWidget(self.todo_list)

        remember_layout = QVBoxLayout()
        remember_label = QLabel("💡 기억할 일")
        remember_label.setStyleSheet("font-weight: bold; font-size: 14px; margin-bottom: 5px;")
        self.remember_list = QListWidget()
        self.remember_list.setStyleSheet("background-color: transparent; border: 1px solid rgba(0,0,0,30); border-radius: 5px;")
        remember_layout.addWidget(remember_label)
        remember_layout.addWidget(self.remember_list)

        done_layout = QVBoxLayout()
        
        done_todo_label = QLabel("✅ 완료된 일 (진행 중)")
        done_todo_label.setStyleSheet("font-weight: bold; font-size: 14px; margin-bottom: 5px;")
        self.done_todo_list = QListWidget()
        self.done_todo_list.setStyleSheet("background-color: transparent; border: 1px solid rgba(0,0,0,30); border-radius: 5px;")
        
        done_remember_label = QLabel("✅ 완료된 일 (기억할 일)")
        done_remember_label.setStyleSheet("font-weight: bold; font-size: 14px; margin-bottom: 5px; margin-top: 10px;")
        self.done_remember_list = QListWidget()
        self.done_remember_list.setStyleSheet("background-color: transparent; border: 1px solid rgba(0,0,0,30); border-radius: 5px;")
        
        done_layout.addWidget(done_todo_label)
        done_layout.addWidget(self.done_todo_list)
        done_layout.addWidget(done_remember_label)
        done_layout.addWidget(self.done_remember_list)

        # --- 탭 너비 비율 적용 (5 : 3 : 2) ---
        lists_layout.addLayout(todo_layout, stretch=5)
        lists_layout.addLayout(remember_layout, stretch=3)
        lists_layout.addLayout(done_layout, stretch=2)
        bg_layout.addLayout(lists_layout)

        add_layout = QHBoxLayout()
        self.new_task_input = QLineEdit()
        self.new_task_input.setPlaceholderText("새 할 일 입력...")
        self.new_task_input.setStyleSheet("background-color: white; color: black; padding: 5px; border-radius: 3px; border: 1px solid #ccc;")
        
        self.date_picker = QDateEdit()
        self.date_picker.setDate(QDate.currentDate())
        self.date_picker.setCalendarPopup(True)
        self.date_picker.setMinimumWidth(120) 
        self.date_picker.setStyleSheet("background-color: white; color: black; padding: 5px; border-radius: 3px; border: 1px solid #ccc;")
        
        custom_calendar = DropdownCalendarWidget()
        custom_calendar.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)
        custom_calendar.setStyleSheet(CALENDAR_STYLE)
        self.date_picker.setCalendarWidget(custom_calendar)
        
        add_todo_btn = QPushButton("진행 중 추가")
        add_todo_btn.setStyleSheet("background-color: white; color: black; padding: 5px 15px; border-radius: 3px; border: 1px solid #ccc;")
        add_todo_btn.clicked.connect(lambda: self.add_task(is_remember=False))

        add_rem_btn = QPushButton("기억할 일 추가")
        add_rem_btn.setStyleSheet("background-color: white; color: black; padding: 5px 15px; border-radius: 3px; border: 1px solid #ccc;")
        add_rem_btn.clicked.connect(lambda: self.add_task(is_remember=True))
        
        add_layout.addWidget(self.new_task_input)
        add_layout.addWidget(self.date_picker)
        add_layout.addWidget(add_todo_btn)
        add_layout.addWidget(add_rem_btn)
        bg_layout.addLayout(add_layout)

        bottom_layout = QHBoxLayout()
        
        delete_btn = QPushButton("🗑️ 삭제")
        delete_btn.setStyleSheet("background-color: white; color: black; padding: 5px 15px; border-radius: 3px; border: 1px solid #ccc;")
        delete_btn.clicked.connect(self.open_delete_dialog)

        color_btn = QPushButton("🎨 색상")
        color_btn.setStyleSheet("background-color: white; color: black; padding: 5px 15px; border-radius: 3px; border: 1px solid #ccc;")
        color_btn.clicked.connect(self.choose_color)
        
        exit_btn = QPushButton("❌ 종료")
        exit_btn.setStyleSheet("background-color: white; color: black; padding: 5px 15px; border-radius: 3px; border: 1px solid #ccc;")
        exit_btn.clicked.connect(QApplication.instance().quit)
        
        bottom_layout.addWidget(delete_btn)
        bottom_layout.addWidget(color_btn)
        bottom_layout.addWidget(exit_btn)
        bottom_layout.addStretch() 
        
        size_grip = QSizeGrip(self)
        bottom_layout.addWidget(size_grip, 0, Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignRight)
        
        bg_layout.addLayout(bottom_layout)

    def open_delete_dialog(self):
        if not self.tasks: return  
            
        dialog = DeleteDialog(self.tasks, self)
        if dialog.exec():
            indices_to_delete = dialog.get_indices_to_delete()
            if indices_to_delete:
                for idx in sorted(indices_to_delete, reverse=True):
                    del self.tasks[idx]
                self.save_data()
                self.refresh_lists()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton: self.oldPos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if self.oldPos is not None:
            delta = event.globalPosition().toPoint() - self.oldPos
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.oldPos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        self.oldPos = None
        self.save_settings()

    def choose_color(self):
        color = QColorDialog.getColor(parent=self)
        if color.isValid():
            self.bg_color = f"rgba({color.red()}, {color.green()}, {color.blue()}, 230)"
            self.update_bg_color()
            self.save_settings()

    def update_bg_color(self):
        self.bg_widget.setStyleSheet(f"background-color: {self.bg_color}; border-radius: 10px; border: 1px solid rgba(0,0,0,50);")

    def load_settings(self):
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                settings = json.load(f)
                self.bg_color = settings.get("bg_color", self.bg_color)
                self.win_x = settings.get("win_x")
                self.win_y = settings.get("win_y")
                self.win_w = settings.get("win_w", 850)
                self.win_h = settings.get("win_h", 500)

    def save_settings(self):
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump({
                "bg_color": self.bg_color, 
                "win_x": self.x(), 
                "win_y": self.y(),
                "win_w": self.width(),
                "win_h": self.height()
            }, f)

    def load_data(self):
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                self.tasks = json.load(f)
        else:
            self.tasks = []

    def save_data(self):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(self.tasks, f, ensure_ascii=False, indent=4)

    def add_task(self, is_remember=False):
        title = self.new_task_input.text().strip()
        if not title: return
            
        deadline = "" if is_remember else self.date_picker.date().toString("yyyy-MM-dd")
        new_task = {
            "title": title,
            "deadline": deadline,
            "memo": "",
            "category": "기타",
            "is_completed": False
        }
        
        if not is_remember and self.gcal_manager.service:
            event_id = self.gcal_manager.create_event(title, deadline)
            if event_id:
                new_task["gcal_id"] = event_id

        self.tasks.append(new_task)
        self.new_task_input.clear()
        self.save_data()
        self.refresh_lists()

    def refresh_lists(self):
        self.todo_list.clear()
        self.remember_list.clear()
        self.done_todo_list.clear()
        self.done_remember_list.clear()

        query = self.search_input.text().strip().lower().replace(".", "-") if hasattr(self, 'search_input') else ""

        todo_tasks, remember_tasks, done_todo_tasks, done_remember_tasks = [], [], [], []

        for t in self.tasks:
            title_match = query in t["title"].lower()
            memo_match = query in t.get("memo", "").lower()
            cat_match = query in t.get("category", "").lower()
            date_match = query in t.get("deadline", "")
            
            if query and not (title_match or memo_match or cat_match or date_match):
                continue
                
            is_done = t["is_completed"]
            has_date = bool(t.get("deadline"))
            
            if not is_done and has_date: todo_tasks.append(t)
            elif not is_done and not has_date: remember_tasks.append(t)
            elif is_done and has_date: done_todo_tasks.append(t)
            elif is_done and not has_date: done_remember_tasks.append(t)

        todo_tasks.sort(key=lambda x: datetime.strptime(x["deadline"], "%Y-%m-%d").date())
        done_todo_tasks.sort(key=lambda x: datetime.strptime(x["deadline"], "%Y-%m-%d").date(), reverse=True)

        def add_items_to_list(widget_list, tasks):
            for task in tasks:
                item = QListWidgetItem()
                widget = TaskWidget(task, self)
                item.setSizeHint(widget.sizeHint())
                widget_list.addItem(item)
                widget_list.setItemWidget(item, widget)

        add_items_to_list(self.todo_list, todo_tasks)
        add_items_to_list(self.remember_list, remember_tasks)
        add_items_to_list(self.done_todo_list, done_todo_tasks)
        add_items_to_list(self.done_remember_list, done_remember_tasks)

    def closeEvent(self, event):
        self.save_data()
        self.save_settings()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    font = QFont("Malgun Gothic", 10) 
    font.setStyleHint(QFont.StyleHint.SansSerif)
    app.setFont(font)
    
    window = ChecklistApp()
    window.show()
    sys.exit(app.exec())