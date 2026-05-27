"""
simulation_manager.py: Gestor de simulación paralela para la GUI.
"""
from typing import Type, Dict, Any, List
import time
from core.processor_base import ProcessorBase
import struct

class SimulationManager:
    def __init__(self, proc_class_1: Type[ProcessorBase], proc_class_2: Type[ProcessorBase]):
        """
        Inicializa el gestor con las dos clases de procesadores seleccionadas.
        cycle_time_ms define el tiempo que representa cada ciclo para el cálculo del 'Tiempo desde inicio'. (Se debe cambiar)
        """
        self.p1 = proc_class_1()
        self.p2 = proc_class_2()
        self.program_loaded = False

    def load_assembly(self, machine_code: List[int]):
        """Carga el código máquina en ambos procesadores."""
        self.p1.load_program(machine_code)
        self.p2.load_program(machine_code)
        self.program_loaded = True

    def is_finished(self) -> bool:
        """Devuelve True si ambos procesadores han hecho halt."""
        return self.p1.halted and self.p2.halted

    def step(self):
        """Avanza un ciclo de reloj para ambos procesadores si no han terminado."""
        if not self.p1.halted:
            self.p1.step()
        if not self.p2.halted:
            self.p2.step()

    def _get_memory_vector(self, proc: ProcessorBase) -> Dict[str, str]:
        """
        Genera el 'vector resultante' de memoria desde la dirección 0 
        hasta la última celda que haya sido utilizada (distinta de 0).
        """
        mem_vector = {}
        last_active_addr = 0
        
        # Escanear para encontrar cuál es la última celda ocupada
        for addr in range(0, len(proc.memory), 4):
            val = struct.unpack_from("<I", proc.memory, addr)[0]
            if val != 0:
                last_active_addr = addr

        # Construir el vector desde 0 hasta ese límite
        for addr in range(0, last_active_addr + 4, 4):
            val = struct.unpack_from("<I", proc.memory, addr)[0]
            addr_hex = f"0x{addr:08X}"
            val_hex = f"0x{val:08X}"
            mem_vector[addr_hex] = val_hex
            
        return mem_vector

    def _extract_proc_state(self, proc: ProcessorBase) -> Dict[str, Any]:
        """Empaqueta todo el estado del procesador para la GUI."""
        registers_hex = [f"0x{reg & 0xFFFF_FFFF:08X}" for reg in proc.regs]
        
        return {
            "name": proc.name,
            "halted": proc.halted,
            "cycle": proc.stats.cycles,
            "elapsed_time_ms": proc.stats.cycles * proc.cycle_time_ps,
            "pc": f"0x{proc.pc:08X}",
            "registers": registers_hex,
            "pipeline_stages": proc.get_stage_labels(),
            "memory_vector": self._get_memory_vector(proc),
            "stats": {
                "instructions": proc.stats.instructions,
                "stalls": getattr(proc.stats, 'stalls', 0),
                "forwards": getattr(proc.stats, 'forwards', 0)
            }
        }

    def get_full_state(self) -> Dict[str, Any]:
        """Devuelve el estado de ambos procesadores listo para la interfaz o terminal."""
        return {
            "processor_1": self._extract_proc_state(self.p1),
            "processor_2": self._extract_proc_state(self.p2),
        }