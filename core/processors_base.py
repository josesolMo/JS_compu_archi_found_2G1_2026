"""
Clase base abstracta para 10 instrucciones RV32I.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
import struct

# ──────────────────────────────────────────────
#  Constantes ISA RV32I
# ──────────────────────────────────────────────
XLEN = 32
NUM_REGS = 32
MEM_SIZE = 4096  # bytes

# Opcodes
OP_JAL    = 0b1101111
OP_JALR   = 0b1100111
OP_BRANCH = 0b1100011
OP_LOAD   = 0b0000011
OP_STORE  = 0b0100011
OP_IMM    = 0b0010011   # addi
OP_REG    = 0b0110011   # add, sub, and, or

# funct3
F3_BEQ  = 0b000
F3_WORD = 0b010  # para lw y sw

# funct3 para ALU
F3_ADD_SUB = 0b000
F3_XOR     = 0b100
F3_OR      = 0b110
F3_AND     = 0b111

F7_NORMAL  = 0b0000000
F7_ALT     = 0b0100000   # sub


@dataclass
class DecodedInstr:
    """Campos decodificados de una instrucción de 32 bits."""
    raw:    int = 0
    opcode: int = 0
    rd:     int = 0
    funct3: int = 0
    rs1:    int = 0
    rs2:    int = 0
    funct7: int = 0
    imm:    int = 0          
    valid:  bool = True
    mnemonic: str = "NOP"

    @staticmethod
    def decode(word: int) -> "DecodedInstr":
        if word == 0:  # Manejo básico de burbuja o NOP real
            return DecodedInstr(mnemonic="NOP")

        d = DecodedInstr(raw=word)
        d.opcode = word & 0x7F
        d.rd     = (word >> 7)  & 0x1F
        d.funct3 = (word >> 12) & 0x07
        d.rs1    = (word >> 15) & 0x1F
        d.rs2    = (word >> 20) & 0x1F
        d.funct7 = (word >> 25) & 0x7F

        op = d.opcode
        # Decodificación de inmediatos para los formatos requeridos (I, S, B, J)
        if op in (OP_IMM, OP_LOAD, OP_JALR):
            d.imm = DecodedInstr._sign_extend(word >> 20, 12)
        elif op == OP_STORE:
            imm = ((word >> 25) << 5) | ((word >> 7) & 0x1F)
            d.imm = DecodedInstr._sign_extend(imm, 12)
        elif op == OP_BRANCH:
            imm = (((word >> 31) & 1) << 12 |
                   ((word >>  7) & 1) << 11 |
                   ((word >> 25) & 0x3F) << 5 |
                   ((word >>  8) & 0x0F) << 1)
            d.imm = DecodedInstr._sign_extend(imm, 13)
        elif op == OP_JAL:
            imm = (((word >> 31) & 1) << 20 |
                   ((word >> 12) & 0xFF) << 12 |
                   ((word >> 20) & 1) << 11 |
                   ((word >> 21) & 0x3FF) << 1)
            d.imm = DecodedInstr._sign_extend(imm, 21)
            
        d.mnemonic = DecodedInstr._mnemonic(d)
        return d

    @staticmethod
    def _sign_extend(value: int, bits: int) -> int:
        sign_bit = 1 << (bits - 1)
        return (value & (sign_bit - 1)) - (value & sign_bit)

    @staticmethod
    def _mnemonic(d: "DecodedInstr") -> str:
        op = d.opcode
        try:
            if op == OP_JAL:   return f"JAL   x{d.rd}, {d.imm}"
            if op == OP_JALR:  return f"JALR  x{d.rd}, x{d.rs1}, {d.imm}"
            if op == OP_LOAD:  return f"LW    x{d.rd}, {d.imm}(x{d.rs1})"
            if op == OP_STORE: return f"SW    x{d.rs2}, {d.imm}(x{d.rs1})"
            if op == OP_BRANCH:
                if d.funct3 == F3_BEQ: return f"BEQ   x{d.rs1}, x{d.rs2}, {d.imm}"
            if op == OP_IMM:
                if d.funct3 == F3_ADD_SUB: return f"ADDI  x{d.rd}, x{d.rs1}, {d.imm}"
            if op == OP_REG:
                if d.funct3 == F3_ADD_SUB:
                    return f"SUB   x{d.rd}, x{d.rs1}, x{d.rs2}" if d.funct7 == F7_ALT else f"ADD   x{d.rd}, x{d.rs1}, x{d.rs2}"
                if d.funct3 == F3_AND: return f"AND   x{d.rd}, x{d.rs1}, x{d.rs2}"
                if d.funct3 == F3_OR:  return f"OR    x{d.rd}, x{d.rs1}, x{d.rs2}"
        except Exception:
            pass
        return f"RAW 0x{d.raw:08X}"


@dataclass
class ExecutionStats:
    cycles:        int   = 0
    instructions:  int   = 0
    stalls:        int   = 0   
    forwards:      int   = 0   

    @property
    def cpi(self) -> float:
        return self.cycles / self.instructions if self.instructions else 0.0

    @property
    def time_ms(self) -> float:
        return float(self.cycles)

    def reset(self):
        self.cycles = 0
        self.instructions = 0
        self.stalls = 0
        self.forwards = 0


class ProcessorBase(ABC):
    name: str = "Base"

    def __init__(self):
        self.pc:   int       = 0
        self.regs: list[int] = [0] * NUM_REGS
        self.memory: bytearray = bytearray(MEM_SIZE)
        self.stats:  ExecutionStats = ExecutionStats()
        self.halted: bool    = False

        self.pipeline_state: dict[str, Optional[DecodedInstr]] = {
            "IF": None, "ID": None, "EX": None, "MEM": None, "WB": None
        }

    def load_program(self, instructions: list[int], base_addr: int = 0):
        self.reset()
        for i, word in enumerate(instructions):
            addr = base_addr + i * 4
            if addr + 4 <= MEM_SIZE:
                self.memory[addr:addr+4] = struct.pack("<I", word & 0xFFFF_FFFF)

    def mem_read_word(self, addr: int) -> int:
        addr &= ~3  
        if addr < 0 or addr >= MEM_SIZE: return 0
        return struct.unpack_from("<I", self.memory, addr)[0]

    def mem_write_word(self, addr: int, value: int):
        addr &= ~3
        if 0 <= addr < MEM_SIZE:
            struct.pack_into("<I", self.memory, addr, value & 0xFFFF_FFFF)

    def reg_read(self, idx: int) -> int:
        return 0 if idx == 0 else self.regs[idx]

    def reg_write(self, idx: int, value: int):
        if idx != 0:
            self.regs[idx] = value & 0xFFFF_FFFF

    def alu_op(self, funct3: int, funct7: int, a: int, b: int) -> int:
        """Soporta exclusivamente ADD, SUB, AND, OR."""
        if funct3 == F3_ADD_SUB: 
            return (a - b) if funct7 == F7_ALT else (a + b)
        elif funct3 == F3_AND:     return a & b
        elif funct3 == F3_OR:      return a | b
        return 0

    @staticmethod
    def _signed(v: int) -> int:
        return v if v < 0x8000_0000 else v - 0x1_0000_0000

    def reset(self):
        self.pc = 0
        self.regs = [0] * NUM_REGS
        self.stats.reset()
        self.halted = False
        for k in self.pipeline_state:
            self.pipeline_state[k] = None

    @abstractmethod
    def step(self):
        ...

    @abstractmethod
    def get_stage_labels(self) -> dict[str, str]:
        ...