import sys
import math
import random
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QTabWidget, QLabel, QPushButton, QFrame, QScrollArea, QGridLayout, 
    QComboBox, QSpinBox, QMessageBox, QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit, QButtonGroup
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPalette, QColor, QFont, QBrush

# --- ESTILOS GLOBALES ---
BG_COLOR = "#111827"
PANEL_COLOR = "#1F2937"
BORDER_COLOR = "#334155"
TEXT_COLOR = "#E5E7EB"
ACCENT_BLUE = "#3B82F6"
FREE_GRAY = "#374151"
USED_BLUE = "#2563EB"
ERROR_RED = "#EF4444"
SUCCESS_GREEN = "#10B981"
DARK_TEXT = "#111827" 

# Paleta unificada (Colores Pastel)
COLORES_PASTEL = [
    "#A7F3D0", "#FBCFE8", "#BAE6FD", "#FDE047", "#E9D5FF",
    "#FED7AA", "#FECACA", "#99F6E4", "#D9F99D", "#DDD6FE"
]

ESTILO_GLOBAL = f"""
    QMainWindow {{ background-color: {BG_COLOR}; }}
    QWidget {{ color: {TEXT_COLOR}; font-family: 'Segoe UI', sans-serif; }}
    QTabWidget::pane {{ border: 1px solid {BORDER_COLOR}; border-radius: 8px; background: {PANEL_COLOR}; }}
    QTabBar::tab {{ background: {BG_COLOR}; border: 1px solid {BORDER_COLOR}; padding: 8px 20px; font-weight: bold; border-top-left-radius: 6px; border-top-right-radius: 6px; }}
    QTabBar::tab:selected {{ background: {PANEL_COLOR}; color: {ACCENT_BLUE}; border-top: 2px solid {ACCENT_BLUE}; }}
    QPushButton {{ background-color: {ACCENT_BLUE}; color: white; border-radius: 6px; padding: 6px 12px; font-weight: bold; border: none; }}
    QPushButton:hover {{ background-color: #60A5FA; }}
    QSpinBox, QComboBox, QLineEdit {{ background-color: {BG_COLOR}; color: white; border: 1px solid {BORDER_COLOR}; padding: 5px; border-radius: 4px; }}
    QTableWidget {{ background-color: {BG_COLOR}; color: {TEXT_COLOR}; gridline-color: {BORDER_COLOR}; border-radius: 6px; border: 1px solid {BORDER_COLOR}; }}
    QHeaderView::section {{ background-color: {PANEL_COLOR}; color: {ACCENT_BLUE}; font-weight: bold; border: 1px solid {BORDER_COLOR}; padding: 5px; }}
"""

class BlockFrame(QFrame):
    def __init__(self, text, is_used=False, size_text="", custom_bg=None, text_color="white"):
        super().__init__()
        self.setFrameShape(QFrame.Shape.StyledPanel)
        color = custom_bg if custom_bg else (USED_BLUE if is_used else FREE_GRAY)
        
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {color};
                border: 1px solid #111827; 
                border-radius: 0px;
            }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 5, 2, 5)
        
        lbl_title = QLabel(text)
        lbl_title.setStyleSheet(f"font-weight: bold; font-size: 13px; border: none; background: transparent; color: {text_color};")
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_title)
        
        if size_text:
            lbl_size = QLabel(size_text)
            lbl_size.setStyleSheet(f"font-size: 11px; font-weight: bold; border: none; background: transparent; color: {text_color};")
            lbl_size.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(lbl_size)

class BuddyBlock:
    def __init__(self, size, addr, free=True, pid=None, real_size=0, color=None):
        self.size = size
        self.addr = addr
        self.free = free
        self.pid = pid
        self.real_size = real_size
        self.color = color

class VisualizadorMemoria(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gestión Dinámica & Virtual de Memoria - Avance 3")
        self.resize(1100, 750)
        self.setStyleSheet(ESTILO_GLOBAL)

        self.memoria_total = 1024
        
        self.pid_bits = 1
        self.pid_lista = 1
        self.pid_buddy = 1
        self.ultimo_idx_next_fit = 0 
        
        self.procesos_bits_activos = {} 
        self.color_index_bits = 0
        self.color_index_lista = 0
        self.color_index_buddy = 0

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        title = QLabel("Visor General de Memoria (ASO - Avance 3)")
        title.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {ACCENT_BLUE}; margin-bottom: 10px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        self.tabs = QTabWidget()
        self.tabs.addTab(self.crear_mapa_bits(), "🔲 Mapa de Bits")
        self.tabs.addTab(self.crear_listas_ligadas(), "🔗 Lista Ligada & Estrategias")
        self.tabs.addTab(self.crear_sistema_asociados(), "🌳 Sistema Asociados")
        self.tabs.addTab(self.crear_reemplazo_paginas(), "🔄 Memoria Virtual (Reemplazo)")
        
        layout.addWidget(self.tabs)

    # ==========================================
    # 1. MAPA DE BITS
    # ==========================================
    def crear_mapa_bits(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        control_panel1 = QHBoxLayout()
        control_panel1.addWidget(QLabel("Unidad Asignada (MB):"))
        self.spin_unidad = QSpinBox()
        self.spin_unidad.setRange(1, 512)
        self.spin_unidad.setValue(8)
        control_panel1.addWidget(self.spin_unidad)
        
        btn_crear = QPushButton("Generar Mapa")
        btn_crear.clicked.connect(self.inicializar_mapa_bits)
        control_panel1.addWidget(btn_crear)
        control_panel1.addStretch()
        layout.addLayout(control_panel1)
        
        control_panel2 = QHBoxLayout()
        lbl_creacion = QLabel("Creación de Procesos | ")
        lbl_creacion.setStyleSheet("font-weight: bold; color: #60A5FA;")
        control_panel2.addWidget(lbl_creacion)
        
        control_panel2.addWidget(QLabel("Proceso:"))
        self.input_nombre_bits = QLineEdit()
        self.input_nombre_bits.setPlaceholderText("Ej. P1")
        self.input_nombre_bits.setFixedWidth(80)
        control_panel2.addWidget(self.input_nombre_bits)
        
        control_panel2.addSpacing(15)
        
        control_panel2.addWidget(QLabel("Tamaño (MB):"))
        self.spin_proc_bits = QSpinBox()
        self.spin_proc_bits.setRange(1, 1024)
        self.spin_proc_bits.setValue(100)
        control_panel2.addWidget(self.spin_proc_bits)
        
        btn_add_bits = QPushButton("Agregar Proceso")
        btn_add_bits.clicked.connect(self.agregar_proceso_bits)
        control_panel2.addWidget(btn_add_bits)
        
        control_panel2.addStretch()
        layout.addLayout(control_panel2)

        self.info_bits = QLabel("Memoria total: 1024 MB. Genere el mapa para iniciar.")
        self.info_bits.setStyleSheet("color: #9CA3AF; margin-bottom: 5px;")
        layout.addWidget(self.info_bits)

        split_layout = QHBoxLayout()
        
        scroll_grid = QScrollArea()
        scroll_grid.setWidgetResizable(True)
        scroll_grid.setStyleSheet("border: 1px solid #334155; background: #0F172A; border-radius: 6px;")
        
        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setSpacing(2)
        scroll_grid.setWidget(self.grid_widget)
        
        split_layout.addWidget(scroll_grid, stretch=6)
        
        self.tabla_procesos_bits = QTableWidget(0, 3)
        self.tabla_procesos_bits.setHorizontalHeaderLabels(["Proceso", "Tamaño", "Acción"])
        self.tabla_procesos_bits.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla_procesos_bits.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla_procesos_bits.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.tabla_procesos_bits.setStyleSheet(f"background-color: {BG_COLOR}; color: {TEXT_COLOR}; gridline-color: {BORDER_COLOR};")
        
        split_layout.addWidget(self.tabla_procesos_bits, stretch=4)
        
        layout.addLayout(split_layout)
        
        self.mapa_arreglo = []
        self.unidad_actual = 8
        self.inicializar_mapa_bits()
        
        return tab

    def inicializar_mapa_bits(self):
        self.unidad_actual = self.spin_unidad.value()
        total_casillas = math.ceil(self.memoria_total / self.unidad_actual)
        self.mapa_arreglo = [0] * total_casillas
        self.pid_bits = 1
        self.procesos_bits_activos.clear()
        self.color_index_bits = 0
        
        self.input_nombre_bits.clear()
        self.input_nombre_bits.setPlaceholderText(f"Ej. P{self.pid_bits}")
        
        self.info_bits.setText(f"Memoria: 1024 MB | Unidad: {self.unidad_actual} MB | Cuadrícula: {total_casillas} casillas libres.")
        self.dibujar_mapa_bits()
        self.actualizar_tabla_bits()

    def agregar_proceso_bits(self):
        if not self.mapa_arreglo: return
        
        nombre_custom = self.input_nombre_bits.text().strip()
        if not nombre_custom:
            nombre_custom = f"P{self.pid_bits}"
            
        size = self.spin_proc_bits.value()
        casillas_requeridas = math.ceil(size / self.unidad_actual)
        
        consecutivos = 0
        start_idx = -1
        
        for i, val in enumerate(self.mapa_arreglo):
            if val == 0:
                if consecutivos == 0: start_idx = i
                consecutivos += 1
                if consecutivos == casillas_requeridas:
                    color_elegido = COLORES_PASTEL[self.color_index_bits]
                    self.color_index_bits = (self.color_index_bits + 1) % len(COLORES_PASTEL)
                    
                    self.procesos_bits_activos[self.pid_bits] = {
                        'name': nombre_custom,
                        'size': size,
                        'color': color_elegido
                    }
                    
                    for j in range(start_idx, start_idx + casillas_requeridas):
                        self.mapa_arreglo[j] = self.pid_bits
                        
                    self.info_bits.setText(f"Proceso '{nombre_custom}' ({size}MB) llenó {casillas_requeridas} casillas.")
                    self.pid_bits += 1
                    
                    self.input_nombre_bits.clear()
                    self.input_nombre_bits.setPlaceholderText(f"Ej. P{self.pid_bits}")
                    
                    self.dibujar_mapa_bits()
                    self.actualizar_tabla_bits()
                    return
            else:
                consecutivos = 0
                
        QMessageBox.warning(self, "Memoria Insuficiente", "No hay suficientes casillas contiguas libres.")

    def liberar_proceso_bits(self, pid):
        liberadas = 0
        nombre = self.procesos_bits_activos[pid]['name'] if pid in self.procesos_bits_activos else f"P{pid}"
        
        for i in range(len(self.mapa_arreglo)):
            if self.mapa_arreglo[i] == pid:
                self.mapa_arreglo[i] = 0
                liberadas += 1
                
        if pid in self.procesos_bits_activos:
            del self.procesos_bits_activos[pid]
            
        self.info_bits.setText(f"Proceso '{nombre}' liberado. Se vaciaron {liberadas} casillas.")
        self.dibujar_mapa_bits()
        self.actualizar_tabla_bits()

    def dibujar_mapa_bits(self):
        for i in reversed(range(self.grid_layout.count())): 
            self.grid_layout.itemAt(i).widget().setParent(None)
            
        columnas = 25 
        for i, val in enumerate(self.mapa_arreglo):
            r = i // columnas
            c = i % columnas
            
            lbl = QLabel(str(1 if val > 0 else 0))
            lbl.setFixedSize(22, 22)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            if val > 0:
                data = self.procesos_bits_activos[val]
                lbl.setStyleSheet(f"background-color: {data['color']}; color: {DARK_TEXT}; font-size: 10px; font-weight: bold; border-radius: 2px;")
                lbl.setToolTip(data['name'])
            else:
                lbl.setStyleSheet(f"background-color: {FREE_GRAY}; color: #9CA3AF; font-size: 10px; border-radius: 2px;")
                lbl.setToolTip("Libre")
                
            self.grid_layout.addWidget(lbl, r, c)

    def actualizar_tabla_bits(self):
        self.tabla_procesos_bits.setRowCount(0)
        for pid, data in self.procesos_bits_activos.items():
            row = self.tabla_procesos_bits.rowCount()
            self.tabla_procesos_bits.insertRow(row)
            
            item_pid = QTableWidgetItem(data['name'])
            item_pid.setBackground(QBrush(QColor(data['color'])))
            item_pid.setForeground(QBrush(QColor(DARK_TEXT)))
            font = item_pid.font()
            font.setBold(True)
            item_pid.setFont(font)
            item_pid.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabla_procesos_bits.setItem(row, 0, item_pid)
            
            item_size = QTableWidgetItem(f"{data['size']} MB")
            item_size.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabla_procesos_bits.setItem(row, 1, item_size)
            
            btn_liberar = QPushButton("Liberar")
            btn_liberar.setStyleSheet("""
                QPushButton { background-color: #475569; color: white; padding: 4px; font-size: 11px; border-radius: 3px; }
                QPushButton:hover { background-color: #64748B; }
            """)
            btn_liberar.clicked.connect(lambda checked, p=pid: self.liberar_proceso_bits(p))
            self.tabla_procesos_bits.setCellWidget(row, 2, btn_liberar)

    # ==========================================
    # 2. LISTAS LIGADAS
    # ==========================================
    def crear_listas_ligadas(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        lbl_mem = QLabel("Memoria total: 1024 MB")
        lbl_mem.setStyleSheet("color: #9CA3AF; margin-bottom: 5px;")
        layout.addWidget(lbl_mem)

        lbl_crea = QLabel("Creación de Procesos")
        lbl_crea.setStyleSheet("font-weight: bold; font-size: 16px; color: #60A5FA;")
        layout.addWidget(lbl_crea)

        control_panel = QHBoxLayout()
        control_panel.addWidget(QLabel("Proceso:"))
        self.input_nombre_lista = QLineEdit()
        self.input_nombre_lista.setPlaceholderText("Ej. P1")
        self.input_nombre_lista.setFixedWidth(80)
        control_panel.addWidget(self.input_nombre_lista)
        
        control_panel.addSpacing(10)
        control_panel.addWidget(QLabel("Tamaño (MB):"))
        self.spin_proc_lista = QSpinBox()
        self.spin_proc_lista.setRange(1, 1024)
        self.spin_proc_lista.setValue(64)
        control_panel.addWidget(self.spin_proc_lista)
        
        control_panel.addSpacing(10)
        control_panel.addWidget(QLabel("Estrategia:"))
        self.combo_estrategia = QComboBox()
        self.combo_estrategia.addItems(["First Fit (Primer Ajuste)", "Next Fit (Siguiente Ajuste)", "Best Fit (Mejor Ajuste)", "Worst Fit (Peor Ajuste)"])
        control_panel.addWidget(self.combo_estrategia)
        
        control_panel.addSpacing(10)
        btn_simular = QPushButton("Agregar Proceso")
        btn_simular.clicked.connect(self.agregar_proceso_lista)
        control_panel.addWidget(btn_simular)
        control_panel.addStretch()
        
        layout.addLayout(control_panel)

        scroll_bar = QScrollArea()
        scroll_bar.setFixedHeight(120)
        scroll_bar.setWidgetResizable(True)
        scroll_bar.setStyleSheet("border: 1px solid #334155; background: #0F172A; border-radius: 6px;")
        
        self.contenedor_nodos_lista = QWidget()
        self.layout_nodos = QHBoxLayout(self.contenedor_nodos_lista)
        self.layout_nodos.setSpacing(0)
        self.layout_nodos.setContentsMargins(10, 20, 10, 20)
        scroll_bar.setWidget(self.contenedor_nodos_lista)
        layout.addWidget(scroll_bar)

        self.tabla_lista = QTableWidget(0, 5)
        self.tabla_lista.setHorizontalHeaderLabels(["Tipo (H/P)", "Inicio (MB)", "Tamaño (MB)", "Siguiente", "Acción"])
        self.tabla_lista.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla_lista.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla_lista.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.tabla_lista.setStyleSheet(f"background-color: {BG_COLOR}; color: {TEXT_COLOR}; gridline-color: {BORDER_COLOR};")
        layout.addWidget(self.tabla_lista)
        
        self.nodos_memoria = [{"tipo": "H", "id": "Hueco", "size": self.memoria_total, "color": FREE_GRAY}]
        self.renderizar_lista()
        
        return tab

    def agregar_proceso_lista(self):
        size = self.spin_proc_lista.value()
        estrategia = self.combo_estrategia.currentText()
        
        nombre_custom = self.input_nombre_lista.text().strip()
        if not nombre_custom:
            nombre_custom = f"P{self.pid_lista}"
        
        huecos = [(idx, n) for idx, n in enumerate(self.nodos_memoria) if n["tipo"] == "H" and n["size"] >= size]
        if not huecos:
            QMessageBox.warning(self, "Error", "No hay un hueco lo suficientemente grande para este proceso.")
            return

        seleccionado_idx = -1
        
        if "First" in estrategia: 
            seleccionado_idx = huecos[0][0]
        elif "Next" in estrategia:
            huecos_adelante = [h for h in huecos if h[0] >= self.ultimo_idx_next_fit]
            if huecos_adelante:
                seleccionado_idx = huecos_adelante[0][0]
            else:
                seleccionado_idx = huecos[0][0]
        elif "Best" in estrategia: 
            seleccionado_idx = min(huecos, key=lambda x: x[1]["size"])[0]
        elif "Worst" in estrategia: 
            seleccionado_idx = max(huecos, key=lambda x: x[1]["size"])[0]

        nodo_h = self.nodos_memoria[seleccionado_idx]
        sobrante = nodo_h["size"] - size
        
        color_pastel = COLORES_PASTEL[self.color_index_lista]
        self.color_index_lista = (self.color_index_lista + 1) % len(COLORES_PASTEL)
        
        self.pid_lista += 1
        self.nodos_memoria[seleccionado_idx] = {
            "tipo": "P", 
            "id": nombre_custom, 
            "size": size, 
            "color": color_pastel
        }
        
        self.ultimo_idx_next_fit = seleccionado_idx + 1 
        
        if sobrante > 0:
            self.nodos_memoria.insert(seleccionado_idx + 1, {"tipo": "H", "id": "Hueco", "size": sobrante, "color": FREE_GRAY})
            
        self.input_nombre_lista.clear()
        self.input_nombre_lista.setPlaceholderText(f"Ej. P{self.pid_lista}")
        self.renderizar_lista()

    def liberar_proceso_lista(self, pid_liberar):
        for i, n in enumerate(self.nodos_memoria):
            if n["id"] == pid_liberar and n["tipo"] == "P":
                n["tipo"] = "H"
                n["id"] = "Hueco"
                n["color"] = FREE_GRAY
                break
                
        i = 0
        while i < len(self.nodos_memoria) - 1:
            if self.nodos_memoria[i]["tipo"] == "H" and self.nodos_memoria[i+1]["tipo"] == "H":
                self.nodos_memoria[i]["size"] += self.nodos_memoria[i+1]["size"]
                del self.nodos_memoria[i+1]
                if self.ultimo_idx_next_fit > i:
                    self.ultimo_idx_next_fit -= 1
            else:
                i += 1
                
        self.renderizar_lista()

    def renderizar_lista(self):
        for i in reversed(range(self.layout_nodos.count())): 
            self.layout_nodos.itemAt(i).widget().setParent(None)
        self.tabla_lista.setRowCount(0)
        
        inicio_mb = 0
        for nodo in self.nodos_memoria:
            is_used = nodo["tipo"] == "P"
            color_fondo = nodo["color"]
            color_texto = DARK_TEXT if is_used else "#FFFFFF"
            
            texto_etiqueta = f"{nodo['id']}\n{nodo['size']} MB"
            
            block = BlockFrame(texto_etiqueta, is_used, "", custom_bg=color_fondo, text_color=color_texto)
            self.layout_nodos.addWidget(block, stretch=nodo["size"])
            
            row = self.tabla_lista.rowCount()
            self.tabla_lista.insertRow(row)
            
            prefijo = "(P)" if is_used else "(H)"
            item_tipo = QTableWidgetItem(f"{prefijo} {nodo['id']}")
            item_tipo.setBackground(QBrush(QColor(color_fondo)))
            item_tipo.setForeground(QBrush(QColor(color_texto)))
            font = item_tipo.font()
            font.setBold(True)
            item_tipo.setFont(font)
            self.tabla_lista.setItem(row, 0, item_tipo)
            
            self.tabla_lista.setItem(row, 1, QTableWidgetItem(f"{inicio_mb} MB"))
            self.tabla_lista.setItem(row, 2, QTableWidgetItem(f"{nodo['size']} MB"))
            
            siguiente_mb = inicio_mb + nodo["size"]
            txt_siguiente = "null" if nodo == self.nodos_memoria[-1] else f"{siguiente_mb} MB"
            self.tabla_lista.setItem(row, 3, QTableWidgetItem(txt_siguiente))
            
            if is_used:
                btn_liberar = QPushButton("Liberar")
                btn_liberar.setStyleSheet("background-color: #475569; color: white; padding: 4px; border-radius: 3px;")
                pid = nodo["id"]
                btn_liberar.clicked.connect(lambda checked, p=pid: self.liberar_proceso_lista(p))
                self.tabla_lista.setCellWidget(row, 4, btn_liberar)
            else:
                btn_liberar = QPushButton("Liberar")
                btn_liberar.setEnabled(False)
                btn_liberar.setStyleSheet("background-color: #1F2937; color: #4B5563; padding: 4px; border-radius: 3px;")
                self.tabla_lista.setCellWidget(row, 4, btn_liberar)
                
            inicio_mb = siguiente_mb


    # ==========================================
    # 3. SISTEMA DE ASOCIADOS
    # ==========================================
    def crear_sistema_asociados(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        lbl_mem = QLabel("Memoria total: 1024 MB")
        lbl_mem.setStyleSheet("color: #9CA3AF; margin-bottom: 5px;")
        layout.addWidget(lbl_mem)

        lbl_crea = QLabel("Creación de Procesos")
        lbl_crea.setStyleSheet("font-weight: bold; font-size: 16px; color: #60A5FA;")
        layout.addWidget(lbl_crea)

        control_panel = QHBoxLayout()
        control_panel.addWidget(QLabel("Proceso:"))
        self.input_nombre_buddy = QLineEdit()
        self.input_nombre_buddy.setPlaceholderText("Ej. P1")
        self.input_nombre_buddy.setFixedWidth(80)
        control_panel.addWidget(self.input_nombre_buddy)
        
        control_panel.addSpacing(10)
        control_panel.addWidget(QLabel("Tamaño (MB):"))
        self.spin_proc_buddy = QSpinBox()
        self.spin_proc_buddy.setRange(1, 1024)
        self.spin_proc_buddy.setValue(128)
        control_panel.addWidget(self.spin_proc_buddy)
        
        control_panel.addSpacing(10)
        btn_add = QPushButton("Agregar Proceso")
        btn_add.clicked.connect(self.agregar_proceso_buddy)
        control_panel.addWidget(btn_add)
        control_panel.addStretch()
        
        layout.addLayout(control_panel)

        scroll_bar = QScrollArea()
        scroll_bar.setFixedHeight(120)
        scroll_bar.setWidgetResizable(True)
        scroll_bar.setStyleSheet("border: 1px solid #334155; background: #0F172A; border-radius: 6px;")
        
        self.contenedor_buddy = QWidget()
        self.layout_buddy = QHBoxLayout(self.contenedor_buddy)
        self.layout_buddy.setSpacing(0)
        self.layout_buddy.setContentsMargins(10, 20, 10, 20)
        scroll_bar.setWidget(self.contenedor_buddy)
        layout.addWidget(scroll_bar)

        self.tabla_buddy = QTableWidget(0, 4)
        self.tabla_buddy.setHorizontalHeaderLabels(["Proceso", "Tamaño Real (MB)", "Bloque Buddy (MB)", "Acción"])
        self.tabla_buddy.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla_buddy.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla_buddy.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.tabla_buddy.setStyleSheet(f"background-color: {BG_COLOR}; color: {TEXT_COLOR}; gridline-color: {BORDER_COLOR};")
        layout.addWidget(self.tabla_buddy)

        self.bloques_buddy = [BuddyBlock(self.memoria_total, 0)]
        self.renderizar_buddy()
        
        return tab

    def get_potencia_2(self, num):
        if num <= 0: return 1
        return 2 ** math.ceil(math.log2(num))

    def agregar_proceso_buddy(self):
        size_req = self.spin_proc_buddy.value()
        target_size = self.get_potencia_2(size_req)
        
        nombre_custom = self.input_nombre_buddy.text().strip()
        if not nombre_custom:
            nombre_custom = f"P{self.pid_buddy}"
        
        bloques_validos = [b for b in self.bloques_buddy if b.free and b.size >= target_size]
        if not bloques_validos:
            QMessageBox.warning(self, "Error", f"No hay bloque libre de {target_size}MB.")
            return
            
        bloques_validos.sort(key=lambda x: x.size)
        mejor_bloque = bloques_validos[0]
        
        while mejor_bloque.size > target_size:
            mejor_bloque.size //= 2
            nuevo_buddy = BuddyBlock(mejor_bloque.size, mejor_bloque.addr + mejor_bloque.size)
            idx = self.bloques_buddy.index(mejor_bloque)
            self.bloques_buddy.insert(idx + 1, nuevo_buddy)
            
        mejor_bloque.free = False
        mejor_bloque.pid = nombre_custom
        mejor_bloque.real_size = size_req
        mejor_bloque.color = COLORES_PASTEL[self.color_index_buddy]
        
        self.color_index_buddy = (self.color_index_buddy + 1) % len(COLORES_PASTEL)
        self.pid_buddy += 1
        
        self.input_nombre_buddy.clear()
        self.input_nombre_buddy.setPlaceholderText(f"Ej. P{self.pid_buddy}")
        self.renderizar_buddy()

    def liberar_proceso_buddy(self, pid_liberar):
        bloque = next((b for b in self.bloques_buddy if b.pid == pid_liberar), None)
        if not bloque: return
        
        bloque.free = True
        bloque.pid = None
        bloque.real_size = 0
        bloque.color = None
        
        fusionado = True
        while fusionado:
            fusionado = False
            for i, b in enumerate(self.bloques_buddy):
                if b.free:
                    buddy_addr = b.addr ^ b.size
                    
                    buddy_idx = -1
                    for j, cand in enumerate(self.bloques_buddy):
                        if cand.addr == buddy_addr and cand.size == b.size and cand.free:
                            buddy_idx = j
                            break
                            
                    if buddy_idx != -1:
                        izq_idx = min(i, buddy_idx)
                        der_idx = max(i, buddy_idx)
                        
                        self.bloques_buddy[izq_idx].size *= 2
                        del self.bloques_buddy[der_idx]
                        fusionado = True
                        break 
                        
        self.renderizar_buddy()

    def renderizar_buddy(self):
        for i in reversed(range(self.layout_buddy.count())): 
            self.layout_buddy.itemAt(i).widget().setParent(None)
            
        self.tabla_buddy.setRowCount(0)
            
        for b in self.bloques_buddy:
            if b.free:
                texto = f"Buddy\n{b.size} MB"
                color_fondo = FREE_GRAY
                color_texto = "#FFFFFF"
            else:
                texto = f"{b.pid}\n{b.size} MB"
                color_fondo = b.color
                color_texto = DARK_TEXT
                
            frame = BlockFrame(texto, not b.free, "", custom_bg=color_fondo, text_color=color_texto)
            frame.setFixedHeight(80)
            self.layout_buddy.addWidget(frame, stretch=b.size)
            
            if not b.free:
                row = self.tabla_buddy.rowCount()
                self.tabla_buddy.insertRow(row)
                
                item_pid = QTableWidgetItem(b.pid)
                item_pid.setBackground(QBrush(QColor(b.color)))
                item_pid.setForeground(QBrush(QColor(color_texto)))
                font = item_pid.font()
                font.setBold(True)
                item_pid.setFont(font)
                item_pid.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tabla_buddy.setItem(row, 0, item_pid)
                
                item_real = QTableWidgetItem(f"{b.real_size} MB")
                item_real.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tabla_buddy.setItem(row, 1, item_real)
                
                item_buddy = QTableWidgetItem(f"{b.size} MB")
                item_buddy.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tabla_buddy.setItem(row, 2, item_buddy)
                
                btn_liberar = QPushButton("Liberar")
                btn_liberar.setStyleSheet("background-color: #475569; color: white; padding: 4px; border-radius: 3px;")
                pid = b.pid
                btn_liberar.clicked.connect(lambda checked, p=pid: self.liberar_proceso_buddy(p))
                self.tabla_buddy.setCellWidget(row, 3, btn_liberar)

    # ==========================================
    # 4. MEMORIA VIRTUAL (100% REACTIVA)
    # ==========================================
    def crear_reemplazo_paginas(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        lbl_titulo = QLabel("Algoritmos de reemplazo de páginas")
        lbl_titulo.setStyleSheet("font-size: 16px; font-weight: bold; color: #60A5FA; margin-bottom: 10px;")
        layout.addWidget(lbl_titulo)
        
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Cadena:"))
        self.input_refs = QLineEdit("2 3 2 1 5 2 4 5 3 2 5 2")
        row1.addWidget(self.input_refs)
        
        row1.addSpacing(20)
        self.lbl_nru_info1 = QLabel("Tiempos con (*):")
        self.input_nru_tiempos = QLineEdit("4 8")
        self.input_nru_tiempos.setFixedWidth(100)
        
        row1.addWidget(self.lbl_nru_info1)
        row1.addWidget(self.input_nru_tiempos)
        layout.addLayout(row1)
        
        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Marcos:"))
        self.spin_marcos = QSpinBox()
        self.spin_marcos.setRange(1, 10)
        self.spin_marcos.setValue(3)
        self.spin_marcos.setMinimumWidth(80) 
        row2.addWidget(self.spin_marcos)
        
        row2.addSpacing(20)
        btn_simular_reemplazo = QPushButton("Simular")
        btn_simular_reemplazo.clicked.connect(self.simular_reemplazo)
        
        btn_limpiar = QPushButton("Limpiar")
        btn_limpiar.setStyleSheet("background-color: #475569; color: white;")
        btn_limpiar.clicked.connect(self.limpiar_reemplazo)
        
        row2.addWidget(btn_simular_reemplazo)
        row2.addWidget(btn_limpiar)
        
        row2.addSpacing(20)
        self.lbl_nru_info2 = QLabel("En (*), 'M' es fijado en 1 y 'R' en 0.")
        self.lbl_nru_info2.setStyleSheet("font-size: 11px; color: #9CA3AF; font-style: italic;")
        row2.addWidget(self.lbl_nru_info2)
        
        row2.addStretch()
        
        self.lbl_nru_info1.hide()
        self.input_nru_tiempos.hide()
        self.lbl_nru_info2.hide()
        
        layout.addLayout(row2)
        
        layout_tabs = QHBoxLayout()
        layout_tabs.setSpacing(0)
        
        self.btn_group = QButtonGroup(self)
        self.algo_buttons = {}
        
        for algo in ["OPT", "NRU", "FIFO", "LRU"]:
            btn = QPushButton(algo)
            btn.setCheckable(True)
            btn.setStyleSheet(f"""
                QPushButton {{ background-color: {PANEL_COLOR}; border: 1px solid {BORDER_COLOR}; color: {TEXT_COLOR}; padding: 8px 20px; }}
                QPushButton:checked {{ background-color: {BG_COLOR}; border-bottom: 2px solid {ACCENT_BLUE}; color: {ACCENT_BLUE}; }}
                QPushButton:hover:!checked {{ background-color: #334155; }}
            """)
            btn.clicked.connect(self.cambiar_tab_algoritmo)
            self.btn_group.addButton(btn)
            self.algo_buttons[algo] = btn
            layout_tabs.addWidget(btn)
            
        layout_tabs.addStretch()
        layout.addLayout(layout_tabs)
        self.algo_buttons["FIFO"].setChecked(True)
        self.algoritmo_seleccionado = "FIFO"
        
        self.tabla_reemplazo = QTableWidget()
        self.tabla_reemplazo.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla_reemplazo.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.tabla_reemplazo.horizontalHeader().setVisible(False)
        self.tabla_reemplazo.verticalHeader().setVisible(False)
        self.tabla_reemplazo.setStyleSheet(f"background-color: {BG_COLOR}; color: {TEXT_COLOR}; gridline-color: {BORDER_COLOR}; border: 1px solid {BORDER_COLOR};")
        layout.addWidget(self.tabla_reemplazo)
        
        # --- AQUÍ ESTÁ EL AJUSTE PARA ALINEAR A LA IZQUIERDA ---
        self.lbl_resultados = QLabel("")
        self.lbl_resultados.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.lbl_resultados.setStyleSheet(f"font-size: 14px; color: {TEXT_COLOR}; margin-top: 10px; margin-left: 5px;")
        layout.addWidget(self.lbl_resultados)
        
        # --- CONEXIONES PARA ACTUALIZACIÓN AUTOMÁTICA ---
        self.spin_marcos.valueChanged.connect(self.auto_simular)
        self.input_refs.textChanged.connect(self.auto_simular)
        self.input_nru_tiempos.textChanged.connect(self.auto_simular)
        
        # Iniciar tabla por defecto
        self.auto_simular()
        
        return tab

    # Función intermediaria segura (No muestra popups si te equivocas escribiendo)
    def auto_simular(self, *args):
        try:
            txt = self.input_refs.text().replace(",", " ")
            if [int(x) for x in txt.split() if x.isdigit()]:
                self.simular_reemplazo(silent=True)
            else:
                self.limpiar_reemplazo()
        except Exception:
            self.limpiar_reemplazo()

    def cambiar_tab_algoritmo(self):
        for algo, btn in self.algo_buttons.items():
            if btn.isChecked():
                self.algoritmo_seleccionado = algo
                if algo == "NRU":
                    self.lbl_nru_info1.show()
                    self.input_nru_tiempos.show()
                    self.lbl_nru_info2.show()
                else:
                    self.lbl_nru_info1.hide()
                    self.input_nru_tiempos.hide()
                    self.lbl_nru_info2.hide()
                
                # Simular automáticamente al cambiar de pestaña
                self.auto_simular()
                break

    def limpiar_reemplazo(self):
        self.tabla_reemplazo.clear()
        self.tabla_reemplazo.setRowCount(0)
        self.tabla_reemplazo.setColumnCount(0)
        self.lbl_resultados.setText("")

    def simular_reemplazo(self, checked=False, silent=False):
        try:
            txt_refs = self.input_refs.text().replace(",", " ")
            secuencia = [int(x) for x in txt_refs.split() if x.isdigit()]
            if not secuencia: raise ValueError()
        except Exception:
            if not silent:
                QMessageBox.warning(self, "Error", "Ingrese una lista de números separados por coma o espacio.")
            return
            
        marcos_totales = self.spin_marcos.value()
        algoritmo = self.algoritmo_seleccionado
        
        tiempos_nru = []
        if algoritmo == "NRU":
            txt_nru = self.input_nru_tiempos.text().replace(",", " ")
            tiempos_nru = [int(x) for x in txt_nru.split() if x.isdigit()]
        
        memoria = []       
        fallos = 0
        fifo_queue = []    
        lru_time = {}      
        nru_bits = {}      
        
        filas_tabla = 3 + marcos_totales
        num_columnas = len(secuencia) + 1
        
        self.tabla_reemplazo.setRowCount(filas_tabla)
        self.tabla_reemplazo.setColumnCount(num_columnas)
        
        self.crear_celda_tabla(0, 0, "Tiempos", bold=True, bg=PANEL_COLOR, fg=TEXT_COLOR)
        self.crear_celda_tabla(1, 0, "Paginas", bold=True, bg=ACCENT_BLUE, fg="white")
        for i in range(marcos_totales):
            self.crear_celda_tabla(i + 2, 0, f"Marco {i+1}", bold=True, bg=PANEL_COLOR, fg=TEXT_COLOR)
        self.crear_celda_tabla(filas_tabla - 1, 0, "Fallo", bold=True, bg=ERROR_RED, fg="white")
        
        col_actual = 1
        
        for step, ref in enumerate(secuencia):
            tiempo_real = step + 1
            hubo_fallo = False
            
            if ref in memoria:
                lru_time[ref] = step
                nru_bits[ref] = 1 
            else:
                hubo_fallo = True
                fallos += 1
                
                if len(memoria) < marcos_totales:
                    memoria.append(ref)
                    fifo_queue.append(ref)
                    lru_time[ref] = step
                    nru_bits[ref] = 1
                else:
                    pagina_a_reemplazar = -1
                    
                    if algoritmo == "FIFO":
                        pagina_a_reemplazar = fifo_queue.pop(0)
                        fifo_queue.append(ref)
                        
                    elif algoritmo == "LRU":
                        pagina_a_reemplazar = min(memoria, key=lambda p: lru_time.get(p, -1))
                        
                    elif algoritmo == "OPT":
                        futuro = secuencia[step+1:]
                        max_distancia = -1
                        for p in memoria:
                            if p not in futuro:
                                pagina_a_reemplazar = p
                                break 
                            else:
                                distancia = futuro.index(p)
                                if distancia > max_distancia:
                                    max_distancia = distancia
                                    pagina_a_reemplazar = p
                                    
                    elif algoritmo == "NRU":
                        clase_0 = [p for p in memoria if nru_bits.get(p, 0) == 0]
                        clase_1 = [p for p in memoria if nru_bits.get(p, 0) == 1]
                        
                        if clase_0: pagina_a_reemplazar = clase_0[0]
                        else: pagina_a_reemplazar = clase_1[0]
                            
                    idx_reemplazo = memoria.index(pagina_a_reemplazar)
                    memoria[idx_reemplazo] = ref
                    lru_time[ref] = step
                    nru_bits[ref] = 1
                    if pagina_a_reemplazar in nru_bits: del nru_bits[pagina_a_reemplazar]
            
            if algoritmo == "NRU" and (tiempo_real in tiempos_nru):
                for p in nru_bits.keys(): nru_bits[p] = 0
                
            if algoritmo == "NRU" and (tiempo_real in tiempos_nru):
                self.crear_celda_tabla(0, col_actual, f"{tiempo_real}*", bg=BG_COLOR, fg=TEXT_COLOR)
            else:
                self.crear_celda_tabla(0, col_actual, str(tiempo_real), bg=BG_COLOR, fg=TEXT_COLOR)
                
            self.crear_celda_tabla(1, col_actual, str(ref), bold=True, bg=ACCENT_BLUE, fg="white")
            
            for i in range(marcos_totales):
                if i < len(memoria):
                    self.crear_celda_tabla(i + 2, col_actual, str(memoria[i]), bg=BG_COLOR, fg=TEXT_COLOR)
                else:
                    self.crear_celda_tabla(i + 2, col_actual, "", bg=BG_COLOR, fg=TEXT_COLOR)
                    
            if hubo_fallo:
                self.crear_celda_tabla(filas_tabla - 1, col_actual, "F", bold=True, bg=ERROR_RED, fg="white")
            else:
                self.crear_celda_tabla(filas_tabla - 1, col_actual, "OK", bold=True, bg=SUCCESS_GREEN, fg="white")
                
            col_actual += 1

        for i in range(num_columnas):
            self.tabla_reemplazo.setColumnWidth(i, 40)
        self.tabla_reemplazo.setColumnWidth(0, 70) 

        total_tiempos = len(secuencia)
        frecuencia = fallos / total_tiempos if total_tiempos > 0 else 0
        rendimiento = (1 - frecuencia) * 100
        
        texto_resultados = (
            f"<b>RESULTADOS DE LA SIMULACIÓN</b><br>"
            f"Cantidad de fallos: {fallos}<br>"
            f"Frecuencia (Fallos/Tiempo): {frecuencia:.2f} ({fallos}/{total_tiempos})<br>"
            f"Rendimiento (1 - Frecuencia): {rendimiento:.2f}%"
        )
        self.lbl_resultados.setText(texto_resultados)

    def crear_celda_tabla(self, row, col, text, bold=False, bg="white", fg="black"):
        item = QTableWidgetItem(text)
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        item.setBackground(QBrush(QColor(bg)))
        item.setForeground(QBrush(QColor(fg)))
        if bold:
            font = item.font()
            font.setBold(True)
            item.setFont(font)
        self.tabla_reemplazo.setItem(row, col, item)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = VisualizadorMemoria()
    ventana.show()
    sys.exit(app.exec())