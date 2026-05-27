import tkinter as tk
from tkinter import ttk


class SimuladorGUI(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Simulador de Procesadores")
        self.state("zoomed")
        self.configure(bg="#f2f2f2")

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

        combo = ttk.Combobox(frame, values=["Paso a Paso", "Automática", "Completa", "Detectar Hazard"], width=18)
        combo.set("Paso a Paso")
        combo.grid(row=0, column=0, padx=4)

        ttk.Button(frame, text="RUN").grid(row=0, column=1, padx=4)

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

        text = tk.Text(frame, width=28, height=7)
        text.pack(fill="both")

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

        if len(activos) >= 1:
            self.dibujar_por_tipo(self.area_p1, activos[0])

        if len(activos) >= 2:
            self.dibujar_por_tipo(self.area_p2, activos[1])
    
    def dibujar_por_tipo(self, frame, tipo):

        if tipo == "Uniciclo":
            canvas = self.dibujar_datapath_uniciclo(frame)
        elif tipo == "Multiciclo":
            canvas = self.dibujar_datapath_multiciclo(frame)
        elif tipo == "Segmentado (Stalls)":
            canvas = self.dibujar_datapath_segmentado_stalls(frame)
        elif tipo == "Segmentado (Forwarding)":
            canvas = self.dibujar_datapath_segmentado_forwarding(frame)
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
            value="P1"
        ).pack(side="left", expand=True)

        ttk.Radiobutton(
            barra,
            text="P2",
            variable=self.procesador_actual,
            value="P2"
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
            value="P1"
        ).pack(side="left", expand=True)

        ttk.Radiobutton(
            barra,
            text="P2",
            variable=self.memoria_actual,
            value="P2"
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
        frame.grid(row=fila, column=0, sticky="nsew", pady=5)

        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(1, weight=1)

        self.tabla_pipeline(frame)

        area = ttk.Frame(frame, height=220)
        area.grid(row=1, column=0, sticky="nsew")
        area.grid_propagate(False)

        area.columnconfigure(0, weight=1)
        area.rowconfigure(0, weight=1)

        if titulo == "Procesador 1":
            self.area_p1 = area
        else:
            self.area_p2 = area
    
    def dibujar_datapath_uniciclo(self, frame):

        canvas = tk.Canvas(frame, bg="white", height=230)

        def bloque(x1, y1, x2, y2, texto):
            canvas.create_rectangle(x1, y1, x2, y2, width=1)
            canvas.create_text((x1+x2)//2, (y1+y2)//2, text=texto)

        def cable(x1, y1, x2, y2, arrow="last", dash=None):
            canvas.create_line(x1, y1, x2, y2, width=1, arrow=arrow, dash=dash)

        # Bloques
        bloque(20, 95, 120, 145, "PC")
        bloque(190, 95, 310, 145, "Instruction\nMemory")
        bloque(390, 95, 510, 145, "Register\nFile")
        bloque(390, 175, 510, 225, "Immediate\nGenerator")
        bloque(590, 95, 710, 145, "ALU")
        bloque(790, 95, 920, 145, "Data Memory")
        bloque(790, 20, 920, 70, "WB MUX")
        bloque(1010, 95, 1130, 145, "PC + 4 /\nBranch")
        bloque(290, 10, 410, 60, "Control Unit")

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
    
    def dibujar_datapath_multiciclo(self, frame):

        canvas = tk.Canvas(frame, bg="white", height=210)

        def bloque(x1, y1, x2, y2, texto):
            canvas.create_rectangle(x1, y1, x2, y2, width=1)
            canvas.create_text((x1+x2)//2, (y1+y2)//2, text=texto, font=("Arial", 8))

        def cable(x1, y1, x2, y2, dash=None):
            canvas.create_line(x1, y1, x2, y2, width=1, arrow="last", dash=dash)

        # Bloques
        bloque(20, 95, 70, 125, "PC")
        bloque(100, 95, 165, 125, "MUX\nPC")
        bloque(200, 90, 275, 130, "Unified\nMemory")

        bloque(330, 75, 385, 105, "IR")
        bloque(330, 130, 385, 160, "MDR")

        bloque(455, 105, 545, 140, "Register\nFile")
        bloque(455, 35, 545, 65, "Sign\nExtend")

        bloque(610, 65, 670, 95, "Reg B")
        bloque(610, 135, 670, 165, "Reg A")

        bloque(725, 55, 795, 85, "MUX\nSrcB")
        bloque(725, 135, 795, 165, "MUX\nSrcA")

        bloque(850, 95, 910, 125, "ALU")
        bloque(960, 95, 1030, 125, "ALU\nOut")
        bloque(1080, 95, 1160, 125, "MUX\nResult")

        bloque(610, 5, 710, 35, "Control Unit")

        # Ruta principal
        cable(70, 110, 100, 110)
        cable(165, 110, 200, 110)

        canvas.create_line(275, 110, 305, 110)
        canvas.create_line(305, 110, 305, 90)
        cable(305, 90, 330, 90)

        canvas.create_line(305, 110, 305, 145)
        cable(305, 145, 330, 145)

        # IR hacia Register File
        canvas.create_line(385, 90, 420, 90)
        canvas.create_line(420, 90, 420, 122)
        cable(420, 122, 455, 122)

        # IR hacia Sign Extend
        canvas.create_line(385, 90, 420, 90)
        canvas.create_line(420, 90, 420, 50)
        cable(420, 50, 455, 50)

        # MDR hacia Register File
        canvas.create_line(385, 145, 420, 145)
        canvas.create_line(420, 145, 420, 132)
        cable(420, 132, 455, 132)

        # Register File hacia Reg A / Reg B
        canvas.create_line(545, 122, 580, 122)
        canvas.create_line(580, 122, 580, 80)
        cable(580, 80, 610, 80)

        canvas.create_line(580, 122, 580, 150)
        cable(580, 150, 610, 150)

        # Registros hacia MUX
        cable(670, 80, 725, 80)
        cable(670, 150, 725, 150)

        # Sign Extend hacia MUX SrcB
        canvas.create_line(545, 50, 700, 50)
        canvas.create_line(700, 50, 700, 70)
        cable(700, 70, 725, 70)

        # MUX hacia ALU
        canvas.create_line(795, 70, 825, 70)
        canvas.create_line(825, 70, 825, 103)
        cable(825, 103, 850, 103)

        canvas.create_line(795, 150, 825, 150)
        canvas.create_line(825, 150, 825, 117)
        cable(825, 117, 850, 117)

        # ALU -> ALU Out -> MUX Result
        cable(910, 110, 960, 110)
        cable(1030, 110, 1080, 110)

        # MUX Result -> MUX PC por arriba
        canvas.create_line(1160, 110, 1185, 110)
        canvas.create_line(1185, 110, 1185, 50)
        canvas.create_line(1185, 50, 132, 50)
        cable(132, 50, 132, 95)

        # MUX Result -> Register File por abajo
        canvas.create_line(1120, 125, 1120, 190)
        canvas.create_line(1120, 190, 500, 190)
        cable(500, 190, 500, 140)

        # PC -> MUX SrcA por abajo
        canvas.create_line(45, 125, 45, 200)
        canvas.create_line(45, 200, 760, 200)
        cable(760, 200, 760, 165)

        # ALU Out -> Unified Memory por abajo
        canvas.create_line(995, 125, 995, 205)
        canvas.create_line(995, 205, 238, 205)
        cable(238, 205, 238, 130)

        # Control Unit señales punteadas
        cable(650, 35, 760, 55, dash=(3, 3))
        cable(660, 35, 760, 135, dash=(3, 3))
        cable(710, 20, 880, 95, dash=(3, 3))
        cable(710, 15, 1120, 95, dash=(3, 3))
        cable(610, 20, 132, 95, dash=(3, 3))

        return canvas
        
    def dibujar_datapath_segmentado_stalls(self, frame):

        canvas = tk.Canvas(frame, bg="white", height=210)

        def bloque(x1, y1, x2, y2, texto):
            canvas.create_rectangle(x1, y1, x2, y2, width=1)
            canvas.create_text(
                (x1+x2)//2,
                (y1+y2)//2,
                text=texto,
                font=("Arial", 8)
            )

        def cable(x1, y1, x2, y2, dash=None):
            canvas.create_line(
                x1, y1, x2, y2,
                width=1,
                arrow="last",
                dash=dash
            )

        # Bloques principales
        bloque(20, 80, 70, 110, "PC")
        bloque(120, 80, 205, 110, "Instruction\nMemory")

        bloque(260, 45, 295, 155, "IF/ID")
        bloque(355, 45, 450, 75, "Register\nFile")
        bloque(355, 125, 450, 155, "Sign Extend")

        bloque(520, 45, 555, 155, "ID/EX")
        bloque(625, 80, 700, 110, "ALU")
        bloque(625, 155, 715, 185, "PC+4/Branch")

        bloque(775, 45, 810, 155, "EX/\nMEM")
        bloque(875, 80, 965, 110, "Data\nMemory")

        bloque(1035, 45, 1070, 155, "MEM/\nWB")
        bloque(1130, 80, 1210, 110, "MUX\nResult")

        bloque(190, 175, 430, 205, "Hazard Unit")
        bloque(200, 5, 290, 35, "Control Unit")

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
        canvas.create_line(662, 110, 662, 155, width=1, arrow="last")

        # PC+4/Branch hacia PC por abajo
        canvas.create_line(670, 170, 45, 170, width=1)
        canvas.create_line(45, 170, 45, 110, width=1, arrow="last")

        # Camino superior de writeback / PC update
        canvas.create_line(1210, 95, 1240, 95, width=1)
        canvas.create_line(1240, 95, 1240, 25, width=1)
        canvas.create_line(1240, 25, 45, 25, width=1)
        canvas.create_line(45, 25, 45, 80, width=1, arrow="last")

        # MEM/WB hacia MUX Result
        cable(1070, 95, 1130, 95)

        # Forward visual desde MEM/WB hacia EX/MEM
        canvas.create_line(1052, 45, 1052, 30, width=1)
        canvas.create_line(1052, 30, 792, 30, width=1)
        canvas.create_line(792, 30, 792, 45, width=1, arrow="last")

        # Control Unit punteado
        canvas.create_line(290, 20, 1052, 20, width=1, dash=(3, 3))
        canvas.create_line(1052, 20, 1052, 45, width=1, arrow="last", dash=(3, 3))

        canvas.create_line(290, 25, 792, 25, width=1, dash=(3, 3))
        canvas.create_line(792, 25, 792, 45, width=1, arrow="last", dash=(3, 3))

        canvas.create_line(290, 30, 537, 30, width=1, dash=(3, 3))
        canvas.create_line(537, 30, 537, 45, width=1, arrow="last", dash=(3, 3))

        # Control Unit hacia Register File
        canvas.create_line(245, 35, 245, 60, width=1, dash=(3, 3))
        canvas.create_line(245, 60, 355, 60, width=1, arrow="last", dash=(3, 3))

        # Hazard Unit conexiones
        canvas.create_line(278, 155, 278, 175, width=1, arrow="last")
        canvas.create_line(370, 175, 370, 155, width=1, arrow="last")

        canvas.create_line(430, 190, 535, 190, width=1)
        canvas.create_line(535, 190, 535, 155, width=1, arrow="last")

        canvas.create_line(190, 190, 45, 190, width=1)
        canvas.create_line(45, 190, 45, 110, width=1, arrow="last")

        # Hazard Unit hacia Control Unit
        canvas.create_line(230, 175, 230, 35, width=1, dash=(3, 3))
        canvas.create_line(230, 35, 245, 35, width=1, arrow="last", dash=(3, 3))

        return canvas
    
    def dibujar_datapath_segmentado_forwarding(self, frame):

        canvas = tk.Canvas(frame, bg="white", height=210)

        def bloque(x1, y1, x2, y2, texto):
            canvas.create_rectangle(x1, y1, x2, y2, width=1)
            canvas.create_text(
                (x1+x2)//2,
                (y1+y2)//2,
                text=texto,
            font=("Arial", 8)
            )

        def cable(x1, y1, x2, y2, dash=None):
            canvas.create_line(
                x1, y1, x2, y2,
                width=1,
                arrow="last",
                dash=dash
            )

        # Bloques
        bloque(20, 80, 70, 110, "PC")
        bloque(120, 80, 205, 110, "Instruction\nMemory")

        bloque(260, 45, 295, 155, "IF/ID")
        bloque(355, 45, 450, 75, "Register\nFile")
        bloque(355, 125, 450, 155, "Sign Extend")

        bloque(520, 45, 555, 155, "ID/EX")

        bloque(635, 80, 710, 110, "ALU")
        bloque(635, 155, 725, 185, "PC+4/Branch")

        bloque(785, 45, 820, 155, "EX/\nMEM")
        bloque(885, 80, 975, 110, "Data\nMemory")

        bloque(1045, 45, 1080, 155, "MEM/\nWB")
        bloque(1140, 80, 1220, 110, "MUX\nResult")

        bloque(190, 175, 430, 205, "Hazard Unit")
        bloque(200, 5, 290, 35, "Control Unit")

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
        canvas.create_line(672, 110, 672, 155, width=1, arrow="last")

        # PC+4/Branch -> PC
        canvas.create_line(680, 170, 45, 170, width=1)
        canvas.create_line(45, 170, 45, 110, width=1, arrow="last")

        # Writeback superior
        canvas.create_line(1220, 95, 1245, 95, width=1)
        canvas.create_line(1245, 95, 1245, 25, width=1)
        canvas.create_line(1245, 25, 45, 25, width=1)
        canvas.create_line(45, 25, 45, 80, width=1, arrow="last")

        # Forwarding EX/MEM -> ALU entrada superior
        canvas.create_line(802, 45, 802, 35, width=1)
        canvas.create_line(802, 35, 670, 35, width=1)
        canvas.create_line(670, 35, 670, 80, width=1, arrow="last")

        # Forwarding MEM/WB -> ALU entrada inferior
        canvas.create_line(1062, 155, 1062, 195, width=1)
        canvas.create_line(1062, 195, 695, 195, width=1)
        canvas.create_line(695, 195, 695, 110, width=1, arrow="last")

        # Forwarding MEM/WB -> EX/MEM
        canvas.create_line(1062, 45, 1062, 35, width=1)
        canvas.create_line(1062, 35, 802, 35, width=1)
        canvas.create_line(802, 35, 802, 45, width=1, arrow="last")

        # MUX Result -> Register File
        canvas.create_line(1180, 110, 1180, 195, width=1)
        canvas.create_line(1180, 195, 402, 195, width=1)
        canvas.create_line(402, 195, 402, 75, width=1, arrow="last")

        # Hazard Unit conexiones
        canvas.create_line(278, 155, 278, 175, width=1, arrow="last")
        canvas.create_line(370, 175, 370, 155, width=1, arrow="last")

        canvas.create_line(430, 190, 538, 190, width=1)
        canvas.create_line(538, 190, 538, 155, width=1, arrow="last")

        canvas.create_line(190, 190, 45, 190, width=1)
        canvas.create_line(45, 190, 45, 110, width=1, arrow="last")

        # Hazard Unit -> ALU/Forwarding
        canvas.create_line(430, 185, 650, 185, width=1)
        canvas.create_line(650, 185, 650, 110, width=1, arrow="last")

        canvas.create_line(430, 200, 1080, 200, width=1)
        canvas.create_line(1080, 200, 1080, 155, width=1, arrow="last")

        # Control Unit punteado
        canvas.create_line(290, 20, 1062, 20, width=1, dash=(3, 3))
        canvas.create_line(1062, 20, 1062, 45, width=1, arrow="last", dash=(3, 3))

        canvas.create_line(290, 25, 802, 25, width=1, dash=(3, 3))
        canvas.create_line(802, 25, 802, 45, width=1, arrow="last", dash=(3, 3))

        canvas.create_line(290, 30, 537, 30, width=1, dash=(3, 3))
        canvas.create_line(537, 30, 537, 45, width=1, arrow="last", dash=(3, 3))

        canvas.create_line(245, 35, 245, 60, width=1, dash=(3, 3))
        canvas.create_line(245, 60, 355, 60, width=1, arrow="last", dash=(3, 3))

        # Hazard -> Control Unit
        canvas.create_line(230, 175, 230, 35, width=1, dash=(3, 3))
        canvas.create_line(230, 35, 245, 35, width=1, arrow="last", dash=(3, 3))

        return canvas

    def tabla_pipeline(self, parent):
        tabla = ttk.Treeview(
            parent,
            columns=("PC", "CICLO", "TIEMPO", "IF", "ID", "EX", "MEM", "WB"),
            show="headings",
            height=1
        )

        columnas = ["PC", "CICLO", "TIEMPO", "IF", "ID", "EX", "MEM", "WB"]

        for col in columnas:
            tabla.heading(col, text=col)
            tabla.column(col, width=110, anchor="center")

        tabla.grid(row=0, column=0, sticky="ew")

    

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

        for i in range(1, 6):
            tabla.insert("", "end", values=(i, "Item", "Item", "Item", "Item", "Item", "Item"))

        tabla.pack(fill="x")