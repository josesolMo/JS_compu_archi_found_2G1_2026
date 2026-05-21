"""
Los 4 procesadores RV32I restringidos a un set de 10 instrucciones.
"""

from __future__ import annotations
from copy import deepcopy
from dataclasses import dataclass
from typing import Optional

from .processor_base import (
    ProcessorBase, DecodedInstr,
    OP_JAL, OP_JALR, OP_BRANCH, OP_LOAD, OP_STORE, OP_IMM, OP_REG,
    F3_BEQ, F7_ALT
)

# ════════════════════════════════════════════════════════════
#  1. PROCESADOR UNICICLO
# ════════════════════════════════════════════════════════════
class Unicycle(ProcessorBase):
    name = "Uniciclo"

    def step(self):
        if self.halted: return

        word = self.mem_read_word(self.pc)
        if word == 0: # Fin de programa implícito
            self.halted = True
            return

        instr = DecodedInstr.decode(word)
        self.pipeline_state["IF"] = instr

        rs1_val = self.reg_read(instr.rs1)
        rs2_val = self.reg_read(instr.rs2)

        next_pc = (self.pc + 4) & 0xFFFF_FFFF
        op = instr.opcode

        if op == OP_JAL:
            self.reg_write(instr.rd, next_pc)
            next_pc = (self.pc + instr.imm) & 0xFFFF_FFFF

        elif op == OP_JALR:
            target = (rs1_val + instr.imm) & ~1
            self.reg_write(instr.rd, next_pc)
            next_pc = target & 0xFFFF_FFFF

        elif op == OP_BRANCH:
            if instr.funct3 == F3_BEQ and rs1_val == rs2_val:
                next_pc = (self.pc + instr.imm) & 0xFFFF_FFFF

        elif op == OP_LOAD:  # lw
            addr = (rs1_val + instr.imm) & 0xFFFF_FFFF
            self.reg_write(instr.rd, self.mem_read_word(addr))

        elif op == OP_STORE: # sw
            addr = (rs1_val + instr.imm) & 0xFFFF_FFFF
            self.mem_write_word(addr, rs2_val)

        elif op == OP_IMM:   # addi
            result = (rs1_val + instr.imm) & 0xFFFF_FFFF
            self.reg_write(instr.rd, result)

        elif op == OP_REG:   # add, sub, and, or
            result = self.alu_op(instr.funct3, instr.funct7, rs1_val, rs2_val)
            self.reg_write(instr.rd, result & 0xFFFF_FFFF)

        else:
            self.halted = True
            return

        self.pc = next_pc
        self.stats.cycles += 1
        self.stats.instructions += 1

    def get_stage_labels(self) -> dict[str, str]:
        instr = self.pipeline_state.get("IF")
        lbl   = instr.mnemonic if instr else "—"
        return {"IF": lbl, "ID": lbl, "EX": lbl, "MEM": lbl, "WB": lbl}


# ════════════════════════════════════════════════════════════
#  2. PROCESADOR MULTICICLO
# ════════════════════════════════════════════════════════════
class Multicycle(ProcessorBase):
    name = "Multiciclo"
    STATES = ["IF", "ID", "EX", "MEM", "WB"]

    def __init__(self):
        super().__init__()
        self._state:   str = "IF"
        self._instr:   Optional[DecodedInstr] = None
        self._rs1_val: int = 0
        self._rs2_val: int = 0
        self._alu_out: int = 0

    def reset(self):
        super().reset()
        self._state   = "IF"
        self._instr   = None
        self._rs1_val = 0
        self._rs2_val = 0
        self._alu_out = 0

    def step(self):
        if self.halted: return
        self.stats.cycles += 1

        if self._state == "IF":
            word = self.mem_read_word(self.pc)
            if word == 0:
                self.halted = True
                return
            self._instr = DecodedInstr.decode(word)
            self.pipeline_state["IF"] = self._instr
            self._state = "ID"

        elif self._state == "ID":
            self._rs1_val = self.reg_read(self._instr.rs1)
            self._rs2_val = self.reg_read(self._instr.rs2)
            self.pipeline_state["ID"] = self._instr
            self._state = "EX"

        elif self._state == "EX":
            op = self._instr.opcode
            if op in (OP_JAL, OP_JALR):
                self._alu_out = (self.pc + 4) & 0xFFFF_FFFF
            elif op in (OP_LOAD, OP_STORE):
                self._alu_out = (self._rs1_val + self._instr.imm) & 0xFFFF_FFFF
            elif op == OP_IMM:
                self._alu_out = (self._rs1_val + self._instr.imm) & 0xFFFF_FFFF
            elif op == OP_REG:
                self._alu_out = self.alu_op(self._instr.funct3, self._instr.funct7, self._rs1_val, self._rs2_val)
            
            self.pipeline_state["EX"] = self._instr
            self._state = "MEM" if op in (OP_LOAD, OP_STORE) else "WB"

        elif self._state == "MEM":
            if self._instr.opcode == OP_LOAD:
                self._alu_out = self.mem_read_word(self._alu_out) # Reutilizado para guardar el dato leído
            elif self._instr.opcode == OP_STORE:
                self.mem_write_word(self._alu_out, self._rs2_val)
            self.pipeline_state["MEM"] = self._instr
            self._state = "WB"

        elif self._state == "WB":
            op = self._instr.opcode
            if op in (OP_LOAD, OP_IMM, OP_REG, OP_JAL, OP_JALR):
                self.reg_write(self._instr.rd, self._alu_out)

            # Actualización del PC al final del ciclo WB
            if op == OP_JAL:
                self.pc = (self.pc + self._instr.imm) & 0xFFFF_FFFF
            elif op == OP_JALR:
                self.pc = (self._rs1_val + self._instr.imm) & ~1 & 0xFFFF_FFFF
            elif op == OP_BRANCH and self._instr.funct3 == F3_BEQ and self._rs1_val == self._rs2_val:
                self.pc = (self.pc + self._instr.imm) & 0xFFFF_FFFF
            else:
                self.pc = (self.pc + 4) & 0xFFFF_FFFF

            self.pipeline_state["WB"] = self._instr
            self.stats.instructions += 1
            self._state = "IF"

    def get_stage_labels(self) -> dict[str, str]:
        cur = self._instr
        label = cur.mnemonic if cur else "—"
        return {s: (label if s == self._state else "—") for s in self.STATES}