"""
main.py: Pruebas rápidas para ProcessorBase y derivados.
"""
from core.processors_base import ProcessorBase, DecodedInstr

class DummyProcessor(ProcessorBase):
    """Implementación mínima para pruebas de ProcessorBase."""
    def step(self):
        self.halted = True  # No hace nada, solo para test
    def get_stage_labels(self):
        return {k: k for k in self.pipeline_state}

def main():
    print("== Prueba rápida ProcessorBase ==")
    proc = DummyProcessor()
    print(f"PC inicial: {proc.pc}")
    print(f"Regs: {proc.regs}")
    print(f"Memoria: {len(proc.memory)} bytes")
    print(f"Stats: {proc.stats}")
    # Prueba de registro
    proc.reg_write(1, 123)
    print(f"Reg 1 tras escribir 123: {proc.reg_read(1)}")
    # Prueba de memoria
    proc.mem_write_word(0, 0xDEADBEEF)
    print(f"Mem[0]: {hex(proc.mem_read_word(0))}")
    # Prueba de decodificación
    instr = DecodedInstr.decode(0x00C58533)  # Ejemplo: add x10, x11, x12
    print(f"Decodificado: {instr}")
    print(f"Mnemonic: {instr.mnemonic}")
    # Prueba de reset
    proc.reset()
    print(f"PC tras reset: {proc.pc}")
    print(f"Regs tras reset: {proc.regs}")

if __name__ == "__main__":
    main()
