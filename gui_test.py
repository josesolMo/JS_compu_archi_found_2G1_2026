from core.processors import PipelinedStall, PipelinedForwarding, Unicycle, Multicycle
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
    manager = SimulationManager(Unicycle, PipelinedForwarding, cycle_time_ms=500)
    manager.load_assembly(machine_code)
    
    print("Iniciando Simulación...\n")
    
    while not manager.is_finished():
        manager.step()
        estado = manager.get_full_state()
        
        p1 = estado["processor_1"]
        p2 = estado["processor_2"]
        
        print(f"--- CICLO {p1['cycle']} (P1) | CICLO {p2['cycle']} (P2) ---")
        
        # PC formateado en Hexadecimal automáticamente
        print(f"[{p1['name']}] Tiempo: {p1['elapsed_time_ms']}ms | PC: {p1['pc']} | Pipeline: {p1['pipeline_stages']}")
        print(f"[{p2['name']}] Tiempo: {p2['elapsed_time_ms']}ms | PC: {p2['pc']} | Pipeline: {p2['pipeline_stages']}")
        
        # Mostrar los primeros 10 registros en hexadecimal para inspección
        print(f"[{p1['name']}] Regs (x1-x31): {[p1['registers'][i] for i in range(1, 32)]}")
        print(f"[{p2['name']}] Regs (x1-x31): {[p2['registers'][i] for i in range(1, 32)]}")
        print("-" * 60)
        
        # Mostrar vetor resultante de memoria (desde 0 hasta la última celda ocupada)
        print(f"[{p1['name']}] Vector de Memoria: {p1['memory_vector']}")
        print(f"[{p2['name']}] Vector de Memoria: {p2['memory_vector']}")
        print("-" * 60)

        # Descomentar para ir paso a paso presionando enter
        #input("Presione Enter para el siguiente ciclo...")

    # Mostrar estado final
    final = manager.get_full_state()
    print("=== SIMULACIÓN TERMINADA ===")
    print(f"Memoria P1: {final['processor_1']['memory_vector']}")
    print(f"Memoria P2: {final['processor_2']['memory_vector']}")

if __name__ == "__main__":
    main()