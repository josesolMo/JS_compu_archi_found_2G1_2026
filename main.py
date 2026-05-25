"""
main.py: Pruebas de los procesadores
"""

from core.processors import Unicycle, Multicycle, PipelinedStall, PipelinedForwarding

def main():
    # Estructura del programa:
    # 0:  addi x1, x0, 10        # x1 = 10
    # 4:  addi x2, x0, 20        # x2 = 20
    # 8:  add  x3, x1, x2        # x3 = 30
    # 12: sub  x4, x3, x1        # x4 = 20
    # 16: and  x5, x3, x2        # x5 = 20
    # 20: or   x6, x1, x2        # x6 = 30
    # 24: sw   x6, 0(x0)         # mem[0] = 30
    # 28: lw   x7, 0(x0)         # x7 = 30
    # 32: beq  x7, x6, +8        # Salta a PC 40 (esquiva el jal)
    # 36: jal  x8, +8            # Esto no se ejecuta si el beq es exitoso
    # 40: addi x9, x0, 99        # x9 = 99 (Fin de la simulación)

    prog_all = [
        0x00A00093,  # addi x1, x0, 10
        0x01400113,  # addi x2, x0, 20
        0x002081B3,  # add  x3, x1, x2
        0x40118233,  # sub  x4, x3, x1
        0x0021F2B3,  # and  x5, x3, x2
        0x0020E333,  # or   x6, x1, x2
        0x00602023,  # sw   x6, 0(x0)
        0x00002383,  # lw   x7, 0(x0)
        0x00638463,  # beq  x7, x6, +8
        0x0080046F,  # jal  x8, +8
        0x06300493   # addi x9, x0, 99
    ]

    procesadores = [
        (Unicycle, "Unicycle"),
        (Multicycle, "Multicycle"),
        (PipelinedStall, "PipelinedStall"),
        (PipelinedForwarding, "PipelinedForwarding")
    ]

    for proc_class, nombre in procesadores:
        proc = proc_class()
        proc.load_program(prog_all)
        
        while not proc.halted:
            proc.step()
            
        print(f"\n== {nombre} (10 instrucciones) ==")
        for i in range(1, 10):
            print(f"x{i}: {proc.reg_read(i)}")
        print(f"mem[0]: {proc.mem_read_word(0)}")
        print(f"Ciclos: {proc.stats.cycles}, Instrucciones: {proc.stats.instructions}, Stalls: {getattr(proc.stats, 'stalls', 0)}, Forwards: {getattr(proc.stats, 'forwards', 0)}")

if __name__ == "__main__":
    main()