import math
import subprocess
import os
import re
from capstone import *

md = Cs(CS_ARCH_X86, CS_MODE_64)

tim_func = "counter_read_time"
tim_ty = "uint64_t"
tim_key = "time"
incl_tim_ty = "#include <stdint.h>\n"

class Exp:
    num_cycles: int
    cache_misses: int
    vect_sse: bool
    vect_avx2: bool
    vect_avx512: bool

    def __init__(
            self,
            num_cycles,
            cache_references = 0,
            cache_misses = 0,
            vect_sse = False,
            vect_avx2 = False,
            vect_avx512 = False
    ):
        self.num_cycles = num_cycles
        self.cache_references = cache_references
        self.cache_misses = cache_misses
        self.vect_sse = vect_sse
        self.vect_avx2 = vect_avx2
        self.vect_avx512 = vect_avx512

    def cache_misses_percent(self):
        return int((self.cache_misses/self.cache_references)*10000)/100

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
        c = incl_tim_ty + "#include <stdio.h>\n" + "#include <immintrin.h>\n"
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
        c += loop.to_c_loop(
            init_ident=1,
            ident_step=ident_step,
        )
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
        c += ident_step*" " + "printf(\"" + tim_key + ": %llu\\n\", duration);\n"
        c += "}\n"
            
        return c

def evaluate(loop):
        #
        f = open(f"/tmp/{loop.name}.c","w")
        f.write(to_c_function(loop,name=loop.name,gen_main=True))
        f.close()
        #
        c_path = f"/tmp/{loop.name}.c"
        asm_path = f"/tmp/{loop.name}.s"
        bin_path = f"/tmp/{loop.name}"
        
        comp_result = subprocess.run(
            ["gcc", "-S", "-O3", c_path, "-o", asm_path],
            capture_output=True,
            text=True
        )

        if comp_result.returncode != 0:
            print(f"{c_path} compilation error during evaluation.")
            return None

        comp_result = subprocess.run(
            ["gcc", "-O3", asm_path, "-o", bin_path],
            capture_output=True,
            text=True
        )
        
        run_cmd = [
            "perf","stat", "-B", "-e",
            "cache-references,cache-misses",
            bin_path
        ]
        # Get number cycles
        exe_result = subprocess.run(
            run_cmd,
            capture_output=True,
            text=True
        )

        norm_stdout = str(exe_result.stdout)
        ncycles = int(re.search("time: ([0-9]+)", norm_stdout).group(1))
        
        norm_stderr = re.sub(' +', ' ', exe_result.stderr)
        norm_stderr = re.sub(r'(\d)\s+(\d)', r'\1\2', norm_stderr)
        crefs = int(re.search("([0-9]+) cache-references",
                              norm_stderr).group(1),
                    )
        cmisses = int(re.search("([0-9]+) cache-misses",
                                norm_stderr).group(1)
                      )

        with open(asm_path) as f:
            asm_str = f.read()

        avx2,avx512 = "ymm" in asm_str,"zmm" in asm_str
        
        sse_vect_instr = [
            'addps',
            'subps',
            'mulps',
            'divps',
            'rcpps',
            'sqrtps',
            'maxps',
            'minps',
            'rsqrtps'
        ]
        sse = False
        for ins in sse_vect_instr:
            if ins in asm_str:
                sse = True
                break
        
        # os.remove(c_path)
        os.remove(asm_path)
        # os.remove(bin_path)
        
        assert(cmisses < crefs)
        exp = Exp(
            num_cycles=ncycles,
            cache_references=crefs,
            cache_misses = cmisses,
            vect_sse=sse,
            vect_avx2=avx2,
            vect_avx512=avx512
        )
        return exp
