import sys
import getpass
from PyQt6.QtCore import Qt, QSize
from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QLabel, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QFrame, QSizePolicy, QGridLayout, QMessageBox,
    QComboBox, QLineEdit, QSpinBox, QScrollArea
)
from PyQt6.QtGui import QIcon, QPalette, QColor, QBrush

# Estilos globales
BG_COLOR = "#111827"
PANEL_COLOR = "#1F2937"
BORDER_COLOR = "#334155"
TEXT_COLOR = "#E5E7EB"
ACCENT_BLUE = "#3B82F6"

ESTILO_GLOBAL = f"""
    QMainWindow {{ background-color: {BG_COLOR}; }}
    QWidget {{ color: {TEXT_COLOR}; font-family: 'Segoe UI', sans-serif; font-size: 13px; }}
    QTabWidget::pane {{ border: 1px solid {BORDER_COLOR}; border-radius: 8px; background: {PANEL_COLOR}; top: -1px; }}
    QTabBar::tab {{ background: {BG_COLOR}; border: 1px solid {BORDER_COLOR}; border-bottom: none; padding: 9px 16px; font-weight: bold; border-top-left-radius: 6px; border-top-right-radius: 6px; margin-right: 3px; color: #94A3B8; }}
    QTabBar::tab:selected {{ background: {PANEL_COLOR}; color: {ACCENT_BLUE}; border-top: 2px solid {ACCENT_BLUE}; }}
    QTableWidget {{ background-color: {BG_COLOR}; color: {TEXT_COLOR}; gridline-color: {BORDER_COLOR}; border-radius: 6px; border: 1px solid {BORDER_COLOR}; alternate-background-color: #172033; }}
    QHeaderView::section {{ background-color: #243244; color: {ACCENT_BLUE}; font-weight: bold; border: 1px solid {BORDER_COLOR}; padding: 7px; }}
"""

class OSModuleFrame(QFrame):
    def __init__(self, title, icon=None):
        super().__init__()
        self.setStyleSheet(f"QFrame {{ background-color: {PANEL_COLOR}; border-radius: 10px; border: 1px solid {BORDER_COLOR}; padding: 4px; }}")
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
        title_label.setStyleSheet(f"font-weight: bold; color: {ACCENT_BLUE}; margin-bottom: 2px; border: none;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.header_layout.addWidget(title_label)
        self.header_layout.addStretch()
        self.layout.addLayout(self.header_layout)

    def addWidget(self, widget):
        self.layout.addWidget(widget)


# ====================================================================
# 1. LÓGICA DEL SISTEMA DE ARCHIVOS (ASIGNACIÓN CONTINUA)
# ====================================================================
class ContinuousFileSystem:
    def __init__(self):
        self.total_blocks = 20
        self.disk = [None] * self.total_blocks 
        self.directory = {}

    def get_free_space(self):
        return self.disk.count(None)

    def create_file(self, name, size):
        if not name: return False, "El nombre no puede estar vacío."
        if name in self.directory: return False, f"El archivo '{name}' ya existe."
        if size <= 0: return False, "El tamaño debe ser mayor a 0."
        if size > self.get_free_space(): return False, "Espacio insuficiente."

        consecutive = 0
        start_idx = -1
        
        for i in range(self.total_blocks):
            if self.disk[i] is None:
                if consecutive == 0:
                    start_idx = i
                consecutive += 1
                if consecutive == size:
                    for j in range(start_idx, start_idx + size):
                        self.disk[j] = name
                    self.directory[name] = {'start': start_idx, 'size': size}
                    return True, f"Archivo '{name}' asignado en bloques {start_idx} al {start_idx+size-1}."
            else:
                consecutive = 0
                
        return False, "No hay suficientes bloques CONTIGUOS (Fragmentación externa)."

    def delete_file(self, name):
        if name not in self.directory: return False, "El archivo no existe."
        start = self.directory[name]['start']
        size = self.directory[name]['size']
        for i in range(start, start + size):
            self.disk[i] = None
        del self.directory[name]
        return True, f"Archivo '{name}' eliminado."

    def consult_file(self, name):
        if name not in self.directory: return False, "El archivo no existe."
        data = self.directory[name]
        info = (
            f"METADATOS (ASIGNACIÓN CONTINUA):\n"
            f"-----------------------------------------\n"
            f"- Archivo: {name}\n"
            f"- Bloque Inicial: {data['start']}\n"
            f"- Longitud Total: {data['size']} bloques\n"
            f"- Bloques Físicos Ocupados: {[i for i in range(data['start'], data['start'] + data['size'])]}\n"
        )
        return True, info

    def rename_file(self, old_name, new_name):
        if old_name not in self.directory: return False, "El archivo no existe."
        if not new_name: return False, "Nombre vacío."
        if new_name in self.directory: return False, "El nuevo nombre ya existe."
        
        data = self.directory.pop(old_name)
        self.directory[new_name] = data
        for i in range(data['start'], data['start'] + data['size']):
            self.disk[i] = new_name
        return True, f"Archivo renombrado a '{new_name}'."


# ====================================================================
# 2. LÓGICA DEL SISTEMA DE ARCHIVOS (LISTA LIGADA)
# ====================================================================
class LinkedListFileSystem:
    def __init__(self):
        self.total_blocks = 20
        self.disk = [(None, -1)] * self.total_blocks 
        self.directory = {} 

    def get_free_space(self):
        return sum(1 for block, next_ptr in self.disk if block is None)

    def create_file(self, name, size):
        if not name: return False, "El nombre no puede estar vacío."
        if name in self.directory: return False, f"El archivo '{name}' ya existe."
        if size <= 0: return False, "El tamaño debe ser mayor a 0."
        if size > self.get_free_space(): return False, "Espacio insuficiente."

        blocks_needed = size
        first_block = -1
        last_block = -1

        for i in range(self.total_blocks):
            if self.disk[i][0] is None:
                if first_block == -1:
                    first_block = i
                    self.directory[name] = first_block
                
                if last_block != -1:
                    self.disk[last_block] = (name, i)

                self.disk[i] = (name, -1)
                last_block = i
                blocks_needed -= 1

                if blocks_needed == 0:
                    break
                    
        return True, f"Archivo '{name}' creado como lista ligada (Inicio: {first_block})."

    def delete_file(self, name):
        if name not in self.directory: return False, "El archivo no existe."
        current_block = self.directory[name]
        while current_block != -1:
            next_block = self.disk[current_block][1]
            self.disk[current_block] = (None, -1)
            current_block = next_block
        del self.directory[name]
        return True, f"Archivo '{name}' eliminado."

    def consult_file(self, name):
        if name not in self.directory: return False, "El archivo no existe."
        start = self.directory[name]
        
        # Simulando el salto secuencial en disco (O(n) complejidad)
        blocks = []
        curr = start
        while curr != -1:
            blocks.append(curr)
            curr = self.disk[curr][1]
            
        info = (
            f"METADATOS (LISTA LIGADA):\n"
            f"-----------------------------------------\n"
            f"- Archivo: {name}\n"
            f"- Bloque Inicial: {start}\n"
            f"- Ruta de Punteros Físicos (Lectura Secuencial): {' -> '.join(map(str, blocks))}\n"
            f"- Fragmentos Totales: {len(blocks)} bloques\n"
        )
        return True, info

    def rename_file(self, old_name, new_name):
        if old_name not in self.directory: return False, "El archivo no existe."
        if not new_name: return False, "Nombre vacío."
        if new_name in self.directory: return False, "El nuevo nombre ya existe."
        
        start = self.directory.pop(old_name)
        self.directory[new_name] = start
        
        curr = start
        while curr != -1:
            nxt = self.disk[curr][1]
            self.disk[curr] = (new_name, nxt)
            curr = nxt
        return True, f"Archivo renombrado a '{new_name}'."


# ====================================================================
# 3. LÓGICA DEL SISTEMA DE ARCHIVOS (MÉTODO I-NODOS)
# ====================================================================
class INodeFileSystem:
    def __init__(self):
        self.total_blocks = 20
        self.disk = [None] * self.total_blocks 
        self.inodes = {}
        self.next_inode_id = 1 
        try:
            self.current_user = getpass.getuser()
        except:
            self.current_user = "Usuario_OS"

    def get_free_space(self):
        return self.disk.count(None)

    def create_file(self, name, size):
        if not name: return False, "El nombre no puede estar vacío."
        if name in self.inodes: return False, f"El archivo '{name}' ya existe."
        if size <= 0: return False, "El tamaño debe ser mayor a 0."
        if size > self.get_free_space(): return False, "Espacio insuficiente."

        allocated_blocks = []
        for i in range(self.total_blocks):
            if self.disk[i] is None:
                self.disk[i] = name
                allocated_blocks.append(i)
                if len(allocated_blocks) == size:
                    break
        
        timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        peso_inodo = 32 + (len(allocated_blocks) * 4)
        inode_index = self.next_inode_id
        self.next_inode_id += 1
        
        self.inodes[name] = {
            'id': inode_index,           
            'size': size,
            'blocks': allocated_blocks,
            'created_at': timestamp,
            'created_by': self.current_user,
            'modified_by': self.current_user,
            'modified_at': timestamp,
            'inode_size_bytes': peso_inodo
        }
        return True, f"Archivo '{name}' creado. I-Nodo asignado: #{inode_index}"

    def delete_file(self, name):
        if not name or name not in self.inodes: return False, f"El archivo '{name}' no existe."
        blocks_to_free = self.inodes[name]['blocks']
        for b in blocks_to_free:
            self.disk[b] = None
        del self.inodes[name]
        return True, f"Archivo '{name}' eliminado."

    def consult_file(self, name):
        if not name or name not in self.inodes: return False, f"El archivo '{name}' no existe."
        data = self.inodes[name]
        data['modified_at'] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        info = (
            f"METADATOS DEL I-NODO #{data['id']}:\n"
            f"-----------------------------------------\n"
            f"- Archivo: {name}\n"
            f"- Tamaño en disco: {data['size']} bloques\n"
            f"- Referencias físicas: {data['blocks']}\n"
            f"- Propietario/Creador: {data['created_by']}\n"
            f"- Fecha de Creación: {data['created_at']}\n"
            f"- Último Acceso/Modif.: {data['modified_by']} ({data['modified_at']})\n"
            f"- Peso del I-Nodo: {data['inode_size_bytes']} bytes\n"
        )
        return True, info

    def rename_file(self, old_name, new_name):
        if not old_name or old_name not in self.inodes: return False, f"El archivo '{old_name}' no existe."
        if not new_name: return False, "El nuevo nombre no puede estar vacío."
        if new_name in self.inodes: return False, f"El archivo '{new_name}' ya existe."
        data = self.inodes.pop(old_name)
        data['modified_at'] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        self.inodes[new_name] = data
        for i in range(self.total_blocks):
            if self.disk[i] == old_name:
                self.disk[i] = new_name
        return True, f"Archivo renombrado a '{new_name}'."


class GestorArchivosWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gestión de Sistema de Archivos - Avance 5")
        self.resize(1150, 750)
        self.setStyleSheet(ESTILO_GLOBAL)

        self.fs_continuous = ContinuousFileSystem()
        self.fs_linked = LinkedListFileSystem()
        self.fs_inode = INodeFileSystem()

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        self.main_layout = QVBoxLayout(main_widget)

        title = QLabel("Módulo de Administración de Archivos (Avance 5)")
        title.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {ACCENT_BLUE}; margin-bottom: 10px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addWidget(title)

        self.tabs = QTabWidget()
        self.tabs.addTab(self.setup_continuous_tab(), "1. Asignación Continua")
        self.tabs.addTab(self.setup_linked_tab(), "2. Asignación por Lista Ligada")
        self.tabs.addTab(self.setup_fs_tab(), "3. Asignación por I-Nodos")
        self.main_layout.addWidget(self.tabs)

    # ====================================================================
    # PESTAÑA: ASIGNACIÓN CONTINUA
    # ====================================================================
    def setup_continuous_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        disk_frame = OSModuleFrame("Disco Duro - 20 Bloques (Asignación Continua)", "media-optical")
        disk_frame.setMinimumHeight(185)
        disk_frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.blocks_grid_cont = QGridLayout()
        self.block_labels_cont = []
        for i in range(20):
            lbl = QLabel(f"[{i}]\nLibre")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet("background-color: #374151; border: 1px solid #4B5563; border-radius: 4px; padding: 6px; min-height: 35px;")
            self.block_labels_cont.append(lbl)
            self.blocks_grid_cont.addWidget(lbl, i // 10, i % 10)
        disk_frame.layout.addLayout(self.blocks_grid_cont)
        self.lbl_space_cont = QLabel("Espacio Disponible: 20 / 20 bloques")
        self.lbl_space_cont.setStyleSheet(f"color: {ACCENT_BLUE}; font-weight: bold; margin-top: 5px;")
        disk_frame.addWidget(self.lbl_space_cont)
        layout.addWidget(disk_frame)

        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(15)
        
        control_frame = OSModuleFrame("Operaciones", "document-new")
        control_frame.setFixedWidth(380)
        control_frame.setMinimumHeight(400)
        control_frame.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        
        form_layout = QGridLayout()
        form_layout.setSpacing(10)
        
        form_layout.addWidget(QLabel("Crear Nombre:"), 0, 0)
        self.input_cont_name = QLineEdit()
        self.input_cont_name.setStyleSheet(f"background-color: {BG_COLOR}; border: 1px solid {ACCENT_BLUE}; padding: 4px; border-radius: 4px;")
        form_layout.addWidget(self.input_cont_name, 0, 1)
        
        form_layout.addWidget(QLabel("Bloques:"), 1, 0)
        self.input_cont_size = QSpinBox()
        self.input_cont_size.setRange(1, 20)
        self.input_cont_size.setStyleSheet(f"background-color: {BG_COLOR}; border: 1px solid {ACCENT_BLUE}; padding: 4px; border-radius: 4px;")
        form_layout.addWidget(self.input_cont_size, 1, 1)
        
        form_layout.addWidget(QLabel("Seleccionar:"), 2, 0)
        self.combo_cont_files = QComboBox()
        self.combo_cont_files.setStyleSheet(f"background-color: {BG_COLOR}; border: 1px solid {ACCENT_BLUE}; color: {ACCENT_BLUE}; font-weight: bold; border-radius: 4px; padding: 4px;")
        form_layout.addWidget(self.combo_cont_files, 2, 1)

        form_layout.addWidget(QLabel("Nuevo Nombre:"), 3, 0)
        self.input_cont_rename = QLineEdit()
        self.input_cont_rename.setStyleSheet(f"background-color: {BG_COLOR}; border: 1px solid {ACCENT_BLUE}; padding: 4px; border-radius: 4px;")
        form_layout.addWidget(self.input_cont_rename, 3, 1)
        
        control_frame.layout.addLayout(form_layout)
        control_frame.layout.addSpacing(10)
        
        btn_create = QPushButton("1. Crear Archivo")
        btn_create.setFixedHeight(38)
        btn_create.setStyleSheet("QPushButton { background-color: #2563EB; border-radius: 6px; } QPushButton:hover { background-color: #3B82F6; }")
        btn_create.clicked.connect(self.handle_cont_create)
        control_frame.addWidget(btn_create)
        
        btn_consult = QPushButton("2. Consultar Archivo")
        btn_consult.setFixedHeight(38)
        btn_consult.setStyleSheet("QPushButton { background-color: #059669; border-radius: 6px; } QPushButton:hover { background-color: #10B981; }")
        btn_consult.clicked.connect(self.handle_cont_consult)
        control_frame.addWidget(btn_consult)
        
        btn_delete = QPushButton("3. Eliminar Archivo")
        btn_delete.setFixedHeight(38)
        btn_delete.setStyleSheet("QPushButton { background-color: #DC2626; border-radius: 6px; } QPushButton:hover { background-color: #EF4444; }")
        btn_delete.clicked.connect(self.handle_cont_delete)
        control_frame.addWidget(btn_delete)

        btn_rename = QPushButton("4. Renombrar Archivo")
        btn_rename.setFixedHeight(38)
        btn_rename.setStyleSheet("QPushButton { background-color: #D97706; border-radius: 6px; } QPushButton:hover { background-color: #F59E0B; }")
        btn_rename.clicked.connect(self.handle_cont_rename)
        control_frame.addWidget(btn_rename)
        
        control_frame.layout.addStretch()
        bottom_layout.addWidget(control_frame)

        table_frame = OSModuleFrame("Directorio (Asignación Continua)", "view-list-details")
        self.table_cont = QTableWidget(0, 3)
        self.table_cont.setHorizontalHeaderLabels(["Archivo", "Bloque Inicial", "Longitud (Bloques)"])
        self.table_cont.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_cont.setStyleSheet(f"background-color: {BG_COLOR}; gridline-color: {BORDER_COLOR};")
        self.table_cont.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table_frame.addWidget(self.table_cont)
        bottom_layout.addWidget(table_frame)

        layout.addLayout(bottom_layout)
        return tab

    def handle_cont_create(self):
        name = self.input_cont_name.text().strip()
        size = self.input_cont_size.value()
        success, msg = self.fs_continuous.create_file(name, size)
        if success:
            self.input_cont_name.clear()
            self.update_cont_ui()
        else: QMessageBox.warning(self, "Error", msg)

    def handle_cont_consult(self):
        name = self.combo_cont_files.currentText()
        if not name: return
        success, msg = self.fs_continuous.consult_file(name)
        if success: QMessageBox.information(self, "Consulta Continua", msg)
        else: QMessageBox.warning(self, "Error", msg)

    def handle_cont_delete(self):
        name = self.combo_cont_files.currentText()
        if not name: return
        self.fs_continuous.delete_file(name)
        self.update_cont_ui()

    def handle_cont_rename(self):
        old = self.combo_cont_files.currentText()
        new = self.input_cont_rename.text().strip()
        success, msg = self.fs_continuous.rename_file(old, new)
        if success:
            self.input_cont_rename.clear()
            self.update_cont_ui()
        else: QMessageBox.warning(self, "Error", msg)

    def update_cont_ui(self):
        colores = ["#8B5CF6", "#3B82F6", "#EC4899", "#F59E0B", "#10B981"]
        archivos = list(self.fs_continuous.directory.keys())
        self.combo_cont_files.clear()
        self.combo_cont_files.addItems(archivos)
        
        for i in range(self.fs_continuous.total_blocks):
            val = self.fs_continuous.disk[i]
            if val is None:
                self.block_labels_cont[i].setText(f"[{i}]\nLibre")
                self.block_labels_cont[i].setStyleSheet("background-color: #1F2937; color: #9CA3AF; border: 1px dashed #4B5563; border-radius:4px;")
            else:
                self.block_labels_cont[i].setText(f"[{i}]\n{val}")
                c_idx = archivos.index(val) % len(colores)
                self.block_labels_cont[i].setStyleSheet(f"background-color: {colores[c_idx]}; color: white; border: 1px solid white; font-weight:bold; border-radius:4px;")
                
        self.lbl_space_cont.setText(f"Espacio Disponible: {self.fs_continuous.get_free_space()} / 20 bloques")
        
        self.table_cont.setRowCount(0)
        for name, data in self.fs_continuous.directory.items():
            r = self.table_cont.rowCount()
            self.table_cont.insertRow(r)
            self.table_cont.setItem(r, 0, QTableWidgetItem(name))
            self.table_cont.setItem(r, 1, QTableWidgetItem(str(data['start'])))
            self.table_cont.setItem(r, 2, QTableWidgetItem(f"{data['size']} blqs"))

    # ====================================================================
    # PESTAÑA: LISTA LIGADA
    # ====================================================================
    def setup_linked_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        disk_frame = OSModuleFrame("Disco Duro - 20 Bloques (Lista Ligada)", "media-optical")
        disk_frame.setMinimumHeight(185)
        disk_frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.blocks_grid_link = QGridLayout()
        self.block_labels_link = []
        for i in range(20):
            lbl = QLabel(f"[{i}]\nLibre")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet("background-color: #374151; border: 1px solid #4B5563; border-radius: 4px; padding: 2px;")
            self.block_labels_link.append(lbl)
            self.blocks_grid_link.addWidget(lbl, i // 10, i % 10)
        disk_frame.layout.addLayout(self.blocks_grid_link)
        self.lbl_space_link = QLabel("Espacio Disponible: 20 / 20 bloques")
        self.lbl_space_link.setStyleSheet(f"color: {ACCENT_BLUE}; font-weight: bold; margin-top: 5px;")
        disk_frame.addWidget(self.lbl_space_link)
        layout.addWidget(disk_frame)

        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(15)
        
        control_frame = OSModuleFrame("Operaciones", "document-new")
        control_frame.setFixedWidth(380)
        control_frame.setMinimumHeight(400)
        control_frame.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        
        form_layout = QGridLayout()
        form_layout.setSpacing(10)
        
        form_layout.addWidget(QLabel("Crear Nombre:"), 0, 0)
        self.input_link_name = QLineEdit()
        self.input_link_name.setStyleSheet(f"background-color: {BG_COLOR}; border: 1px solid {ACCENT_BLUE}; padding: 4px; border-radius: 4px;")
        form_layout.addWidget(self.input_link_name, 0, 1)
        
        form_layout.addWidget(QLabel("Bloques:"), 1, 0)
        self.input_link_size = QSpinBox()
        self.input_link_size.setRange(1, 20)
        self.input_link_size.setStyleSheet(f"background-color: {BG_COLOR}; border: 1px solid {ACCENT_BLUE}; padding: 4px; border-radius: 4px;")
        form_layout.addWidget(self.input_link_size, 1, 1)
        
        form_layout.addWidget(QLabel("Seleccionar:"), 2, 0)
        self.combo_link_files = QComboBox()
        self.combo_link_files.setStyleSheet(f"background-color: {BG_COLOR}; border: 1px solid {ACCENT_BLUE}; color: {ACCENT_BLUE}; font-weight: bold; border-radius: 4px; padding: 4px;")
        form_layout.addWidget(self.combo_link_files, 2, 1)

        form_layout.addWidget(QLabel("Nuevo Nombre:"), 3, 0)
        self.input_link_rename = QLineEdit()
        self.input_link_rename.setStyleSheet(f"background-color: {BG_COLOR}; border: 1px solid {ACCENT_BLUE}; padding: 4px; border-radius: 4px;")
        form_layout.addWidget(self.input_link_rename, 3, 1)
        
        control_frame.layout.addLayout(form_layout)
        control_frame.layout.addSpacing(10)
        
        btn_create = QPushButton("1. Crear Archivo")
        btn_create.setFixedHeight(38)
        btn_create.setStyleSheet("QPushButton { background-color: #2563EB; border-radius: 6px; } QPushButton:hover { background-color: #3B82F6; }")
        btn_create.clicked.connect(self.handle_link_create)
        control_frame.addWidget(btn_create)
        
        btn_consult = QPushButton("2. Consultar Punteros")
        btn_consult.setFixedHeight(38)
        btn_consult.setStyleSheet("QPushButton { background-color: #059669; border-radius: 6px; } QPushButton:hover { background-color: #10B981; }")
        btn_consult.clicked.connect(self.handle_link_consult)
        control_frame.addWidget(btn_consult)
        
        btn_delete = QPushButton("3. Eliminar Archivo")
        btn_delete.setFixedHeight(38)
        btn_delete.setStyleSheet("QPushButton { background-color: #DC2626; border-radius: 6px; } QPushButton:hover { background-color: #EF4444; }")
        btn_delete.clicked.connect(self.handle_link_delete)
        control_frame.addWidget(btn_delete)

        btn_rename = QPushButton("4. Renombrar Archivo")
        btn_rename.setFixedHeight(38)
        btn_rename.setStyleSheet("QPushButton { background-color: #D97706; border-radius: 6px; } QPushButton:hover { background-color: #F59E0B; }")
        btn_rename.clicked.connect(self.handle_link_rename)
        control_frame.addWidget(btn_rename)
        
        control_frame.layout.addStretch()
        bottom_layout.addWidget(control_frame)

        table_frame = OSModuleFrame("Directorio (Lista Ligada)", "view-list-details")
        self.table_link = QTableWidget(0, 2)
        self.table_link.setHorizontalHeaderLabels(["Archivo", "Bloque Inicial"])
        self.table_link.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_link.setStyleSheet(f"background-color: {BG_COLOR}; gridline-color: {BORDER_COLOR};")
        self.table_link.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table_frame.addWidget(self.table_link)
        bottom_layout.addWidget(table_frame)

        layout.addLayout(bottom_layout)
        return tab

    def handle_link_create(self):
        name = self.input_link_name.text().strip()
        size = self.input_link_size.value()
        success, msg = self.fs_linked.create_file(name, size)
        if success:
            self.input_link_name.clear()
            self.update_link_ui()
        else: QMessageBox.warning(self, "Error", msg)
        
    def handle_link_consult(self):
        name = self.combo_link_files.currentText()
        if not name: return
        success, msg = self.fs_linked.consult_file(name)
        if success: QMessageBox.information(self, "Consulta Lista Ligada", msg)
        else: QMessageBox.warning(self, "Error", msg)

    def handle_link_delete(self):
        name = self.combo_link_files.currentText()
        if not name: return
        self.fs_linked.delete_file(name)
        self.update_link_ui()

    def handle_link_rename(self):
        old = self.combo_link_files.currentText()
        new = self.input_link_rename.text().strip()
        success, msg = self.fs_linked.rename_file(old, new)
        if success:
            self.input_link_rename.clear()
            self.update_link_ui()
        else: QMessageBox.warning(self, "Error", msg)

    def update_link_ui(self):
        colores = ["#8B5CF6", "#3B82F6", "#EC4899", "#F59E0B", "#10B981"]
        archivos = list(self.fs_linked.directory.keys())
        self.combo_link_files.clear()
        self.combo_link_files.addItems(archivos)
        
        for i in range(self.fs_linked.total_blocks):
            nombre, ptr = self.fs_linked.disk[i]
            if nombre is None:
                self.block_labels_link[i].setText(f"[{i}]\nLibre")
                self.block_labels_link[i].setStyleSheet("background-color: #1F2937; color: #9CA3AF; border: 1px dashed #4B5563; border-radius:4px;")
            else:
                ptr_text = str(ptr) if ptr != -1 else "FIN"
                self.block_labels_link[i].setText(f"[{i}] {nombre}\n-> {ptr_text}")
                c_idx = archivos.index(nombre) % len(colores)
                self.block_labels_link[i].setStyleSheet(f"background-color: {colores[c_idx]}; color: white; border: 1px solid white; font-size: 11px; border-radius:4px; font-weight:bold;")
                
        self.lbl_space_link.setText(f"Espacio Disponible: {self.fs_linked.get_free_space()} / 20 bloques")
        
        self.table_link.setRowCount(0)
        for name, block in self.fs_linked.directory.items():
            r = self.table_link.rowCount()
            self.table_link.insertRow(r)
            self.table_link.setItem(r, 0, QTableWidgetItem(name))
            self.table_link.setItem(r, 1, QTableWidgetItem(str(block)))

    # ====================================================================
    # PESTAÑA: I-NODOS
    # ====================================================================
    def setup_fs_tab(self):
        fs_tab = QWidget()
        main_layout = QVBoxLayout(fs_tab)
        main_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background-color: transparent; border: none; }")

        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)

        disk_frame = OSModuleFrame("Disco Duro - 20 Bloques (Asignación por I-Nodos)", "media-optical")
        disk_frame.setMinimumHeight(185)
        disk_frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        self.blocks_grid = QGridLayout()
        self.block_labels = []
        for i in range(20):
            lbl = QLabel(f"[{i}]\nLibre")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet("background-color: #374151; border: 1px solid #4B5563; border-radius: 4px; padding: 6px; min-height: 35px;")
            self.block_labels.append(lbl)
            self.blocks_grid.addWidget(lbl, i // 10, i % 10)
            
        disk_frame.layout.addLayout(self.blocks_grid)
        self.lbl_space = QLabel("Espacio Disponible: 20 / 20 bloques libres")
        self.lbl_space.setStyleSheet("color: #34D399; font-weight: bold; margin-top: 5px; font-size: 13px;")
        disk_frame.addWidget(self.lbl_space)
        layout.addWidget(disk_frame)

        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(15)
        
        control_frame = OSModuleFrame("Operaciones", "document-new")
        control_frame.setFixedWidth(380)
        control_frame.setMinimumHeight(400)
        control_frame.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        
        form_layout = QGridLayout()
        form_layout.setSpacing(10)
        
        form_layout.addWidget(QLabel("Crear Nombre:"), 0, 0)
        self.input_fs_name = QLineEdit()
        self.input_fs_name.setStyleSheet(f"background-color: {BG_COLOR}; border: 1px solid {ACCENT_BLUE}; padding: 4px; border-radius: 4px;")
        form_layout.addWidget(self.input_fs_name, 0, 1)
        
        form_layout.addWidget(QLabel("Bloques:"), 1, 0)
        self.input_fs_size = QSpinBox()
        self.input_fs_size.setRange(1, 20)
        self.input_fs_size.setStyleSheet(f"background-color: {BG_COLOR}; border: 1px solid {ACCENT_BLUE}; padding: 4px; border-radius: 4px;")
        form_layout.addWidget(self.input_fs_size, 1, 1)
        
        form_layout.addWidget(QLabel("Seleccionar:"), 2, 0)
        self.combo_fs_files = QComboBox()
        self.combo_fs_files.setStyleSheet(f"background-color: {BG_COLOR}; border: 1px solid {ACCENT_BLUE}; color: {ACCENT_BLUE}; font-weight: bold; border-radius: 4px; padding: 4px;")
        form_layout.addWidget(self.combo_fs_files, 2, 1)

        form_layout.addWidget(QLabel("Nuevo Nombre:"), 3, 0)
        self.input_fs_rename = QLineEdit()
        self.input_fs_rename.setStyleSheet(f"background-color: {BG_COLOR}; border: 1px solid {ACCENT_BLUE}; padding: 4px; border-radius: 4px;")
        form_layout.addWidget(self.input_fs_rename, 3, 1)
        
        control_frame.layout.addLayout(form_layout)
        control_frame.layout.addSpacing(10)
        
        btn_create = QPushButton("1. Crear Archivo")
        btn_create.setFixedHeight(38)
        btn_create.setStyleSheet("QPushButton { background-color: #2563EB; border-radius: 6px; } QPushButton:hover { background-color: #3B82F6; }")
        btn_create.clicked.connect(self.handle_fs_create)
        control_frame.addWidget(btn_create)
        
        btn_consult = QPushButton("2. Consultar I-Nodo")
        btn_consult.setFixedHeight(38)
        btn_consult.setStyleSheet("QPushButton { background-color: #059669; border-radius: 6px; } QPushButton:hover { background-color: #10B981; }")
        btn_consult.clicked.connect(self.handle_fs_consult)
        control_frame.addWidget(btn_consult)
        
        btn_delete = QPushButton("3. Eliminar Archivo")
        btn_delete.setFixedHeight(38)
        btn_delete.setStyleSheet("QPushButton { background-color: #DC2626; border-radius: 6px; } QPushButton:hover { background-color: #EF4444; }")
        btn_delete.clicked.connect(self.handle_fs_delete)
        control_frame.addWidget(btn_delete)

        btn_rename = QPushButton("4. Renombrar Archivo")
        btn_rename.setFixedHeight(38)
        btn_rename.setStyleSheet("QPushButton { background-color: #D97706; border-radius: 6px; } QPushButton:hover { background-color: #F59E0B; }")
        btn_rename.clicked.connect(self.handle_fs_rename)
        control_frame.addWidget(btn_rename)
        
        control_frame.layout.addStretch()
        bottom_layout.addWidget(control_frame)
        
        table_frame = OSModuleFrame("Tabla de Control de I-Nodos Activos", "view-list-details")
        table_frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        self.table_inodes = QTableWidget(0, 8)
        self.table_inodes.setHorizontalHeaderLabels([
            "ID I-Nodo", "Archivo", "Tamaño", "Punteros", "Creador", "Creación", "Modificado", "Peso I-Nodo"
        ])
        self.table_inodes.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_inodes.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table_frame.addWidget(self.table_inodes)
        
        bottom_layout.addWidget(table_frame, stretch=1)
        layout.addLayout(bottom_layout)

        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)
        
        return fs_tab

    def handle_fs_create(self):
        name = self.input_fs_name.text().strip()
        size = self.input_fs_size.value()
        success, msg = self.fs_inode.create_file(name, size)
        if success:
            self.input_fs_name.clear()
            self.actualizar_sistema_archivos()
        else: QMessageBox.warning(self, "Error al crear", msg)

    def handle_fs_consult(self):
        name = self.combo_fs_files.currentText().strip()
        if not name: return
        success, msg = self.fs_inode.consult_file(name)
        if success: QMessageBox.information(self, f"Consulta de I-Nodo: {name}", msg)
        else: QMessageBox.warning(self, "Error de Consulta", msg)

    def handle_fs_delete(self):
        name = self.combo_fs_files.currentText().strip()
        if not name: return
        success, msg = self.fs_inode.delete_file(name)
        if success: self.actualizar_sistema_archivos()
        else: QMessageBox.warning(self, "Error al eliminar", msg)

    def handle_fs_rename(self):
        old_name = self.combo_fs_files.currentText().strip()
        new_name = self.input_fs_rename.text().strip()
        success, msg = self.fs_inode.rename_file(old_name, new_name)
        if success:
            self.input_fs_rename.clear()
            self.actualizar_sistema_archivos()
        else: QMessageBox.warning(self, "Error al renombrar", msg)

    def actualizar_sistema_archivos(self):
        colores = ["#8B5CF6", "#3B82F6", "#EC4899", "#F59E0B", "#10B981", "#EF4444"]
        archivos_unicos = list(self.fs_inode.inodes.keys())

        current_selection = self.combo_fs_files.currentText()
        self.combo_fs_files.clear()
        self.combo_fs_files.addItems(archivos_unicos)
        if current_selection in archivos_unicos:
            self.combo_fs_files.setCurrentText(current_selection)

        for i in range(self.fs_inode.total_blocks):
            estado = self.fs_inode.disk[i]
            if estado is None:
                self.block_labels[i].setText(f"[{i}]\nLibre")
                self.block_labels[i].setStyleSheet("background-color: #1F2937; border: 1px dashed #4B5563; color: #9CA3AF; border-radius: 4px; padding: 5px;")
            else:
                self.block_labels[i].setText(f"[{i}]\n{estado}")
                color_idx = archivos_unicos.index(estado) % len(colores)
                color = colores[color_idx]
                self.block_labels[i].setStyleSheet(f"background-color: {color}; border: 1px solid white; color: white; font-weight: bold; border-radius: 4px; padding: 5px;")

        libres = self.fs_inode.get_free_space()
        self.lbl_space.setText(f"Espacio Disponible: {libres} / {self.fs_inode.total_blocks} bloques libres")

        self.table_inodes.setRowCount(0)
        for name, data in self.fs_inode.inodes.items():
            row = self.table_inodes.rowCount()
            self.table_inodes.insertRow(row)
            self.table_inodes.setItem(row, 0, QTableWidgetItem(f"#{data['id']}"))
            self.table_inodes.setItem(row, 1, QTableWidgetItem(name))
            self.table_inodes.setItem(row, 2, QTableWidgetItem(f"{data['size']} blqs"))
            self.table_inodes.setItem(row, 3, QTableWidgetItem(str(data['blocks'])))
            self.table_inodes.setItem(row, 4, QTableWidgetItem(data['created_by']))
            self.table_inodes.setItem(row, 5, QTableWidgetItem(data['created_at']))
            self.table_inodes.setItem(row, 6, QTableWidgetItem(data['modified_at']))
            self.table_inodes.setItem(row, 7, QTableWidgetItem(f"{data['inode_size_bytes']} bytes"))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GestorArchivosWindow()
    window.show()
    sys.exit(app.exec())