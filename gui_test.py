from core.processors import PipelinedStall, PipelinedForwarding
from assembler import MiniAssembler
from simulation_manager import SimulationManager

# 1. GUI recoge el texto de instrucciones ensamblador (Ejemplo hardcodeado aquí)
codigo_asm = """
addi x1, x0, 10
addi x2, x0, 20
add  x3, x1, x2
sub  x4, x3, x1
and  x5, x3, x2
or   x6, x1, x2
sw   x6, 0(x0)
lw   x7, 0(x0)
beq  x7, x6, +8
jal  x8, +8
addi x9, x0, 99
"""

def main():
    # 2. Ensamblar código
    machine_code = MiniAssembler.assemble_program(codigo_asm)
    
    # 3. Inicializar el Gestor (El usuario eligió Pipelined Stall vs Forwarding, 500ms por ciclo simulado)
    manager = SimulationManager(PipelinedStall, PipelinedForwarding, cycle_time_ms=500)
    manager.load_assembly(machine_code)
    
    print("Iniciando Simulación...\n")
    
    # 4. Bucle principal de la GUI (Step by step)
    while not manager.is_finished():
        manager.step()
        estado = manager.get_full_state()
        
        # === SIMULACIÓN DE LO QUE HARÍA LA GUI ===
        p1 = estado["processor_1"]
        p2 = estado["processor_2"]
        
        print(f"--- CICLO {p1['cycle']} (P1) | CICLO {p2['cycle']} (P2) ---")
        
        # Mostrar tiempos y PC
        print(f"[{p1['name']}] Tiempo: {p1['elapsed_time_ms']}ms | PC: {p1['pc']:04} | Pipeline: {p1['pipeline_stages']}")
        print(f"[{p2['name']}] Tiempo: {p2['elapsed_time_ms']}ms | PC: {p2['pc']:04} | Pipeline: {p2['pipeline_stages']}")
        
        # Aquí la GUI actualizaría las tablas de registros y memoria...
        
        # Pausa para poder leer la consola (La GUI usaría un botón "Next")
        print("")

    # Mostrar estado final
    final = manager.get_full_state()
    print("=== SIMULACIÓN TERMINADA ===")
    print(f"Memoria P1: {final['processor_1']['memory']}")
    print(f"Memoria P2: {final['processor_2']['memory']}")

if __name__ == "__main__":
    main()