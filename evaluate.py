import math
import subprocess
import os

tim_func = "counter_read_time"
tim_ty = "uint64_t"
incl_tim_ty = "#include <stdint.h>\n"

def gen_timing_function(ident_step):
    c = ""
    c += incl_tim_ty
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

def to_c_function(
            loop,
            name,
            ident_step=2,
            braces=True,
            gen_main=False,
            instrument=True
    ):
        
        instrument = gen_main and instrument
        c = incl_tim_ty + "#include <stdio.h>\n"
        c += gen_timing_function(ident_step) if instrument else c

        # Generate the function embedding the loop

        data_list = {}
        for n,s in loop.shapes.items():
            p = ident_step*" " + f"float {n}"
            for ds in s:
                p += f"[{ds}]"
            data_list[n] = p

        c += "\n"
        c += f"void {name}(\n"
        for i,d in enumerate(data_list.values()):
            c += d
            if i < len(data_list) - 1:
                c += ","
            c += "\n"
        c += ")\n{\n"
        c += loop.to_c_loop(init_ident=1,ident_step=ident_step,braces=braces)
        c += "}\n"

        # Generate the main function
        
        if not gen_main:
            return c
        
        c += "\n"
        c += "int main() {\n"
        for d in data_list.values():
            c += d + ";\n"
        c += ident_step*" " + f"{tim_ty} startt = {tim_func}();" + "\n"
        c += ident_step*" " + f"{name}("
        for i,n in enumerate(data_list.keys()):
            c += n
            if i < len(data_list) - 1:
                c += ","
        c += ");\n"
        c += ident_step*" " + f"{tim_ty} endt = {tim_func}();" + "\n"
        c += ident_step*" " + f"{tim_ty} duration = endt - startt;" + "\n"
        c += ident_step*" " + "printf(\"%llu\\n\", duration);\n"
        c += "}\n"
            
        return c

def evaluate(loop):
        #
        f = open(f"/tmp/{loop.name}.c","w")
        f.write(to_c_function(loop,name=loop.name,gen_main=True))
        f.close()
        #
        c_path = f"/tmp/{loop.name}.c"
        bin_path = f"/tmp/{loop.name}"
        comp_result = subprocess.run(
            ["gcc", "-O3", c_path, "-o", bin_path],
            capture_output=True,
            text=True
        )
        if comp_result.returncode != 0:
            print(f"{c_path} compilation error during evaluation.")
            return None

        exe_result = subprocess.run(
            [bin_path],
            capture_output=True,
            text=True
        )

        os.remove(c_path)
        os.remove(bin_path)

        ncycles = int(exe_result.stdout)
        return ncycles
