from core.processors import PipelinedStall, PipelinedForwarding, Unicycle, Multicycle
from assembler import MiniAssembler
from simulation_manager import SimulationManager
import time

# GUI recoge el texto de instrucciones ensamblador y el tiempo de ejecución (Valores quemados aquí)
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

VELOCIDAD_GUI_MS = 500 # Milisegundos por ciclo simulado (ajustable para acelerar o ralentizar la simulación)
VELOCIDAD_GUI_SEG = VELOCIDAD_GUI_MS / 1000  # Segundos por ciclo simulado

def main():
    # Ensamblar código
    machine_code = MiniAssembler.assemble_program(codigo_asm)
    
    # Inicializar el Gestor (El usuario puede elegir qué procesadores comparar)
    manager = SimulationManager(Unicycle, PipelinedForwarding)
    manager.load_assembly(machine_code)
    
    print("Iniciando Simulación...\n")
    
    while not manager.is_finished():
        manager.step()
        estado = manager.get_full_state()
        
        p1 = estado["processor_1"]
        p2 = estado["processor_2"]
        
        print(f"--- CICLO {p1['cycle']} (P1) | CICLO {p2['cycle']} (P2) ---")
        
        # PC formateado en Hexadecimal automáticamente
        print(f"[{p1['name']}] Tiempo: {p1['elapsed_time_ms']}ps | PC: {p1['pc']} | Pipeline: {p1['pipeline_stages']}")
        print(f"[{p2['name']}] Tiempo: {p2['elapsed_time_ms']}ps | PC: {p2['pc']} | Pipeline: {p2['pipeline_stages']}")
        
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

        # Simular el tiempo de cada ciclo para que la GUI no se actualice instantáneamente
        time.sleep(VELOCIDAD_GUI_SEG)

    # Mostrar estado final
    final = manager.get_full_state()
    print("=== SIMULACIÓN TERMINADA ===")
    print(f"Memoria P1: {final['processor_1']['memory_vector']}")
    print(f"Memoria P2: {final['processor_2']['memory_vector']}")

if __name__ == "__main__":
    main()