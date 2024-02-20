import math

def divisors(n):
    divs = [1]
    for i in range(2,int(math.sqrt(n))+1):
        if n%i == 0:
            divs.extend([i,n/i])
    divs.extend([n])
    return list(set(divs))

def gen_timing_function(name,ty,ident_step):
    c = ""
    c += "#include <stdint.h>\n"
    c += "\n"
    c += f"static inline {ty} {name}(void)" + "\n"
    c += "{\n"
    c += ident_step*" " + f"{ty} a, d;" + "\n"
    c += ident_step*" " + "__asm__ __volatile__ (\n"
    c += 2*ident_step*" " + "\"rdtsc\\n\\t\"\n"
    c += 2*ident_step*" " + ": \"=a\" (a), \"=d\" (d)\n"
    c += ident_step*" " + ");\n"
    c += ident_step*" " + "return (d << 32) | (a & 0xffffffff);\n"
    c += "}\n"
    return c
