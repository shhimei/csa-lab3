import argparse

from isa import Opcode, Operand, Term, write_code

DATA_MEM_MAX_SIZE = 0xFFFF
ADDR_MEM_MAX_SIZE = '0x7FF'

instructions = {'mov', 'push', 'pop', 'call', 'ret', 'add', 'mul', 'div', 'mod', 'jmp', 'sub', 'jn', 'jz', 'halt', 'sv','ld', 'test'}
data_mem_instr = {'db'}


def remove_comments(statement):
    semicolon = ';'
    sem_ind = -1
    if semicolon in statement:
        sem_ind = statement.index(semicolon)
    if sem_ind >= 0:
        del (statement[sem_ind], statement[len(statement) - 1])
    return statement


def decode_as_register(operand):
    if operand == 'acc':
        return '1'
    elif operand == 'dr':
        return '3'
    elif operand == 'br':
        return '4'
    elif operand == 'sp':
        return '5'
    return operand


def is_register(operand):
    if operand == 'acc' or operand == 'dr' or operand == 'br' or operand == 'sp' or operand == 'r7':
        return True
    else:
        return False


def decode_address(num):
    hex_num = hex(num)
    if hex_num > ADDR_MEM_MAX_SIZE:
        # throw exception
        pass
    if hex_num < '0':
        # throw exception
        pass
    return hex_num


def decode_instr(command, operand):
    command_args = []
    if operand.cmd == Opcode.MOV and operand.p1 is not None and operand.p2 is not None:
        command_args.append(operand.p1)
        command_args.append(operand.p2)
        command |= {"opcode": operand.cmd, "operands": command_args}
    if operand.cmd == Opcode.HALT and operand.p1 is None and operand.p2 is None:
        command |= {"opcode": operand.cmd, "operands": command_args}
        del command["operands"]
    if operand.cmd == Opcode.ADD and operand.p1 is not None and operand.p2 is not None:
        command_args.append(operand.p1)
        command_args.append(operand.p2)
        command |= {"opcode": operand.cmd, "operands": command_args}


# TODO вытащить парсинг в отдельные функции
def translate(program):
    lines = program.readlines()
    statements = []
    for line in lines:
        statement = remove_comments(line.strip().split())
        if statement:
            statements.append(statement)

    code = []
    labels = []
    address = 0
    data_addr = 0
    LoC = 0
    for line, statement in enumerate(statements, 1):
        struct = {"opcode": None, "address": None}
        if statement[0] in data_mem_instr:
            struct["opcode"] = Opcode(statement[0])
            struct["address"] = data_addr
            struct |= {"data": int(statement[1], 0)}
            data_addr += 1
            code.append(struct)
            continue

        struct = {"opcode": None, "address": None}
        label = {"label": None, "addr": None}

        if statement[0] not in instructions:
            if ":" in statement[0]:
                label["label"] = statement[0].strip().replace(':', '')
                # TODO check: label address or next address (2nd option I suppose)
                label["addr"] = address
            else:
                print("error: no such instruction", statement[0])
            labels.append(label)
            continue
        size = len(statement)
        struct["opcode"] = Opcode(statement[0])
        struct["address"] = address
        if size == 2:
            arg = statement[1]
            is_label = False
            for label in labels:
                if arg == label["label"]:
                    struct |= {"op": label["addr"]}
                    is_label = True
            if not is_label:
                op = {"type": "const", "value": arg}
                mem_dict = {"addr": None, "offset": None, "scale": None}
                if "[" in arg:
                    op["type"] = "mem"
                    tmp_arg = arg
                    tmp_arg = tmp_arg.replace('[', '').replace(']', '')
                    if "+" in tmp_arg:
                        tmp_arg = tmp_arg.split("+")
                        if "*" in tmp_arg[0] or "*" in tmp_arg[1]:
                            if "*" in tmp_arg[0]:
                                tmp_arr = tmp_arg[0].split("*")

                                for i in tmp_arr:
                                    if is_register(i):
                                        mem_dict["addr"] = i
                                    else:
                                        mem_dict["scale"] = i
                                if is_register(tmp_arg[1]):
                                    mem_dict["addr"] = tmp_arg[1]
                                else:
                                    mem_dict["offset"] = tmp_arg[1]

                            if "*" in tmp_arg[1]:
                                tmp_arr = tmp_arg[1].split("*")
                                print("possible scale", tmp_arr)
                                for i in tmp_arr:
                                    if is_register(i):
                                        mem_dict["addr"] = i
                                    else:
                                        mem_dict["scale"] = i

                                if is_register(tmp_arg[0]):
                                    mem_dict["addr"] = tmp_arg[0]
                                else:
                                    mem_dict["offset"] = ord(tmp_arg[0])
                        else:
                            for i in tmp_arg:
                                if is_register(i):
                                    mem_dict["addr"] = i
                                else:
                                    mem_dict["offset"] = i
                    else:
                        if is_register(tmp_arg):
                            mem_dict["addr"] = tmp_arg
                        else:
                            mem_dict["offset"] = tmp_arg
                    op["value"] = mem_dict
                elif is_register(arg):
                    op["type"] = "reg"
                struct |= {"op": op}
        elif size == 3:
            struct |= {"dest": None, "source": None}

            mem_dict = {"addr": None, "offset": None, "scale": None}

            op1 = {"type": "reg", "value": None}
            op2 = {"type": "reg", "value": None}

            if "[" in statement[1] or "[" in statement[2]:

                if "[" in statement[1]:
                    op1["type"] = "mem"
                    tmp_arg = statement[1]
                    op2["value"] = statement[2]
                else:
                    op2["type"] = "mem"
                    tmp_arg = statement[2]
                    op1["value"] = statement[1]

                tmp_arg = tmp_arg.replace('[', '').replace(']', '')
                if "+" in tmp_arg:
                    tmp_arg = tmp_arg.split("+")
                    if "*" in tmp_arg[0] or "*" in tmp_arg[1]:
                        if "*" in tmp_arg[0]:
                            tmp_arr = tmp_arg[0].split("*")

                            for i in tmp_arr:
                                if is_register(i):
                                    mem_dict["addr"] = i
                                else:
                                    mem_dict["scale"] = i
                            if is_register(tmp_arg[1]):
                                mem_dict["addr"] = tmp_arg[1]
                            else:
                                mem_dict["offset"] = tmp_arg[1]

                        if "*" in tmp_arg[1]:
                            tmp_arr = tmp_arg[1].split("*")
                            print("possible scale", tmp_arr)
                            for i in tmp_arr:
                                if is_register(i):
                                    mem_dict["addr"] = i
                                else:
                                    mem_dict["scale"] = i

                            if is_register(tmp_arg[0]):
                                mem_dict["addr"] = tmp_arg[0]
                            else:
                                mem_dict["offset"] = ord(tmp_arg[0])
                    else:
                        for i in tmp_arg:
                            if is_register(i):
                                mem_dict["addr"] = i
                            else:
                                mem_dict["offset"] = i
                else:
                    if is_register(tmp_arg):
                        mem_dict["addr"] = tmp_arg
                    else:
                        mem_dict["offset"] = tmp_arg
            else:
                op1["value"] = statement[1]
                op2["value"] = statement[2]

                # only source register can be constant
                if not is_register(op2["value"]):
                    op2["type"] = "const"

            if op1["type"] == "mem":
                op1["value"] = mem_dict
            if op2["type"] == "mem":
                op2["value"] = mem_dict

            struct["source"] = op2
            struct["dest"] = op1
        address += 1
        code.append(struct)
        LoC = line
    cnt_instr = 0
    for c in code:
        opcode = c['opcode']
        if opcode is Opcode.JMP or opcode is Opcode.JN or opcode is Opcode.CALL or opcode is Opcode.JZ:
            if type(c['op']) is int:
                continue
            arg = c['op']['value']
            for label in labels:
                if arg == label["label"]:
                    c['op'] = label['addr']
        if opcode is not Opcode.DB:
            cnt_instr += 1
    return code, cnt_instr, LoC


def main(file, target):
    with open(file, 'r') as program:
        code, instr, line = translate(program)
    print("source LoC:", line, " code instr: ", instr)
    write_code(target, code)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Videos to images')
    parser.add_argument('asm', type=str, help='asm instructions')
    parser.add_argument('res', type=str, help='translation result')
    args = parser.parse_args()
    main(file=args.asm, target=args.res)
