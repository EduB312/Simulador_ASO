import sys
import random
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QTabWidget, QLabel, QPushButton, QFrame, QScrollArea, QGridLayout, QComboBox
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPalette, QColor, QFont

# --- ESTILOS GLOBALES ---
BG_COLOR = "#111827"
PANEL_COLOR = "#1F2937"
BORDER_COLOR = "#334155"
TEXT_COLOR = "#E5E7EB"
ACCENT_BLUE = "#3B82F6"
FREE_GRAY = "#374151"
USED_BLUE = "#2563EB"
HOLE_GREEN = "#059669"

ESTILO_GLOBAL = f"""
    QMainWindow {{ background-color: {BG_COLOR}; }}
    QWidget {{ color: {TEXT_COLOR}; font-family: 'Segoe UI', sans-serif; }}
    QTabWidget::pane {{ border: 1px solid {BORDER_COLOR}; border-radius: 8px; background: {PANEL_COLOR}; }}
    QTabBar::tab {{ background: {BG_COLOR}; border: 1px solid {BORDER_COLOR}; padding: 8px 20px; font-weight: bold; border-top-left-radius: 6px; border-top-right-radius: 6px; }}
    QTabBar::tab:selected {{ background: {PANEL_COLOR}; color: {ACCENT_BLUE}; border-top: 2px solid {ACCENT_BLUE}; }}
    QPushButton {{ background-color: {ACCENT_BLUE}; color: white; border-radius: 6px; padding: 8px 15px; font-weight: bold; }}
    QPushButton:hover {{ background-color: #60A5FA; }}
"""

class BlockFrame(QFrame):
    """Marco estilizado para representar bloques de memoria."""
    def __init__(self, text, is_used=False, size_text=""):
        super().__init__()
        self.setFrameShape(QFrame.Shape.StyledPanel)
        color = USED_BLUE if is_used else FREE_GRAY
        border = "#60A5FA" if is_used else "#9CA3AF"
        
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {color};
                border: 2px solid {border};
                border-radius: 8px;
            }}
        """)
        layout = QVBoxLayout(self)
        
        lbl_title = QLabel(text)
        lbl_title.setStyleSheet("font-weight: bold; font-size: 14px; border: none; background: transparent;")
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_title)
        
        if size_text:
            lbl_size = QLabel(size_text)
            lbl_size.setStyleSheet("font-size: 11px; color: #D1D5DB; border: none; background: transparent;")
            lbl_size.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(lbl_size)


class VisualizadorMemoria(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gestión Avanzada de Memoria")
        self.resize(950, 600)
        self.setStyleSheet(ESTILO_GLOBAL)

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # Título principal
        title = QLabel("Visor de Estructuras de Memoria")
        title.setStyleSheet(f"font-size: 22px; font-weight: bold; color: {ACCENT_BLUE}; margin-bottom: 10px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Contenedor de pestañas
        self.tabs = QTabWidget()
        self.tabs.addTab(self.crear_mapa_bits(), " Mapa de Bits")
        self.tabs.addTab(self.crear_listas_ligadas(), " Listas Ligadas & Estrategias")
        self.tabs.addTab(self.crear_sistema_asociados(), " Sistema de Asociados (Buddy)")
        layout.addWidget(self.tabs)

    # ==========================================
    # 1. MAPA DE BITS
    # ==========================================
    def crear_mapa_bits(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        desc = QLabel("Cada cuadro representa un bloque de memoria. <font color='#60A5FA'><b>Azul (1)</b></font> = Ocupado, <font color='#9CA3AF'><b>Gris (0)</b></font> = Libre.")
        desc.setStyleSheet("font-size: 14px; margin-bottom: 10px;")
        layout.addWidget(desc)

        grid_widget = QWidget()
        self.grid_layout = QGridLayout(grid_widget)
        self.grid_layout.setSpacing(2)
        
        self.bits_labels = []
        self.generar_mapa_bits_aleatorio()

        layout.addWidget(grid_widget, alignment=Qt.AlignmentFlag.AlignCenter)
        
        btn_refresh = QPushButton("↻ Generar Nuevo Mapa")
        btn_refresh.setFixedWidth(200)
        btn_refresh.clicked.connect(self.generar_mapa_bits_aleatorio)
        layout.addWidget(btn_refresh, alignment=Qt.AlignmentFlag.AlignCenter)
        
        return tab

    def generar_mapa_bits_aleatorio(self):
        # Limpiar grid anterior
        for i in reversed(range(self.grid_layout.count())): 
            self.grid_layout.itemAt(i).widget().setParent(None)
            
        filas, columnas = 10, 32
        for r in range(filas):
            for c in range(columnas):
                estado = random.choice([0, 0, 1]) # Mayor probabilidad de libre
                lbl = QLabel(str(estado))
                lbl.setFixedSize(22, 22)
                lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                
                if estado == 1:
                    lbl.setStyleSheet(f"background-color: {USED_BLUE}; color: white; font-size: 10px; font-weight: bold; border-radius: 3px;")
                else:
                    lbl.setStyleSheet(f"background-color: {FREE_GRAY}; color: #9CA3AF; font-size: 10px; border-radius: 3px;")
                
                self.grid_layout.addWidget(lbl, r, c)

    # ==========================================
    # 2. LISTAS LIGADAS Y ESTRATEGIAS
    # ==========================================
    def crear_listas_ligadas(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Panel de control
        control_panel = QHBoxLayout()
        control_panel.addWidget(QLabel("Estrategia de Asignación:"))
        
        self.combo_estrategia = QComboBox()
        self.combo_estrategia.addItems(["First Fit (Primer Ajuste)", "Best Fit (Mejor Ajuste)", "Worst Fit (Peor Ajuste)"])
        self.combo_estrategia.setStyleSheet(f"background: {BG_COLOR}; padding: 5px; border: 1px solid {BORDER_COLOR}; border-radius: 5px;")
        control_panel.addWidget(self.combo_estrategia)
        
        btn_simular = QPushButton("▶ Asignar Proceso de 40KB")
        btn_simular.clicked.connect(self.simular_asignacion_lista)
        control_panel.addWidget(btn_simular)
        control_panel.addStretch()
        layout.addLayout(control_panel)

        # Area de lista
        self.scroll_lista = QScrollArea()
        self.scroll_lista.setWidgetResizable(True)
        self.scroll_lista.setStyleSheet("border: none; background: transparent;")
        
        self.contenedor_nodos = QWidget()
        self.layout_nodos = QHBoxLayout(self.contenedor_nodos)
        self.layout_nodos.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.scroll_lista.setWidget(self.contenedor_nodos)
        
        layout.addWidget(self.scroll_lista)
        self.dibujar_nodos_iniciales()
        
        return tab

    def dibujar_nodos_iniciales(self):
        self.nodos_memoria = [
            {"tipo": "P", "id": "P1", "size": 20},
            {"tipo": "H", "id": "Hueco", "size": 50},
            {"tipo": "P", "id": "P2", "size": 30},
            {"tipo": "H", "id": "Hueco", "size": 120},
            {"tipo": "P", "id": "P3", "size": 10},
            {"tipo": "H", "id": "Hueco", "size": 45}
        ]
        self.renderizar_lista()

    def renderizar_lista(self):
        # Limpiar layout
        for i in reversed(range(self.layout_nodos.count())): 
            self.layout_nodos.itemAt(i).widget().setParent(None)
            
        for i, nodo in enumerate(self.nodos_memoria):
            is_used = nodo["tipo"] == "P"
            block = BlockFrame(nodo["id"], is_used, f"{nodo['size']} KB")
            block.setFixedSize(100, 70)
            self.layout_nodos.addWidget(block)
            
            # Flecha apuntador (excepto el último)
            if i < len(self.nodos_memoria) - 1:
                lbl_arrow = QLabel("➔")
                lbl_arrow.setStyleSheet(f"font-size: 20px; color: {ACCENT_BLUE}; font-weight: bold;")
                self.layout_nodos.addWidget(lbl_arrow)

    def simular_asignacion_lista(self):
        estrategia = self.combo_estrategia.currentText()
        size_req = 40
        
        # Buscar huecos
        huecos = [(idx, n) for idx, n in enumerate(self.nodos_memoria) if n["tipo"] == "H" and n["size"] >= size_req]
        
        if not huecos:
            return # No hay espacio

        seleccionado_idx = -1
        if "First" in estrategia:
            seleccionado_idx = huecos[0][0]
        elif "Best" in estrategia:
            seleccionado_idx = min(huecos, key=lambda x: x[1]["size"])[0]
        elif "Worst" in estrategia:
            seleccionado_idx = max(huecos, key=lambda x: x[1]["size"])[0]

        # Dividir el hueco
        nodo_h = self.nodos_memoria[seleccionado_idx]
        espacio_sobrante = nodo_h["size"] - size_req
        
        nuevo_proceso = {"tipo": "P", "id": "P_New", "size": size_req}
        self.nodos_memoria[seleccionado_idx] = nuevo_proceso
        
        if espacio_sobrante > 0:
            nuevo_hueco = {"tipo": "H", "id": "Hueco", "size": espacio_sobrante}
            self.nodos_memoria.insert(seleccionado_idx + 1, nuevo_hueco)
            
        self.renderizar_lista()

    # ==========================================
    # 3. SISTEMA DE ASOCIADOS (BUDDY SYSTEM)
    # ==========================================
    def crear_sistema_asociados(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        desc = QLabel("El sistema divide los bloques en mitades (colegas) hasta encontrar el tamaño adecuado (potencias de 2).")
        desc.setStyleSheet("font-size: 14px; margin-bottom: 10px;")
        layout.addWidget(desc)

        self.layout_buddy = QVBoxLayout()
        self.layout_buddy.setSpacing(10)
        
        # Estado inicial (Simulación visual estática para entendimiento)
        niveles = [
            [("1024 KB (Libre)", False)],
            [("512 KB (Ocupado)", True), ("512 KB (Libre)", False)],
            [("256 KB (Ocupado)", True), ("256 KB (Libre)", False), ("512 KB (Libre)", False)]
        ]

        for nivel in niveles:
            row_widget = QWidget()
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(0,0,0,0)
            
            for texto, usado in nivel:
                bloque = BlockFrame(texto.split()[0], usado, texto.split()[1])
                bloque.setFixedHeight(60)
                row_layout.addWidget(bloque)
                
            self.layout_buddy.addWidget(row_widget)

        layout.addLayout(self.layout_buddy)
        layout.addStretch()

        btn_dividir = QPushButton("Simular División (Asignar 128KB)")
        btn_dividir.setFixedWidth(250)
        btn_dividir.clicked.connect(self.simular_buddy)
        layout.addWidget(btn_dividir, alignment=Qt.AlignmentFlag.AlignCenter)
        
        return tab

    def simular_buddy(self):
        # Añade visualmente un nivel extra dividiendo el bloque libre de 256KB
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0,0,0,0)
        
        bloques = [
            ("256 KB (Ocupado)", True),
            ("128 KB (Ocupado Px)", True), 
            ("128 KB (Libre)", False),
            ("512 KB (Libre)", False)
        ]
        
        for texto, usado in bloques:
            bloque = BlockFrame(texto.split()[0], usado, " ".join(texto.split()[1:]))
            bloque.setFixedHeight(60)
            row_layout.addWidget(bloque)
            
        self.layout_buddy.addWidget(row_widget)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = VisualizadorMemoria()
    ventana.show()
    sys.exit(app.exec())