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
                command=self.limitar_seleccion
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
        #self.dibujo_cpu(frame)

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

    def dibujo_cpu(self, parent):
        canvas = tk.Canvas(parent, height=210, bg="white")
        canvas.grid(row=1, column=0, sticky="nsew", pady=5)

        bloques = [
            ("PC", 40, 80),
            ("Instruction\nMemory", 150, 80),
            ("IF/ID", 280, 60),
            ("Register File", 390, 60),
            ("ID/EX", 520, 60),
            ("ALU", 650, 80),
            ("EX/MEM", 780, 60),
            ("Data\nMemory", 900, 80),
            ("MEM/WB", 1030, 60),
            ("MUX Result", 1150, 80),
        ]

        for texto, x, y in bloques:
            canvas.create_rectangle(x, y, x + 80, y + 40, outline="gray")
            canvas.create_text(x + 40, y + 20, text=texto, font=("Arial", 8))

        for i in range(len(bloques) - 1):
            x1 = bloques[i][1] + 80
            y1 = bloques[i][2] + 20
            x2 = bloques[i + 1][1]
            y2 = bloques[i + 1][2] + 20
            canvas.create_line(x1, y1, x2, y2, arrow="last")

        canvas.create_rectangle(430, 140, 520, 170, outline="gray")
        canvas.create_text(475, 155, text="Sign Extend", font=("Arial", 8))

        canvas.create_rectangle(610, 145, 710, 175, outline="gray")
        canvas.create_text(660, 160, text="PC+4/Branch", font=("Arial", 8))

        canvas.create_rectangle(260, 175, 520, 200, outline="gray")
        canvas.create_text(390, 187, text="Hazard Unit", font=("Arial", 8))

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