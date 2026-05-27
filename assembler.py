"""
assembler.py: Mini-Ensamblador para las 10 instrucciones soportadas.
"""
import re

class MiniAssembler:
    # Diccionarios de opcodes y functs
    R_TYPE = {"add": (0b0110011, 0b000, 0b0000000), "sub": (0b0110011, 0b000, 0b0100000),
              "and": (0b0110011, 0b111, 0b0000000), "or":  (0b0110011, 0b110, 0b0000000)}
    I_TYPE = {"addi": (0b0010011, 0b000)}
    LOAD   = {"lw": (0b0000011, 0b010)}
    STORE  = {"sw": (0b0100011, 0b010)}
    BRANCH = {"beq": (0b1100011, 0b000)}
    JUMP   = {"jal": 0b1101111, "jalr": (0b1100111, 0b000)}

    @staticmethod
    def parse_reg(reg_str: str) -> int:
        return int(reg_str.replace("x", "").strip())

    @classmethod
    def assemble_line(cls, line: str) -> int:
        line = line.split("#")[0].strip() # Quitar comentarios
        if not line: return 0

        parts = re.split(r'[\s,]+', line)
        mnemonic = parts[0].lower()

        try:
            if mnemonic in cls.R_TYPE: # add rd, rs1, rs2
                op, f3, f7 = cls.R_TYPE[mnemonic]
                rd, rs1, rs2 = map(cls.parse_reg, parts[1:4])
                return (f7 << 25) | (rs2 << 20) | (rs1 << 15) | (f3 << 12) | (rd << 7) | op

            elif mnemonic in cls.I_TYPE: # addi rd, rs1, imm
                op, f3 = cls.I_TYPE[mnemonic]
                rd, rs1 = map(cls.parse_reg, parts[1:3])
                imm = int(parts[3]) & 0xFFF
                return (imm << 20) | (rs1 << 15) | (f3 << 12) | (rd << 7) | op

            elif mnemonic in cls.LOAD: # lw rd, imm(rs1)
                op, f3 = cls.LOAD[mnemonic]
                rd = cls.parse_reg(parts[1])
                match = re.match(r'([-+]?\d+)\(x(\d+)\)', parts[2])
                imm = int(match.group(1)) & 0xFFF
                rs1 = int(match.group(2))
                return (imm << 20) | (rs1 << 15) | (f3 << 12) | (rd << 7) | op

            elif mnemonic in cls.STORE: # sw rs2, imm(rs1)
                op, f3 = cls.STORE[mnemonic]
                rs2 = cls.parse_reg(parts[1])
                match = re.match(r'([-+]?\d+)\(x(\d+)\)', parts[2])
                imm = int(match.group(1)) & 0xFFF
                rs1 = int(match.group(2))
                imm_11_5 = (imm >> 5) & 0x7F
                imm_4_0  = imm & 0x1F
                return (imm_11_5 << 25) | (rs2 << 20) | (rs1 << 15) | (f3 << 12) | (imm_4_0 << 7) | op

            elif mnemonic in cls.BRANCH: # beq rs1, rs2, imm
                op, f3 = cls.BRANCH[mnemonic]
                rs1, rs2 = map(cls.parse_reg, parts[1:3])
                imm = int(parts[3]) & 0x1FFF
                imm_12 = (imm >> 12) & 0x1
                imm_11 = (imm >> 11) & 0x1
                imm_10_5 = (imm >> 5) & 0x3F
                imm_4_1 = (imm >> 1) & 0xF
                return (imm_12 << 31) | (imm_10_5 << 25) | (rs2 << 20) | (rs1 << 15) | (f3 << 12) | (imm_4_1 << 8) | (imm_11 << 7) | op

            elif mnemonic == "jal": # jal rd, imm
                op = cls.JUMP["jal"]
                rd = cls.parse_reg(parts[1])
                imm = int(parts[2]) & 0x1FFFFF
                imm_20 = (imm >> 20) & 0x1
                imm_19_12 = (imm >> 12) & 0xFF
                imm_11 = (imm >> 11) & 0x1
                imm_10_1 = (imm >> 1) & 0x3FF
                return (imm_20 << 31) | (imm_10_1 << 21) | (imm_11 << 20) | (imm_19_12 << 12) | (rd << 7) | op
                
        except Exception as e:
            print(f"Error ensamblando '{line}': {e}")
            return 0
            
        return 0

    @classmethod
    def assemble_program(cls, source_code: str) -> list[int]:
        lines = source_code.strip().split('\n')
        return [cls.assemble_line(line) for line in lines if line.strip() and not line.strip().startswith('#')]