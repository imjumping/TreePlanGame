'''
Apache license 2.0
Version 2.0, January 2004
Read https://www.apache.org/licenses/LICENSE-2.0
Full License is /LICENCE
'''
import sys
import os
import json
import datetime
import sounddevice as sd
import numpy as np
from PySide6 import QtCore, QtWidgets, QtGui

# 全局音频响度
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


def load_progress():
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {
        "progress": 0.0,
        "seedlings": 0,
        "trees": 0,
        "giants": 0,
        "last_date": str(datetime.date.today())
    }


def save_progress(data):
    with open(SAVE_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


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


# ======================
# 自定义流式布局（保持不变）
# ======================
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


# ======================
# 屏幕键盘（新增）
# ======================
class VirtualKeyboard(QtWidgets.QDialog):
    def __init__(self, parent=None, title="输入数字"):
        super().__init__(parent)
        self.setWindowFlags(QtCore.Qt.WindowType.FramelessWindowHint | QtCore.Qt.WindowType.Popup)
        self.setWindowTitle(title)
        self.input_value = ""
        layout = QtWidgets.QVBoxLayout()

        self.display = QtWidgets.QLineEdit()
        self.display.setReadOnly(True)
        self.display.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
        self.display.setStyleSheet("font-size: 18px; padding: 8px;")
        layout.addWidget(self.display)

        grid = QtWidgets.QGridLayout()
        buttons = [
            '1', '2', '3',
            '4', '5', '6',
            '7', '8', '9',
            '清空', '0', '删除'
        ]
        positions = [(i, j) for i in range(4) for j in range(3)]
        for pos, btn_text in zip(positions, buttons):
            btn = QtWidgets.QPushButton(btn_text)
            btn.setFixedSize(60, 50)
            btn.setStyleSheet("font-size: 16px;")
            btn.clicked.connect(lambda _, t=btn_text: self.button_clicked(t))
            grid.addWidget(btn, *pos)

        layout.addLayout(grid)

        btn_ok = QtWidgets.QPushButton("确定")
        btn_ok.setFixedHeight(40)
        btn_ok.setStyleSheet("font-size: 16px;")
        btn_ok.clicked.connect(self.accept)
        layout.addWidget(btn_ok)

        self.setLayout(layout)

    def button_clicked(self, text):
        if text == "清空":
            self.input_value = ""
        elif text == "删除":
            self.input_value = self.input_value[:-1]
        elif text.isdigit():
            self.input_value += text
        self.display.setText(self.input_value)

    def get_value(self):
        return self.input_value

    def set_value(self, val):
        self.input_value = str(val)
        self.display.setText(self.input_value)

    @staticmethod
    def get_int(parent=None, title="输入数字", value=0, min_val=0, max_val=999):
        dialog = VirtualKeyboard(parent, title)
        dialog.set_value(value)
        if dialog.exec():
            try:
                num = int(dialog.get_value())
                if min_val <= num <= max_val:
                    return num, True
            except ValueError:
                pass
        return value, False


# ======================
# 带虚拟键盘的 SpinBox（新增）
# ======================
class VirtualSpinBox(QtWidgets.QSpinBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)  # 防止实体键盘输入，强制用虚拟键盘
        self.setStyleSheet("background-color: #f0f0f0;")

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            val, ok = VirtualKeyboard.get_int(
                self,
                title="输入数值",
                value=self.value(),
                min_val=self.minimum(),
                max_val=self.maximum()
            )
            if ok:
                self.setValue(val)
        super().mousePressEvent(event)


class VirtualDoubleSpinBox(QtWidgets.QDoubleSpinBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setStyleSheet("background-color: #f0f0f0;")

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            # 模拟整数输入，保留1位小数
            val_int = int(self.value() * 10)
            val_int, ok = VirtualKeyboard.get_int(
                self,
                title="输入数值（×10）",
                value=val_int,
                min_val=int(self.minimum() * 10),
                max_val=int(self.maximum() * 10)
            )
            if ok:
                self.setValue(val_int / 10.0)
        super().mousePressEvent(event)


# ======================
# 树管理器（优化 update 返回值）
# ======================
class TreeManager:
    def __init__(self):
        self.morning_mode = False
        self.threshold_low = 35
        self.threshold_high = 50
        self.growth_speed = 25.0  # %/秒
        self.merge_count = 10

        self.progress = 0.0
        self.seedlings = 0
        self.trees = 0
        self.giants = 0
        self.last_date = str(datetime.date.today())

    def load_from_data(self, data):
        self.progress = data.get("progress", 0.0)
        self.seedlings = data.get("seedlings", 0)
        self.trees = data.get("trees", 0)
        self.giants = data.get("giants", 0)
        self.last_date = data.get("last_date", str(datetime.date.today()))

    def save_to_data(self):
        return {
            "progress": self.progress,
            "seedlings": self.seedlings,
            "trees": self.trees,
            "giants": self.giants,
            "last_date": self.last_date
        }

    def update(self, loudness):
        today = str(datetime.date.today())
        if self.last_date != today:
            self.submit_daily_score()
            self.last_date = today

        time_step = 0.01
        growth_increment = self.growth_speed * time_step

        if self.morning_mode:
            if loudness > self.threshold_high:
                self.progress += growth_increment
            else:
                self.progress = max(0.0, self.progress - 0.1)
        else:
            if loudness < self.threshold_low:
                self.progress += growth_increment
            else:
                self.progress *= 0.92

        tree_changed = False
        if self.progress >= 100:
            self.progress = 0
            self.seedlings += 1
            self._merge_trees()
            tree_changed = True

        return tree_changed

    def _merge_trees(self):
        if self.seedlings >= self.merge_count:
            new_trees = self.seedlings // self.merge_count
            self.trees += new_trees
            self.seedlings %= self.merge_count
            if self.trees >= self.merge_count:
                new_giants = self.trees // self.merge_count
                self.giants += new_giants
                self.trees %= self.merge_count

    def submit_daily_score(self):
        total_score = (
                self.seedlings * 1 +
                self.trees * self.merge_count +
                self.giants * (self.merge_count ** 2)
        )
        if total_score == 0:
            return
        board = load_leaderboard()
        today_str = str(datetime.date.today())
        if not any(item["date"] == today_str for item in board):
            board.append({"date": today_str, "score": total_score})
            board = bubble_sort_leaderboard(board)
            board = board[:30]
            save_leaderboard(board)


# ======================
# 设置窗口（使用虚拟 SpinBox）
# ======================
class SettingsDialog(QtWidgets.QDialog):
    def __init__(self, tree_manager, parent=None):
        super().__init__(parent)
        self.setWindowTitle("设置")
        self.resize(320, 220)
        self.tree_manager = tree_manager

        layout = QtWidgets.QFormLayout()

        self.low_spin = VirtualSpinBox()
        self.low_spin.setRange(1, 200)
        self.low_spin.setValue(self.tree_manager.threshold_low)

        self.high_spin = VirtualSpinBox()
        self.high_spin.setRange(1, 200)
        self.high_spin.setValue(self.tree_manager.threshold_high)

        self.speed_spin = VirtualDoubleSpinBox()
        self.speed_spin.setRange(0.1, 100.0)
        self.speed_spin.setSingleStep(1.0)
        self.speed_spin.setValue(self.tree_manager.growth_speed)

        self.merge_spin = VirtualSpinBox()
        self.merge_spin.setRange(2, 10)
        self.merge_spin.setValue(self.tree_manager.merge_count)
        layout.addRow("提示：按上下可以打开数字键盘", self.low_spin)
        layout.addRow("安静阈值（小声<）:", self.low_spin)
        layout.addRow("朗读阈值（大声>）:", self.high_spin)
        layout.addRow("增长速度（%/秒，实际会除以10，比如150是15.0）:", self.speed_spin)
        layout.addRow("合并数量:", self.merge_spin)

        ok_btn = QtWidgets.QPushButton("确定")
        ok_btn.clicked.connect(self.apply_and_close)
        layout.addWidget(ok_btn)
        self.setLayout(layout)

    def apply_and_close(self):
        self.tree_manager.threshold_low = self.low_spin.value()
        self.tree_manager.threshold_high = self.high_spin.value()
        self.tree_manager.growth_speed = self.speed_spin.value()
        self.tree_manager.merge_count = self.merge_spin.value()
        self.accept()


# ======================
# 主窗口（优化树显示逻辑）
# ======================
class LoudnessMonitor(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("中 暑 游 戏")
        self.resize(440, 400)

        self.tree_manager = TreeManager()
        saved = load_progress()
        self.tree_manager.load_from_data(saved)

        # ===== 顶部：早读模式开关 + 信息 + 设置按钮 =====
        topLayout = QtWidgets.QHBoxLayout()

        infoLayout = QtWidgets.QVBoxLayout()
        self.zuozhelabel = QtWidgets.QLabel("侯皓铭 - 制作")
        self.classlabel = QtWidgets.QLabel("使用PySide6开发")
        self.zuozhelabel.setStyleSheet("font-size: 12px; color: #555;")
        self.classlabel.setStyleSheet("font-size: 12px; color: #555;")
        infoLayout.addWidget(self.zuozhelabel)
        infoLayout.addWidget(self.classlabel)
        infoLayout.addStretch()
        topLayout.addLayout(infoLayout)

        self.morningCheckBox = QtWidgets.QCheckBox("早读模式")
        self.morningCheckBox.setChecked(self.tree_manager.morning_mode)
        self.morningCheckBox.stateChanged.connect(self.toggle_morning_mode)
        self.morningCheckBox.setStyleSheet("font-size: 14px; font-weight: bold;")
        topLayout.addStretch()
        topLayout.addWidget(self.morningCheckBox)
        topLayout.addStretch()

        self.setButton = QtWidgets.QPushButton("⚙")
        self.setButton.setFixedSize(30, 30)
        self.setButton.setStyleSheet("""
            QPushButton {
                border-radius: 15px;
                background-color: #000000;
                color: white;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #333333;
            }
        """)
        self.setButton.clicked.connect(self.open_settings)
        topLayout.addWidget(self.setButton)

        # ===== 主标题 =====
        self.titleLabel = QtWidgets.QLabel("-- 正在监听 --")
        self.titleLabel.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.titleLabel.setStyleSheet("font-size: 22px; font-weight: bold; margin: 8px 0;")

        # ===== 进度条 =====
        self.progressBar = QtWidgets.QProgressBar()
        self.progressBar.setRange(0, 100)
        self.progressBar.setValue(0)

        # ===== 树显示区 =====
        self.treeDisplay = QtWidgets.QWidget()
        self.treeDisplay.setFixedHeight(120)
        self.treeDisplay.setStyleSheet("""
            background-color: #e0f7fa;
            border-radius: 20px;
            padding: 8px;
        """)
        self.treeLayout = FlowLayout(self.treeDisplay)

        # ===== 按钮 =====
        self.rankButton = QtWidgets.QPushButton("🏆 查看排行榜")
        self.rankButton.clicked.connect(self.show_leaderboard)

        # ===== 主布局 =====
        mainLayout = QtWidgets.QVBoxLayout()
        mainLayout.addLayout(topLayout)
        mainLayout.addWidget(self.titleLabel)
        mainLayout.addWidget(self.progressBar)
        mainLayout.addWidget(QtWidgets.QLabel("你的小树林："))
        mainLayout.addWidget(self.treeDisplay)
        mainLayout.addWidget(self.rankButton)
        mainLayout.addStretch()
        self.setLayout(mainLayout)

        # ===== 启动 =====
        self.stream = start_microphone_monitor()
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_display)
        self.timer.start(10)
        self._last_icons = None
        self.update_tree_display()

    def toggle_morning_mode(self, state):
        self.tree_manager.morning_mode = (state == QtCore.Qt.CheckState.Checked.value)
        self.save_current_progress()

    def update_display(self):
        global result_sound
        mode_text = "（早读模式）" if self.tree_manager.morning_mode else "（安静模式）"
        self.titleLabel.setText(f"动静: {result_sound} {mode_text}")

        tree_changed = self.tree_manager.update(result_sound)
        self.progressBar.setValue(int(min(100, self.tree_manager.progress)))

        if tree_changed:
            self.update_tree_display()

        if getattr(self, '_save_counter', 0) % 500 == 0:
            self.save_current_progress()
        self._save_counter = getattr(self, '_save_counter', 0) + 1

    def update_tree_display(self):
        new_icons = ["🌱"] * self.tree_manager.seedlings + \
                    ["🌳"] * self.tree_manager.trees + \
                    ["大🌳"] * self.tree_manager.giants

        if self._last_icons == new_icons:
            return
        self._last_icons = new_icons

        while self.treeLayout.count():
            item = self.treeLayout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not new_icons:
            label = QtWidgets.QLabel("（保持安静或大声朗读来种树吧！）")
            label.setStyleSheet("color: gray; font-size: 12px;")
            self.treeLayout.addWidget(label)
        else:
            for icon in new_icons:
                label = QtWidgets.QLabel(icon)
                label.setStyleSheet("font-size: 24px; margin: 2px;")
                self.treeLayout.addWidget(label)

    def save_current_progress(self):
        data = self.tree_manager.save_to_data()
        save_progress(data)

    def open_settings(self):
        dialog = SettingsDialog(self.tree_manager, self)
        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            self.save_current_progress()

    def show_leaderboard(self):
        board = load_leaderboard()
        if not board:
            QtWidgets.QMessageBox.information(self, "排行榜", "暂无排行榜数据。")
            return
        msg = "🏆 近期排行榜\n\n"
        for i, item in enumerate(board[:10], 1):
            date_obj = datetime.datetime.strptime(item["date"], "%Y-%m-%d")
            readable_date = date_obj.strftime("%m月%d日")
            msg += f"{i}. {readable_date} — {item['score']} 分\n"
        QtWidgets.QMessageBox.information(self, "排行榜", msg)

    def closeEvent(self, event):
        self.save_current_progress()
        self.timer.stop()
        self.stream.stop()
        self.stream.close()
        event.accept()


# ======================
# 启动
# ======================
if __name__ == "__main__":
    print("log: 开始！")

    app = QtWidgets.QApplication(sys.argv)

    window = LoudnessMonitor()
    window.show()
    sys.exit(app.exec())