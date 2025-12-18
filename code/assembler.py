#!/usr/bin/env python3
"""
Simple MIPS Assembler for generating .x files from .s assembly files.
Supports a subset of MIPS instructions needed for cache benchmarks.
"""

import re
import sys
import os

# Register name to number mapping
REGS = {
    '$zero': 0, '$0': 0,
    '$at': 1, '$1': 1,
    '$v0': 2, '$v1': 3, '$2': 2, '$3': 3,
    '$a0': 4, '$a1': 5, '$a2': 6, '$a3': 7,
    '$4': 4, '$5': 5, '$6': 6, '$7': 7,
    '$t0': 8, '$t1': 9, '$t2': 10, '$t3': 11,
    '$t4': 12, '$t5': 13, '$t6': 14, '$t7': 15,
    '$8': 8, '$9': 9, '$10': 10, '$11': 11,
    '$12': 12, '$13': 13, '$14': 14, '$15': 15,
    '$s0': 16, '$s1': 17, '$s2': 18, '$s3': 19,
    '$s4': 20, '$s5': 21, '$s6': 22, '$s7': 23,
    '$16': 16, '$17': 17, '$18': 18, '$19': 19,
    '$20': 20, '$21': 21, '$22': 22, '$23': 23,
    '$t8': 24, '$t9': 25, '$24': 24, '$25': 25,
    '$k0': 26, '$k1': 27, '$26': 26, '$27': 27,
    '$gp': 28, '$28': 28,
    '$sp': 29, '$29': 29,
    '$fp': 30, '$30': 30,
    '$ra': 31, '$31': 31,
}

def parse_reg(r):
    """Parse a register name/number and return the register number."""
    r = r.strip().lower()
    if r in REGS:
        return REGS[r]
    raise ValueError(f"Unknown register: {r}")

def parse_imm(imm):
    """Parse an immediate value (decimal or hex)."""
    imm = imm.strip()
    if imm.startswith('0x') or imm.startswith('0X'):
        return int(imm, 16)
    elif imm.startswith('-'):
        return int(imm)
    else:
        return int(imm)

def sign_extend_16(val):
    """Sign extend a 16-bit value to fit in immediate field."""
    val = val & 0xFFFF
    return val

def encode_r_type(opcode, rs, rt, rd, shamt, funct):
    """Encode R-type instruction."""
    return (opcode << 26) | (rs << 21) | (rt << 16) | (rd << 11) | (shamt << 6) | funct

def encode_i_type(opcode, rs, rt, imm):
    """Encode I-type instruction."""
    return (opcode << 26) | (rs << 21) | (rt << 16) | sign_extend_16(imm)

def encode_j_type(opcode, target):
    """Encode J-type instruction."""
    return (opcode << 26) | (target & 0x3FFFFFF)

class MIPSAssembler:
    def __init__(self):
        self.labels = {}
        self.instructions = []
        self.base_addr = 0x00400000  # Text segment start
        
    def first_pass(self, lines):
        """First pass: collect labels and their addresses."""
        addr = self.base_addr
        for line in lines:
            line = line.split('#')[0].strip()  # Remove comments
            if not line:
                continue
            if line.startswith('.'):  # Directive
                continue
            if ':' in line:
                parts = line.split(':', 1)
                label = parts[0].strip()
                self.labels[label] = addr
                rest = parts[1].strip()
                if rest:  # Instruction on same line as label
                    addr += 4
            else:
                addr += 4
                
    def parse_memory_operand(self, operand):
        """Parse memory operand like '0($t1)' or 'offset($reg)'."""
        operand = operand.strip()
        match = re.match(r'(-?\d+|0x[0-9a-fA-F]+)?\s*\(\s*(\$\w+)\s*\)', operand)
        if match:
            offset = parse_imm(match.group(1)) if match.group(1) else 0
            reg = parse_reg(match.group(2))
            return offset, reg
        raise ValueError(f"Invalid memory operand: {operand}")
    
    def assemble_instruction(self, mnemonic, operands, current_addr):
        """Assemble a single instruction."""
        mnemonic = mnemonic.lower()
        
        # R-type arithmetic
        if mnemonic in ['add', 'addu', 'sub', 'subu', 'and', 'or', 'xor', 'nor', 'slt', 'sltu']:
            rd, rs, rt = [parse_reg(op) for op in operands.split(',')]
            funct = {'add': 0x20, 'addu': 0x21, 'sub': 0x22, 'subu': 0x23,
                    'and': 0x24, 'or': 0x25, 'xor': 0x26, 'nor': 0x27,
                    'slt': 0x2A, 'sltu': 0x2B}[mnemonic]
            return encode_r_type(0, rs, rt, rd, 0, funct)
        
        # Shifts
        if mnemonic in ['sll', 'srl', 'sra']:
            rd, rt, shamt = operands.split(',')
            rd, rt = parse_reg(rd), parse_reg(rt)
            shamt = parse_imm(shamt)
            funct = {'sll': 0x00, 'srl': 0x02, 'sra': 0x03}[mnemonic]
            return encode_r_type(0, 0, rt, rd, shamt, funct)
        
        if mnemonic in ['sllv', 'srlv', 'srav']:
            rd, rt, rs = [parse_reg(op) for op in operands.split(',')]
            funct = {'sllv': 0x04, 'srlv': 0x06, 'srav': 0x07}[mnemonic]
            return encode_r_type(0, rs, rt, rd, 0, funct)
        
        # I-type arithmetic
        if mnemonic in ['addi', 'addiu', 'andi', 'ori', 'xori', 'slti', 'sltiu']:
            parts = operands.split(',')
            rt, rs = parse_reg(parts[0]), parse_reg(parts[1])
            imm = parse_imm(parts[2])
            opcode = {'addi': 0x08, 'addiu': 0x09, 'andi': 0x0C,
                     'ori': 0x0D, 'xori': 0x0E, 'slti': 0x0A, 'sltiu': 0x0B}[mnemonic]
            return encode_i_type(opcode, rs, rt, imm)
        
        # Load upper immediate
        if mnemonic == 'lui':
            parts = operands.split(',')
            rt = parse_reg(parts[0])
            imm = parse_imm(parts[1])
            return encode_i_type(0x0F, 0, rt, imm)
        
        # Load/Store
        if mnemonic in ['lw', 'lh', 'lhu', 'lb', 'lbu', 'sw', 'sh', 'sb']:
            parts = operands.split(',', 1)
            rt = parse_reg(parts[0])
            offset, rs = self.parse_memory_operand(parts[1])
            opcode = {'lb': 0x20, 'lh': 0x21, 'lw': 0x23, 'lbu': 0x24, 'lhu': 0x25,
                     'sb': 0x28, 'sh': 0x29, 'sw': 0x2B}[mnemonic]
            return encode_i_type(opcode, rs, rt, offset)
        
        # Branches
        if mnemonic in ['beq', 'bne']:
            parts = operands.split(',')
            rs, rt = parse_reg(parts[0]), parse_reg(parts[1])
            target = parts[2].strip()
            if target in self.labels:
                target_addr = self.labels[target]
                offset = (target_addr - (current_addr + 4)) >> 2
            else:
                offset = parse_imm(target)
            opcode = {'beq': 0x04, 'bne': 0x05}[mnemonic]
            return encode_i_type(opcode, rs, rt, offset)
        
        if mnemonic in ['bgtz', 'blez']:
            parts = operands.split(',')
            rs = parse_reg(parts[0])
            target = parts[1].strip()
            if target in self.labels:
                target_addr = self.labels[target]
                offset = (target_addr - (current_addr + 4)) >> 2
            else:
                offset = parse_imm(target)
            opcode = {'bgtz': 0x07, 'blez': 0x06}[mnemonic]
            return encode_i_type(opcode, rs, 0, offset)
        
        # Jump
        if mnemonic == 'j':
            target = operands.strip()
            if target in self.labels:
                target_addr = self.labels[target]
            else:
                target_addr = parse_imm(target)
            return encode_j_type(0x02, target_addr >> 2)
        
        if mnemonic == 'jal':
            target = operands.strip()
            if target in self.labels:
                target_addr = self.labels[target]
            else:
                target_addr = parse_imm(target)
            return encode_j_type(0x03, target_addr >> 2)
        
        if mnemonic == 'jr':
            rs = parse_reg(operands)
            return encode_r_type(0, rs, 0, 0, 0, 0x08)
        
        if mnemonic == 'jalr':
            parts = operands.split(',')
            if len(parts) == 2:
                rd, rs = parse_reg(parts[0]), parse_reg(parts[1])
            else:
                rd, rs = 31, parse_reg(parts[0])
            return encode_r_type(0, rs, 0, rd, 0, 0x09)
        
        # Move pseudo-instructions
        if mnemonic == 'move':
            parts = operands.split(',')
            rd, rs = parse_reg(parts[0]), parse_reg(parts[1])
            return encode_r_type(0, rs, 0, rd, 0, 0x21)  # addu rd, rs, $zero
        
        # HI/LO registers
        if mnemonic == 'mfhi':
            rd = parse_reg(operands)
            return encode_r_type(0, 0, 0, rd, 0, 0x10)
        
        if mnemonic == 'mflo':
            rd = parse_reg(operands)
            return encode_r_type(0, 0, 0, rd, 0, 0x12)
        
        if mnemonic == 'mthi':
            rs = parse_reg(operands)
            return encode_r_type(0, rs, 0, 0, 0, 0x11)
        
        if mnemonic == 'mtlo':
            rs = parse_reg(operands)
            return encode_r_type(0, rs, 0, 0, 0, 0x13)
        
        # Multiply/Divide
        if mnemonic in ['mult', 'multu', 'div', 'divu']:
            parts = operands.split(',')
            rs, rt = parse_reg(parts[0]), parse_reg(parts[1])
            funct = {'mult': 0x18, 'multu': 0x19, 'div': 0x1A, 'divu': 0x1B}[mnemonic]
            return encode_r_type(0, rs, rt, 0, 0, funct)
        
        # Syscall
        if mnemonic == 'syscall':
            return encode_r_type(0, 0, 0, 0, 0, 0x0C)
        
        # NOP
        if mnemonic == 'nop':
            return 0
        
        raise ValueError(f"Unknown instruction: {mnemonic}")
    
    def second_pass(self, lines):
        """Second pass: generate machine code."""
        addr = self.base_addr
        for line in lines:
            original_line = line
            line = line.split('#')[0].strip()  # Remove comments
            if not line:
                continue
            if line.startswith('.'):  # Skip directives
                continue
            
            # Handle labels on same line as instruction
            if ':' in line:
                parts = line.split(':', 1)
                line = parts[1].strip()
                if not line:
                    continue
            
            # Parse instruction
            parts = line.split(None, 1)
            mnemonic = parts[0]
            operands = parts[1] if len(parts) > 1 else ''
            
            try:
                code = self.assemble_instruction(mnemonic, operands, addr)
                self.instructions.append(code)
                addr += 4
            except Exception as e:
                print(f"Error assembling: {original_line}", file=sys.stderr)
                print(f"  {e}", file=sys.stderr)
                raise
    
    def assemble(self, filename):
        """Assemble a file."""
        with open(filename, 'r') as f:
            lines = f.readlines()
        
        self.first_pass(lines)
        self.second_pass(lines)
        
        return self.instructions
    
    def write_hex(self, filename):
        """Write assembled code to .x file."""
        with open(filename, 'w') as f:
            for inst in self.instructions:
                f.write(f'{inst:08x}\n')


def print_help():
    print("""MIPS Assembler - Convert .s assembly files to .x hex files

Usage:
    assembler.py <file.s> [output.x]    Assemble a single file
    assembler.py --all <directory>      Assemble all .s files in directory
    assembler.py --help                 Show this help message

Supported Instructions:
    R-type:  add, addu, sub, subu, and, or, xor, nor, slt, sltu
             sll, srl, sra, sllv, srlv, srav
             mult, multu, div, divu, mfhi, mflo, mthi, mtlo
             jr, jalr
    I-type:  addi, addiu, andi, ori, xori, slti, sltiu, lui
             lw, lh, lhu, lb, lbu, sw, sh, sb
             beq, bne, bgtz, blez
    J-type:  j, jal
    Other:   syscall, nop, move

Examples:
    python assembler.py myprogram.s
    python assembler.py myprogram.s output.x
    python assembler.py --all inputs/benchmarks/
""")

def main():
    if len(sys.argv) < 2 or sys.argv[1] in ['--help', '-h', 'help']:
        print_help()
        sys.exit(0 if len(sys.argv) >= 2 else 1)
    
    if sys.argv[1] == '--all':
        directory = sys.argv[2] if len(sys.argv) > 2 else '.'
        for filename in os.listdir(directory):
            if filename.endswith('.s'):
                input_path = os.path.join(directory, filename)
                output_path = os.path.join(directory, filename[:-2] + '.x')
                print(f"Assembling {input_path} -> {output_path}")
                try:
                    asm = MIPSAssembler()
                    asm.assemble(input_path)
                    asm.write_hex(output_path)
                except Exception as e:
                    print(f"  FAILED: {e}")
    else:
        input_file = sys.argv[1]
        if len(sys.argv) > 2:
            output_file = sys.argv[2]
        else:
            output_file = input_file.rsplit('.', 1)[0] + '.x'
        
        asm = MIPSAssembler()
        asm.assemble(input_file)
        asm.write_hex(output_file)
        print(f"Assembled {len(asm.instructions)} instructions to {output_file}")


if __name__ == '__main__':
    main()

