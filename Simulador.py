import sys
from datetime import datetime

from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTabWidget,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QTreeWidget,
    QTreeWidgetItem,
    QPlainTextEdit,
    QFrame,
    QSizePolicy,
    QGridLayout,
    QMessageBox,
    QProgressBar,
    QComboBox,
)

from PyQt6.QtCore import Qt, QTimer, QSize
from PyQt6.QtGui import (
    QIcon,
    QPalette,
    QColor,
    QTextCharFormat,
)

from Kernel import Kernel

PANEL_STYLE = """
QFrame {
    background-color: #1F2937;
    border-radius: 10px;
    border: 1px solid #334155;
    padding: 4px;
}
"""

PANEL_HEADER_STYLE = """
QLabel {
    font-weight: bold;
    color: #60A5FA;
    margin-bottom: 2px;
}
"""

TABLE_STYLE = """
QTableWidget {
    background-color: #111827;
    color: #E5E7EB;
    gridline-color: #334155;
    selection-background-color: #2563EB;
    selection-color: #FFFFFF;
    border-radius: 6px;
    border: 1px solid #334155;
    alternate-background-color: #172033;
}

QTableWidget::item {
    padding: 6px;
}

QTableWidget::item:selected {
    background-color: #2563EB;
    color: #FFFFFF;
}

QHeaderView::section {
    background-color: #243244;
    color: #60A5FA;
    font-weight: bold;
    border: 1px solid #334155;
    padding: 7px;
}
"""

TREE_STYLE = """
QTreeWidget {
    background-color: #111827;
    color: #E5E7EB;
    border-radius: 6px;
    border: 1px solid #334155;
    alternate-background-color: #172033;
}

QTreeWidget::item {
    padding: 5px;
}

QTreeWidget::item:selected {
    background-color: #2563EB;
    color: #FFFFFF;
}

QTreeWidget::item:hover {
    background-color: #1E3A5F;
}
"""

COMBO_STYLE = """
QComboBox {
    background-color: #111827;
    color: #60A5FA;
    font-weight: bold;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 4px 8px;
}
QComboBox:hover {
    border: 1px solid #60A5FA;
}
QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 20px;
    border-left-width: 0px;
}
QComboBox QAbstractItemView {
    background-color: #1F2937;
    color: #E5E7EB;
    selection-background-color: #2563EB;
    selection-color: #FFFFFF;
    border: 1px solid #334155;
}
"""


class OSModuleFrame(QFrame):

    def __init__(self, title, icon=None):
        super().__init__()

        self.setStyleSheet(PANEL_STYLE)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(8, 6, 8, 8)
        self.layout.setSpacing(6)

        self.header_layout = QHBoxLayout()
        self.header_layout.setContentsMargins(0, 0, 0, 0)

        if icon:
            icon_label = QLabel()
            icon_label.setPixmap(QIcon.fromTheme(icon).pixmap(QSize(20, 20)))
            self.header_layout.addWidget(icon_label)

        title_label = QLabel(f"[ {title} ]")
        title_label.setStyleSheet(PANEL_HEADER_STYLE)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.header_layout.addWidget(title_label)
        self.header_layout.addStretch()

        self.layout.addLayout(self.header_layout)

    def addWidget(self, widget):
        self.layout.addWidget(widget)


class MemoryMapWidget(QWidget):

    def __init__(self, rows=16, cols=32):
        super().__init__()

        self.rows = rows
        self.cols = cols

        self.layout = QGridLayout(self)
        self.layout.setSpacing(1)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.blocks = []

        for r in range(rows):
            row = []
            for c in range(cols):
                label = QLabel()
                label.setFixedSize(QSize(10, 10))
                label.setToolTip(f"Bloque {r * cols + c}")
                self.layout.addWidget(label, r, c)
                row.append(label)
            self.blocks.append(row)

        self.update_memory(0)

    def update_memory(self, percentage):
        percentage = max(0, min(100, percentage))
        total_blocks = self.rows * self.cols
        used_blocks = int(total_blocks * (percentage / 100))

        for index in range(total_blocks):
            row = index // self.cols
            col = index % self.cols

            label = self.blocks[row][col]

            if index < used_blocks:
                label.setStyleSheet(
                    """
                    background-color: #3B82F6;
                    border: 1px solid #2563EB;
                    """
                )
            else:
                label.setStyleSheet(
                    """
                    background-color: #1E293B;
                    border: 1px solid #334155;
                    """
                )


class OSConsoleLog(QPlainTextEdit):

    def __init__(self):
        super().__init__()

        self.setReadOnly(True)
        self.setStyleSheet(
            """
            QPlainTextEdit {
                background-color: #0B1120;
                color: #E5E7EB;
                font-family: Consolas, monospace;
                font-size: 11px;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 5px;
            }
            """
        )

    def addLogEntry(self, log_type, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        text_format = QTextCharFormat()

        if log_type == "INFO":
            text_format.setForeground(QColor("#60A5FA"))
        elif log_type == "WARN":
            text_format.setForeground(QColor("#F59E0B"))
        elif log_type == "ERR":
            text_format.setForeground(QColor("#EF4444"))
        else:
            text_format.setForeground(QColor("#E5E7EB"))

        self.setCurrentCharFormat(text_format)
        self.appendPlainText(f"[{timestamp}] <{log_type}> {message}")
        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())


class OSSimulatorWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.kernel = Kernel()

        self.setWindowTitle("SO SIMULADOR - Kernel Control Center v2.0")
        self.resize(1400, 900)

        dark_palette = QPalette()
        dark_palette.setColor(QPalette.ColorRole.Window, QColor("#111827"))
        dark_palette.setColor(QPalette.ColorRole.WindowText, QColor("#E5E7EB"))
        dark_palette.setColor(QPalette.ColorRole.Base, QColor("#111827"))
        dark_palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#172033"))
        dark_palette.setColor(QPalette.ColorRole.Text, QColor("#E5E7EB"))
        dark_palette.setColor(QPalette.ColorRole.Button, QColor("#1F2937"))
        dark_palette.setColor(QPalette.ColorRole.ButtonText, QColor("#E5E7EB"))
        dark_palette.setColor(QPalette.ColorRole.Highlight, QColor("#2563EB"))
        dark_palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#FFFFFF"))

        self.setPalette(dark_palette)

        self.setStyleSheet(
            """
            QWidget {
                color: #E5E7EB;
                font-family: 'Segoe UI';
                font-size: 13px;
            }

            QToolTip {
                background-color: #1F2937;
                color: #FFFFFF;
                border: 1px solid #3B82F6;
                padding: 5px;
            }

            QProgressBar {
                background-color: #111827;
                border: 1px solid #334155;
                border-radius: 6px;
                text-align: center;
                color: #FFFFFF;
                font-weight: bold;
                height: 20px;
            }

            QProgressBar::chunk {
                background-color: #3B82F6;
                border-radius: 5px;
            }

            QMessageBox {
                background-color: #1F2937;
            }

            QMessageBox QLabel {
                color: #E5E7EB;
            }
            """
        )

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(10)

        self.setup_status_bar()
        self.setup_central_modules()
        self.setup_lower_section()

        self.sim_timer = QTimer(self)
        self.sim_timer.timeout.connect(self.update_sim_data)
        self.sim_timer.start(1000)

        self.actualizar_interfaz_completa()

        self.os_log.addLogEntry("INFO", "Kernel v2.0 inicializado.")
        self.os_log.addLogEntry("INFO", "CPU VM-CPU-01 creada.")
        self.os_log.addLogEntry("INFO", "Memoria RAM de 1024 MB disponible.")
        self.os_log.addLogEntry("INFO", "Dispositivos de E/S inicializados.")
        self.os_log.addLogEntry("INFO", "Sistema de archivos montado.")
        self.os_log.addLogEntry("INFO", "Simulador listo.")

    def setup_status_bar(self):
        status_frame = QFrame()
        status_frame.setStyleSheet(
            """
            QFrame {
                background-color: #1F2937;
                border-radius: 10px;
                border: 1px solid #334155;
            }
            """
        )

        status_layout = QHBoxLayout(status_frame)
        status_layout.setContentsMargins(12, 6, 12, 6)

        self.so_title_label = QLabel("Simulador SO")
        self.so_title_label.setStyleSheet(
            """
            font-size: 20px;
            font-weight: bold;
            color: #60A5FA;
            """
        )
        status_layout.addWidget(self.so_title_label)
        status_layout.addStretch()

        lbl_alg = QLabel("Algoritmo:")
        lbl_alg.setStyleSheet("font-weight: bold; color: #94A3B8;")
        status_layout.addWidget(lbl_alg)

        self.combo_algoritmo = QComboBox()
        self.combo_algoritmo.setStyleSheet(COMBO_STYLE)
        self.combo_algoritmo.addItems(self.kernel.ALGORITMOS_DISPONIBLES)
        self.combo_algoritmo.currentTextChanged.connect(self.al_cambiar_algoritmo)
        status_layout.addWidget(self.combo_algoritmo)

        status_layout.addSpacing(15)

        self.time_label = QLabel("System Time: 00:00")
        self.time_label.setStyleSheet(
            """
            font-size: 15px;
            font-weight: bold;
            color: #E5E7EB;
            """
        )
        status_layout.addWidget(self.time_label)
        status_layout.addStretch()

        kernel_label = QLabel("Kernel State:")
        kernel_label.setStyleSheet("color: #94A3B8; font-weight: bold;")
        status_layout.addWidget(kernel_label)

        self.kernel_status_led = QLabel()
        self.kernel_status_led.setFixedSize(14, 14)
        status_layout.addWidget(self.kernel_status_led)

        self.kernel_state_label = QLabel("STOPPED")
        self.kernel_state_label.setStyleSheet(
            """
            font-weight: bold;
            color: #EF4444;
            """
        )
        status_layout.addWidget(self.kernel_state_label)

        self.load_label = QLabel("Overall System Load: 0%")
        self.load_label.setStyleSheet(
            """
            font-weight: bold;
            color: #60A5FA;
            """
        )
        status_layout.addSpacing(20)
        status_layout.addWidget(self.load_label)

        self.main_layout.addWidget(status_frame)

    def al_cambiar_algoritmo(self, nuevo_algoritmo):
        if hasattr(self, "kernel"):
            self.kernel.cambiar_algoritmo(nuevo_algoritmo)
            self.os_log.addLogEntry("INFO", f"Estrategia cambiada a: {nuevo_algoritmo}")
            self.actualizar_interfaz_completa()

    def setup_central_modules(self):
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet(
            """
            QTabWidget::pane {
                border: 1px solid #334155;
                border-radius: 10px;
                background-color: #1F2937;
                top: -1px;
            }

            QTabBar::tab {
                background: #111827;
                border: 1px solid #334155;
                border-bottom: none;
                padding: 9px 16px;
                color: #94A3B8;
                font-weight: bold;
                margin-right: 3px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
            }

            QTabBar::tab:selected {
                background: #1F2937;
                color: #60A5FA;
                border-top: 2px solid #3B82F6;
            }

            QTabBar::tab:hover {
                background: #243244;
                color: #E5E7EB;
            }
            """
        )

        self.tab_widget.addTab(self.setup_cpu_tab(), "[ CPU ]")
        self.tab_widget.addTab(self.setup_process_tab(), "[ Procesos ]")
        self.tab_widget.addTab(self.setup_memory_tab(), "[ Memoria ]")
        self.tab_widget.addTab(self.setup_io_tab(), "[ Dispositivos de E/S ]")
        self.tab_widget.addTab(self.setup_fs_tab(), "[ Sistema de Archivos ]")

        self.main_layout.addWidget(self.tab_widget)

    def setup_cpu_tab(self):
        cpu_tab = QWidget()
        layout = QVBoxLayout(cpu_tab)

        cpu_frame = OSModuleFrame("CPU [ NÚCLEO 1 ]", "processor")

        self.cpu_model_label = QLabel()
        self.cpu_process_label = QLabel()
        self.cpu_state_label = QLabel()
        self.cpu_load_label = QLabel()
        self.cpu_progress = QProgressBar()
        self.cpu_progress.setRange(0, 100)
        self.cpu_progress.setTextVisible(True)

        for label in [
            self.cpu_model_label,
            self.cpu_process_label,
            self.cpu_state_label,
            self.cpu_load_label,
        ]:
            label.setStyleSheet(
                """
                font-size: 14px;
                padding: 5px;
                color: #CBD5E1;
                """
            )
            cpu_frame.addWidget(label)

        cpu_frame.addWidget(self.cpu_progress)
        layout.addWidget(cpu_frame)
        layout.addStretch()

        return cpu_tab

    def setup_process_tab(self):
        process_tab = QWidget()
        layout = QVBoxLayout(process_tab)
        layout.setContentsMargins(0, 0, 0, 0)

        process_frame = OSModuleFrame("Procesos Actuales", "task-due")

        self.process_table = QTableWidget(0, 7)
        self.process_table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )
        self.process_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.process_table.setHorizontalHeaderLabels(
            ["PID", "Name", "State", "Priority", "CPU%", "Memory%", "Time"]
        )
        self.process_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.process_table.setStyleSheet(TABLE_STYLE)
        
        # Forzar política de expansión para que ocupe todo el alto disponible sin descuadrarse
        self.process_table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        process_frame.addWidget(self.process_table)

        button_layout = QHBoxLayout()

        self.btn_new_process = QPushButton("+ Nuevo Proceso")
        self.btn_new_process.clicked.connect(self.nuevo_proceso)
        self.btn_new_process.setStyleSheet(
            """
            QPushButton {
                background-color: #2563EB;
                color: white;
                border-radius: 6px;
                padding: 8px 15px;
                font-weight: bold;
                border: 1px solid #3B82F6;
            }

            QPushButton:hover {
                background-color: #3B82F6;
            }

            QPushButton:disabled {
                background-color: #374151;
                color: #9CA3AF;
                border: 1px solid #4B5563;
            }
            """
        )
        button_layout.addWidget(self.btn_new_process)

        self.btn_kill_process = QPushButton("Matar Proceso")
        self.btn_kill_process.clicked.connect(self.matar_proceso)
        self.btn_kill_process.setStyleSheet(
            """
            QPushButton {
                background-color: #B91C1C;
                color: white;
                border-radius: 6px;
                padding: 8px 15px;
                font-weight: bold;
                border: 1px solid #EF4444;
            }

            QPushButton:hover {
                background-color: #DC2626;
            }

            QPushButton:disabled {
                background-color: #374151;
                color: #9CA3AF;
                border: 1px solid #4B5563;
            }
            """
        )
        button_layout.addWidget(self.btn_kill_process)
        button_layout.addStretch()

        process_frame.layout.addLayout(button_layout)
        layout.addWidget(process_frame)

        return process_tab

    def setup_memory_tab(self):
        memory_tab = QWidget()
        layout = QVBoxLayout(memory_tab)

        memory_frame = OSModuleFrame(
            "Administración de Memoria", "utilities-terminal"
        )

        self.memory_total_label = QLabel()
        self.memory_used_label = QLabel()
        self.memory_available_label = QLabel()
        self.memory_fragmentation_label = QLabel()

        for label in [
            self.memory_total_label,
            self.memory_used_label,
            self.memory_available_label,
            self.memory_fragmentation_label,
        ]:
            label.setStyleSheet(
                """
                font-size: 14px;
                padding: 3px;
                color: #CBD5E1;
                """
            )
            memory_frame.addWidget(label)

        self.memory_progress = QProgressBar()
        self.memory_progress.setRange(0, 100)
        memory_frame.addWidget(self.memory_progress)

        self.memory_map = MemoryMapWidget()
        memory_frame.addWidget(self.memory_map)

        layout.addWidget(memory_frame)

        return memory_tab

    def setup_io_tab(self):
        io_tab = QWidget()
        layout = QVBoxLayout(io_tab)

        io_frame = OSModuleFrame(
            "Dispositivos de Entrada/Salida", "media-mount"
        )

        self.io_table = QTableWidget(0, 3)
        self.io_table.setHorizontalHeaderLabels(["Dispositivo", "Estado", "Latencia"])
        self.io_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.io_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.io_table.setStyleSheet(TABLE_STYLE)

        io_frame.addWidget(self.io_table)
        layout.addWidget(io_frame)

        return io_tab

    def setup_fs_tab(self):
        fs_tab = QWidget()
        layout = QVBoxLayout(fs_tab)

        fs_frame = OSModuleFrame("Sistema de Archivos", "document-open")

        self.fs_status_label = QLabel()
        self.fs_status_label.setStyleSheet(
            """
            font-size: 14px;
            font-weight: bold;
            padding: 5px;
            color: #22C55E;
            """
        )
        fs_frame.addWidget(self.fs_status_label)

        self.fs_tree = QTreeWidget()
        self.fs_tree.setHeaderHidden(True)
        self.fs_tree.setStyleSheet(TREE_STYLE)

        fs_frame.addWidget(self.fs_tree)
        layout.addWidget(fs_frame)

        return fs_tab

    def setup_lower_section(self):
        lower_layout = QHBoxLayout()
        lower_layout.setSpacing(10)

        self.control_group = QFrame()
        self.control_group.setStyleSheet(PANEL_STYLE)

        control_layout = QVBoxLayout(self.control_group)

        title_label = QLabel("[ Botones Principales ]")
        title_label.setStyleSheet(PANEL_HEADER_STYLE)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        control_layout.addWidget(title_label)

        grid_buttons = QGridLayout()
        grid_buttons.setSpacing(8)

        self.btn_iniciar = QPushButton("▶️ Iniciar SO")
        self.btn_iniciar.clicked.connect(self.iniciar_so)

        self.btn_detener = QPushButton("■ Detener")
        self.btn_detener.clicked.connect(self.detener_so)

        self.btn_reiniciar = QPushButton("↻ Reiniciar")
        self.btn_reiniciar.clicked.connect(self.reiniciar_so)

        self.btn_clock1 = QPushButton("Avanzar Reloj +1")
        self.btn_clock1.clicked.connect(lambda: self.avanzar_reloj(1))

        self.btn_clock10 = QPushButton("Avanzar Reloj +10")
        self.btn_clock10.clicked.connect(lambda: self.avanzar_reloj(10))

        self.btn_clock60 = QPushButton("Avanzar Reloj +60")
        self.btn_clock60.clicked.connect(lambda: self.avanzar_reloj(60))

        self.btn_config = QPushButton("Configuración")
        self.btn_config.clicked.connect(self.mostrar_configuracion)

        self.btn_test = QPushButton("Test Error Log")
        self.btn_test.clicked.connect(self.test_error)

        button_list = [
            (self.btn_iniciar, "#16A34A", 0, 0),
            (self.btn_detener, "#DC2626", 0, 1),
            (self.btn_reiniciar, "#2563EB", 0, 2),
            (self.btn_clock1, "#475569", 0, 3),
            (self.btn_clock10, "#334155", 1, 0),
            (self.btn_clock60, "#334155", 1, 1),
            (self.btn_config, "#475569", 1, 2),
            (self.btn_test, "#7C3AED", 1, 3),
        ]

        for btn, color, row, col in button_list:
            btn.setSizePolicy(
                QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
            )
            btn.setStyleSheet(
                f"""
                QPushButton {{
                    background-color: {color};
                    color: #FFFFFF;
                    border-radius: 7px;
                    font-weight: bold;
                    border: 1px solid #475569;
                    padding: 9px;
                }}

                QPushButton:hover {{
                    background-color: #3B82F6;
                    border: 1px solid #60A5FA;
                }}

                QPushButton:disabled {{
                    background-color: #374151;
                    color: #6B7280;
                    border: 1px solid #4B5563;
                }}
                """
            )
            grid_buttons.addWidget(btn, row, col)

        control_layout.addLayout(grid_buttons)

        self.control_group.setMinimumHeight(220)
        lower_layout.addWidget(self.control_group, stretch=1)

        self.log_module = OSModuleFrame("Log del Sistema", "utilities-log-viewer")
        self.os_log = OSConsoleLog()

        self.os_log.setMinimumHeight(180)

        self.log_module.addWidget(self.os_log)

        lower_layout.addWidget(self.log_module, stretch=1)
        self.main_layout.addLayout(lower_layout)

    def actualizar_interfaz_completa(self):
        self.actualizar_estado_kernel()
        self.actualizar_reloj()
        self.actualizar_cpu()
        self.actualizar_procesos()
        self.actualizar_memoria()
        self.actualizar_dispositivos()
        self.actualizar_sistema_archivos()

    def actualizar_estado_kernel(self):
        estado = self.kernel.estado_kernel
        self.kernel_state_label.setText(estado)

        es_activo = self.kernel.esta_ejecutando()

        self.btn_new_process.setEnabled(es_activo)
        self.btn_kill_process.setEnabled(es_activo)
        self.btn_clock1.setEnabled(es_activo)
        self.btn_clock10.setEnabled(es_activo)
        self.btn_clock60.setEnabled(es_activo)

        if estado == "RUNNING":
            self.kernel_status_led.setStyleSheet(
                """
                background-color: #22C55E;
                border-radius: 7px;
                border: 1px solid #16A34A;
                """
            )
            self.kernel_state_label.setStyleSheet(
                """
                font-weight: bold;
                color: #22C55E;
                """
            )
        elif estado == "STOPPED":
            self.kernel_status_led.setStyleSheet(
                """
                background-color: #EF4444;
                border-radius: 7px;
                border: 1px solid #DC2626;
                """
            )
            self.kernel_state_label.setStyleSheet(
                """
                font-weight: bold;
                color: #EF4444;
                """
            )
        else:
            self.kernel_status_led.setStyleSheet(
                """
                background-color: #F59E0B;
                border-radius: 7px;
                border: 1px solid #D97706;
                """
            )
            self.kernel_state_label.setStyleSheet(
                """
                font-weight: bold;
                color: #F59E0B;
                """
            )

    def actualizar_reloj(self):
        total_seconds = self.kernel.system_time_counter
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        self.time_label.setText(f"System Time: {minutes:02}:{seconds:02}")

    def actualizar_cpu(self):
        cpu = self.kernel.cpu
        self.cpu_model_label.setText(f"Modelo: {cpu.modelo}")

        if cpu.proceso_actual:
            self.cpu_process_label.setText(
                f"Proceso actual: {cpu.proceso_actual.nombre} (PID {cpu.proceso_actual.pid})"
            )
        else:
            self.cpu_process_label.setText("Proceso actual: Ninguno")

        estado = "Ocupada" if cpu.ocupado else "Disponible"
        self.cpu_state_label.setText(f"Estado: {estado}")
        self.cpu_load_label.setText(f"Carga general: {cpu.carga_general}%")
        self.cpu_progress.setValue(int(cpu.carga_general))
        self.load_label.setText(f"Overall System Load: {cpu.carga_general}%")

    def actualizar_procesos(self):
        self.process_table.setRowCount(0)
        for proceso in self.kernel.procesos:
            row = self.process_table.rowCount()
            self.process_table.insertRow(row)
            datos = proceso.obtener_datos_tabla()
            for column, value in enumerate(datos):
                item = QTableWidgetItem(str(value))
                self.process_table.setItem(row, column, item)

    def actualizar_memoria(self):
        memoria = self.kernel.memoria
        total = memoria.capacidad_total_mb
        usada = memoria.memoria_usada_mb
        disponible = memoria.memoria_disponible()

        porcentaje = 0
        if total > 0:
            porcentaje = int((usada / total) * 100)

        self.memory_total_label.setText(f"Memoria total: {total} MB")
        self.memory_used_label.setText(f"Memoria usada: {usada} MB ({porcentaje}%)")
        self.memory_available_label.setText(f"Memoria disponible: {disponible} MB")
        self.memory_fragmentation_label.setText(
            f"Fragmentación: {memoria.fragmentacion_pct}%"
        )

        self.memory_progress.setValue(porcentaje)
        self.memory_map.update_memory(porcentaje)

    def actualizar_dispositivos(self):
        self.io_table.setRowCount(0)
        for dispositivo in self.kernel.dispositivos:
            row = self.io_table.rowCount()
            self.io_table.insertRow(row)
            datos = [dispositivo.nombre, dispositivo.estado, dispositivo.latencia]
            for column, value in enumerate(datos):
                item = QTableWidgetItem(str(value))
                self.io_table.setItem(row, column, item)

    def actualizar_sistema_archivos(self):
        fs = self.kernel.sistema_archivos
        self.fs_tree.clear()

        if fs.montado:
            self.fs_status_label.setText("Estado: MONTADO")
            self.fs_status_label.setStyleSheet(
                """
                font-size: 14px;
                font-weight: bold;
                padding: 5px;
                color: #22C55E;
                """
            )
        else:
            self.fs_status_label.setText("Estado: DESMONTADO")
            self.fs_status_label.setStyleSheet(
                """
                font-size: 14px;
                font-weight: bold;
                padding: 5px;
                color: #EF4444;
                """
            )

        root = QTreeWidgetItem(self.fs_tree, ["/"])

        for directory in fs.directorios.get("/", []):
            dir_item = QTreeWidgetItem(root, [directory])
            full_path = "/" + directory
            self.crear_arbol_directorio(dir_item, full_path, fs)

        for ruta in fs.archivos:
            if ruta.count("/") == 1:
                QTreeWidgetItem(root, [ruta])

        self.fs_tree.expandAll()

    def crear_arbol_directorio(self, parent_item, path, fs):
        for directory in fs.directorios.get(path, []):
            child = QTreeWidgetItem(parent_item, [directory])
            child_path = path.rstrip("/") + "/" + directory
            self.crear_arbol_directorio(child, child_path, fs)

        for file_path in fs.archivos:
            parent_path = file_path.rsplit("/", 1)[0]
            if parent_path == path:
                filename = file_path.rsplit("/", 1)[1]
                QTreeWidgetItem(parent_item, ["📄 " + filename])

    def update_sim_data(self):
        if not self.kernel.esta_ejecutando():
            self.actualizar_estado_kernel()
            return

        self.kernel.avanzar_reloj(1)
        self.kernel.actualizar_procesos()
        self.actualizar_interfaz_completa()

        if self.kernel.system_time_counter % 5 == 0:
            self.os_log.addLogEntry(
                "INFO",
                f"Kernel actualizó el sistema. Carga: {self.kernel.cpu.carga_general}%",
            )

    def iniciar_so(self):
        if self.kernel.esta_ejecutando():
            self.os_log.addLogEntry(
                "WARN", "El sistema operativo ya está ejecutándose."
            )
            return

        self.kernel.iniciar()
        self.actualizar_interfaz_completa()
        self.os_log.addLogEntry("INFO", "Sistema operativo iniciado correctamente.")

    def detener_so(self):
        if not self.kernel.esta_ejecutando():
            self.os_log.addLogEntry(
                "WARN", "El sistema operativo ya está detenido."
            )
            return

        self.kernel.detener()
        self.actualizar_interfaz_completa()
        self.os_log.addLogEntry("WARN", "Sistema operativo detenido.")

    def reiniciar_so(self):
        self.kernel.reiniciar()
        self.actualizar_interfaz_completa()
        self.os_log.addLogEntry("INFO", "Sistema operativo reiniciado.")

    def avanzar_reloj(self, segundos):
        if not self.kernel.esta_ejecutando():
            self.os_log.addLogEntry(
                "WARN", "El SO está detenido. No se puede avanzar el reloj."
            )
            QMessageBox.warning(
                self,
                "Sistema Detenido",
                "Debes iniciar el SO para poder avanzar el reloj.",
            )
            return

        self.kernel.avanzar_reloj(segundos)
        self.actualizar_interfaz_completa()
        self.os_log.addLogEntry("INFO", f"Reloj avanzado +{segundos} segundos.")

    def nuevo_proceso(self):
        if not self.kernel.esta_ejecutando():
            self.os_log.addLogEntry(
                "WARN", "El SO está detenido. No se pueden crear procesos."
            )
            QMessageBox.warning(
                self,
                "Sistema Detenido",
                "Debes iniciar el SO para crear nuevos procesos.",
            )
            return

        proceso = self.kernel.crear_proceso_aleatorio()
        self.actualizar_interfaz_completa()
        self.os_log.addLogEntry(
            "INFO", f"Nuevo proceso creado: {proceso.nombre} (PID {proceso.pid})"
        )

    def matar_proceso(self):
        if not self.kernel.esta_ejecutando():
            self.os_log.addLogEntry(
                "WARN", "El SO está detenido. No se pueden gestionar procesos."
            )
            QMessageBox.warning(
                self,
                "Sistema Detenido",
                "Debes iniciar el SO para eliminar o gestionar procesos.",
            )
            return

        fila = self.process_table.currentRow()

        if fila < 0:
            QMessageBox.warning(
                self, "Matar proceso", "Selecciona primero un proceso."
            )
            return

        pid_item = self.process_table.item(fila, 0)
        if pid_item is None:
            return

        try:
            pid = int(pid_item.text())
        except ValueError:
            QMessageBox.warning(self, "Error", "El PID seleccionado no es válido.")
            return

        if pid == 1:
            QMessageBox.warning(
                self,
                "Proceso protegido",
                "El proceso init (PID 1) no puede eliminarse.",
            )
            return

        proceso = self.kernel.buscar_proceso(pid)
        if proceso is None:
            QMessageBox.warning(
                self,
                "Proceso no encontrado",
                "El proceso seleccionado ya no existe.",
            )
            return

        respuesta = QMessageBox.question(
            self,
            "Confirmar eliminación",
            f"¿Deseas eliminar el proceso {proceso.nombre} (PID {pid})?",
        )

        if respuesta != QMessageBox.StandardButton.Yes:
            return

        eliminado = self.kernel.eliminar_proceso(pid)
        if eliminado:
            self.actualizar_interfaz_completa()
            self.os_log.addLogEntry("INFO", f"Proceso PID {pid} eliminado.")
        else:
            self.os_log.addLogEntry(
                "ERR", f"No fue posible eliminar el proceso PID {pid}."
            )

    def mostrar_configuracion(self):
        info = self.kernel.obtener_informacion_sistema()

        mensaje = f"""
CONFIGURACIÓN DEL SISTEMA

Kernel:
Estado: {info["kernel"]}

CPU:
Carga: {info["cpu"]}%

Memoria:
Total: {info["memoria_total"]} MB
Usada: {info["memoria_usada"]} MB
Fragmentación: {info["fragmentacion"]}%

Procesos:
Cantidad: {info["procesos"]}

Dispositivos:
Cantidad: {info["dispositivos"]}

Sistema de archivos:
{info["sistema_archivos"]}
"""

        QMessageBox.information(self, "Configuración del Sistema", mensaje)

    def test_error(self):
        self.os_log.addLogEntry(
            "ERR", "Test: Fallo simulado en asignación de memoria."
        )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = OSSimulatorWindow()
    window.show()
    sys.exit(app.exec())