'''
Apache license 2.0
Version 2.0, January 2004
Read https://www.apache.org/licenses/LICENSE-2.0
Full License is in /LICENCE file
'''
import sys
import os
import json
import datetime
import sounddevice as sd
import numpy as np
from PySide6 import QtCore, QtWidgets, QtGui
result_sound = 0
def audio_callback(indata, frames, time_info, status):
    global result_sound
    if status:
        print(status, file=sys.stderr)
    rms = np.sqrt(np.mean(indata ** 2))
    loudness = int(rms * 1000)
    result_sound = loudness


def start_microphone_monitor():
    stream = sd.InputStream(
        callback=audio_callback,
        channels=1,
        samplerate=16000,
        blocksize=512,
        dtype='float32'
    )
    stream.start()
    return stream

# 数据路径
APP_NAME = "PlanTree"
APPDATA_PATH = os.path.join(os.getenv('APPDATA'), APP_NAME)
os.makedirs(APPDATA_PATH, exist_ok=True)
SAVE_FILE = os.path.join(APPDATA_PATH, "progress.json")
LEADERBOARD_FILE = os.path.join(APPDATA_PATH, "leaderboard.json")
DAILY_PROGRESS_FILE = os.path.join(APPDATA_PATH, "daily_progress.json")  # 新增：每日独立进度


def load_progress():
    """加载主进度（永久积累）"""
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {
        "total_seedlings": 0,
        "total_trees": 0,
        "total_giants": 0,
        "merge_count": 10
    }


def save_progress(data):
    with open(SAVE_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_daily_progress():
    """加载每日独立进度"""
    today = str(datetime.date.today())
    if os.path.exists(DAILY_PROGRESS_FILE):
        try:
            with open(DAILY_PROGRESS_FILE, 'r', encoding='utf-8') as f:
                all_data = json.load(f)
                # 获取今天的数据，如果不存在则创建新的
                if today in all_data:
                    return all_data[today]
        except:
            pass
    # 返回今天的初始数据
    return {
        "date": today,
        "progress": 0.0,
        "seedlings": 0,
        "trees": 0,
        "giants": 0
    }


def save_daily_progress(data):
    """保存每日进度"""
    today = str(datetime.date.today())
    all_data = {}
    if os.path.exists(DAILY_PROGRESS_FILE):
        try:
            with open(DAILY_PROGRESS_FILE, 'r', encoding='utf-8') as f:
                all_data = json.load(f)
        except:
            pass

    # 只保留最近7天的数据
    all_data[today] = data
    # 清理旧数据
    today_date = datetime.date.today()
    to_delete = []
    for date_str in list(all_data.keys()):
        try:
            date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
            if (today_date - date_obj).days > 7:
                to_delete.append(date_str)
        except:
            to_delete.append(date_str)

    for key in to_delete:
        all_data.pop(key, None)

    with open(DAILY_PROGRESS_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)


def load_leaderboard():
    if os.path.exists(LEADERBOARD_FILE):
        try:
            with open(LEADERBOARD_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return []


def save_leaderboard(board):
    with open(LEADERBOARD_FILE, 'w', encoding='utf-8') as f:
        json.dump(board, f, ensure_ascii=False, indent=2)


def bubble_sort_leaderboard(board):
    n = len(board)
    for i in range(n):
        for j in range(0, n - i - 1):
            if board[j]["score"] < board[j + 1]["score"]:
                board[j], board[j + 1] = board[j + 1], board[j]
    return board


class FlowLayout(QtWidgets.QLayout):
    def __init__(self, parent=None, margin=0, spacing=-1):
        super().__init__(parent)
        if parent is not None:
            self.setContentsMargins(margin, margin, margin, margin)
        self.setSpacing(spacing if spacing >= 0 else 6)
        self._item_list = []

    def __del__(self):
        while self.count():
            self.takeAt(0)

    def addItem(self, item):
        self._item_list.append(item)

    def count(self):
        return len(self._item_list)

    def itemAt(self, index):
        if 0 <= index < len(self._item_list):
            return self._item_list[index]
        return None

    def takeAt(self, index):
        if 0 <= index < len(self._item_list):
            return self._item_list.pop(index)
        return None

    def expandingDirections(self):
        return QtCore.Qt.Orientation(0)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self._do_layout(QtCore.QRect(0, 0, width, 0), test=True)

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._do_layout(rect, test=False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QtCore.QSize()
        for item in self._item_list:
            size = size.expandedTo(item.minimumSize())
        left, top, right, bottom = self.getContentsMargins()
        size += QtCore.QSize(left + right, top + bottom)
        return size

    def _do_layout(self, rect, test=False):
        x = rect.x()
        y = rect.y()
        line_height = 0
        spacing = self.spacing()

        for item in self._item_list:
            next_x = x + item.sizeHint().width() + spacing
            if next_x - spacing > rect.right() and line_height > 0:
                x = rect.x()
                y = y + line_height + spacing
                next_x = x + item.sizeHint().width() + spacing
                line_height = 0

            if not test:
                item.setGeometry(QtCore.QRect(QtCore.QPoint(x, y), item.sizeHint()))
            x = next_x
            line_height = max(line_height, item.sizeHint().height())

        return y + line_height - rect.y()


class TreeManager:
    def __init__(self):
        self.morning_mode = False
        self.threshold_low = 60
        self.threshold_high = 60
        self.growth_speed = 25.0  # %/秒
        self.merge_count = 10

        # 每日独立进度
        self.daily_progress = 0.0
        self.daily_seedlings = 0
        self.daily_trees = 0
        self.daily_giants = 0

        # 总进度（永久积累）
        self.total_seedlings = 0
        self.total_trees = 0
        self.total_giants = 0

    def load_from_data(self, main_data, daily_data):
        # 加载主进度
        self.merge_count = main_data.get("merge_count", 10)
        self.total_seedlings = main_data.get("total_seedlings", 0)
        self.total_trees = main_data.get("total_trees", 0)
        self.total_giants = main_data.get("total_giants", 0)

        # 加载每日进度
        self.daily_progress = daily_data.get("progress", 0.0)
        self.daily_seedlings = daily_data.get("seedlings", 0)
        self.daily_trees = daily_data.get("trees", 0)
        self.daily_giants = daily_data.get("giants", 0)

    def save_main_progress(self):
        """保存主进度"""
        return {
            "total_seedlings": self.total_seedlings,
            "total_trees": self.total_trees,
            "total_giants": self.total_giants,
            "merge_count": self.merge_count
        }

    def save_daily_progress(self):
        """保存每日进度"""
        return {
            "date": str(datetime.date.today()),
            "progress": self.daily_progress,
            "seedlings": self.daily_seedlings,
            "trees": self.daily_trees,
            "giants": self.daily_giants
        }

    def update(self, loudness):
        time_step = 0.01
        growth_increment = self.growth_speed * time_step

        if self.morning_mode:
            if loudness > self.threshold_high:
                self.daily_progress += growth_increment
            else:
                self.daily_progress = max(0.0, self.daily_progress - 0.1)
        else:
            if loudness < self.threshold_low:
                self.daily_progress += growth_increment
            else:
                self.daily_progress *= 0.92

        tree_changed = False
        if self.daily_progress >= 100:
            self.daily_progress = 0
            self.daily_seedlings += 1
            self.total_seedlings += 1  # 添加到总进度
            self._merge_trees()
            tree_changed = True

        return tree_changed

    def _merge_trees(self):
        # 处理每日进度的合并
        if self.daily_seedlings >= self.merge_count:
            new_trees = self.daily_seedlings // self.merge_count
            self.daily_trees += new_trees
            self.daily_seedlings %= self.merge_count
            if self.daily_trees >= self.merge_count:
                new_giants = self.daily_trees // self.merge_count
                self.daily_giants += new_giants
                self.daily_trees %= self.merge_count

        # 处理总进度的合并
        if self.total_seedlings >= self.merge_count:
            new_trees = self.total_seedlings // self.merge_count
            self.total_trees += new_trees
            self.total_seedlings %= self.merge_count
            if self.total_trees >= self.merge_count:
                new_giants = self.total_trees // self.merge_count
                self.total_giants += new_giants
                self.total_trees %= self.merge_count

    def submit_daily_score(self):
        daily_score = self.get_daily_score()
        if daily_score == 0:
            return

        board = load_leaderboard()
        today_str = str(datetime.date.today())

        # 检查今天是否已有记录
        existing_index = -1
        for i, item in enumerate(board):
            if item["date"] == today_str:
                existing_index = i
                break

        if existing_index >= 0:
            # 更新已有记录（如果分数更高）
            if daily_score > board[existing_index]["score"]:
                board[existing_index]["score"] = daily_score
        else:
            # 添加新记录
            board.append({"date": today_str, "score": daily_score})

        # 排序并保留前30
        board = bubble_sort_leaderboard(board)
        board = board[:30]
        save_leaderboard(board)

    def get_daily_score(self):
        """返回当日分数"""
        return (
            self.daily_seedlings * 1 +
            self.daily_trees * self.merge_count +
            self.daily_giants * (self.merge_count ** 2)
        )

    def get_total_score(self):
        """返回总分数"""
        return (
            self.total_seedlings * 1 +
            self.total_trees * self.merge_count +
            self.total_giants * (self.merge_count ** 2)
        )


class SettingsDialog(QtWidgets.QDialog):
    def __init__(self, tree_manager, parent=None):
        super().__init__(parent)
        self.setWindowTitle("设置")
        self.resize(400, 300)
        self.tree_manager = tree_manager

        layout = QtWidgets.QVBoxLayout()

        # 暗色模式样式
        self.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
                color: #e0e0e0;
            }
            QLabel {
                color: #e0e0e0;
            }
            QSlider::groove:horizontal {
                background-color: #404040;
                height: 6px;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background-color: #0078d4;
                width: 18px;
                height: 18px;
                margin: -6px 0;
                border-radius: 9px;
            }
            QSlider::handle:horizontal:hover {
                background-color: #1084d6;
            }
        """)

        # 安静阈值滑块
        low_layout = QtWidgets.QHBoxLayout()
        low_label = QtWidgets.QLabel("安静阈值:")
        self.low_value_label = QtWidgets.QLabel(str(tree_manager.threshold_low))
        self.low_slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.low_slider.setRange(0, 600)
        self.low_slider.setValue(tree_manager.threshold_low)
        self.low_slider.valueChanged.connect(
            lambda v: (setattr(tree_manager, 'threshold_low', v),
                      self.low_value_label.setText(str(v))))
        low_layout.addWidget(low_label)
        low_layout.addWidget(self.low_slider)
        low_layout.addWidget(self.low_value_label)

        # 朗读阈值滑块
        high_layout = QtWidgets.QHBoxLayout()
        high_label = QtWidgets.QLabel("朗读阈值:")
        self.high_value_label = QtWidgets.QLabel(str(tree_manager.threshold_high))
        self.high_slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.high_slider.setRange(0, 600)
        self.high_slider.setValue(tree_manager.threshold_high)
        self.high_slider.valueChanged.connect(
            lambda v: (setattr(tree_manager, 'threshold_high', v),
                      self.high_value_label.setText(str(v))))
        high_layout.addWidget(high_label)
        high_layout.addWidget(self.high_slider)
        high_layout.addWidget(self.high_value_label)

        # 增长速度滑块
        speed_layout = QtWidgets.QHBoxLayout()
        speed_label = QtWidgets.QLabel("增长速度:")
        self.speed_value_label = QtWidgets.QLabel(f"{tree_manager.growth_speed:.1f}")
        self.speed_slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.speed_slider.setRange(10, 10000)  # 对应1.0-50.0
        self.speed_slider.setValue(int(tree_manager.growth_speed * 10))
        self.speed_slider.valueChanged.connect(
            lambda v: (setattr(tree_manager, 'growth_speed', v/10.0),
                      self.speed_value_label.setText(f"{v/10.0:.1f}")))
        speed_layout.addWidget(speed_label)
        speed_layout.addWidget(self.speed_slider)
        speed_layout.addWidget(self.speed_value_label)

        # 合并数量滑块
        merge_layout = QtWidgets.QHBoxLayout()
        merge_label = QtWidgets.QLabel("合并数量:")
        self.merge_value_label = QtWidgets.QLabel(str(tree_manager.merge_count))
        self.merge_slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.merge_slider.setRange(1, 1000)
        self.merge_slider.setValue(tree_manager.merge_count)
        self.merge_slider.valueChanged.connect(
            lambda v: (setattr(tree_manager, 'merge_count', v),
                      self.merge_value_label.setText(str(v))))
        merge_layout.addWidget(merge_label)
        merge_layout.addWidget(self.merge_slider)
        merge_layout.addWidget(self.merge_value_label)

        layout.addLayout(low_layout)
        layout.addLayout(high_layout)
        layout.addLayout(speed_layout)
        layout.addLayout(merge_layout)
        layout.addSpacing(20)

        # 说明文字
        tip_label = QtWidgets.QLabel(
            "提示：\n"
            "• 安静模式：声音小于安静阈值时增长\n"
            "• 早读模式：声音大于朗读阈值时增长\n"
            "• 每天进度独立，但总进度会永久积累"
        )
        tip_label.setWordWrap(True)
        tip_label.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(tip_label)

        layout.addStretch()

        # 按钮
        btn_layout = QtWidgets.QHBoxLayout()
        ok_btn = QtWidgets.QPushButton("确定")
        ok_btn.setStyleSheet("""
            QPushButton {
                background-color: #0078d4;
                color: white;
                padding: 8px 20px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1084d6;
            }
        """)
        ok_btn.clicked.connect(self.accept)

        cancel_btn = QtWidgets.QPushButton("取消")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #5c5c5c;
                color: white;
                padding: 8px 20px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #6c6c6c;
            }
        """)
        cancel_btn.clicked.connect(self.reject)

        btn_layout.addStretch()
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        btn_layout.addStretch()

        layout.addLayout(btn_layout)
        self.setLayout(layout)


class LoudnessMonitor(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("种 树 游 戏")
        self.resize(480, 420)

        # 应用暗色主题
        self.setStyleSheet("""
            QWidget {
                background-color: #1e1e1e;
                color: #e0e0e0;
            }
            QProgressBar {
                border: 1px solid #444;
                border-radius: 5px;
                text-align: center;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: #0078d4;
                border-radius: 4px;
            }
            QPushButton {
                background-color: #3c3c3c;
                color: white;
                border: 1px solid #555;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #4c4c4c;
            }
            QCheckBox {
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
            }
        """)

        self.tree_manager = TreeManager()
        main_saved = load_progress()
        daily_saved = load_daily_progress()
        self.tree_manager.load_from_data(main_saved, daily_saved)

        # ===== 顶部区域 =====
        topLayout = QtWidgets.QHBoxLayout()

        # 左侧信息
        infoLayout = QtWidgets.QVBoxLayout()
        self.author_label = QtWidgets.QLabel("侯皓铭 - 制作（GitHub：imjumping）")
        self.license_label = QtWidgets.QLabel("Apache license 2.0协议开源")
        self.author_label.setStyleSheet("font-size: 11px; color: #888;")
        self.license_label.setStyleSheet("font-size: 11px; color: #888;")
        infoLayout.addWidget(self.author_label)
        infoLayout.addWidget(self.license_label)
        infoLayout.addStretch()
        topLayout.addLayout(infoLayout)

        # 中间：日期和模式切换
        centerLayout = QtWidgets.QVBoxLayout()
        today = datetime.date.today()
        self.date_label = QtWidgets.QLabel(f"{today.month}月{today.day}日")
        self.date_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #4CAF50;")
        self.date_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        centerLayout.addWidget(self.date_label)

        self.morningCheckBox = QtWidgets.QCheckBox("早读模式")
        self.morningCheckBox.setChecked(self.tree_manager.morning_mode)
        self.morningCheckBox.stateChanged.connect(self.toggle_morning_mode)
        self.morningCheckBox.setStyleSheet("font-size: 13px; font-weight: bold;")
        centerLayout.addWidget(self.morningCheckBox)
        topLayout.addLayout(centerLayout)

        # 右侧设置按钮
        self.setButton = QtWidgets.QPushButton("⚙")
        self.setButton.setFixedSize(36, 36)
        self.setButton.setStyleSheet("""
            QPushButton {
                border-radius: 18px;
                background-color: #0078d4;
                color: white;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1084d6;
            }
        """)
        self.setButton.clicked.connect(self.open_settings)
        topLayout.addWidget(self.setButton)

        # ===== 主标题和音量显示 =====
        self.titleLabel = QtWidgets.QLabel("-- 正在监听 --")
        self.titleLabel.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.titleLabel.setStyleSheet("font-size: 20px; font-weight: bold; margin: 10px 0; color: #4CAF50;")

        # ===== 进度条 =====
        self.progressBar = QtWidgets.QProgressBar()
        self.progressBar.setRange(0, 100)
        self.progressBar.setValue(0)
        self.progressBar.setFormat("当日进度: %p%")
        self.progressBar.setStyleSheet("""
            QProgressBar {
                height: 25px;
                font-size: 12px;
            }
        """)

        # ===== 分数显示 =====
        scoreLayout = QtWidgets.QHBoxLayout()
        self.daily_score_label = QtWidgets.QLabel("当日: 0")
        self.daily_score_label.setStyleSheet("font-size: 14px; color: #FF9800;")
        self.total_score_label = QtWidgets.QLabel("总计: 0")
        self.total_score_label.setStyleSheet("font-size: 14px; color: #2196F3;")
        scoreLayout.addWidget(self.daily_score_label)
        scoreLayout.addWidget(QtWidgets.QLabel(" | "))
        scoreLayout.addWidget(self.total_score_label)
        scoreLayout.addStretch()

        # ===== 树显示区 =====
        tree_label = QtWidgets.QLabel("R a i n f o r e s t")
        tree_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #4CAF50; margin-top: 10px;")

        self.treeDisplay = QtWidgets.QWidget()
        self.treeDisplay.setFixedHeight(130)
        self.treeDisplay.setStyleSheet("""
            background-color: #2d2d2d;
            border: 2px solid #444;
            border-radius: 15px;
            padding: 10px;
        """)
        self.treeLayout = FlowLayout(self.treeDisplay, spacing=8)

        # ===== 按钮区域 =====
        buttonLayout = QtWidgets.QHBoxLayout()
        self.rankButton = QtWidgets.QPushButton("📊 查看排行榜")
        self.rankButton.setIconSize(QtCore.QSize(16, 16))
        self.rankButton.clicked.connect(self.show_leaderboard)

        self.resetButton = QtWidgets.QPushButton("🔄 重置")
        self.resetButton.setIconSize(QtCore.QSize(16, 16))
        self.resetButton.clicked.connect(self.reset_for_new_day)
        self.resetButton.setToolTip("这会清除今天的进度")

        buttonLayout.addWidget(self.rankButton)
        buttonLayout.addWidget(self.resetButton)
        buttonLayout.addStretch()

        # ===== 主布局 =====
        mainLayout = QtWidgets.QVBoxLayout()
        mainLayout.addLayout(topLayout)
        mainLayout.addWidget(self.titleLabel)
        mainLayout.addWidget(self.progressBar)
        mainLayout.addLayout(scoreLayout)
        mainLayout.addWidget(tree_label)
        mainLayout.addWidget(self.treeDisplay)
        mainLayout.addLayout(buttonLayout)
        mainLayout.addStretch()

        self.setLayout(mainLayout)

        # ===== 启动 =====
        self.stream = start_microphone_monitor()
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_display)
        self.timer.start(10)
        self._last_icons = None
        self.update_tree_display()
        self.update_score_display()

    def toggle_morning_mode(self, state):
        self.tree_manager.morning_mode = (state == QtCore.Qt.CheckState.Checked.value)
        self.save_current_progress()

    def update_display(self):
        global result_sound

        # 更新标题显示
        mode_text = "（早毒模式）" if self.tree_manager.morning_mode else "（静以修身）"
        threshold = self.tree_manager.threshold_high if self.tree_manager.morning_mode else self.tree_manager.threshold_low
        self.titleLabel.setText(f"当前音量: {result_sound}  目标: {'>' if self.tree_manager.morning_mode else '<'}{threshold} {mode_text}")

        # 更新进度
        tree_changed = self.tree_manager.update(result_sound)
        self.progressBar.setValue(int(min(100, self.tree_manager.daily_progress)))

        if tree_changed:
            self.update_tree_display()
            self.update_score_display()

        # 每5秒自动保存一次
        if getattr(self, '_save_counter', 0) % 500 == 0:
            self.save_current_progress()
        self._save_counter = getattr(self, '_save_counter', 0) + 1

    def update_tree_display(self):
        new_icons = ["🌱"] * self.tree_manager.daily_seedlings + \
                    ["🌳"] * self.tree_manager.daily_trees + \
                    ["🎄"] * self.tree_manager.daily_giants

        if self._last_icons == new_icons:
            return
        self._last_icons = new_icons

        while self.treeLayout.count():
            item = self.treeLayout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not new_icons:
            label = QtWidgets.QLabel("饿啊！这还没树")
            label.setStyleSheet("color: #888; font-size: 13px; font-style: italic;")
            self.treeLayout.addWidget(label)
        else:
            for icon in new_icons:
                label = QtWidgets.QLabel(icon)
                if icon == "🌲":
                    label.setStyleSheet("font-size: 32px; margin: 2px;")
                elif icon == "🌳":
                    label.setStyleSheet("font-size: 28px; margin: 2px;")
                else:
                    label.setStyleSheet("font-size: 24px; margin: 2px;")
                self.treeLayout.addWidget(label)

    def update_score_display(self):
        """更新分数显示"""
        daily_score = self.tree_manager.get_daily_score()
        total_score = self.tree_manager.get_total_score()
        self.daily_score_label.setText(f"当日: {daily_score}")
        self.total_score_label.setText(f"总计: {total_score}")

    def save_current_progress(self):
        """保存所有进度"""
        # 保存主进度
        main_data = self.tree_manager.save_main_progress()
        save_progress(main_data)

        # 保存当日进度
        daily_data = self.tree_manager.save_daily_progress()
        save_daily_progress(daily_data)

    def open_settings(self):
        dialog = SettingsDialog(self.tree_manager, self)
        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            self.save_current_progress()
            self.update_tree_display()

    def show_leaderboard(self):
        board = load_leaderboard()
        if not board:
            QtWidgets.QMessageBox.information(self, "排行榜", "应用数据目录下没有JSON文件")
            return

        # 创建暗色风格的对话框
        msg_box = QtWidgets.QMessageBox(self)
        msg_box.setWindowTitle("排行榜")
        msg_box.setStyleSheet("""
            QMessageBox {
                background-color: #2b2b2b;
                color: #e0e0e0;
            }
            QLabel {
                color: #e0e0e0;
            }
        """)

        msg = "🏆 近 期 排 行 榜 🏆\n\n"
        for i, item in enumerate(board[:10], 1):
            try:
                date_obj = datetime.datetime.strptime(item["date"], "%Y-%m-%d")
                readable_date = date_obj.strftime("%m月%d日")
                # 高亮显示今天的数据
                if item["date"] == str(datetime.date.today()):
                    msg += f"🏅 {i}. {readable_date} — {item['score']} 分 (今日)\n"
                else:
                    msg += f"{i}. {readable_date} — {item['score']} 分\n"
            except:
                msg += f"{i}. {item['date']} — {item['score']} 分\n"

        if len(board) > 10:
            msg += f"\n... 共 {len(board)} 条记录"

        msg_box.setText(msg)
        msg_box.exec()

    def reset_for_new_day(self):
        """手动重置当日进度（主要用于测试）"""
        reply = QtWidgets.QMessageBox.question(
            self, '饿啊~',
            '警告！今天的进度将彻底清零，继续？',
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No,
            QtWidgets.QMessageBox.StandardButton.No
        )

        if reply == QtWidgets.QMessageBox.StandardButton.Yes:
            # 提交当前分数到排行榜
            self.tree_manager.submit_daily_score()

            # 重置当日进度
            self.tree_manager.daily_progress = 0.0
            self.tree_manager.daily_seedlings = 0
            self.tree_manager.daily_trees = 0
            self.tree_manager.daily_giants = 0

            # 更新显示
            self.progressBar.setValue(0)
            self.update_tree_display()
            self.update_score_display()
            self.save_current_progress()

            QtWidgets.QMessageBox.information(self, "提示", "当日进度已重置！")

    def closeEvent(self, event):
        # 关闭时提交当日分数
        self.tree_manager.submit_daily_score()
        self.save_current_progress()
        self.timer.stop()
        self.stream.stop()
        self.stream.close()
        event.accept()


# ======================
# 启动
# ======================
if __name__ == "__main__":
    print("log: TreePlanGay is starting... （细节gay）")

    app = QtWidgets.QApplication(sys.argv)

    # 设置应用程序暗色风格
    app.setStyle("Fusion")
    dark_palette = QtGui.QPalette()
    dark_palette.setColor(QtGui.QPalette.ColorRole.Window, QtGui.QColor(30, 30, 30))
    dark_palette.setColor(QtGui.QPalette.ColorRole.WindowText, QtGui.QColor(224, 224, 224))
    dark_palette.setColor(QtGui.QPalette.ColorRole.Base, QtGui.QColor(43, 43, 43))
    dark_palette.setColor(QtGui.QPalette.ColorRole.AlternateBase, QtGui.QColor(53, 53, 53))
    dark_palette.setColor(QtGui.QPalette.ColorRole.ToolTipBase, QtGui.QColor(224, 224, 224))
    dark_palette.setColor(QtGui.QPalette.ColorRole.ToolTipText, QtGui.QColor(224, 224, 224))
    dark_palette.setColor(QtGui.QPalette.ColorRole.Text, QtGui.QColor(224, 224, 224))
    dark_palette.setColor(QtGui.QPalette.ColorRole.Button, QtGui.QColor(60, 60, 60))
    dark_palette.setColor(QtGui.QPalette.ColorRole.ButtonText, QtGui.QColor(224, 224, 224))
    dark_palette.setColor(QtGui.QPalette.ColorRole.BrightText, QtGui.QColor(255, 255, 255))
    dark_palette.setColor(QtGui.QPalette.ColorRole.Link, QtGui.QColor(42, 130, 218))
    dark_palette.setColor(QtGui.QPalette.ColorRole.Highlight, QtGui.QColor(42, 130, 218))
    dark_palette.setColor(QtGui.QPalette.ColorRole.HighlightedText, QtGui.QColor(0, 0, 0))
    app.setPalette(dark_palette)

    window = LoudnessMonitor()
    window.show()
    sys.exit(app.exec())