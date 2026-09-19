#!/usr/bin/env python3
"""gubby - a multitool desktop app"""

import sys, os, uuid, socket, json, random, string, urllib.parse, re, time, base64, difflib
from datetime import datetime

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QListWidget, QListWidgetItem, QLabel, QPushButton, QTextEdit,
    QLineEdit, QSpinBox, QCheckBox, QComboBox, QFileDialog,
    QProgressBar, QFrame, QGridLayout, QGroupBox, QDoubleSpinBox,
    QPlainTextEdit
)
from PyQt6.QtCore import Qt, QSize, QTimer, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QPixmap, QIcon, QPainter, QMovie

try:
    import qrcode
    HAS_QRCODE = True
except ImportError:
    HAS_QRCODE = False

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

BG = "#1e1e2e"
SIDEBAR = "#181825"
INPUT_BG = "#313244"
TEXT = "#cdd6f4"
ACCENT = "#cba6f7"
GREEN = "#a6e3a1"
RED = "#f38ba8"
BLUE = "#89b4fa"
SURFACE = "#45475a"
OVERLAY = "#585b70"
YELLOW = "#f9e2af"
PEACH = "#fab387"
MAUVE = "#cba6f7"
TEAL = "#94e2d5"

STYLESHEET = (
    "QMainWindow, QWidget { background-color: #1e1e2e; color: #cdd6f4; font-family: Segoe UI, Consolas, monospace; font-size: 13px; }"
    "QListWidget { background-color: #181825; color: #cdd6f4; border: none; padding: 4px; font-size: 13px; }"
    "QListWidget::item { padding: 8px 12px; border-radius: 6px; margin: 2px 4px; }"
    "QListWidget::item:selected { background-color: #cba6f7; color: #1e1e2e; }"
    "QListWidget::item:hover { background-color: #45475a; }"
    "QTextEdit, QPlainTextEdit, QLineEdit { background-color: #313244; color: #cdd6f4; border: 1px solid #45475a; border-radius: 6px; padding: 6px; font-family: Consolas, monospace; font-size: 13px; }"
    "QTextEdit:focus, QPlainTextEdit:focus, QLineEdit:focus { border: 1px solid #cba6f7; }"
    "QPushButton { background-color: #cba6f7; color: #1e1e2e; border: none; border-radius: 6px; padding: 8px 16px; font-weight: bold; font-size: 13px; }"
    "QPushButton:hover { background-color: #cba6f7; }"
    "QPushButton:pressed { background-color: #45475a; color: #cdd6f4; }"
    "QPushButton[cssClass='danger'] { background-color: #f38ba8; }"
    "QPushButton[cssClass='success'] { background-color: #a6e3a1; }"
    "QPushButton[cssClass='blue'] { background-color: #89b4fa; }"
    "QComboBox { background-color: #313244; color: #cdd6f4; border: 1px solid #45475a; border-radius: 6px; padding: 6px; }"
    "QComboBox::drop-down { border: none; }"
    "QComboBox QAbstractItemView { background-color: #313244; color: #cdd6f4; selection-background-color: #cba6f7; }"
    "QSpinBox, QDoubleSpinBox { background-color: #313244; color: #cdd6f4; border: 1px solid #45475a; border-radius: 6px; padding: 4px; }"
    "QProgressBar { background-color: #313244; border: 1px solid #45475a; border-radius: 6px; text-align: center; color: #cdd6f4; }"
    "QProgressBar::chunk { background-color: #cba6f7; border-radius: 5px; }"
    "QLabel { color: #cdd6f4; }"
    "QGroupBox { border: 1px solid #45475a; border-radius: 6px; margin-top: 8px; padding-top: 12px; font-weight: bold; }"
    "QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 4px; }"
    "QScrollArea { border: none; }"
    "QCheckBox { color: #cdd6f4; spacing: 6px; }"
    "QCheckBox::indicator { width: 16px; height: 16px; border: 1px solid #45475a; border-radius: 3px; background-color: #313244; }"
    "QCheckBox::indicator:checked { background-color: #cba6f7; border-color: #cba6f7; }"
    "QRadioButton { color: #cdd6f4; spacing: 6px; }"
)

def make_btn(text, css_class=None, handler=None):
    b = QPushButton(text)
    if css_class:
        b.setProperty("cssClass", css_class)
    if handler:
        b.clicked.connect(handler)
    return b

def make_input(placeholder="", text=""):
    e = QLineEdit()
    if placeholder:
        e.setPlaceholderText(placeholder)
    if text:
        e.setText(text)
    return e

def make_label(text, size=13, bold=False, color=TEXT):
    l = QLabel(text)
    f = l.font()
    f.setPointSize(size)
    f.setBold(bold)
    l.setFont(f)
    l.setStyleSheet(f"color: {color};")
    return l

def make_h_line():
    line = QFrame()
    line.setFrameShape(QFrame.Shape.HLine)
    line.setStyleSheet(f"color: {SURFACE};")
    return line

ASCII_FONT = {
    'A': ["  #  "," # # ","#   #","#####","#   #","#   #","#   #"],
    'B': ["#### ","#   #","#### ","#   #","#   #","#   #","#### "],
    'C': [" ####","#    ","#    ","#    ","#    ","#    "," ####"],
    'D': ["#### ","#   #","#   #","#   #","#   #","#   #","#### "],
    'E': ["#####","#    ","#### ","#    ","#    ","#    ","#####"],
    'F': ["#####","#    ","#### ","#    ","#    ","#    ","#    "],
    'G': [" ####","#    ","#  ##","#   #","#   #","#   #"," ### "],
    'H': ["#   #","#   #","#   #","#####","#   #","#   #","#   #"],
    'I': ["#####","  #  ","  #  ","  #  ","  #  ","  #  ","#####"],
    'J': ["#####","   # ","   # ","   # ","   # ","#  # "," ##  "],
    'K': ["#   #","#  # ","# #  ","##   ","# #  ","#  # ","#   #"],
    'L': ["#    ","#    ","#    ","#    ","#    ","#    ","#####"],
    'M': ["#   #","## ##","# # #","#   #","#   #","#   #","#   #"],
    'N': ["#   #","##  #","# # #","#  ##","#   #","#   #","#   #"],
    'O': [" ### ","#   #","#   #","#   #","#   #","#   #"," ### "],
    'P': ["#### ","#   #","#### ","#    ","#    ","#    ","#    "],
    'Q': [" ### ","#   #","#   #","#   #","# # #","#  # "," ## #"],
    'R': ["#### ","#   #","#### ","# #  ","#  # ","#   #","#   #"],
    'S': [" ####","#    "," ### ","    #","    #","#   #"," ### "],
    'T': ["#####","  #  ","  #  ","  #  ","  #  ","  #  ","  #  "],
    'U': ["#   #","#   #","#   #","#   #","#   #","#   #"," ### "],
    'V': ["#   #","#   #","#   #","#   #"," # # "," # # ","  #  "],
    'W': ["#   #","#   #","#   #","# # #","# # #","## ##","#   #"],
    'X': ["#   #"," # # ","  #  ","  #  ","  #  "," # # ","#   #"],
    'Y': ["#   #"," # # ","  #  ","  #  ","  #  ","  #  ","  #  "],
    'Z': ["#####","    #","   # ","  #  "," #   ","#    ","#####"],
    '0': [" ### ","#   #","#  ##","# # #","##  #","#   #"," ### "],
    '1': ["  #  "," ##  ","  #  ","  #  ","  #  ","  #  ","#####"],
    '2': [" ### ","#   #","    #","  ## "," #   ","#    ","#####"],
    '3': ["#####","    #","  ## ","    #","    #","#   #"," ### "],
    '4': ["#   #","#   #","#   #","#####","    #","    #","    #"],
    '5': ["#####","#    ","#### ","    #","    #","#   #"," ### "],
    '6': [" ####","#    ","#### ","#   #","#   #","#   #"," ### "],
    '7': ["#####","    #","   # ","  #  "," #   ","#    ","#    "],
    '8': [" ### ","#   #"," ### ","#   #","#   #","#   #"," ### "],
    '9': [" ### ","#   #","#   #"," ####","    #","   # "," ##  "],
    ' ': ["     ","     ","     ","     ","     ","     ","     "],
    '.': ["     ","     ","     ","     ","     "," ##  "," ##  "],
    '!': ["  #  ","  #  ","  #  ","  #  ","  #  ","     ","  #  "],
    '?': [" ### ","#   #","    #","  ## ","  #  ","     ","  #  "],
    '-': ["     ","     ","     ","#####","     ","     ","     "],
    '_': ["     ","     ","     ","     ","     ","     ","#####"],
    '+': ["     ","  #  ","  #  ","#####","  #  ","  #  ","     "],
    '=': ["     ","     ","#####","     ","#####","     ","     "],
}

def ascii_art(text):
    text = text.upper()
    lines = [""] * 7
    for ch in text:
        glyph = ASCII_FONT.get(ch, ASCII_FONT["?"])
        for i in range(7):
            lines[i] += glyph[i] + " "
    return "\n".join(lines)

class HttpRequestThread(QThread):
    finished = pyqtSignal(str, int)
    error = pyqtSignal(str)

    def __init__(self, method, url, body=""):
        super().__init__()
        self.method = method
        self.url = url
        self.body = body

    def run(self):
        import urllib.request, urllib.error
        try:
            req = urllib.request.Request(self.url, method=self.method)
            if self.body and self.method in ("POST", "PUT", "PATCH"):
                req.data = self.body.encode("utf-8")
                req.add_header("Content-Type", "application/json")
            resp = urllib.request.urlopen(req, timeout=15)
            code = resp.getcode()
            data = resp.read().decode("utf-8", errors="replace")
            self.finished.emit(data, code)
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace") if e.fp else ""
            self.finished.emit(body, e.code)
        except Exception as e:
            self.error.emit(str(e))

class PortScanThread(QThread):
    found = pyqtSignal(int)
    progress = pyqtSignal(int)
    finished_scan = pyqtSignal()

    def __init__(self, host, port_start, port_end):
        super().__init__()
        self.host = host
        self.start_port = port_start
        self.end_port = port_end
        self._stop = False

    def run(self):
        total = self.end_port - self.start_port + 1
        for i, port in enumerate(range(self.start_port, self.end_port + 1)):
            if self._stop:
                break
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(0.3)
                if s.connect_ex((self.host, port)) == 0:
                    self.found.emit(port)
                s.close()
            except Exception:
                pass
            if total > 0:
                self.progress.emit(int((i + 1) / total * 100))
        self.finished_scan.emit()

    def stop(self):
        self._stop = True

class QStackedWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._widgets = []
        self._current = -1

    def addWidget(self, wdg):
        self._layout.addWidget(wdg)
        self._widgets.append(wdg)
        wdg.hide()
        return len(self._widgets) - 1

    def setCurrentIndex(self, idx):
        if idx < 0 or idx >= len(self._widgets):
            return
        if self._current >= 0:
            self._widgets[self._current].hide()
        self._current = idx
        self._widgets[idx].show()


def widget_text_diff():
    w = QWidget()
    lay = QVBoxLayout(w)
    lay.addWidget(make_label("Text Diff", 16, True, ACCENT))
    row = QHBoxLayout()
    left = QTextEdit()
    left.setPlaceholderText("Original text...")
    right = QTextEdit()
    right.setPlaceholderText("Modified text...")
    row.addWidget(left)
    row.addWidget(right)
    lay.addLayout(row)
    diff_out = QTextEdit()
    diff_out.setReadOnly(True)
    diff_out.setStyleSheet(f"background-color: {INPUT_BG};")
    lay.addWidget(diff_out)

    def do_diff():
        a = left.toPlainText().splitlines()
        b = right.toPlainText().splitlines()
        lines = []
        for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b).get_opcodes():
            if tag == "equal":
                for line in a[i1:i2]:
                    lines.append(f"  {line}")
            elif tag == "replace":
                for line in a[i1:i2]:
                    lines.append(f"- {line}")
                for line in b[j1:j2]:
                    lines.append(f"+ {line}")
            elif tag == "insert":
                for line in b[j1:j2]:
                    lines.append(f"+ {line}")
            elif tag == "delete":
                for line in a[i1:i2]:
                    lines.append(f"- {line}")
        diff_out.setPlainText("\n".join(lines) if lines else "(no differences)")

    lay.addWidget(make_btn("Compare", handler=do_diff))
    return w

def widget_base64():
    w = QWidget()
    lay = QVBoxLayout(w)
    lay.addWidget(make_label("Base64 Encode / Decode", 16, True, ACCENT))
    inp = QTextEdit()
    inp.setPlaceholderText("Input text...")
    lay.addWidget(inp)
    row = QHBoxLayout()
    def do_encode():
        out.setPlainText(base64.b64encode(inp.toPlainText().encode()).decode())
    def do_decode():
        try:
            out.setPlainText(base64.b64decode(inp.toPlainText().encode()).decode())
        except Exception as e:
            out.setPlainText(f"Error: {e}")
    row.addWidget(make_btn("Encode", handler=do_encode))
    row.addWidget(make_btn("Decode", handler=do_decode))
    lay.addLayout(row)
    out = QTextEdit()
    out.setReadOnly(True)
    out.setPlaceholderText("Output...")
    lay.addWidget(out)
    row2 = QHBoxLayout()
    row2.addWidget(make_btn("Copy Output", css_class="blue", handler=lambda: QApplication.clipboard().setText(out.toPlainText())))
    row2.addStretch()
    lay.addLayout(row2)
    return w

def widget_url_codec():
    w = QWidget()
    lay = QVBoxLayout(w)
    lay.addWidget(make_label("URL Encode / Decode", 16, True, ACCENT))
    inp = QLineEdit()
    inp.setPlaceholderText("Enter URL or encoded string...")
    lay.addWidget(inp)
    out = QLineEdit()
    out.setReadOnly(True)
    out.setPlaceholderText("Result...")
    lay.addWidget(out)
    row = QHBoxLayout()
    row.addWidget(make_btn("Encode", handler=lambda: out.setText(urllib.parse.quote(inp.text()))))
    row.addWidget(make_btn("Decode", handler=lambda: out.setText(urllib.parse.unquote(inp.text()))))
    lay.addLayout(row)
    return w

def widget_json_formatter():
    w = QWidget()
    lay = QVBoxLayout(w)
    lay.addWidget(make_label("JSON Formatter", 16, True, ACCENT))
    inp = QTextEdit()
    inp.setPlaceholderText("Paste JSON here...")
    lay.addWidget(inp)
    err = QLabel("")
    err.setStyleSheet(f"color: {RED};")
    lay.addWidget(err)
    out = QTextEdit()
    out.setReadOnly(True)
    lay.addWidget(out)
    def fmt_json(indent):
        err.setText("")
        try:
            obj = json.loads(inp.toPlainText())
            out.setPlainText(json.dumps(obj, indent=indent))
        except Exception as e:
            err.setText(str(e))
            out.setPlainText("")
    row = QHBoxLayout()
    row.addWidget(make_btn("Format", handler=lambda: fmt_json(2)))
    row.addWidget(make_btn("Minify", handler=lambda: fmt_json(0)))
    row.addWidget(make_btn("Copy", css_class="blue", handler=lambda: QApplication.clipboard().setText(out.toPlainText())))
    lay.addLayout(row)
    return w

def widget_markdown_preview():
    w = QWidget()
    lay = QVBoxLayout(w)
    lay.addWidget(make_label("Markdown Preview", 16, True, ACCENT))
    row = QHBoxLayout()
    inp = QTextEdit()
    inp.setPlaceholderText("Write markdown here...")
    inp.setPlainText("# Hello\n\n**Bold** and *italic*\n\n- Item 1\n- Item 2\n\n```\ncode block\n```")
    preview = QTextEdit()
    preview.setReadOnly(True)
    row.addWidget(inp)
    row.addWidget(preview)
    lay.addLayout(row)
    def render_md():
        t = inp.toPlainText()
        lines = t.split("\n")
        out_lines = []
        in_code = False
        for line in lines:
            if line.strip().startswith("```"):
                in_code = not in_code
                out_lines.append("<br>" if in_code else "")
                continue
            if in_code:
                out_lines.append(f'<span style="font-family:Consolas;color:{YELLOW}">{line}</span><br>')
                continue
            if line.startswith("### "):
                out_lines.append(f'<h3 style="color:{BLUE}">{line[4:]}</h3>')
            elif line.startswith("## "):
                out_lines.append(f'<h2 style="color:{BLUE}">{line[3:]}</h2>')
            elif line.startswith("# "):
                out_lines.append(f'<h1 style="color:{ACCENT}">{line[2:]}</h1>')
            elif line.startswith("- "):
                out_lines.append(f"&nbsp;&nbsp;&bull; {line[2:]}<br>")
            elif line.strip() == "":
                out_lines.append("<br>")
            else:
                t2 = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", line)
                t2 = re.sub(r"\*(.+?)\*", r"<i>\1</i>", t2)
                t2 = re.sub(r"`(.+?)`", f'<span style="color:{GREEN}">\1</span>', t2)
                out_lines.append(f"{t2}<br>")
        preview.setHtml("".join(out_lines))
    btn_row = QHBoxLayout()
    btn_row.addWidget(make_btn("Render", css_class="success", handler=render_md))
    btn_row.addStretch()
    lay.addLayout(btn_row)
    return w

def widget_word_counter():
    w = QWidget()
    lay = QVBoxLayout(w)
    lay.addWidget(make_label("Word Counter", 16, True, ACCENT))
    inp = QTextEdit()
    inp.setPlaceholderText("Type or paste text here...")
    lay.addWidget(inp)
    stats = make_label("Words: 0 | Chars: 0 | Lines: 0 | Sentences: 0", 14, False, BLUE)
    lay.addWidget(stats)
    def update():
        t = inp.toPlainText()
        words = len(t.split()) if t.strip() else 0
        chars = len(t)
        lines = t.count("\n") + (1 if t else 0)
        sents = len(re.split(r"[.!?]+", t.strip())) if t.strip() else 0
        stats.setText(f"Words: {words} | Chars: {chars} | Lines: {lines} | Sentences: {sents}")
    inp.textChanged.connect(update)
    return w

def widget_lorem_ipsum():
    w = QWidget()
    lay = QVBoxLayout(w)
    lay.addWidget(make_label("Lorem Ipsum Generator", 16, True, ACCENT))
    row = QHBoxLayout()
    row.addWidget(make_label("Paragraphs:"))
    count = QSpinBox()
    count.setRange(1, 50)
    count.setValue(3)
    row.addWidget(count)
    row.addStretch()
    lay.addLayout(row)
    pool = [
        "Lorem ipsum dolor sit amet, consectetur adipiscing elit.",
        "Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.",
        "Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris.",
        "Nisi ut aliquip ex ea commodo consequat duis aute irure dolor.",
        "In reprehenderit in voluptate velit esse cillum dolore eu fugiat.",
        "Nulla pariatur excepteur sint occaecat cupidatat non proident.",
        "Sunt in culpa qui officia deserunt mollit anim id est laborum.",
        "Curabitur pretium tincidunt lacus nunc pellentesque magna.",
        "Donec ac odio tempor orci dapibus ultrices in iaculis nunc.",
        "Praesent elementum facilisis leo vel fringilla est ullamcorper.",
    ]
    out = QTextEdit()
    out.setReadOnly(True)
    lay.addWidget(out)
    def gen():
        paras = []
        for _ in range(count.value()):
            sentences = random.sample(pool, min(len(pool), random.randint(3, 6)))
            paras.append(" ".join(sentences))
        out.setPlainText("\n\n".join(paras))
    lay.addWidget(make_btn("Generate", css_class="success", handler=gen))
    return w

def widget_password_gen():
    w = QWidget()
    lay = QVBoxLayout(w)
    lay.addWidget(make_label("Password Generator", 16, True, ACCENT))
    row = QHBoxLayout()
    row.addWidget(make_label("Length:"))
    length = QSpinBox()
    length.setRange(4, 128)
    length.setValue(16)
    row.addWidget(length)
    lay.addLayout(row)
    cb_upper = QCheckBox("ABC (Uppercase)")
    cb_upper.setChecked(True)
    cb_lower = QCheckBox("abc (Lowercase)")
    cb_lower.setChecked(True)
    cb_digits = QCheckBox("123 (Digits)")
    cb_digits.setChecked(True)
    cb_symbols = QCheckBox("!@# (Symbols)")
    cb_symbols.setChecked(True)
    for cb in [cb_upper, cb_lower, cb_digits, cb_symbols]:
        lay.addWidget(cb)
    out = QLineEdit()
    out.setReadOnly(True)
    lay.addWidget(out)
    def gen():
        pool = ""
        if cb_upper.isChecked(): pool += string.ascii_uppercase
        if cb_lower.isChecked(): pool += string.ascii_lowercase
        if cb_digits.isChecked(): pool += string.digits
        if cb_symbols.isChecked(): pool += string.punctuation
        if not pool:
            out.setText("(select at least one character set)")
            return
        out.setText("".join(random.choices(pool, k=length.value())))
    row2 = QHBoxLayout()
    row2.addWidget(make_btn("Generate", css_class="success", handler=gen))
    row2.addWidget(make_btn("Copy", css_class="blue", handler=lambda: QApplication.clipboard().setText(out.text())))
    lay.addLayout(row2)
    return w

def widget_uuid_gen():
    w = QWidget()
    lay = QVBoxLayout(w)
    lay.addWidget(make_label("UUID Generator", 16, True, ACCENT))
    row = QHBoxLayout()
    row.addWidget(make_label("Count:"))
    count = QSpinBox()
    count.setRange(1, 100)
    count.setValue(5)
    row.addWidget(count)
    row.addStretch()
    lay.addLayout(row)
    out = QTextEdit()
    out.setReadOnly(True)
    lay.addWidget(out)
    def gen():
        uuids = [str(uuid.uuid4()) for _ in range(count.value())]
        out.setPlainText("\n".join(uuids))
    row2 = QHBoxLayout()
    row2.addWidget(make_btn("Generate", css_class="success", handler=gen))
    row2.addWidget(make_btn("Copy All", css_class="blue", handler=lambda: QApplication.clipboard().setText(out.toPlainText())))
    lay.addLayout(row2)
    return w

def widget_color_picker():
    w = QWidget()
    lay = QVBoxLayout(w)
    lay.addWidget(make_label("Color Picker", 16, True, ACCENT))
    row = QHBoxLayout()
    row.addWidget(make_label("Hex:"))
    inp = make_input("#cba6f7")
    inp.setMaximumWidth(200)
    row.addWidget(inp)
    row.addStretch()
    lay.addLayout(row)
    preview = QLabel()
    preview.setFixedSize(200, 100)
    preview.setStyleSheet("background-color: #cba6f7; border-radius: 8px;")
    lay.addWidget(preview)
    info = make_label("RGB: 203, 166, 247")
    lay.addWidget(info)
    def update_color():
        h = inp.text().strip().lstrip("#")
        if len(h) == 6:
            try:
                r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
                preview.setStyleSheet(f"background-color: #{h}; border-radius: 8px;")
                info.setText(f"RGB: {r}, {g}, {b}")
            except ValueError:
                pass
    inp.textChanged.connect(update_color)
    update_color()
    return w

def widget_image_base64():
    w = QWidget()
    lay = QVBoxLayout(w)
    lay.addWidget(make_label("Image to Base64", 16, True, ACCENT))
    chosen = [None]
    path_lbl = make_label("No file selected")
    lay.addWidget(path_lbl)
    def pick():
        path, _ = QFileDialog.getOpenFileName(w, "Select Image", "", "Images (*.png *.jpg *.jpeg *.gif *.bmp *.webp)")
        if path:
            chosen[0] = path
            path_lbl.setText(path)
    lay.addWidget(make_btn("Choose Image", handler=pick))
    out = QTextEdit()
    out.setReadOnly(True)
    out.setPlaceholderText("Base64 output...")
    lay.addWidget(out)
    def convert():
        if not chosen[0]:
            return
        try:
            with open(chosen[0], "rb") as f:
                data = base64.b64encode(f.read()).decode()
            out.setPlainText(data)
        except Exception as e:
            out.setPlainText(f"Error: {e}")
    row = QHBoxLayout()
    row.addWidget(make_btn("Convert", css_class="success", handler=convert))
    row.addWidget(make_btn("Copy", css_class="blue", handler=lambda: QApplication.clipboard().setText(out.toPlainText())))
    lay.addLayout(row)
    return w

def widget_qr_code():
    w = QWidget()
    lay = QVBoxLayout(w)
    lay.addWidget(make_label("QR Code Generator", 16, True, ACCENT))
    inp = make_input("Enter text or URL...")
    lay.addWidget(inp)
    preview = QLabel()
    preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
    preview.setMinimumSize(256, 256)
    preview.setStyleSheet(f"background-color: {INPUT_BG}; border-radius: 8px;")
    lay.addWidget(preview)
    err = QLabel("")
    err.setStyleSheet(f"color: {RED};")
    lay.addWidget(err)
    def gen():
        if not HAS_QRCODE:
            err.setText("qrcode library not installed. Run: pip install qrcode[pil]")
            return
        err.setText("")
        data = inp.text()
        if not data:
            return
        qr = qrcode.QRCode(version=1, box_size=8, border=2)
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        import io
        bio = io.BytesIO()
        img.save(bio, format="PNG")
        bio.seek(0)
        pixmap = QPixmap()
        pixmap.loadFromData(bio.read())
        preview.setPixmap(pixmap.scaled(256, 256, Qt.AspectRatioMode.KeepAspectRatio))
    lay.addWidget(make_btn("Generate QR", css_class="success", handler=gen))
    return w

def widget_ip_lookup():
    w = QWidget()
    lay = QVBoxLayout(w)
    lay.addWidget(make_label("IP Lookup", 16, True, ACCENT))
    inp = make_input("Enter hostname (e.g. google.com)")
    lay.addWidget(inp)
    out = QTextEdit()
    out.setReadOnly(True)
    lay.addWidget(out)
    def lookup():
        host = inp.text().strip()
        if not host:
            return
        try:
            result = socket.gethostbyname_ex(host)
            lines = [f"Hostname: {result[0]}", "IP Addresses:"]
            for ip in result[2]:
                lines.append(f"  {ip}")
            if result[1]:
                lines.insert(1, f"Aliases: {", ".join(result[1])}")
            out.setPlainText("\n".join(lines))
        except Exception as e:
            out.setPlainText(f"Error: {e}")
    lay.addWidget(make_btn("Lookup", css_class="blue", handler=lookup))
    return w

def widget_http_request():
    w = QWidget()
    lay = QVBoxLayout(w)
    lay.addWidget(make_label("HTTP Request Tester", 16, True, ACCENT))
    row = QHBoxLayout()
    method = QComboBox()
    method.addItems(["GET", "POST", "PUT", "DELETE", "PATCH"])
    row.addWidget(method)
    url = make_input("https://httpbin.org/get")
    row.addWidget(url)
    lay.addLayout(row)
    lay.addWidget(make_label("Body (for POST/PUT/PATCH):"))
    body = QTextEdit()
    body.setPlaceholderText('{"key": "value"}')
    body.setMaximumHeight(100)
    lay.addWidget(body)
    status_lbl = make_label("")
    lay.addWidget(status_lbl)
    resp_out = QTextEdit()
    resp_out.setReadOnly(True)
    lay.addWidget(resp_out)
    thread_ref = [None]
    def send():
        if thread_ref[0] and thread_ref[0].isRunning():
            return
        status_lbl.setText("Sending...")
        status_lbl.setStyleSheet(f"color: {YELLOW};")
        t = HttpRequestThread(method.currentText(), url.text(), body.toPlainText())
        def on_finish(data, code):
            resp_out.setPlainText(data)
            status_lbl.setText(f"Status: {code}")
            if 200 <= code < 300:
                status_lbl.setStyleSheet(f"color: {GREEN};")
            else:
                status_lbl.setStyleSheet(f"color: {RED};")
        t.finished.connect(on_finish)
        def on_error(e):
            resp_out.setPlainText(f"Error: {e}")
            status_lbl.setText("Error")
            status_lbl.setStyleSheet(f"color: {RED};")
        t.error.connect(on_error)
        thread_ref[0] = t
        t.start()
    lay.addWidget(make_btn("Send Request", css_class="success", handler=send))
    return w

def widget_port_scanner():
    w = QWidget()
    lay = QVBoxLayout(w)
    lay.addWidget(make_label("Port Scanner", 16, True, ACCENT))
    row = QHBoxLayout()
    row.addWidget(make_label("Host:"))
    host = make_input("127.0.0.1")
    host.setMaximumWidth(200)
    row.addWidget(host)
    row.addWidget(make_label("Ports:"))
    pstart = QSpinBox()
    pstart.setRange(1, 65535)
    pstart.setValue(1)
    pend = QSpinBox()
    pend.setRange(1, 65535)
    pend.setValue(1024)
    row.addWidget(pstart)
    row.addWidget(make_label("-"))
    row.addWidget(pend)
    row.addStretch()
    lay.addLayout(row)
    prog = QProgressBar()
    prog.setValue(0)
    lay.addWidget(prog)
    open_ports = QTextEdit()
    open_ports.setReadOnly(True)
    open_ports.setPlaceholderText("Open ports will appear here...")
    lay.addWidget(open_ports)
    thread_ref = [None]
    def start_scan():
        if thread_ref[0] and thread_ref[0].isRunning():
            thread_ref[0].stop()
            return
        open_ports.clear()
        h = host.text().strip()
        if not h:
            return
        try:
            socket.gethostbyname(h)
        except Exception:
            open_ports.setPlainText(f"Cannot resolve {h}")
            return
        t = PortScanThread(h, pstart.value(), pend.value())
        t.found.connect(lambda p: open_ports.append(f"Port {p}: OPEN"))
        t.progress.connect(lambda v: prog.setValue(v))
        t.finished_scan.connect(lambda: prog.setValue(100))
        thread_ref[0] = t
        t.start()
    lay.addWidget(make_btn("Scan Ports", css_class="success", handler=start_scan))
    return w

def widget_dns_lookup():
    w = QWidget()
    lay = QVBoxLayout(w)
    lay.addWidget(make_label("DNS Lookup", 16, True, ACCENT))
    inp = make_input("Enter domain (e.g. example.com)")
    lay.addWidget(inp)
    out = QTextEdit()
    out.setReadOnly(True)
    lay.addWidget(out)
    def lookup():
        domain = inp.text().strip()
        if not domain:
            return
        try:
            result = socket.gethostbyname_ex(domain)
            lines = [f"Domain: {result[0]}", "A Records:"]
            for ip in result[2]:
                lines.append(f"  {ip}")
            if result[1]:
                lines.append("Aliases:")
                for a in result[1]:
                    lines.append(f"  {a}")
            try:
                rev = socket.gethostbyaddr(result[2][0])
                lines.append(f"Reverse DNS: {rev[0]}")
            except Exception:
                pass
            out.setPlainText("\n".join(lines))
        except Exception as e:
            out.setPlainText(f"Error: {e}")
    lay.addWidget(make_btn("Resolve", css_class="blue", handler=lookup))
    return w

def widget_pomodoro():
    w = QWidget()
    lay = QVBoxLayout(w)
    lay.addWidget(make_label("Pomodoro Timer", 16, True, ACCENT))
    row = QHBoxLayout()
    row.addWidget(make_label("Work (min):"))
    work_min = QSpinBox(); work_min.setRange(1, 120); work_min.setValue(25)
    row.addWidget(work_min)
    row.addWidget(make_label("Break (min):"))
    break_min = QSpinBox(); break_min.setRange(1, 60); break_min.setValue(5)
    row.addWidget(break_min); row.addStretch()
    lay.addLayout(row)
    timer_lbl = make_label("25:00", 48, True, GREEN)
    timer_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    lay.addWidget(timer_lbl)
    phase_lbl = make_label("Work", 16, True)
    phase_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    lay.addWidget(phase_lbl)
    state = {"running": False, "is_work": True, "seconds": 25 * 60, "timer": None}
    def tick():
        if not state["running"]: return
        state["seconds"] -= 1
        if state["seconds"] <= 0:
            state["is_work"] = not state["is_work"]
            if state["is_work"]:
                state["seconds"] = work_min.value() * 60
                phase_lbl.setText("Work")
                phase_lbl.setStyleSheet(f"color: {GREEN}; font-size: 16px; font-weight: bold;")
            else:
                state["seconds"] = break_min.value() * 60
                phase_lbl.setText("Break")
                phase_lbl.setStyleSheet(f"color: {BLUE}; font-size: 16px; font-weight: bold;")
        m, s = divmod(state["seconds"], 60)
        timer_lbl.setText(f"{m:02d}:{s:02d}")
    def start():
        if state["running"]:
            state["running"] = False; return
        state["running"] = True
        if state["seconds"] == 0:
            state["seconds"] = work_min.value() * 60; state["is_work"] = True
        if not state["timer"]:
            state["timer"] = QTimer(); state["timer"].timeout.connect(tick)
        state["timer"].start(1000)
    def reset():
        state["running"] = False; state["is_work"] = True
        state["seconds"] = work_min.value() * 60
        m, s = divmod(state["seconds"], 60)
        timer_lbl.setText(f"{m:02d}:{s:02d}")
        phase_lbl.setText("Work")
        phase_lbl.setStyleSheet(f"color: {GREEN}; font-size: 16px; font-weight: bold;")
    row2 = QHBoxLayout()
    row2.addWidget(make_btn("Start / Pause", css_class="success", handler=start))
    row2.addWidget(make_btn("Reset", css_class="danger", handler=reset))
    row2.addStretch()
    lay.addLayout(row2)
    return w

def widget_stopwatch():
    w = QWidget()
    lay = QVBoxLayout(w)
    lay.addWidget(make_label("Stopwatch", 16, True, ACCENT))
    display = make_label("00:00:00.000", 48, True, ACCENT)
    display.setAlignment(Qt.AlignmentFlag.AlignCenter)
    lay.addWidget(display)
    state = {"running": False, "elapsed": 0, "start": 0, "laps": [], "timer": None}
    def tick():
        if not state["running"]: return
        now = time.time()
        elapsed = state["elapsed"] + (now - state["start"])
        h = int(elapsed // 3600); m = int((elapsed % 3600) // 60)
        s = int(elapsed % 60); ms = int((elapsed % 1) * 1000)
        display.setText(f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}")
    def start_stop():
        if state["running"]:
            state["elapsed"] += time.time() - state["start"]; state["running"] = False
        else:
            state["start"] = time.time(); state["running"] = True
            if not state["timer"]:
                state["timer"] = QTimer(); state["timer"].timeout.connect(tick)
            state["timer"].start(10)
    def lap():
        if state["running"]:
            elapsed = state["elapsed"] + (time.time() - state["start"])
            state["laps"].append(elapsed)
            m = int((elapsed % 3600) // 60); s = int(elapsed % 60); ms = int((elapsed % 1) * 1000)
            lap_list.appendPlainText(f"Lap {len(state["laps"])}: {m:02d}:{s:02d}.{ms:03d}")
    def reset():
        state["running"] = False; state["elapsed"] = 0; state["laps"] = []
        display.setText("00:00:00.000"); lap_list.clear()
    row = QHBoxLayout()
    row.addWidget(make_btn("Start / Stop", css_class="success", handler=start_stop))
    row.addWidget(make_btn("Lap", css_class="blue", handler=lap))
    row.addWidget(make_btn("Reset", css_class="danger", handler=reset))
    lay.addLayout(row)
    lap_list = QTextEdit(); lap_list.setReadOnly(True); lap_list.setMaximumHeight(150)
    lay.addWidget(lap_list)
    return w

def widget_unit_converter():
    w = QWidget()
    lay = QVBoxLayout(w)
    lay.addWidget(make_label("Unit Converter", 16, True, ACCENT))
    categories = {
        "Length": {"Meter": 1, "Kilometer": 1000, "Centimeter": 0.01, "Millimeter": 0.001, "Mile": 1609.344, "Yard": 0.9144, "Foot": 0.3048, "Inch": 0.0254},
        "Weight": {"Kilogram": 1, "Gram": 0.001, "Milligram": 0.000001, "Pound": 0.453592, "Ounce": 0.0283495, "Ton": 1000},
        "Temperature": {"Celsius": "C", "Fahrenheit": "F", "Kelvin": "K"}
    }
    cat_dd = QComboBox(); cat_dd.addItems(categories.keys())
    from_dd = QComboBox(); to_dd = QComboBox()
    val_in = QDoubleSpinBox(); val_in.setRange(-1e12, 1e12); val_in.setValue(1)
    result_lbl = make_label("Result: ---", 16, True, GREEN)
    def update_units():
        units = list(categories[cat_dd.currentText()].keys())
        from_dd.clear(); to_dd.clear(); from_dd.addItems(units); to_dd.addItems(units)
    cat_dd.currentTextChanged.connect(update_units); update_units()
    def convert():
        cat = cat_dd.currentText(); v = val_in.value()
        if cat == "Temperature":
            f, t = from_dd.currentText(), to_dd.currentText()
            if f == "Celsius" and t == "Fahrenheit": r = v * 9/5 + 32
            elif f == "Fahrenheit" and t == "Celsius": r = (v - 32) * 5/9
            elif f == "Celsius" and t == "Kelvin": r = v + 273.15
            elif f == "Kelvin" and t == "Celsius": r = v - 273.15
            elif f == "Fahrenheit" and t == "Kelvin": r = (v - 32) * 5/9 + 273.15
            elif f == "Kelvin" and t == "Fahrenheit": r = (v - 273.15) * 9/5 + 32
            else: r = v
        else:
            factor = categories[cat]
            r = v * factor[from_dd.currentText()] / factor[to_dd.currentText()]
        result_lbl.setText(f"Result: {r:,.6g} {to_dd.currentText()}")
    row = QHBoxLayout(); row.addWidget(make_label("Category:")); row.addWidget(cat_dd)
    lay.addLayout(row)
    row2 = QHBoxLayout(); row2.addWidget(from_dd); row2.addWidget(make_label("->")); row2.addWidget(to_dd)
    lay.addLayout(row2)
    row3 = QHBoxLayout(); row3.addWidget(val_in); row3.addWidget(make_btn("Convert", css_class="success", handler=convert))
    lay.addLayout(row3)
    lay.addWidget(result_lbl)
    return w

def widget_notepad():
    w = QWidget()
    lay = QVBoxLayout(w)
    lay.addWidget(make_label("Notepad", 16, True, ACCENT))
    editor = QPlainTextEdit()
    editor.setPlaceholderText("Start typing...")
    editor.setFont(QFont("Consolas", 13))
    lay.addWidget(editor)
    info = make_label("Chars: 0 | Words: 0 | Lines: 1")
    lay.addWidget(info)
    def update():
        t = editor.toPlainText()
        info.setText(f"Chars: {len(t)} | Words: {len(t.split()) if t.strip() else 0} | Lines: {t.count(chr(10)) + 1}")
    editor.textChanged.connect(update)
    row = QHBoxLayout()
    row.addWidget(make_btn("Clear", css_class="danger", handler=lambda: (editor.clear(), update())))
    row.addWidget(make_btn("Copy All", css_class="blue", handler=lambda: QApplication.clipboard().setText(editor.toPlainText())))
    row.addStretch()
    lay.addLayout(row)
    return w

def widget_ascii_art():
    w = QWidget()
    lay = QVBoxLayout(w)
    lay.addWidget(make_label("ASCII Art", 16, True, ACCENT))
    inp = make_input("Enter text (A-Z, 0-9)")
    lay.addWidget(inp)
    out = QTextEdit(); out.setReadOnly(True)
    out.setFont(QFont("Consolas", 9))
    lay.addWidget(out)
    def gen():
        out.setPlainText(ascii_art(inp.text()))
    inp.returnPressed.connect(gen)
    lay.addWidget(make_btn("Generate", css_class="success", handler=gen))
    return w

TOOLS = [
    ("Text Diff", widget_text_diff),
    ("Base64", widget_base64),
    ("URL Encode/Decode", widget_url_codec),
    ("JSON Formatter", widget_json_formatter),
    ("Markdown Preview", widget_markdown_preview),
    ("Word Counter", widget_word_counter),
    ("Lorem Ipsum", widget_lorem_ipsum),
    ("Password Generator", widget_password_gen),
    ("UUID Generator", widget_uuid_gen),
    ("Color Picker", widget_color_picker),
    ("Image to Base64", widget_image_base64),
    ("QR Code Generator", widget_qr_code),
    ("IP Lookup", widget_ip_lookup),
    ("HTTP Request", widget_http_request),
    ("Port Scanner", widget_port_scanner),
    ("DNS Lookup", widget_dns_lookup),
    ("Pomodoro Timer", widget_pomodoro),
    ("Stopwatch", widget_stopwatch),
    ("Unit Converter", widget_unit_converter),
    ("Notepad", widget_notepad),
    ("ASCII Art", widget_ascii_art),
]

TOOLS_PER_SECTION = {
    "Text Tools": list(range(9)),
    "Media": list(range(9, 12)),
    "Network": list(range(12, 16)),
    "Misc": list(range(16, 21)),
}

GUBBY_TIPS = [
    "hey bestie, need help?",
    "try the password generator!",
    "i believe in you",
    "you're doing great sweetie",
    "need a uuid? i gotchu",
    "base64 go brrr",
    "json formatter is *chefs kiss*",
    "lorem ipsum dolor sit amet",
    "port scanner goes brrr",
    "color picker picky picky",
    "ascii art? very fancy",
    "pomodoro time! take breaks!",
    "i'm just a little guy",
    "hover over me for vibes",
    "gubby certified moment",
]

def resource_path(relative):
    base = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, relative)

class GubbyBuddy(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(80, 80)
        self.setStyleSheet("background: transparent;")
        gif_path = resource_path("gubby_bounce.gif")
        self._movie = QMovie(gif_path)
        if self._movie.isValid():
            self._movie.setScaledSize(QSize(64, 64))
            self.setMovie(self._movie)
            self._movie.start()
        self._tip_idx = 0
        self._show_bubble = False
        self._bubble_label = QLabel(parent)
        self._bubble_label.setStyleSheet(
            "background-color: #313244; color: #cdd6f4; border: 1px solid #585b70; "
            "border-radius: 8px; padding: 4px 8px; font-size: 11px;"
        )
        self._bubble_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._bubble_label.hide()
        self.enterEvent = self._on_enter
        self.leaveEvent = self._on_leave

    def _on_enter(self, _e):
        self._show_bubble = True
        self._bubble_label.setText(GUBBY_TIPS[self._tip_idx % len(GUBBY_TIPS)])
        self._tip_idx += 1
        self._bubble_label.adjustSize()
        self._bubble_label.show()
        self._position_bubble()

    def _on_leave(self, _e):
        self._show_bubble = False
        self._bubble_label.hide()

    def _position_bubble(self):
        if self._show_bubble:
            bx = self.x()
            by = self.y() - self._bubble_label.height() - 4
            pw = self.parent().width() if self.parent() else 800
            bw = self._bubble_label.width()
            if bx + bw > pw:
                bx = pw - bw - 8
            if bx < 0:
                bx = 8
            if by < 0:
                by = self.y() + self.height() + 4
            self._bubble_label.move(bx, by)


class Gubby(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("gubby - multitool")
        self.setWindowIcon(QIcon(resource_path("gubby.ico")))
        self.setMinimumSize(1000, 650)
        self.resize(1100, 700)
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        sidebar_widget = QWidget()
        sidebar_widget.setFixedWidth(200)
        sidebar_widget.setStyleSheet(f"background-color: {SIDEBAR};")
        sidebar_layout = QVBoxLayout(sidebar_widget)
        sidebar_layout.setContentsMargins(8, 12, 8, 12)
        title = make_label("gubby", 18, True, ACCENT)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sidebar_layout.addWidget(title)
        sidebar_layout.addWidget(make_h_line())
        sidebar_layout.addSpacing(4)
        self.sidebar_list = QListWidget()
        self.sidebar_list.setFrameShape(QFrame.Shape.NoFrame)
        self.sidebar_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        for section, indices in TOOLS_PER_SECTION.items():
            header_item = QListWidgetItem(f"-- {section} --")
            header_item.setFlags(Qt.ItemFlag.NoItemFlags)
            header_item.setForeground(QColor(OVERLAY))
            fnt = header_item.font(); fnt.setBold(True); fnt.setPointSize(10)
            header_item.setFont(fnt)
            self.sidebar_list.addItem(header_item)
            for idx in indices:
                name, _ = TOOLS[idx]
                item = QListWidgetItem(f"  {name}")
                item.setData(Qt.ItemDataRole.UserRole, idx)
                self.sidebar_list.addItem(item)
        self.sidebar_list.currentItemChanged.connect(self._switch_tool)
        sidebar_layout.addWidget(self.sidebar_list)
        main_layout.addWidget(sidebar_widget)
        self.content = QStackedWidget()
        main_layout.addWidget(self.content)
        for _, factory in TOOLS:
            self.content.addWidget(factory())
        self.sidebar_list.setCurrentRow(1)
        self._buddy = GubbyBuddy(self.content)
        self._buddy.raise_()
        self._buddy.show()
        # reposition after layout settles
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(100, self._position_buddy)

    def _position_buddy(self):
        cw = self.content.width()
        ch = self.content.height()
        self._buddy.move(cw - 85, ch - 130)
        self._buddy.raise_()
        self._buddy._position_bubble()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, '_buddy'):
            self._position_buddy()

    def _switch_tool(self, current, _prev):
        if current is None: return
        idx = current.data(Qt.ItemDataRole.UserRole)
        if idx is not None:
            self.content.setCurrentIndex(idx)


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)
    window = Gubby()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()