import random

class Proceso:
    def __init__(self, pid, nombre, prioridad, memoria, tiempo_ejecucion):
        self.pid = pid
        self.nombre = nombre
        self.estado = "Ready"  # Ready, Running, Terminated
        self.prioridad = prioridad
        self.cpu_pct = round(random.uniform(0.5, 12.0), 1)
        self.memory_pct = memoria
        self.tiempo_restante = tiempo_ejecucion
        self.tiempo_total = tiempo_ejecucion
        self.llegada = 0  # Momento exacto de ingreso al sistema

    def obtener_datos_tabla(self):
        return [
            self.pid,
            self.nombre,
            self.estado,
            self.prioridad,
            f"{self.cpu_pct}%",
            f"{self.memory_pct}%",
            f"{self.tiempo_restante}s"
        ]


class CPU:
    def __init__(self):
        self.modelo = "VM-CPU-01"
        self.frecuencia = "2.8 GHz"
        self.nucleos = 1
        self.arquitectura = "x86_64"
        self.ocupado = False
        self.proceso_actual = None
        self.carga_general = 0.0


class Memoria:
    def __init__(self, capacidad=1024):
        self.capacidad_total_mb = capacidad
        self.memoria_usada_mb = 120
        self.fragmentacion_pct = 2.5

    def memoria_disponible(self):
        return self.capacidad_total_mb - self.memoria_usada_mb


class DispositivoIO:
    def __init__(self, nombre, estado, latencia):
        self.nombre = nombre
        self.estado = estado
        self.latencia = latencia


class SistemaArchivos:
    def __init__(self):
        self.tipo = "ext4"
        self.montado = True
        self.directorios = {"/": ["bin", "etc", "home", "var"]}
        self.archivos = ["/bin/init", "/etc/config", "/home/user/doc.txt"]


class Kernel:
    def __init__(self):
        self.version = "Kernel v2.0"
        self.estado_kernel = "STOPPED"
        self.system_time_counter = 0

        # Lista de los 7 algoritmos de planificación soportados
        self.ALGORITMOS_DISPONIBLES = [
            "FCFS",
            "SJF",
            "Round Robin",
            "Por Prioridad",
            "Por Colas Multiples",
            "Planificacion Garantizada",
            "Planificacion A DOS NIVELeS"
        ]

        self.algoritmo_planificacion = "FCFS"
        self.quantum = 3
        self.quantum_actual = 0

        self.cpu = CPU()
        self.memoria = Memoria()
        self.sistema_archivos = SistemaArchivos()

        self.dispositivos = [
            DispositivoIO("Disco Principal", "ACTIVO", "5ms"),
            DispositivoIO("Teclado/Mouse", "LISTO", "1ms"),
            DispositivoIO("Tarjeta de Red", "ACTIVO", "12ms")
        ]

        self.procesos = []
        self._inicializar_procesos_base()

    def _inicializar_procesos_base(self):
        init = Proceso(1, "init", 0, 2.0, 100)
        init.llegada = 0
        self.procesos = [init]

    def iniciar(self):
        self.estado_kernel = "RUNNING"

    def detener(self):
        self.estado_kernel = "STOPPED"

    def reiniciar(self):
        self.system_time_counter = 0
        self.quantum_actual = 0
        self._inicializar_procesos_base()
        self.cpu.proceso_actual = None
        self.cpu.ocupado = False
        self.iniciar()

    def esta_ejecutando(self):
        return self.estado_kernel == "RUNNING"

    def cambiar_algoritmo(self, nuevo_algoritmo):
        """Método invocado por la interfaz gráfica al cambiar de opción en la lista/botón."""
        if nuevo_algoritmo in self.ALGORITMOS_DISPONIBLES:
            self.algoritmo_planificacion = nuevo_algoritmo
            self.quantum_actual = 0

    def crear_proceso_aleatorio(self):
        pid = random.randint(100, 999)
        nombre = f"Proc_{pid}"
        prioridad = random.choice([10, 20, 30])
        memoria = round(random.uniform(1.0, 15.0), 1)
        tiempo = random.randint(5, 15)

        nuevo = Proceso(pid, nombre, prioridad, memoria, tiempo)
        nuevo.llegada = self.system_time_counter
        self.procesos.append(nuevo)
        return nuevo

    def buscar_proceso(self, pid):
        for p in self.procesos:
            if p.pid == pid:
                return p
        return None

    def eliminar_proceso(self, pid):
        p = self.buscar_proceso(pid)
        if p:
            if self.cpu.proceso_actual == p:
                self.cpu.proceso_actual = None
                self.cpu.ocupado = False
            self.procesos.remove(p)
            return True
        return False

    def avanzar_reloj(self, segundos):
        if not self.esta_ejecutando():
            return

        for _ in range(segundos):
            self.system_time_counter += 1
            self.quantum_actual += 1

            # Descuenta tiempo al proceso actual en ejecucion
            if self.cpu.proceso_actual:
                self.cpu.proceso_actual.tiempo_restante -= 1

                if self.cpu.proceso_actual.tiempo_restante <= 0:
                    self.cpu.proceso_actual.estado = "Terminated"
                    self.procesos.remove(self.cpu.proceso_actual)
                    self.cpu.proceso_actual = None
                    self.cpu.ocupado = False
                    self.quantum_actual = 0

            self.planificar_procesos()

    def planificar_procesos(self):
        if not self.esta_ejecutando():
            return

        # Evaluación según el algoritmo seleccionado en la interfaz
        if self.algoritmo_planificacion == "FCFS":
            self._planificar_fcfs()
        elif self.algoritmo_planificacion == "SJF":
            self._planificar_sjf()
        elif self.algoritmo_planificacion == "Round Robin":
            self._planificar_round_robin()
        elif self.algoritmo_planificacion == "Por Prioridad":
            self._planificar_prioridad()
        elif self.algoritmo_planificacion == "Por Colas Multiples":
            self._planificar_colas_multiples()
        elif self.algoritmo_planificacion == "Planificacion Garantizada":
            self._planificar_garantizada()
        elif self.algoritmo_planificacion == "Planificacion A DOS NIVELeS":
            self._planificar_dos_niveles()

    def _planificar_fcfs(self):
        if self.cpu.proceso_actual is not None:
            return
        listos = [p for p in self.procesos if p.estado == "Ready"]
        if listos:
            listos.sort(key=lambda p: p.llegada)
            siguiente = listos[0]
            siguiente.estado = "Running"
            self.cpu.proceso_actual = siguiente
            self.cpu.ocupado = True

    def _planificar_sjf(self):
        if self.cpu.proceso_actual is not None:
            return
        listos = [p for p in self.procesos if p.estado == "Ready"]
        if listos:
            listos.sort(key=lambda p: p.tiempo_restante)
            siguiente = listos[0]
            siguiente.estado = "Running"
            self.cpu.proceso_actual = siguiente
            self.cpu.ocupado = True

    def _planificar_round_robin(self):
        listos = [p for p in self.procesos if p.estado == "Ready"]
        if self.cpu.proceso_actual is not None:
            if self.quantum_actual >= self.quantum:
                proceso_actual = self.cpu.proceso_actual
                proceso_actual.estado = "Ready"
                self.cpu.proceso_actual = None
                self.cpu.ocupado = False
                self.quantum_actual = 0
            else:
                return

        if self.cpu.proceso_actual is None and listos:
            listos.sort(key=lambda p: p.llegada)
            siguiente = listos[0]
            siguiente.estado = "Running"
            self.cpu.proceso_actual = siguiente
            self.cpu.ocupado = True
            self.quantum_actual = 0

    def _planificar_prioridad(self):
        if self.cpu.proceso_actual is not None:
            return
        listos = [p for p in self.procesos if p.estado == "Ready"]
        if listos:
            listos.sort(key=lambda p: p.prioridad)
            siguiente = listos[0]
            siguiente.estado = "Running"
            self.cpu.proceso_actual = siguiente
            self.cpu.ocupado = True

    def _planificar_colas_multiples(self):
        # Colas múltiples: Separa los procesos por su nivel de prioridad asignado
        if self.cpu.proceso_actual is not None:
            return
        listos = [p for p in self.procesos if p.estado == "Ready"]
        if listos:
            # Atiende primero las colas con menor valor numérico de prioridad, respetando FIFO (llegada)
            listos.sort(key=lambda p: (p.prioridad, p.llegada))
            siguiente = listos[0]
            siguiente.estado = "Running"
            self.cpu.proceso_actual = siguiente
            self.cpu.ocupado = True

    def _planificar_garantizada(self):
        # Planificación garantizada: Busca el equilibrio calculando la proporción de tiempo de CPU recibido
        if self.cpu.proceso_actual is not None:
            return
        listos = [p for p in self.procesos if p.estado == "Ready"]
        if listos:
            # Da prioridad al proceso que tenga menor tiempo ejecutado en proporción a su necesidad
            listos.sort(key=lambda p: (p.tiempo_total - p.tiempo_restante))
            siguiente = listos[0]
            siguiente.estado = "Running"
            self.cpu.proceso_actual = siguiente
            self.cpu.ocupado = True

    def _planificar_dos_niveles(self):
        # Planificación a dos niveles: Cola del sistema (prioridad alta <= 10) y cola de usuario
        if self.cpu.proceso_actual is not None:
            return
        listos = [p for p in self.procesos if p.estado == "Ready"]
        if listos:
            # Prioridad absoluta a procesos del sistema o nivel alto
            sistema = [p for p in listos if p.prioridad <= 10]
            if sistema:
                sistema.sort(key=lambda p: p.llegada)
                siguiente = sistema[0]
            else:
                # Si no hay del sistema, pasa a los de usuario por orden de llegada
                listos.sort(key=lambda p: p.llegada)
                siguiente = listos[0]

            siguiente.estado = "Running"
            self.cpu.proceso_actual = siguiente
            self.cpu.ocupado = True

    def actualizar_procesos(self):
        if not self.esta_ejecutando():
            return
        total_cpu = sum(p.cpu_pct for p in self.procesos if p.estado == "Running")
        self.cpu.carga_general = min(100.0, round(total_cpu + random.uniform(2.0, 8.0), 1))

    def obtener_informacion_sistema(self):
        return {
            "kernel": self.estado_kernel,
            "version": self.version,
            "cpu": self.cpu.carga_general,
            "memoria_total": self.memoria.capacidad_total_mb,
            "memoria_usada": self.memoria.memoria_usada_mb,
            "fragmentacion": self.memoria.fragmentacion_pct,
            "procesos": len(self.procesos),
            "dispositivos": len(self.dispositivos),
            "sistema_archivos": "Montado" if self.sistema_archivos.montado else "Desmontado"
        }