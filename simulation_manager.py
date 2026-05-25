"""
simulation_manager.py: Gestor de simulación paralela para la GUI.
"""
from typing import Type, Dict, Any, List
import time
from core.processor_base import ProcessorBase
import struct

class SimulationManager:
    def __init__(self, proc_class_1: Type[ProcessorBase], proc_class_2: Type[ProcessorBase], cycle_time_ms: int = 500):
        """
        Inicializa el gestor con las dos clases de procesadores seleccionadas.
        cycle_time_ms define el tiempo que representa cada ciclo para el cálculo del 'Tiempo desde inicio'. (Se debe cambiar)
        """
        self.p1 = proc_class_1()
        self.p2 = proc_class_2()
        self.cycle_time_ms = cycle_time_ms
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

    def run_auto(self, delay_sec: float = 0.5, callback=None):
        """Ejecuta la simulación automáticamente hasta que ambos terminen, con un retardo real."""
        while not self.is_finished():
            self.step()
            if callback:
                # callback puede ser usado en GUI para actualizar la pantalla
                callback(self.get_full_state())
            time.sleep(delay_sec)

    def _get_active_memory(self, proc: ProcessorBase) -> Dict[int, int]:
        """
        Extrae la memoria desde la celda 0 hasta la última celda que no sea 0
        Retorna un diccionario {direccion: valor_entero}
        """
        mem_dict = {}
        last_active_addr = 0
        
        # Encontrar la última dirección con datos
        for addr in range(0, len(proc.memory), 4):
            val = struct.unpack_from("<I", proc.memory, addr)[0]
            if val != 0:
                last_active_addr = addr

        # Volcar datos desde 0 hasta el último activo
        for addr in range(0, last_active_addr + 4, 4):
            mem_dict[addr] = struct.unpack_from("<I", proc.memory, addr)[0]
            
        return mem_dict

    def _extract_proc_state(self, proc: ProcessorBase) -> Dict[str, Any]:
        """Empaqueta todo el estado requerido de un procesador en un diccionario."""
        return {
            "name": proc.name,
            "halted": proc.halted,
            "cycle": proc.stats.cycles,
            "elapsed_time_ms": proc.stats.cycles * self.cycle_time_ms,
            "pc": proc.pc,
            "registers": list(proc.regs),
            "pipeline_stages": proc.get_stage_labels(),
            "memory": self._get_active_memory(proc),
            "stats": {
                "instructions": proc.stats.instructions,
                "stalls": getattr(proc.stats, 'stalls', 0),
                "forwards": getattr(proc.stats, 'forwards', 0)
            }
        }

    def get_full_state(self) -> Dict[str, Any]:
        """Devuelve el estado de ambos procesadores listos para ser dibujados en la GUI."""
        return {
            "processor_1": self._extract_proc_state(self.p1),
            "processor_2": self._extract_proc_state(self.p2),
        }