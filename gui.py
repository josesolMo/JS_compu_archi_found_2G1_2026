import tkinter as tk
from tkinter import ttk

from tkinter import messagebox
from assembler import MiniAssembler
from simulation_manager import SimulationManager
from core.processors import Unicycle, Multicycle, PipelinedStall, PipelinedForwarding

class SimuladorGUI(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Simulador de Procesadores")
        self.state("zoomed")
        self.configure(bg="#f2f2f2")
        self.manager = None
        self.after_id = None
        self.historial = []
        self.proc1_tipo = None
        self.proc2_tipo = None
        self.modo_var = tk.StringVar(value="Paso a Paso")

        self.proc_map = {
            "Uniciclo": Unicycle,
            "Multiciclo": Multicycle,
            "Segmentado (Stalls)": PipelinedStall,
            "Segmentado (Forwarding)": PipelinedForwarding
        }

        self.crear_layout()

    def crear_layout(self):
        self.columnconfigure(0, weight=0)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        self.panel_izquierdo()
        self.panel_principal()

    def panel_izquierdo(self):
        left = ttk.Frame(self, padding=8)
        left.grid(row=0, column=0, sticky="ns")

        self.panel_ejecucion(left)
        self.panel_consola(left)
        self.panel_procesadores(left)
        self.panel_registros(left)
        self.panel_memoria(left)

    def panel_principal(self):
        main = ttk.Frame(self, padding=8)
        main.grid(row=0, column=1, sticky="nsew")

        main.columnconfigure(0, weight=1)
        main.rowconfigure(0, weight=1)
        main.rowconfigure(1, weight=1)
        main.rowconfigure(2, weight=0)

        self.frame_cpu(main, "Procesador 1", 0)
        self.frame_cpu(main, "Procesador 2", 1)
        self.frame_resultados(main)

    def panel_ejecucion(self, parent):
        frame = ttk.LabelFrame(parent, text="Modo de ejecución", padding=8)
        frame.pack(fill="x", pady=5)

        self.combo_modo = ttk.Combobox(
            frame,
            textvariable=self.modo_var,
            values=["Paso a Paso", "Automática", "Completa", "Detectar Hazard"],
            width=18,
            state="readonly"
        )
        self.combo_modo.grid(row=0, column=0, padx=4)

        self.btn_run = ttk.Button(frame, text="RUN", command=self.run)
        self.btn_run.grid(row=0, column=1, padx=4)

        self.btn_reset = ttk.Button(
            frame,
            text="RESET",
            command=self.reset_simulacion
        )
        self.btn_reset.grid(row=1, column=1, padx=4, pady=4)

        self.delay_ms = tk.IntVar(value=1)

        spin = ttk.Spinbox(
            frame,
            from_=1,
            to=1000,
            increment=1,
            textvariable=self.delay_ms,
            width=8
        )

        spin.grid(row=1, column=0, pady=6, padx=10, sticky="w")

        ttk.Label(frame, text="ms").grid(row=1, column=0, padx=(80, 0), sticky="w")

    def panel_consola(self, parent):
        frame = ttk.LabelFrame(parent, text="Consola", padding=8)
        frame.pack(fill="x", pady=5)

        self.consola = tk.Text(frame, width=28, height=7)
        self.consola.pack(fill="both")
        text = self.consola

        text.insert("end", "ADDI x1, x0, 5\n")
        text.insert("end", "ADD x2, x1, x3\n")
        text.insert("end", "LW x4, 0(x2)\n")
        text.insert("end", "ADD x5, x4, x1\n")
        text.insert("end", "SW x5, 4(x2)\n")
        text.insert("end", "BEQ x1, x2, -2\n")

    def panel_procesadores(self, parent):

        frame = ttk.LabelFrame(parent, text="Procesadores", padding=8)
        frame.pack(fill="x", pady=5)

        self.cpu_vars = {}

        opciones = [
            "Uniciclo",
            "Multiciclo",
            "Segmentado (Stalls)",
            "Segmentado (Forwarding)"
        ]

        for op in opciones:

            var = tk.BooleanVar(value=False)
            self.cpu_vars[op] = var

            chk = ttk.Checkbutton(
                frame,
                text=op,
                variable=var,
                command=self.actualizar_datapaths
            )

            chk.pack(anchor="w", pady=2)
    
    def limitar_seleccion(self):

        activos = [
            op for op, var in self.cpu_vars.items()
            if var.get()
        ]

        if len(activos) > 2:

            ultimo = activos[-1]
            self.cpu_vars[ultimo].set(False)
    
    def actualizar_datapaths(self):

        activos = [
            op for op, var in self.cpu_vars.items()
            if var.get()
        ]

        if len(activos) > 2:
            ultimo = activos[-1]
            self.cpu_vars[ultimo].set(False)
            activos = activos[:2]

        for widget in self.area_p1.winfo_children():
            widget.destroy()

        for widget in self.area_p2.winfo_children():
            widget.destroy()

        estado = self.manager.get_full_state() if self.manager else None

        self.proc1_tipo = None
        self.proc2_tipo = None

        if len(activos) >= 1:
            self.proc1_tipo = activos[0]
            estado_p1 = estado["processor_1"] if estado else None
            self.dibujar_por_tipo(self.area_p1, activos[0], estado_p1)

        if len(activos) >= 2:
            self.proc2_tipo = activos[1]
            estado_p2 = estado["processor_2"] if estado else None
            self.dibujar_por_tipo(self.area_p2, activos[1], estado_p2)

        self.actualizar_titulos_procesadores()
    
    def dibujar_por_tipo(self, frame, tipo, estado_proc=None):

        if tipo == "Uniciclo":
            canvas = self.dibujar_datapath_uniciclo(frame, estado_proc)
        elif tipo == "Multiciclo":
            canvas = self.dibujar_datapath_multiciclo(frame, estado_proc)
        elif tipo == "Segmentado (Stalls)":
            canvas = self.dibujar_datapath_segmentado_stalls(frame, estado_proc)
        elif tipo == "Segmentado (Forwarding)":
            canvas = self.dibujar_datapath_segmentado_forwarding(frame, estado_proc)
        else:
            return

        canvas.grid(row=0, column=0, sticky="nsew")

    def panel_registros(self, parent):

        frame = ttk.LabelFrame(parent, text="Registros", padding=5)
        frame.pack(fill="both", expand=True, pady=5)

        self.procesador_actual = tk.StringVar(value="P1")

        # Barra superior
        barra = ttk.Frame(frame)
        barra.pack(fill="x", pady=(0, 5))

        ttk.Radiobutton(
            barra,
            text="P1",
            variable=self.procesador_actual,
            value="P1",
            command=self.actualizar_tablas_laterales
        ).pack(side="left", expand=True)

        ttk.Radiobutton(
            barra,
            text="P2",
            variable=self.procesador_actual,
            value="P2",
            command=self.actualizar_tablas_laterales
        ).pack(side="left", expand=True)

        # Contenedor tabla + scroll
        contenedor = ttk.Frame(frame)
        contenedor.pack(fill="both", expand=True)

        tabla = ttk.Treeview(
            contenedor,
            columns=("registro", "valor"),
            show="headings",
            height=6
        )

        tabla.heading("registro", text="Registro")
        tabla.heading("valor", text="Valor")

        tabla.column("registro", width=70, anchor="center")
        tabla.column("valor", width=140, anchor="center")

        # Scroll vertical
        scroll = ttk.Scrollbar(
            contenedor,
            orient="vertical",
            command=tabla.yview
        )

        tabla.configure(yscrollcommand=scroll.set)

        tabla.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        self.tabla_registros = tabla
        self.procesador_actual.trace_add(
            "write",
            lambda *args: self.actualizar_tablas_laterales()
        )

        # Registros vacíos
        for i in range(32):
            tabla.insert(
                "",
                "end",
                values=(f"x{i}", "0x00000000")
            )

    def panel_memoria(self, parent):

        frame = ttk.LabelFrame(parent, text="Memoria", padding=5)
        frame.pack(fill="both", expand=True, pady=5)

        self.memoria_actual = tk.StringVar(value="P1")

        # Botones P1 / P2
        barra = ttk.Frame(frame)
        barra.pack(fill="x", pady=(0, 5))

        ttk.Radiobutton(
            barra,
            text="P1",
            variable=self.memoria_actual,
            value="P1",
            command=self.actualizar_tablas_laterales
        ).pack(side="left", expand=True)

        ttk.Radiobutton(
            barra,
            text="P2",
            variable=self.memoria_actual,
            value="P2",
            command=self.actualizar_tablas_laterales
        ).pack(side="left", expand=True)

        # Contenedor tabla + scroll
        contenedor = ttk.Frame(frame)
        contenedor.pack(fill="both", expand=True)

        tabla = ttk.Treeview(
            contenedor,
            columns=("valor",),
            show="tree headings",
            height=10
        )

        # Columna izquierda (direcciones)
        tabla.heading("#0", text="Dirección")
        tabla.column("#0", width=90, anchor="w")

        # Columna valores
        tabla.heading("valor", text="Valor")
        tabla.column("valor", width=140, anchor="center")

        # Scrollbar
        scroll = ttk.Scrollbar(
            contenedor,
            orient="vertical",
            command=tabla.yview
        )

        tabla.configure(yscrollcommand=scroll.set)

        tabla.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        self.tabla_memoria = tabla
        self.memoria_actual.trace_add(
            "write",
            lambda *args: self.actualizar_tablas_laterales()
        )

        # Espacios de memoria
        for i in range(256):

            direccion = f"0x{i*4:04X}"

            tabla.insert(
                "",
                "end",
                text=direccion,
                values=("0x00000000",)
            )

    def frame_cpu(self, parent, titulo, fila):
        frame = ttk.LabelFrame(parent, text=titulo, padding=5)
        if titulo == "Procesador 1":
            self.frame_proc1 = frame
        else:
            self.frame_proc2 = frame
        frame.grid(row=fila, column=0, sticky="nsew", pady=5)

        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(1, weight=1)

        tabla = self.tabla_pipeline(frame)

        if titulo == "Procesador 1":
            self.tabla_pipeline_p1 = tabla
        else:
            self.tabla_pipeline_p2 = tabla

        area = ttk.Frame(frame, height=220)
        area.grid(row=1, column=0, sticky="nsew")
        area.grid_propagate(False)

        area.columnconfigure(0, weight=1)
        area.rowconfigure(0, weight=1)

        if titulo == "Procesador 1":
            self.area_p1 = area
        else:
            self.area_p2 = area
    
    def dibujar_datapath_uniciclo(self, frame, estado_proc=None):
        stages = estado_proc["pipeline_stages"] if estado_proc else {}
        canvas = tk.Canvas(frame, bg="white", height=230)

        def bloque(x1, y1, x2, y2, texto, etapa=None):
            fill = self.color_por_etapa(etapa, stages) if etapa else "white"
            outline = self.borde_por_etapa(etapa, stages) if etapa else "black"

            canvas.create_rectangle(
                x1, y1, x2, y2,
                width=2 if etapa and stages.get(etapa) not in ("", "—", None) else 1,
                fill=fill,
                outline=outline
            )
            canvas.create_text((x1+x2)//2, (y1+y2)//2, text=texto)

        def cable(x1, y1, x2, y2, dash=None):
            canvas.create_line(x1,y1,x2,y2,width=2,dash=dash)

        # Bloques
        bloque(20, 95, 120, 145, "PC", "IF")
        bloque(190, 95, 310, 145, "Instruction\nMemory", "IF")
        bloque(390, 95, 510, 145, "Register\nFile", "ID")
        bloque(390, 175, 510, 225, "Immediate\nGenerator", "ID")
        bloque(590, 95, 710, 145, "ALU", "EX")
        bloque(790, 95, 920, 145, "Data Memory", "MEM")
        bloque(790, 20, 920, 70, "WB MUX", "WB")
        bloque(1010, 95, 1130, 145, "PC + 4 /\nBranch", "EX")
        bloque(290, 10, 410, 60, "Control Unit", "ID")

        # Ruta principal
        cable(120, 120, 190, 120)
        cable(310, 120, 390, 120)
        cable(510, 120, 590, 120)
        cable(710, 120, 790, 120)
        cable(920, 120, 1010, 120)

        # PC a PC+4/Branch por abajo
        canvas.create_line(70, 145, 70, 215, width=1)
        canvas.create_line(70, 215, 1070, 215, width=1)
        cable(1070, 215, 1070, 145)

        # PC+4/Branch hacia PC por arriba
        canvas.create_line(1130, 120, 1160, 120, width=1)
        canvas.create_line(1160, 120, 1160, 5, width=1)
        canvas.create_line(1160, 5, 70, 5, width=1)
        cable(70, 5, 70, 95)

        # Instruction Memory a Immediate Generator
        canvas.create_line(250, 145, 250, 200, width=1)
        cable(250, 200, 390, 200)

        # Immediate Generator a ALU
        canvas.create_line(510, 200, 650, 200, width=1)
        cable(650, 200, 650, 145)

        # Data Memory a WB MUX
        canvas.create_line(855, 95, 855, 70, width=1)
        cable(855, 70, 855, 70)

        # ALU a WB MUX
        canvas.create_line(650, 95, 650, 45, width=1)
        cable(650, 45, 790, 45)

        # WB MUX a Register File
        canvas.create_line(790, 45, 560, 45, width=1)
        canvas.create_line(560, 45, 560, 95, width=1)
        cable(560, 95, 510, 95)

        # WB MUX a PC+4/Branch
        canvas.create_line(920, 45, 1090, 45, width=1)
        cable(1090, 45, 1090, 95)

        # Control Unit
        cable(350, 60, 350, 120)

        # Control Unit a Register File
        canvas.create_line(410, 45, 430, 45, width=1, dash=(3, 3))
        canvas.create_line(430, 45, 430, 95, width=1, dash=(3, 3))
        cable(430, 95, 430, 95, dash=(3, 3))

        # Control Unit a ALU
        canvas.create_line(410, 35, 620, 35, width=1, dash=(3, 3))
        canvas.create_line(620, 35, 620, 95, width=1, dash=(3, 3))
        cable(620, 95, 620, 95, dash=(3, 3))

        # Control Unit a Data Memory
        canvas.create_line(410, 55, 840, 55, width=1, dash=(3, 3))
        canvas.create_line(840, 55, 840, 95, width=1, dash=(3, 3))
        cable(840, 95, 840, 95, dash=(3, 3))

        # Control Unit a WB MUX
        canvas.create_line(410, 20, 790, 20, width=1, dash=(3, 3))
        cable(790, 20, 790, 45, dash=(3, 3))

        # Control Unit a PC+4/Branch
        canvas.create_line(410, 10, 1130, 10, width=1, dash=(3, 3))
        canvas.create_line(1130, 10, 1130, 95, width=1, dash=(3, 3))
        cable(1130, 95, 1130, 95, dash=(3, 3))

        return canvas
    
    def dibujar_datapath_multiciclo(self, frame, estado_proc=None):
        stages = estado_proc["pipeline_stages"] if estado_proc else {}
        canvas = tk.Canvas(frame, bg="white", height=210)

        def bloque(x1, y1, x2, y2, texto, etapa=None):
            fill = self.color_por_etapa(etapa, stages) if etapa else "white"
            outline = self.borde_por_etapa(etapa, stages) if etapa else "black"

            canvas.create_rectangle(
                x1, y1, x2, y2,
                width=2 if etapa and stages.get(etapa) not in ("", "—", None) else 1,
                fill=fill,
                outline=outline
            )
            canvas.create_text((x1+x2)//2, (y1+y2)//2, text=texto)

        def cable(x1, y1, x2, y2, dash=None):
            canvas.create_line(x1,y1,x2,y2,width=2,dash=dash)

        bloque(20, 95, 70, 125, "PC", "IF")
        bloque(100, 95, 165, 125, "MUX\nPC", "IF")
        bloque(200, 90, 275, 130, "Unified\nMemory", "IF")

        bloque(330, 75, 385, 105, "IR", "ID")
        bloque(330, 130, 385, 160, "MDR", "MEM")

        bloque(455, 105, 545, 140, "Register\nFile", "ID")
        bloque(455, 35, 545, 65, "Sign\nExtend", "ID")

        bloque(610, 65, 670, 95, "Reg B", "ID")
        bloque(610, 135, 670, 165, "Reg A", "ID")

        bloque(725, 55, 795, 85, "MUX\nSrcB", "EX")
        bloque(725, 135, 795, 165, "MUX\nSrcA", "EX")

        bloque(850, 95, 910, 125, "ALU", "EX")
        bloque(960, 95, 1030, 125, "ALU\nOut", "EX")
        bloque(1080, 95, 1160, 125, "MUX\nResult", "WB")

        bloque(610, 5, 710, 35, "Control Unit", "ID")

        cable(70, 110, 100, 110)
        cable(165, 110, 200, 110)

        canvas.create_line(275, 110, 305, 110)
        canvas.create_line(305, 110, 305, 90)
        cable(305, 90, 330, 90)

        canvas.create_line(305, 110, 305, 145)
        cable(305, 145, 330, 145)

        canvas.create_line(385, 90, 420, 90)
        canvas.create_line(420, 90, 420, 122)
        cable(420, 122, 455, 122)

        canvas.create_line(385, 90, 420, 90)
        canvas.create_line(420, 90, 420, 50)
        cable(420, 50, 455, 50)

        canvas.create_line(385, 145, 420, 145)
        canvas.create_line(420, 145, 420, 132)
        cable(420, 132, 455, 132)

        canvas.create_line(545, 122, 580, 122)
        canvas.create_line(580, 122, 580, 80)
        cable(580, 80, 610, 80)

        canvas.create_line(580, 122, 580, 150)
        cable(580, 150, 610, 150)

        cable(670, 80, 725, 80)
        cable(670, 150, 725, 150)

        canvas.create_line(545, 50, 700, 50)
        canvas.create_line(700, 50, 700, 70)
        cable(700, 70, 725, 70)

        canvas.create_line(795, 70, 825, 70)
        canvas.create_line(825, 70, 825, 103)
        cable(825, 103, 850, 103)

        canvas.create_line(795, 150, 825, 150)
        canvas.create_line(825, 150, 825, 117)
        cable(825, 117, 850, 117)

        cable(910, 110, 960, 110)
        cable(1030, 110, 1080, 110)

        canvas.create_line(1160, 110, 1185, 110)
        canvas.create_line(1185, 110, 1185, 50)
        canvas.create_line(1185, 50, 132, 50)
        cable(132, 50, 132, 95)

        canvas.create_line(1120, 125, 1120, 190)
        canvas.create_line(1120, 190, 500, 190)
        cable(500, 190, 500, 140)

        canvas.create_line(45, 125, 45, 200)
        canvas.create_line(45, 200, 760, 200)
        cable(760, 200, 760, 165)

        canvas.create_line(995, 125, 995, 205)
        canvas.create_line(995, 205, 238, 205)
        cable(238, 205, 238, 130)

        cable(650, 35, 760, 55, dash=(3, 3))
        cable(660, 35, 760, 135, dash=(3, 3))
        cable(710, 20, 880, 95, dash=(3, 3))
        cable(710, 15, 1120, 95, dash=(3, 3))
        cable(610, 20, 132, 95, dash=(3, 3))

        return canvas
        
    def dibujar_datapath_segmentado_stalls(self, frame, estado_proc=None):
        stages = estado_proc["pipeline_stages"] if estado_proc else {}
        canvas = tk.Canvas(frame, bg="white", height=210)

        def bloque(x1, y1, x2, y2, texto, etapa=None):
            fill = self.color_por_etapa(etapa, stages) if etapa else "white"
            outline = self.borde_por_etapa(etapa, stages) if etapa else "black"

            canvas.create_rectangle(
                x1, y1, x2, y2,
                width=2 if etapa and stages.get(etapa) not in ("", "—", None) else 1,
                fill=fill,
                outline=outline
            )
            canvas.create_text((x1+x2)//2, (y1+y2)//2, text=texto)

        def cable(x1, y1, x2, y2, dash=None):
            canvas.create_line(x1,y1,x2,y2,width=2,dash=dash)

        bloque(20, 80, 70, 110, "PC", "IF")
        bloque(120, 80, 205, 110, "Instruction\nMemory", "IF")

        bloque(260, 45, 295, 155, "IF/ID", "IF")
        bloque(355, 45, 450, 75, "Register\nFile", "ID")
        bloque(355, 125, 450, 155, "Sign Extend", "ID")

        bloque(520, 45, 555, 155, "ID/EX", "ID")
        bloque(625, 80, 700, 110, "ALU", "EX")
        bloque(625, 155, 715, 185, "PC+4/Branch", "EX")

        bloque(775, 45, 810, 155, "EX/\nMEM", "EX")
        bloque(875, 80, 965, 110, "Data\nMemory", "MEM")

        bloque(1035, 45, 1070, 155, "MEM/\nWB", "MEM")
        bloque(1130, 80, 1210, 110, "MUX\nResult", "WB")

        bloque(190, 175, 430, 205, "Hazard Unit", "ID")
        bloque(200, 5, 290, 35, "Control Unit", "ID")

        # Ruta principal
        cable(70, 95, 120, 95)
        cable(205, 95, 260, 95)

        cable(295, 70, 355, 60)
        cable(295, 140, 355, 140)

        cable(450, 60, 520, 60)
        cable(450, 140, 520, 140)

        cable(555, 95, 625, 95)

        cable(700, 95, 775, 95)
        cable(810, 95, 875, 95)
        cable(965, 95, 1035, 95)
        cable(1070, 95, 1130, 95)

        # ALU hacia PC+4/Branch
        canvas.create_line(662, 110, 662, 155, width=1)

        # PC+4/Branch hacia PC por abajo
        canvas.create_line(670, 170, 45, 170, width=1)
        canvas.create_line(45, 170, 45, 110, width=1)

        # Camino superior de writeback / PC update
        canvas.create_line(1210, 95, 1240, 95, width=1)
        canvas.create_line(1240, 95, 1240, 25, width=1)
        canvas.create_line(1240, 25, 45, 25, width=1)
        canvas.create_line(45, 25, 45, 80, width=1)

        # MEM/WB hacia MUX Result
        cable(1070, 95, 1130, 95)

        # Forward visual desde MEM/WB hacia EX/MEM
        canvas.create_line(1052, 45, 1052, 30, width=1)
        canvas.create_line(1052, 30, 792, 30, width=1)
        canvas.create_line(792, 30, 792, 45, width=1)

        # Control Unit punteado
        canvas.create_line(290, 20, 1052, 20, width=1, dash=(3, 3))
        canvas.create_line(1052, 20, 1052, 45, width=1, dash=(3, 3))

        canvas.create_line(290, 25, 792, 25, width=1, dash=(3, 3))
        canvas.create_line(792, 25, 792, 45, width=1, dash=(3, 3))

        canvas.create_line(290, 30, 537, 30, width=1, dash=(3, 3))
        canvas.create_line(537, 30, 537, 45, width=1, dash=(3, 3))

        # Control Unit hacia Register File
        canvas.create_line(245, 35, 245, 60, width=1, dash=(3, 3))
        canvas.create_line(245, 60, 355, 60, width=1, dash=(3, 3))

        # Hazard Unit conexiones
        canvas.create_line(278, 155, 278, 175, width=1)
        canvas.create_line(370, 175, 370, 155, width=1)

        canvas.create_line(430, 190, 535, 190, width=1)
        canvas.create_line(535, 190, 535, 155, width=1)

        canvas.create_line(190, 190, 45, 190, width=1)
        canvas.create_line(45, 190, 45, 110, width=1)

        # Hazard Unit hacia Control Unit
        canvas.create_line(230, 175, 230, 35, width=1, dash=(3, 3))
        canvas.create_line(230, 35, 245, 35, width=1  , dash=(3, 3))

        return canvas
    
    def dibujar_datapath_segmentado_forwarding(self, frame, estado_proc=None):
        stages = estado_proc["pipeline_stages"] if estado_proc else {}
        canvas = tk.Canvas(frame, bg="white", height=210)

        def bloque(x1, y1, x2, y2, texto, etapa=None):
            fill = self.color_por_etapa(etapa, stages) if etapa else "white"
            outline = self.borde_por_etapa(etapa, stages) if etapa else "black"

            canvas.create_rectangle(
                x1, y1, x2, y2,
                width=2 if etapa and stages.get(etapa) not in ("", "—", None) else 1,
                fill=fill,
                outline=outline
            )
            canvas.create_text((x1+x2)//2, (y1+y2)//2, text=texto)

        def cable(x1, y1, x2, y2, dash=None):
            canvas.create_line(x1,y1,x2,y2,width=2,dash=dash)

        bloque(20, 80, 70, 110, "PC", "IF")
        bloque(120, 80, 205, 110, "Instruction\nMemory", "IF")

        bloque(260, 45, 295, 155, "IF/ID", "IF")
        bloque(355, 45, 450, 75, "Register\nFile", "ID")
        bloque(355, 125, 450, 155, "Sign Extend", "ID")

        bloque(520, 45, 555, 155, "ID/EX", "ID")

        bloque(635, 80, 710, 110, "ALU", "EX")
        bloque(635, 155, 725, 185, "PC+4/Branch", "EX")

        bloque(785, 45, 820, 155, "EX/\nMEM", "EX")
        bloque(885, 80, 975, 110, "Data\nMemory", "MEM")

        bloque(1045, 45, 1080, 155, "MEM/\nWB", "MEM")
        bloque(1140, 80, 1220, 110, "MUX\nResult", "WB")

        bloque(190, 175, 430, 205, "Hazard Unit", "ID")
        bloque(200, 5, 290, 35, "Control Unit", "ID")

        # Ruta principal
        cable(70, 95, 120, 95)
        cable(205, 95, 260, 95)

        cable(295, 70, 355, 60)
        cable(295, 140, 355, 140)

        cable(450, 60, 520, 60)
        cable(450, 140, 520, 140)

        cable(555, 95, 635, 95)

        cable(710, 95, 785, 95)
        cable(820, 95, 885, 95)
        cable(975, 95, 1045, 95)
        cable(1080, 95, 1140, 95)

        # ALU -> PC+4/Branch
        canvas.create_line(672, 110, 672, 155, width=1)

        # PC+4/Branch -> PC
        canvas.create_line(680, 170, 45, 170, width=1)
        canvas.create_line(45, 170, 45, 110, width=1)

        # Writeback superior
        canvas.create_line(1220, 95, 1245, 95, width=1)
        canvas.create_line(1245, 95, 1245, 25, width=1)
        canvas.create_line(1245, 25, 45, 25, width=1)
        canvas.create_line(45, 25, 45, 80, width=1)

        # Forwarding EX/MEM -> ALU entrada superior
        canvas.create_line(802, 45, 802, 35, width=1)
        canvas.create_line(802, 35, 670, 35, width=1)
        canvas.create_line(670, 35, 670, 80, width=1)

        # Forwarding MEM/WB -> ALU entrada inferior
        canvas.create_line(1062, 155, 1062, 195, width=1)
        canvas.create_line(1062, 195, 695, 195, width=1)
        canvas.create_line(695, 195, 695, 110, width=1)

        # Forwarding MEM/WB -> EX/MEM
        canvas.create_line(1062, 45, 1062, 35, width=1)
        canvas.create_line(1062, 35, 802, 35, width=1)
        canvas.create_line(802, 35, 802, 45, width=1)

        # MUX Result -> Register File
        canvas.create_line(1180, 110, 1180, 195, width=1)
        canvas.create_line(1180, 195, 402, 195, width=1)
        canvas.create_line(402, 195, 402, 75, width=1)

        # Hazard Unit conexiones
        canvas.create_line(278, 155, 278, 175, width=1)
        canvas.create_line(370, 175, 370, 155, width=1)

        canvas.create_line(430, 190, 538, 190, width=1)
        canvas.create_line(538, 190, 538, 155, width=1)

        canvas.create_line(190, 190, 45, 190, width=1)
        canvas.create_line(45, 190, 45, 110, width=1)

        # Hazard Unit -> ALU/Forwarding
        canvas.create_line(430, 185, 650, 185, width=1)
        canvas.create_line(650, 185, 650, 110, width=1)

        canvas.create_line(430, 200, 1080, 200, width=1)
        canvas.create_line(1080, 200, 1080, 155, width=1)

        # Control Unit punteado
        canvas.create_line(290, 20, 1062, 20, width=1, dash=(3, 3))
        canvas.create_line(1062, 20, 1062, 45, width=1, dash=(3, 3))

        canvas.create_line(290, 25, 802, 25, width=1, dash=(3, 3))
        canvas.create_line(802, 25, 802, 45, width=1, dash=(3, 3))

        canvas.create_line(290, 30, 537, 30, width=1, dash=(3, 3))
        canvas.create_line(537, 30, 537, 45, width=1, dash=(3, 3))

        canvas.create_line(245, 35, 245, 60, width=1, dash=(3, 3))
        canvas.create_line(245, 60, 355, 60, width=1, dash=(3, 3))

        # Hazard -> Control Unit
        canvas.create_line(230, 175, 230, 35, width=1, dash=(3, 3))
        canvas.create_line(230, 35, 245, 35, width=1, dash=(3, 3))

        return canvas

    def tabla_pipeline(self, parent):
        tabla = ttk.Treeview(
            parent,
            columns=("PC", "CICLO", "TIEMPO", "IF", "ID", "EX", "MEM", "WB"),
            show="headings",
            height=1
        )

        columnas = ["PC", "CICLO", "TIEMPO", "IF", "ID", "EX", "MEM", "WB"]

        style = ttk.Style()

        style.configure("IF.Treeview.Heading", foreground="#1a6bb5")
        style.configure("ID.Treeview.Heading", foreground="#6f42c1")
        style.configure("EX.Treeview.Heading", foreground="#c97a00")
        style.configure("MEM.Treeview.Heading", foreground="#b8860b")
        style.configure("WB.Treeview.Heading", foreground="#2a7a3b")

        for col in columnas:

            tabla.heading(col, text=col)

            tabla.column(col, width=110, anchor="center")

        tabla.heading("IF", text="IF (azul)")
        tabla.heading("ID", text="ID (morado)")
        tabla.heading("EX", text="EX (naranja)")
        tabla.heading("MEM", text="MEM (amarillo)")
        tabla.heading("WB", text="WB (verde)")

        tabla.grid(row=0, column=0, sticky="ew")

        tabla.insert("", "end", iid="estado", values=("", "", "", "", "", "", "", ""))

        return tabla

    def frame_resultados(self, parent):
        frame = ttk.LabelFrame(parent, text="Resultados", padding=5)
        frame.grid(row=2, column=0, sticky="ew", pady=5)

        tabla = ttk.Treeview(
            frame,
            columns=("ejec", "c1", "cpi1", "t1", "c2", "cpi2", "t2"),
            show="headings",
            height=5
        )

        headers = {
            "ejec": "Ejecución",
            "c1": "Ciclos P1",
            "cpi1": "CPI P1",
            "t1": "Tiempo P1",
            "c2": "Ciclos P2",
            "cpi2": "CPI P2",
            "t2": "Tiempo P2",
        }

        for col, txt in headers.items():
            tabla.heading(col, text=txt)
            tabla.column(col, width=120, anchor="center")

        tabla.pack(fill="x")

        self.tabla_resultados = tabla

    def obtener_procesadores_seleccionados(self):
        return [op for op, var in self.cpu_vars.items() if var.get()]


    def crear_manager(self):
        seleccionados = self.obtener_procesadores_seleccionados()

        if len(seleccionados) != 2:
            messagebox.showwarning(
                "Selección inválida",
                "Debe seleccionar exactamente 2 procesadores."
            )
            return False

        codigo = self.consola.get("1.0", "end").strip()

        if not codigo:
            messagebox.showwarning(
                "Código vacío",
                "Debe escribir o cargar instrucciones RISC-V en la consola."
            )
            return False

        machine_code = MiniAssembler.assemble_program(codigo)

        if not machine_code or all(x == 0 for x in machine_code):
            messagebox.showerror(
                "Error",
                "No se pudo ensamblar el programa."
            )
            return False

        self.manager = SimulationManager(
            self.proc_map[seleccionados[0]],
            self.proc_map[seleccionados[1]]
        )

        self.manager.load_assembly(machine_code)
        self.actualizar_datapaths()
        self.actualizar_gui()

        return True


    def run(self):
        modo = self.modo_var.get()

        if self.manager is None or self.manager.is_finished():
            if not self.crear_manager():
                return

        if modo == "Paso a Paso":
            self.step()

        elif modo == "Automática":
            self.run_automatico()

        elif modo == "Completa":
            self.run_completo()

        elif modo == "Detectar Hazard":
            self.run_hazard()


    def step(self):
        if not self.manager:
            return

        if self.manager.is_finished():
            self.registrar_ejecucion()
            return

        self.manager.step()
        self.actualizar_gui()

        if self.manager.is_finished():
            self.registrar_ejecucion()


    def run_automatico(self):
        if not self.manager:
            return

        if self.manager.is_finished():
            self.registrar_ejecucion()
            return

        self.manager.step()
        self.actualizar_gui()

        delay = int(self.delay_ms.get())
        self.after_id = self.after(delay, self.run_automatico)


    def run_completo(self):
        if not self.manager:
            return

        while not self.manager.is_finished():
            self.manager.step()

        self.actualizar_gui()
        self.registrar_ejecucion()


    def run_hazard(self):
        if not self.manager:
            return

        while not self.manager.is_finished():
            self.manager.step()
            estado = self.manager.get_full_state()

            p1 = estado["processor_1"]["pipeline_stages"]
            p2 = estado["processor_2"]["pipeline_stages"]

            if any(v == "burbuja" for v in p1.values()) or any(v == "burbuja" for v in p2.values()):
                self.actualizar_gui()
                return

        self.actualizar_gui()
        self.registrar_ejecucion()


    def actualizar_gui(self):
        if not self.manager:
            return

        estado = self.manager.get_full_state()

        p1 = estado["processor_1"]
        p2 = estado["processor_2"]

        self.actualizar_tabla_pipeline(self.tabla_pipeline_p1, p1)
        self.actualizar_tabla_pipeline(self.tabla_pipeline_p2, p2)

        self.actualizar_tablas_laterales()
        self.actualizar_datapaths()


    def actualizar_tablas_laterales(self):
        if not self.manager:
            return

        estado = self.manager.get_full_state()

        proc_key = "processor_1" if self.procesador_actual.get() == "P1" else "processor_2"
        mem_key = "processor_1" if self.memoria_actual.get() == "P1" else "processor_2"

        proc_state = estado[proc_key]
        mem_state = estado[mem_key]

        # Registros
        self.tabla_registros.delete(*self.tabla_registros.get_children())

        for i, valor in enumerate(proc_state["registers"]):
            self.tabla_registros.insert(
                "",
                "end",
                values=(f"x{i}", valor)
            )

        # Memoria
        self.tabla_memoria.delete(*self.tabla_memoria.get_children())

        memoria = mem_state["memory_vector"]

        for direccion, valor in memoria.items():
            self.tabla_memoria.insert(
                "",
                "end",
                text=direccion,
                values=(valor,)
            )

    def actualizar_tabla_pipeline(self, tabla, estado_proc):
        stages = estado_proc["pipeline_stages"]

        valores = (
            estado_proc["pc"],
            estado_proc["cycle"],
            estado_proc["elapsed_time_ms"],
            stages.get("IF", "—"),
            stages.get("ID", "—"),
            stages.get("EX", "—"),
            stages.get("MEM", "—"),
            stages.get("WB", "—"),
        )

        tabla.item("estado", values=valores)

    def registrar_ejecucion(self):
        if not self.manager:
            return

        estado = self.manager.get_full_state()
        p1 = estado["processor_1"]
        p2 = estado["processor_2"]

        fila = {
            "p1_ciclos": p1["cycle"],
            "p1_cpi": p1["cycle"] / p1["stats"]["instructions"] if p1["stats"]["instructions"] else 0,
            "p1_tiempo": p1["elapsed_time_ms"],
            "p2_ciclos": p2["cycle"],
            "p2_cpi": p2["cycle"] / p2["stats"]["instructions"] if p2["stats"]["instructions"] else 0,
            "p2_tiempo": p2["elapsed_time_ms"],
        }

        self.historial.append(fila)
        self.historial = self.historial[-10:]

        self.tabla_resultados.delete(*self.tabla_resultados.get_children())

        for i, h in enumerate(self.historial, start=1):
            self.tabla_resultados.insert(
                "",
                "end",
                values=(
                    i,
                    h["p1_ciclos"],
                    f'{h["p1_cpi"]:.2f}',
                    h["p1_tiempo"],
                    h["p2_ciclos"],
                    f'{h["p2_cpi"]:.2f}',
                    h["p2_tiempo"],
                )
            )
    
    def reset_simulacion(self):

        # Eliminar manager actual
        self.manager = None

        # Limpiar tablas pipeline
        vacio = ("", "", "", "", "", "", "", "")

        self.tabla_pipeline_p1.item("estado", values=vacio)
        self.tabla_pipeline_p2.item("estado", values=vacio)

        # Limpiar registros
        for item in self.tabla_registros.get_children():
            self.tabla_registros.delete(item)

        # Limpiar memoria
        for item in self.tabla_memoria.get_children():
            self.tabla_memoria.delete(item)

        # Limpiar datapaths
        for widget in self.area_p1.winfo_children():
            widget.destroy()

        for widget in self.area_p2.winfo_children():
            widget.destroy()

        # Reiniciar flags
        self._execution_recorded = False

        print("Simulación reiniciada")

    def actualizar_titulos_procesadores(self):

        nombre1 = "Sin seleccionar"
        nombre2 = "Sin seleccionar"

        if self.proc1_tipo:
            nombre1 = self.proc1_tipo

        if self.proc2_tipo:
            nombre2 = self.proc2_tipo

        self.frame_proc1.config(
            text=f"Procesador 1 — {nombre1}"
        )

        self.frame_proc2.config(
            text=f"Procesador 2 — {nombre2}"
        )
    
    def color_por_etapa(self, etapa, stages):
        valor = stages.get(etapa, "")

        if valor == "burbuja":
            return "#f8d7da"  # rojo claro

        if valor and valor != "—":
            colores = {
                "IF": "#d9ecff",
                "ID": "#e8ddff",
                "EX": "#ffe0b2",
                "MEM": "#fff3cd",
                "WB": "#d4edda",
            }
            return colores.get(etapa, "#ffffff")

        return "#ffffff"


    def borde_por_etapa(self, etapa, stages):
        valor = stages.get(etapa, "")

        if valor == "burbuja":
            return "#cc3333"

        if valor and valor != "—":
            bordes = {
                "IF": "#1a6bb5",
                "ID": "#6f42c1",
                "EX": "#c97a00",
                "MEM": "#b8860b",
                "WB": "#2a7a3b",
            }
            return bordes.get(etapa, "#000000")

        return "#000000"