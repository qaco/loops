import math

tim_func = "counter_read_time"
tim_ty = "uint64_t"

def gen_timing_function(ident_step):
    c = ""
    c += "#include <stdint.h>\n"
    c += "\n"
    c += f"static inline {tim_ty} {tim_func}(void)" + "\n"
    c += "{\n"
    c += ident_step*" " + f"{tim_ty} a, d;" + "\n"
    c += ident_step*" " + "__asm__ __volatile__ (\n"
    c += 2*ident_step*" " + "\"rdtsc\\n\\t\"\n"
    c += 2*ident_step*" " + ": \"=a\" (a), \"=d\" (d)\n"
    c += ident_step*" " + ");\n"
    c += ident_step*" " + "return (d << 32) | (a & 0xffffffff);\n"
    c += "}\n"
    return c
