"""gubby installer - checks python, installs deps, launches gubby"""
import sys, os, subprocess, shutil, urllib.request, tempfile
from PyQt6.QtWidgets import *
from PyQt6.QtGui import QFont, QIcon, QPixmap, QPainter, QColor
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize

BG = "#1e1e2e"
SURFACE = "#313244"
TEXT = "#cdd6f4"
ACCENT = "#cba6f7"
GREEN = "#a6e3a1"
RED = "#f38ba8"
BLUE = "#89b4fa"

STYLE = f"""
QWidget {{ background-color: {BG}; color: {TEXT}; font-family: 'Segoe UI'; }}
QProgressBar {{ border: 1px solid {SURFACE}; border-radius: 8px; background: {SURFACE}; height: 24px; text-align: center; color: {TEXT}; }}
QProgressBar::chunk {{ background: {ACCENT}; border-radius: 7px; }}
QPushButton {{ background: {ACCENT}; color: {BG}; border: none; border-radius: 8px; padding: 10px 24px; font-size: 14px; font-weight: bold; }}
QPushButton:hover {{ background: #b4befe; }}
QPushButton:disabled {{ background: {SURFACE}; color: #6c7086; }}
QLabel {{ color: {TEXT}; }}
"""

class InstallWorker(QThread):
    log = pyqtSignal(str)
    progress = pyqtSignal(int)
    done = pyqtSignal(bool, str)

    def run(self):
        try:
            python_cmd = self._find_python()
            if not python_cmd:
                self.log.emit("python not found. downloading python 3.12...")
                self.progress.emit(10)
                python_cmd = self._install_python()
                self.progress.emit(40)
            else:
                self.log.emit(f"python found: {python_cmd}")
                self.progress.emit(20)

            self.log.emit("installing dependencies...")
            self.progress.emit(50)
            self._run(python_cmd, ["-m", "pip", "install", "--upgrade", "pip"])
            self.progress.emit(60)
            self._run(python_cmd, ["-m", "pip", "install", "PyQt6", "qrcode[pil]", "Pillow"])
            self.progress.emit(80)

            self.log.emit("creating desktop shortcut...")
            self._create_shortcut()
            self.progress.emit(95)

            self.log.emit("done!")
            self.progress.emit(100)
            self.done.emit(True, python_cmd)
        except Exception as e:
            self.done.emit(False, str(e))

    def _find_python(self):
        for cmd in ["python", "python3", "py"]:
            path = shutil.which(cmd)
            if path:
                try:
                    r = subprocess.run([cmd, "--version"], capture_output=True, text=True, timeout=5)
                    if "Python 3" in r.stdout:
                        return cmd
                except:
                    pass
        return None

    def _install_python(self):
        url = "https://www.python.org/ftp/python/3.12.7/python-3.12.7-amd64.exe"
        installer = os.path.join(tempfile.gettempdir(), "python-installer.exe")
        self.log.emit("downloading python...")
        urllib.request.urlretrieve(url, installer)
        self.log.emit("installing python (silent)...")
        subprocess.run([installer, "/quiet", "InstallAllUsers=1", "PrependPath=1", "Include_pip=1", "Include_test=0"], check=True)
        os.remove(installer)
        for p in [r"C:\Python312\python.exe", r"C:\Python312\Scripts\python.exe"]:
            if os.path.exists(p):
                return p
        return "python"

    def _run(self, cmd, args):
        r = subprocess.run([cmd] + args, capture_output=True, text=True, timeout=120)
        self.log.emit(r.stdout.strip() if r.stdout else "")
        if r.returncode != 0:
            self.log.emit(f"warning: {r.stderr.strip()}")

    def _create_shortcut(self):
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        gubby_exe = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dist", "gubby.exe")
        if not os.path.exists(gubby_exe):
            gubby_exe = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gubby.py")
        bat = os.path.join(desktop, "gubby.bat")
        with open(bat, "w") as f:
            f.write(f'@echo off\nstart "" python "{os.path.join(os.path.dirname(os.path.abspath(__file__)), "gubby.py")}"\n')
        self.log.emit(f"shortcut created on desktop")


class Installer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("gubby installer")
        self.setFixedSize(500, 420)
        self.setWindowIcon(QIcon())
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(16)

        title = QLabel("gubby")
        title.setFont(QFont("Segoe UI", 28, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {ACCENT};")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel("a multitool desktop app")
        subtitle.setStyleSheet(f"color: #6c7086; font-size: 13px;")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)

        layout.addSpacing(10)

        self.status = QLabel("ready to install")
        self.status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status)

        self.progress = QProgressBar()
        self.progress.setValue(0)
        layout.addWidget(self.progress)

        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setMaximumHeight(120)
        self.log_box.setStyleSheet(f"background: {SURFACE}; border: 1px solid #45475a; border-radius: 8px; padding: 8px; font-family: Consolas; font-size: 11px;")
        layout.addWidget(self.log_box)

        layout.addStretch()

        self.install_btn = QPushButton("install")
        self.install_btn.clicked.connect(self._start_install)
        layout.addWidget(self.install_btn)

        self.launch_btn = QPushButton("launch gubby")
        self.launch_btn.setEnabled(False)
        self.launch_btn.clicked.connect(self._launch)
        layout.addWidget(self.launch_btn)

        self._python_cmd = None

    def _start_install(self):
        self.install_btn.setEnabled(False)
        self.status.setText("installing...")
        self.worker = InstallWorker()
        self.worker.log.connect(self._log)
        self.worker.progress.connect(self.progress.setValue)
        self.worker.done.connect(self._done)
        self.worker.start()

    def _log(self, msg):
        self.log_box.append(msg)

    def _done(self, ok, msg):
        if ok:
            self.status.setText("installed!")
            self.status.setStyleSheet(f"color: {GREEN};")
            self._python_cmd = msg
            self.launch_btn.setEnabled(True)
        else:
            self.status.setText(f"error: {msg}")
            self.status.setStyleSheet(f"color: {RED};")
            self.install_btn.setEnabled(True)

    def _launch(self):
        gubby_py = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gubby.py")
        subprocess.Popen([self._python_cmd or "python", gubby_py])
        self.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLE)
    w = Installer()
    w.show()
    sys.exit(app.exec())
