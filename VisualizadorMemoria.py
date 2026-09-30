import sys
import math
import random
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QTabWidget, QLabel, QPushButton, QFrame, QScrollArea, QGridLayout, 
    QComboBox, QSpinBox, QMessageBox, QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit
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
    def __init__(self, text, is_used=False, size_text=""):
        super().__init__()
        self.setFrameShape(QFrame.Shape.StyledPanel)
        color = USED_BLUE if is_used else FREE_GRAY
        border = "#60A5FA" if is_used else "#9CA3AF"
        
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {color};
                border: 2px solid {border};
                border-radius: 4px;
            }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 5, 2, 5)
        
        lbl_title = QLabel(text)
        lbl_title.setStyleSheet("font-weight: bold; font-size: 12px; border: none; background: transparent;")
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_title)
        
        if size_text:
            lbl_size = QLabel(size_text)
            lbl_size.setStyleSheet("font-size: 10px; color: #D1D5DB; border: none; background: transparent;")
            lbl_size.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(lbl_size)

class BuddyBlock:
    def __init__(self, size, addr, free=True, pid=None):
        self.size = size
        self.addr = addr
        self.free = free
        self.pid = pid

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
        self.ultimo_idx_next_fit = 0 # Puntero para Next Fit

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        title = QLabel("Visor General de Memoria (ASO - Avance 3)")
        title.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {ACCENT_BLUE}; margin-bottom: 10px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        self.tabs = QTabWidget()
        # Módulos Avance 2 (Asignación Dinámica)
        self.tabs.addTab(self.crear_mapa_bits(), "🔲 Mapa de Bits")
        self.tabs.addTab(self.crear_listas_ligadas(), "🔗 Lista Ligada & Estrategias")
        self.tabs.addTab(self.crear_sistema_asociados(), "🌳 Sistema Asociados")
        # Módulo Avance 3 (Memoria Virtual)
        self.tabs.addTab(self.crear_reemplazo_paginas(), "🔄 Memoria Virtual (Reemplazo)")
        
        layout.addWidget(self.tabs)

    # ==========================================
    # 1. MAPA DE BITS
    # ==========================================
    def crear_mapa_bits(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        control_panel = QHBoxLayout()
        control_panel.addWidget(QLabel("Unidad (MB):"))
        self.spin_unidad = QSpinBox()
        self.spin_unidad.setRange(1, 512)
        self.spin_unidad.setValue(8)
        control_panel.addWidget(self.spin_unidad)
        
        btn_crear = QPushButton("Crear Tabla")
        btn_crear.clicked.connect(self.inicializar_mapa_bits)
        control_panel.addWidget(btn_crear)
        
        control_panel.addSpacing(15)
        control_panel.addWidget(QLabel("Proceso (MB):"))
        self.spin_proc_bits = QSpinBox()
        self.spin_proc_bits.setRange(1, 1024)
        self.spin_proc_bits.setValue(100)
        control_panel.addWidget(self.spin_proc_bits)
        
        btn_add_bits = QPushButton("Añadir")
        btn_add_bits.clicked.connect(self.agregar_proceso_bits)
        control_panel.addWidget(btn_add_bits)

        control_panel.addSpacing(15)
        self.combo_liberar_bits = QComboBox()
        control_panel.addWidget(self.combo_liberar_bits)
        
        btn_liberar_bits = QPushButton("Liberar")
        btn_liberar_bits.setStyleSheet("background-color: #B91C1C;")
        btn_liberar_bits.clicked.connect(self.liberar_proceso_bits)
        control_panel.addWidget(btn_liberar_bits)
        
        control_panel.addStretch()
        layout.addLayout(control_panel)

        self.info_bits = QLabel("Defina la unidad de asignación y cree la tabla para comenzar.")
        self.info_bits.setStyleSheet("color: #9CA3AF; margin-bottom: 10px;")
        layout.addWidget(self.info_bits)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background: transparent;")
        
        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setSpacing(2)
        scroll.setWidget(self.grid_widget)
        
        layout.addWidget(scroll)
        
        self.mapa_arreglo = []
        self.unidad_actual = 8
        self.inicializar_mapa_bits()
        
        return tab

    def inicializar_mapa_bits(self):
        self.unidad_actual = self.spin_unidad.value()
        total_casillas = math.ceil(self.memoria_total / self.unidad_actual)
        self.mapa_arreglo = [0] * total_casillas
        self.pid_bits = 1
        self.info_bits.setText(f"Memoria: 1024 MB | Unidad: {self.unidad_actual} MB | Cuadrícula generada: {total_casillas} casillas (Libres).")
        self.actualizar_combos_liberacion()
        self.dibujar_mapa_bits()

    def agregar_proceso_bits(self):
        if not self.mapa_arreglo: return
        size = self.spin_proc_bits.value()
        casillas_requeridas = math.ceil(size / self.unidad_actual)
        consecutivos = 0
        start_idx = -1
        for i, val in enumerate(self.mapa_arreglo):
            if val == 0:
                if consecutivos == 0: start_idx = i
                consecutivos += 1
                if consecutivos == casillas_requeridas:
                    for j in range(start_idx, start_idx + casillas_requeridas):
                        self.mapa_arreglo[j] = self.pid_bits
                    self.info_bits.setText(f"Proceso P{self.pid_bits} de {size}MB asignado. Llenó {casillas_requeridas} casillas.")
                    self.pid_bits += 1
                    self.actualizar_combos_liberacion()
                    self.dibujar_mapa_bits()
                    return
            else:
                consecutivos = 0
        QMessageBox.warning(self, "Memoria Insuficiente", "No hay suficientes casillas contiguas libres.")

    def liberar_proceso_bits(self):
        pid_str = self.combo_liberar_bits.currentText()
        if not pid_str: return
        pid = int(pid_str.replace("P", ""))
        liberadas = 0
        for i in range(len(self.mapa_arreglo)):
            if self.mapa_arreglo[i] == pid:
                self.mapa_arreglo[i] = 0
                liberadas += 1
        self.info_bits.setText(f"Proceso P{pid} liberado. Se vaciaron {liberadas} casillas.")
        self.actualizar_combos_liberacion()
        self.dibujar_mapa_bits()

    def dibujar_mapa_bits(self):
        for i in reversed(range(self.grid_layout.count())): 
            self.grid_layout.itemAt(i).widget().setParent(None)
        columnas = 32
        for i, val in enumerate(self.mapa_arreglo):
            r = i // columnas
            c = i % columnas
            lbl = QLabel(str(1 if val > 0 else 0))
            lbl.setFixedSize(25, 25)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            if val > 0:
                lbl.setStyleSheet(f"background-color: {USED_BLUE}; color: white; font-size: 10px; font-weight: bold; border-radius: 3px;")
                lbl.setToolTip(f"Ocupado por P{val}")
            else:
                lbl.setStyleSheet(f"background-color: {FREE_GRAY}; color: #9CA3AF; font-size: 10px; border-radius: 3px;")
                lbl.setToolTip("Libre")
            self.grid_layout.addWidget(lbl, r, c)

    # ==========================================
    # 2. LISTAS LIGADAS (+ NEXT FIT)
    # ==========================================
    def crear_listas_ligadas(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        control_panel = QHBoxLayout()
        control_panel.addWidget(QLabel("Estrategia:"))
        self.combo_estrategia = QComboBox()
        self.combo_estrategia.addItems(["First Fit (Primer Ajuste)", "Next Fit (Siguiente Ajuste)", "Best Fit (Mejor Ajuste)", "Worst Fit (Peor Ajuste)"])
        control_panel.addWidget(self.combo_estrategia)
        
        control_panel.addSpacing(15)
        control_panel.addWidget(QLabel("Tamaño (MB):"))
        self.spin_proc_lista = QSpinBox()
        self.spin_proc_lista.setRange(1, 1024)
        self.spin_proc_lista.setValue(200)
        control_panel.addWidget(self.spin_proc_lista)
        
        btn_simular = QPushButton("Añadir Proceso")
        btn_simular.clicked.connect(self.agregar_proceso_lista)
        control_panel.addWidget(btn_simular)

        control_panel.addSpacing(15)
        self.combo_liberar_lista = QComboBox()
        control_panel.addWidget(self.combo_liberar_lista)
        btn_liberar = QPushButton("Liberar Proceso")
        btn_liberar.setStyleSheet("background-color: #B91C1C;")
        btn_liberar.clicked.connect(self.liberar_proceso_lista)
        control_panel.addWidget(btn_liberar)

        control_panel.addStretch()
        layout.addLayout(control_panel)

        self.info_lista = QLabel("Memoria lista. Seleccione estrategia y asigne procesos.")
        self.info_lista.setStyleSheet("color: #9CA3AF; margin-bottom: 5px;")
        layout.addWidget(self.info_lista)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background: transparent;")
        
        self.contenedor_nodos = QWidget()
        self.layout_nodos = QHBoxLayout(self.contenedor_nodos)
        self.layout_nodos.setSpacing(0)
        self.layout_nodos.setContentsMargins(0, 50, 0, 50)
        scroll.setWidget(self.contenedor_nodos)
        layout.addWidget(scroll)
        
        self.nodos_memoria = [{"tipo": "H", "id": "Hueco", "size": self.memoria_total}]
        self.renderizar_lista()
        
        return tab

    def agregar_proceso_lista(self):
        size = self.spin_proc_lista.value()
        estrategia = self.combo_estrategia.currentText()
        
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
        
        nuevo_id = f"P{self.pid_lista}"
        self.pid_lista += 1
        self.nodos_memoria[seleccionado_idx] = {"tipo": "P", "id": nuevo_id, "size": size}
        
        self.ultimo_idx_next_fit = seleccionado_idx + 1 
        
        if sobrante > 0:
            self.nodos_memoria.insert(seleccionado_idx + 1, {"tipo": "H", "id": "Hueco", "size": sobrante})
            
        self.info_lista.setText(f"Estrategia: {estrategia.split('(')[0]} | Proceso {nuevo_id} ({size}MB) asignado en el índice {seleccionado_idx}.")
        self.actualizar_combos_liberacion()
        self.renderizar_lista()

    def liberar_proceso_lista(self):
        pid = self.combo_liberar_lista.currentText()
        if not pid: return

        for i, n in enumerate(self.nodos_memoria):
            if n["id"] == pid:
                n["tipo"] = "H"
                n["id"] = "Hueco"
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
                
        self.info_lista.setText(f"Proceso {pid} liberado. Memoria compactada.")
        self.actualizar_combos_liberacion()
        self.renderizar_lista()

    def renderizar_lista(self):
        for i in reversed(range(self.layout_nodos.count())): 
            self.layout_nodos.itemAt(i).widget().setParent(None)
            
        for nodo in self.nodos_memoria:
            is_used = nodo["tipo"] == "P"
            block = BlockFrame(nodo["id"], is_used, f"{nodo['size']} MB")
            block.setFixedHeight(80)
            self.layout_nodos.addWidget(block, stretch=nodo["size"])

    # ==========================================
    # 3. SISTEMA DE ASOCIADOS
    # ==========================================
    def crear_sistema_asociados(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        control_panel = QHBoxLayout()
        control_panel.addWidget(QLabel("Tamaño Proceso (MB):"))
        self.spin_proc_buddy = QSpinBox()
        self.spin_proc_buddy.setRange(1, 1024)
        self.spin_proc_buddy.setValue(100)
        control_panel.addWidget(self.spin_proc_buddy)
        
        btn_add = QPushButton("Añadir Proceso (Dividir potencias)")
        btn_add.clicked.connect(self.agregar_proceso_buddy)
        control_panel.addWidget(btn_add)
        
        control_panel.addSpacing(20)
        self.combo_liberar_buddy = QComboBox()
        control_panel.addWidget(self.combo_liberar_buddy)
        btn_liberar = QPushButton("Liberar y Unir")
        btn_liberar.setStyleSheet("background-color: #B91C1C;")
        btn_liberar.clicked.connect(self.liberar_proceso_buddy)
        control_panel.addWidget(btn_liberar)
        
        control_panel.addStretch()
        layout.addLayout(control_panel)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background: transparent;")
        
        self.contenedor_buddy = QWidget()
        self.layout_buddy = QHBoxLayout(self.contenedor_buddy)
        self.layout_buddy.setSpacing(2)
        self.layout_buddy.setContentsMargins(0, 50, 0, 50)
        scroll.setWidget(self.contenedor_buddy)
        layout.addWidget(scroll)

        self.bloques_buddy = [BuddyBlock(self.memoria_total, 0)]
        self.renderizar_buddy()
        
        return tab

    def get_potencia_2(self, num):
        if num <= 0: return 1
        return 2 ** math.ceil(math.log2(num))

    def agregar_proceso_buddy(self):
        size_req = self.spin_proc_buddy.value()
        target_size = self.get_potencia_2(size_req)
        
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
        mejor_bloque.pid = f"P{self.pid_buddy}"
        self.pid_buddy += 1
        
        self.actualizar_combos_liberacion()
        self.renderizar_buddy()

    def liberar_proceso_buddy(self):
        pid = self.combo_liberar_buddy.currentText()
        if not pid: return
        
        bloque = next(b for b in self.bloques_buddy if b.pid == pid)
        bloque.free = True
        bloque.pid = None
        
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
                        
        self.actualizar_combos_liberacion()
        self.renderizar_buddy()

    def renderizar_buddy(self):
        for i in reversed(range(self.layout_buddy.count())): 
            self.layout_buddy.itemAt(i).widget().setParent(None)
            
        for b in self.bloques_buddy:
            texto = b.pid if not b.free else "Libre"
            frame = BlockFrame(texto, not b.free, f"{b.size} MB")
            frame.setFixedHeight(80)
            self.layout_buddy.addWidget(frame, stretch=b.size)

    # ==========================================
    # 4. MEMORIA VIRTUAL (REEMPLAZO DE PÁGINAS) - AVANCE 3
    # ==========================================
    def crear_reemplazo_paginas(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        control_panel = QHBoxLayout()
        
        control_panel.addWidget(QLabel("Cadena de Referencias:"))
        self.input_refs = QLineEdit("7, 0, 1, 2, 0, 3, 0, 4, 2, 3")
        self.input_refs.setFixedWidth(200)
        control_panel.addWidget(self.input_refs)
        
        control_panel.addSpacing(10)
        control_panel.addWidget(QLabel("Marcos de Memoria:"))
        self.spin_marcos = QSpinBox()
        self.spin_marcos.setRange(1, 10)
        self.spin_marcos.setValue(3)
        control_panel.addWidget(self.spin_marcos)
        
        control_panel.addSpacing(10)
        control_panel.addWidget(QLabel("Algoritmo:"))
        self.combo_algo_reemplazo = QComboBox()
        self.combo_algo_reemplazo.addItems(["FIFO (First In First Out)", "LRU (Least Recently Used)", "OPT (Óptimo)", "NRU (Not Recently Used)"])
        control_panel.addWidget(self.combo_algo_reemplazo)
        
        control_panel.addSpacing(10)
        btn_simular_reemplazo = QPushButton("▶ Simular Reemplazo")
        btn_simular_reemplazo.setStyleSheet("background-color: #7C3AED; color: white; font-weight: bold; border-radius: 4px;")
        btn_simular_reemplazo.clicked.connect(self.simular_reemplazo)
        control_panel.addWidget(btn_simular_reemplazo)
        
        control_panel.addStretch()
        layout.addLayout(control_panel)
        
        self.lbl_resultados_reemplazo = QLabel("Fallos de Página Totales: 0")
        self.lbl_resultados_reemplazo.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {ERROR_RED};")
        layout.addWidget(self.lbl_resultados_reemplazo)
        
        self.tabla_reemplazo = QTableWidget()
        self.tabla_reemplazo.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla_reemplazo.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.tabla_reemplazo)
        
        return tab

    def simular_reemplazo(self):
        try:
            txt_refs = self.input_refs.text().replace(" ", "")
            secuencia = [int(x) for x in txt_refs.split(",") if x.isdigit()]
            if not secuencia: raise ValueError()
        except Exception:
            QMessageBox.warning(self, "Error", "Ingrese una lista de números separados por coma (ej: 7,0,1,2).")
            return
            
        marcos_totales = self.spin_marcos.value()
        algoritmo = self.combo_algo_reemplazo.currentText().split(" ")[0]
        
        self.tabla_reemplazo.clear()
        self.tabla_reemplazo.setRowCount(len(secuencia))
        self.tabla_reemplazo.setColumnCount(marcos_totales + 2) 
        
        headers = ["Ref Entrante"] + [f"Marco {i+1}" for i in range(marcos_totales)] + ["¿Fallo?"]
        self.tabla_reemplazo.setHorizontalHeaderLabels(headers)
        
        memoria = []       
        fallos = 0
        fifo_queue = []    
        lru_time = {}      
        nru_bits = {}      
        
        for step, ref in enumerate(secuencia):
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
            
            if algoritmo == "NRU" and step % 4 == 0:
                for p in nru_bits.keys(): nru_bits[p] = 0
            
            # --- IMPRESIÓN EN TABLA CORREGIDA ---
            item_ref = QTableWidgetItem(str(ref))
            item_ref.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_ref.setBackground(QBrush(QColor(PANEL_COLOR)))
            font_ref = item_ref.font()
            font_ref.setBold(True)
            item_ref.setFont(font_ref)
            self.tabla_reemplazo.setItem(step, 0, item_ref)
            
            for i in range(marcos_totales):
                texto_marco = str(memoria[i]) if i < len(memoria) else "-"
                item_marco = QTableWidgetItem(texto_marco)
                item_marco.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tabla_reemplazo.setItem(step, i + 1, item_marco)
                
            item_fallo = QTableWidgetItem("⚠️ FALLO" if hubo_fallo else "")
            if hubo_fallo:
                item_fallo.setForeground(QBrush(QColor(ERROR_RED)))
                font_fallo = item_fallo.font()
                font_fallo.setBold(True)
                item_fallo.setFont(font_fallo)
            item_fallo.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabla_reemplazo.setItem(step, marcos_totales + 1, item_fallo)

        self.lbl_resultados_reemplazo.setText(f"Algoritmo: {algoritmo} | Fallos de Página Totales: {fallos}")

    def actualizar_combos_liberacion(self):
        if hasattr(self, 'combo_liberar_bits') and hasattr(self, 'mapa_arreglo'):
            pids_bits = sorted(list(set(self.mapa_arreglo)))
            self.combo_liberar_bits.clear()
            self.combo_liberar_bits.addItems([f"P{p}" for p in pids_bits if p > 0])
        
        if hasattr(self, 'combo_liberar_lista') and hasattr(self, 'nodos_memoria'):
            self.combo_liberar_lista.clear()
            self.combo_liberar_lista.addItems([n["id"] for n in self.nodos_memoria if n["tipo"] == "P"])
        
        if hasattr(self, 'combo_liberar_buddy') and hasattr(self, 'bloques_buddy'):
            self.combo_liberar_buddy.clear()
            self.combo_liberar_buddy.addItems([b.pid for b in self.bloques_buddy if not b.free])

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = VisualizadorMemoria()
    ventana.show()
    sys.exit(app.exec())