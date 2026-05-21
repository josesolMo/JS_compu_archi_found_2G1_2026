"""
main.py: Pruebas rápidas para ProcessorBase y derivados.
"""

from core.processor_base import ProcessorBase, DecodedInstr
from core.processors import Unicycle, Multicycle, PipelinedStall, PipelinedForwarding

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
    proc.reg_write(1, 123)
    print(f"Reg 1 tras escribir 123: {proc.reg_read(1)}")
    proc.mem_write_word(0, 0xDEADBEEF)
    print(f"Mem[0]: {hex(proc.mem_read_word(0))}")
    instr = DecodedInstr.decode(0x00C58533)  # add x10, x11, x12
    print(f"Decodificado: {instr}")
    print(f"Mnemonic: {instr.mnemonic}")
    proc.reset()
    print(f"PC tras reset: {proc.pc}")
    print(f"Regs tras reset: {proc.regs}")

    # Pruebas con Unicycle
    print("\n== Prueba Unicycle ==")
    u = Unicycle()
    # Programa: addi x1, x0, 42; addi x2, x1, 8; add x3, x1, x2
    prog = [
        0x02A00093,  # addi x1, x0, 42
        0x00808113,  # addi x2, x1, 8
        0x002081B3   # add x3, x1, x2
    ]
    u.load_program(prog)
    while not u.halted:
        u.step()
    print(f"x1: {u.reg_read(1)} (esperado 42)")
    print(f"x2: {u.reg_read(2)} (esperado 50)")
    print(f"x3: {u.reg_read(3)} (esperado 92)")
    print(f"Ciclos: {u.stats.cycles}, Instrucciones: {u.stats.instructions}")


    # Pruebas con Multicycle
    print("\n== Prueba Multicycle ==")
    m = Multicycle()
    m.load_program(prog)
    while not m.halted:
        m.step()
    print(f"x1: {m.reg_read(1)} (esperado 42)")
    print(f"x2: {m.reg_read(2)} (esperado 50)")
    print(f"x3: {m.reg_read(3)} (esperado 92)")
    print(f"Ciclos: {m.stats.cycles}, Instrucciones: {m.stats.instructions}")

    # Pruebas con PipelinedStall
    print("\n== Prueba PipelinedStall ==")
    ps = PipelinedStall()
    ps.load_program(prog)
    while not ps.halted:
        ps.step()
    print(f"x1: {ps.reg_read(1)} (esperado 42)")
    print(f"x2: {ps.reg_read(2)} (esperado 50)")
    print(f"x3: {ps.reg_read(3)} (esperado 92)")
    print(f"Ciclos: {ps.stats.cycles}, Instrucciones: {ps.stats.instructions}, Stalls: {ps.stats.stalls}")

    # Pruebas con PipelinedForwarding
    print("\n== Prueba PipelinedForwarding ==")
    pf = PipelinedForwarding()
    pf.load_program(prog)
    while not pf.halted:
        pf.step()
    print(f"x1: {pf.reg_read(1)} (esperado 42)")
    print(f"x2: {pf.reg_read(2)} (esperado 50)")
    print(f"x3: {pf.reg_read(3)} (esperado 92)")
    print(f"Ciclos: {pf.stats.cycles}, Instrucciones: {pf.stats.instructions}, Forwards: {pf.stats.forwards}")

if __name__ == "__main__":
    main()
