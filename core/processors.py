"""
Los 4 procesadores RV32I.
"""

from __future__ import annotations
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
    cycle_time_ps = 770

    def step(self):
        if self.halted: return

        word = self.mem_read_word(self.pc)
        if word == 0:
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
    cycle_time_ps = 410
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
                self._alu_out = self.mem_read_word(self._alu_out)
            elif self._instr.opcode == OP_STORE:
                self.mem_write_word(self._alu_out, self._rs2_val)
            self.pipeline_state["MEM"] = self._instr
            self._state = "WB"

        elif self._state == "WB":
            op = self._instr.opcode
            if op in (OP_LOAD, OP_IMM, OP_REG, OP_JAL, OP_JALR):
                self.reg_write(self._instr.rd, self._alu_out)

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


# ════════════════════════════════════════════════════════════
#  Registros de pipeline acoplados
# ════════════════════════════════════════════════════════════
@dataclass
class IF_ID:
    instr: Optional[DecodedInstr] = None
    pc:    int = 0
    valid: bool = False

@dataclass
class ID_EX:
    instr:    Optional[DecodedInstr] = None
    pc:       int = 0
    rs1_val:  int = 0
    rs2_val:  int = 0
    imm:      int = 0
    valid:    bool = False

@dataclass
class EX_MEM:
    instr:    Optional[DecodedInstr] = None
    alu_out:  int = 0
    rs2_val:  int = 0
    valid:    bool = False

@dataclass
class MEM_WB:
    instr:    Optional[DecodedInstr] = None
    alu_out:  int = 0
    valid:    bool = False


# ════════════════════════════════════════════════════════════
#  3. PIPELINE CON STALLS
# ════════════════════════════════════════════════════════════
class PipelinedStall(ProcessorBase):
    name = "Segmentado (Stalls)"
    cycle_time_ps = 290

    def __init__(self):
        super().__init__()
        self.if_id  = IF_ID()
        self.id_ex  = ID_EX()
        self.ex_mem = EX_MEM()
        self.mem_wb = MEM_WB()

    def step(self):
        if self.halted: return
        self.stats.cycles += 1

        stall = self._detect_data_hazard()
        flush = False
        target_pc = 0

        # ── WB ──────────────────────────────────────────
        if self.mem_wb.valid and self.mem_wb.instr:
            op = self.mem_wb.instr.opcode
            if op in (OP_LOAD, OP_IMM, OP_REG, OP_JAL, OP_JALR):
                self.reg_write(self.mem_wb.instr.rd, self.mem_wb.alu_out)
            self.pipeline_state["WB"] = self.mem_wb.instr
            self.stats.instructions += 1
        else:
            self.pipeline_state["WB"] = None

        # ── MEM ─────────────────────────────────────────
        new_mem_wb = MEM_WB()
        if self.ex_mem.valid and self.ex_mem.instr:
            i = self.ex_mem.instr
            out = self.ex_mem.alu_out
            if i.opcode == OP_LOAD:
                out = self.mem_read_word(out)
            elif i.opcode == OP_STORE:
                self.mem_write_word(out, self.ex_mem.rs2_val)
            new_mem_wb = MEM_WB(instr=i, alu_out=out, valid=True)
            self.pipeline_state["MEM"] = i
        else:
            self.pipeline_state["MEM"] = None

        # ── EX ──────────────────────────────────────────
        new_ex_mem = EX_MEM()
        if self.id_ex.valid and self.id_ex.instr:
            i = self.id_ex.instr
            a, b = self.id_ex.rs1_val, self.id_ex.rs2_val
            out = 0
            
            if i.opcode in (OP_JAL, OP_JALR):
                out = (self.id_ex.pc + 4) & 0xFFFF_FFFF
                flush = True
                target_pc = (self.id_ex.pc + i.imm) & 0xFFFF_FFFF if i.opcode == OP_JAL else (a + i.imm) & ~1 & 0xFFFF_FFFF
            elif i.opcode == OP_BRANCH:
                if i.funct3 == F3_BEQ and a == b:
                    flush = True
                    target_pc = (self.id_ex.pc + i.imm) & 0xFFFF_FFFF
            elif i.opcode in (OP_LOAD, OP_STORE, OP_IMM): 
                out = (a + i.imm) & 0xFFFF_FFFF
            elif i.opcode == OP_REG: 
                out = self.alu_op(i.funct3, i.funct7, a, b)
            
            new_ex_mem = EX_MEM(instr=i, alu_out=out, rs2_val=b, valid=True)
            self.pipeline_state["EX"] = i
        else:
            self.pipeline_state["EX"] = None

        # ── ID ──────────────────────────────────────────
        new_id_ex = ID_EX()
        if flush:
            self.pipeline_state["ID"] = None
        elif stall:
            self.pipeline_state["ID"] = self.if_id.instr
        elif self.if_id.valid and self.if_id.instr:
            i = self.if_id.instr
            new_id_ex = ID_EX(
                instr=i, pc=self.if_id.pc,
                rs1_val=self.reg_read(i.rs1), rs2_val=self.reg_read(i.rs2),
                imm=i.imm, valid=True
            )
            self.pipeline_state["ID"] = i
        else:
            self.pipeline_state["ID"] = None

        # ── IF ──────────────────────────────────────────
        new_if_id = self.if_id
        if flush:
            self.pc = target_pc
            new_if_id = IF_ID()
            self.pipeline_state["IF"] = None
        elif not stall:
            word = self.mem_read_word(self.pc)
            
            if word == 0 and not any([self.if_id.valid, self.id_ex.valid, self.ex_mem.valid, new_mem_wb.valid]):
                self.halted = True
                return
            
            if word != 0:
                instr = DecodedInstr.decode(word)
                new_if_id = IF_ID(instr=instr, pc=self.pc, valid=True)
                self.pipeline_state["IF"] = instr
                self.pc = (self.pc + 4) & 0xFFFF_FFFF
            else:
                new_if_id = IF_ID()
                self.pipeline_state["IF"] = None
        else:
            self.stats.stalls += 1
            self.pipeline_state["IF"] = self.if_id.instr

        # === ACTUALIZACIÓN SINCRONIZADA DE TODOS LOS REGISTROS ===
        self.mem_wb = new_mem_wb
        self.ex_mem = new_ex_mem
        self.id_ex  = new_id_ex
        self.if_id  = new_if_id

    def _detect_data_hazard(self) -> bool:
        id_ = self.if_id
        if not (id_.valid and id_.instr): return False
        
        op = id_.instr.opcode
        uses_rs1 = op in (OP_BRANCH, OP_LOAD, OP_STORE, OP_IMM, OP_REG, OP_JALR)
        uses_rs2 = op in (OP_BRANCH, OP_STORE, OP_REG)
        
        rs1 = id_.instr.rs1 if uses_rs1 else 0
        rs2 = id_.instr.rs2 if uses_rs2 else 0
        
        if rs1 == 0 and rs2 == 0:
            return False

        for stage in [self.id_ex, self.ex_mem]:
            if stage.valid and stage.instr and stage.instr.rd != 0:
                if stage.instr.opcode not in (OP_STORE, OP_BRANCH):
                    rd = stage.instr.rd
                    if (uses_rs1 and rs1 == rd) or (uses_rs2 and rs2 == rd):
                        return True
        return False

    def get_stage_labels(self) -> dict[str, str]:
        def lbl(instr): return instr.mnemonic if instr else "burbuja"
        return {k: lbl(self.pipeline_state.get(k)) for k in self.pipeline_state}


# ════════════════════════════════════════════════════════════
#  4. PIPELINE CON FORWARDING
# ════════════════════════════════════════════════════════════
class PipelinedForwarding(ProcessorBase):
    name = "Segmentado (Forwarding)"
    cycle_time_ps = 290

    def __init__(self):
        super().__init__()
        self.if_id  = IF_ID()
        self.id_ex  = ID_EX()
        self.ex_mem = EX_MEM()
        self.mem_wb = MEM_WB()

    def step(self):
        if self.halted: return
        self.stats.cycles += 1

        stall = self._load_use_hazard()
        flush = False
        target_pc = 0

        # ── WB ──────────────────────────────────────────
        if self.mem_wb.valid and self.mem_wb.instr:
            op = self.mem_wb.instr.opcode
            if op in (OP_LOAD, OP_IMM, OP_REG, OP_JAL, OP_JALR):
                self.reg_write(self.mem_wb.instr.rd, self.mem_wb.alu_out)
            self.pipeline_state["WB"] = self.mem_wb.instr
            self.stats.instructions += 1
        else:
            self.pipeline_state["WB"] = None

        # ── MEM ─────────────────────────────────────────
        new_mem_wb = MEM_WB()
        if self.ex_mem.valid and self.ex_mem.instr:
            i = self.ex_mem.instr
            out = self.ex_mem.alu_out
            if i.opcode == OP_LOAD:
                out = self.mem_read_word(out)
            elif i.opcode == OP_STORE:
                self.mem_write_word(out, self.ex_mem.rs2_val)
            new_mem_wb = MEM_WB(instr=i, alu_out=out, valid=True)
            self.pipeline_state["MEM"] = i
        else:
            self.pipeline_state["MEM"] = None

        # ── EX con forwarding ───────────────────────────
        new_ex_mem = EX_MEM()
        if self.id_ex.valid and self.id_ex.instr:
            i = self.id_ex.instr
            a, b = self._resolve_forwards()
            out = 0
            
            if i.opcode in (OP_JAL, OP_JALR):
                out = (self.id_ex.pc + 4) & 0xFFFF_FFFF
                flush = True
                target_pc = (self.id_ex.pc + i.imm) & 0xFFFF_FFFF if i.opcode == OP_JAL else (a + i.imm) & ~1 & 0xFFFF_FFFF
            elif i.opcode == OP_BRANCH:
                if i.funct3 == F3_BEQ and a == b:
                    flush = True
                    target_pc = (self.id_ex.pc + i.imm) & 0xFFFF_FFFF
            elif i.opcode in (OP_LOAD, OP_STORE, OP_IMM): 
                out = (a + i.imm) & 0xFFFF_FFFF
            elif i.opcode == OP_REG: 
                out = self.alu_op(i.funct3, i.funct7, a, b)
            
            new_ex_mem = EX_MEM(instr=i, alu_out=out, rs2_val=b, valid=True)
            self.pipeline_state["EX"] = i
        else:
            self.pipeline_state["EX"] = None

        # ── ID ──────────────────────────────────────────
        new_id_ex = ID_EX()
        if flush:
            self.pipeline_state["ID"] = None
        elif stall:
            self.pipeline_state["ID"] = self.if_id.instr
        elif self.if_id.valid and self.if_id.instr:
            i = self.if_id.instr
            new_id_ex = ID_EX(
                instr=i, pc=self.if_id.pc,
                rs1_val=self.reg_read(i.rs1), rs2_val=self.reg_read(i.rs2),
                imm=i.imm, valid=True
            )
            self.pipeline_state["ID"] = i
        else:
            self.pipeline_state["ID"] = None

        # ── IF ──────────────────────────────────────────
        new_if_id = self.if_id
        if flush:
            self.pc = target_pc
            new_if_id = IF_ID()
            self.pipeline_state["IF"] = None
        elif not stall:
            word = self.mem_read_word(self.pc)
            
            if word == 0 and not any([self.if_id.valid, self.id_ex.valid, self.ex_mem.valid, new_mem_wb.valid]):
                self.halted = True
                return
            
            if word != 0:
                instr = DecodedInstr.decode(word)
                new_if_id = IF_ID(instr=instr, pc=self.pc, valid=True)
                self.pipeline_state["IF"] = instr
                self.pc = (self.pc + 4) & 0xFFFF_FFFF
            else:
                new_if_id = IF_ID()
                self.pipeline_state["IF"] = None
        else:
            self.stats.stalls += 1
            self.pipeline_state["IF"] = self.if_id.instr

        # === ACTUALIZACIÓN SINCRONIZADA DE TODOS LOS REGISTROS ===
        self.mem_wb = new_mem_wb
        self.ex_mem = new_ex_mem
        self.id_ex  = new_id_ex
        self.if_id  = new_if_id

    def _load_use_hazard(self) -> bool:
        ex = self.id_ex
        id_ = self.if_id
        if not (ex.valid and ex.instr and id_.valid and id_.instr): return False
        if ex.instr.opcode != OP_LOAD or ex.instr.rd == 0: return False
        
        op = id_.instr.opcode
        uses_rs1 = op in (OP_BRANCH, OP_LOAD, OP_STORE, OP_IMM, OP_REG, OP_JALR)
        uses_rs2 = op in (OP_BRANCH, OP_STORE, OP_REG)
        
        rs1 = id_.instr.rs1 if uses_rs1 else 0
        rs2 = id_.instr.rs2 if uses_rs2 else 0
        
        return ex.instr.rd in (rs1, rs2)

    def _resolve_forwards(self) -> tuple[int, int]:
        a = self.id_ex.rs1_val
        b = self.id_ex.rs2_val
        
        if not (self.id_ex.valid and self.id_ex.instr): return a, b
        
        i = self.id_ex.instr
        uses_rs1 = i.opcode in (OP_BRANCH, OP_LOAD, OP_STORE, OP_IMM, OP_REG, OP_JALR)
        uses_rs2 = i.opcode in (OP_BRANCH, OP_STORE, OP_REG)
        
        rs1 = i.rs1 if uses_rs1 else 0
        rs2 = i.rs2 if uses_rs2 else 0

        # Forwarding desde MEM
        if self.ex_mem.valid and self.ex_mem.instr and self.ex_mem.instr.rd != 0:
            if self.ex_mem.instr.opcode not in (OP_STORE, OP_BRANCH):
                rd = self.ex_mem.instr.rd
                if uses_rs1 and rd == rs1: a = self.ex_mem.alu_out; self.stats.forwards += 1
                if uses_rs2 and rd == rs2: b = self.ex_mem.alu_out; self.stats.forwards += 1

        # Forwarding desde WB
        if self.mem_wb.valid and self.mem_wb.instr and self.mem_wb.instr.rd != 0:
            if self.mem_wb.instr.opcode not in (OP_STORE, OP_BRANCH):
                rd = self.mem_wb.instr.rd
                if uses_rs1 and rd == rs1 and not (self.ex_mem.valid and self.ex_mem.instr and self.ex_mem.instr.rd == rs1):
                    a = self.mem_wb.alu_out; self.stats.forwards += 1
                if uses_rs2 and rd == rs2 and not (self.ex_mem.valid and self.ex_mem.instr and self.ex_mem.instr.rd == rs2):
                    b = self.mem_wb.alu_out; self.stats.forwards += 1

        return a, b

    def get_stage_labels(self) -> dict[str, str]:
        def lbl(instr): return instr.mnemonic if instr else "burbuja"
        return {k: lbl(self.pipeline_state.get(k)) for k in self.pipeline_state}