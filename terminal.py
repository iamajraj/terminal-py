import sys
import os
from PyQt5.QtCore import Qt, QProcess
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QTextEdit, QLineEdit, QPushButton, QLabel, QHBoxLayout
from PyQt5.QtGui import QMouseEvent, QFont
from ansi2html import Ansi2HTMLConverter

class CustomTitleBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAutoFillBackground(True)
        self.setStyleSheet("background-color: #444444; color: white;")
        
        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)

        self.title_label = QLabel("Custom Terminal App")
        self.title_label.setFont(QFont("Arial", 14))
        self.layout.addWidget(self.title_label)

        self.layout.addStretch()

        self.minimize_button = QPushButton("-")
        self.minimize_button.setFixedSize(30, 30)
        self.minimize_button.setStyleSheet("background-color: #555555; color: white; border: none;")
        self.minimize_button.clicked.connect(self.minimize_window)
        self.layout.addWidget(self.minimize_button)

        self.maximize_button = QPushButton("[]")
        self.maximize_button.setFixedSize(30, 30)
        self.maximize_button.setStyleSheet("background-color: #555555; color: white; border: none;")
        self.maximize_button.clicked.connect(self.maximize_window)
        self.layout.addWidget(self.maximize_button)

        self.close_button = QPushButton("X")
        self.close_button.setFixedSize(30, 30)
        self.close_button.setStyleSheet("background-color: red; color: white; border: none;")
        self.close_button.clicked.connect(self.close_window)
        self.layout.addWidget(self.close_button)

    def minimize_window(self):
        self.window().showMinimized()

    def maximize_window(self):
        if self.window().isMaximized():
            self.window().showNormal()
        else:
            self.window().showMaximized()

    def close_window(self):
        self.window().close()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.drag_pos = event.globalPos()

    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() == Qt.LeftButton:
            self.window().move(self.window().pos() + event.globalPos() - self.drag_pos)
            self.drag_pos = event.globalPos()
            event.accept()

class TerminalApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #333333;
                color: white;
                border-radius: 10px;
            }
            QScrollBar:vertical {
                border: none;
                background: #444444;
                width: 8px;
                margin: 0px 0px 0px 0px;
            }
            QScrollBar::handle:vertical {
                background: #888888;
                min-height: 20px;
                border-radius: 4px;
            }
            QScrollBar::add-line:vertical {
                height: 0px;
                subcontrol-position: bottom;
                subcontrol-origin: margin;
            }
            QScrollBar::sub-line:vertical {
                height: 0px;
                subcontrol-position: top;
                subcontrol-origin: margin;
            }
            QTextEdit {
                background-color: #222222;
                color: white;
                font-size: 14pt;
                border: none;
            }
            QLineEdit {
                background-color: #444444;
                color: white;
                font-size: 14pt;
                border: none;
                padding: 10px;
            }
            QPushButton {
                background-color: #555555;
                color: white;
                font-size: 14pt;
                border: none;
                padding: 10px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #666666;
            }
            QPushButton:pressed {
                background-color: #777777;
            }
        """)
        self.setGeometry(100, 100, 1000, 700)

        self.current_directory = os.getcwd()

        self.initUI()

    def initUI(self):
        self.setWindowTitle('Custom Terminal App')

        self.title_bar = CustomTitleBar(self)
        self.title_bar.setFixedHeight(40)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Layout
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Add custom title bar
        layout.addWidget(self.title_bar)

        # Text area for terminal output
        self.text_area = QTextEdit()
        self.text_area.setReadOnly(True)
        layout.addWidget(self.text_area)

        # Input field for commands
        self.input_field = QLineEdit()
        self.input_field.returnPressed.connect(self.send_input)
        layout.addWidget(self.input_field)

        # Execute button
        self.execute_button = QPushButton('Execute')
        self.execute_button.clicked.connect(self.send_input)
        layout.addWidget(self.execute_button)

        central_widget.setLayout(layout)

        # QProcess to handle real-time terminal output
        self.process = QProcess()
        self.process.readyReadStandardOutput.connect(self.handle_stdout)
        self.process.readyReadStandardError.connect(self.handle_stderr)
        self.process.finished.connect(self.process_finished)
        self.process_started = False

        self.ansi_converter = Ansi2HTMLConverter()

    def execute_command(self):
        if self.process_started:
            return
        command = self.input_field.text()
        if command:
            self.text_area.append(f'<span style="color: #00ff00;">$ {command}</span>')
            if command.startswith('cd '):
                try:
                    new_dir = command[3:].strip()
                    os.chdir(new_dir)
                    self.current_directory = os.getcwd()
                    self.text_area.append(f'<span style="color: #00ff00;">Directory changed to {self.current_directory}</span>')
                except Exception as e:
                    self.text_area.append(f'<span style="color: #ff0000;">Error: {e}</span>')
            else:
                self.process_started = True
                if os.name == 'nt':  # If the OS is Windows
                    self.process.setWorkingDirectory(self.current_directory)
                    self.process.start("cmd", ["/C", command])
                else:
                    self.process.setWorkingDirectory(self.current_directory)
                    self.process.start("/bin/bash", ["-c", command])
            self.input_field.clear()

    def send_input(self):
        if self.process_started:
            input_text = self.input_field.text()
            self.process.write((input_text + '\n').encode())
            self.input_field.clear()
        else:
            self.execute_command()

    def handle_stdout(self):
        data = self.process.readAllStandardOutput()
        output = data.data().decode('utf-8', errors='replace')
        html_output = self.ansi_converter.convert(output, full=False)
        self.text_area.append(html_output)
        self.text_area.verticalScrollBar().setValue(self.text_area.verticalScrollBar().maximum())

    def handle_stderr(self):
        data = self.process.readAllStandardError()
        error_output = data.data().decode('utf-8', errors='replace')
        html_output = self.ansi_converter.convert(error_output, full=False)
        self.text_area.append(html_output)
        self.text_area.verticalScrollBar().setValue(self.text_area.verticalScrollBar().maximum())

    def process_finished(self):
        self.process_started = False
        self.text_area.append('<span style="color: #00ff00;">Process finished</span>')
        self.text_area.verticalScrollBar().setValue(self.text_area.verticalScrollBar().maximum())

def main():
    app = QApplication(sys.argv)
    app.setStyleSheet("QMainWindow { background: #333333; }")
    terminal_app = TerminalApp()
    terminal_app.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
