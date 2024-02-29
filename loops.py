import random
import copy
import sys
import subprocess
import os

from collections import OrderedDict
from expr import AbsExpr,Var,Add
from aux import divisors, gen_timing_function

tim_func = "counter_read_time"
tim_ty = "uint64_t"

class loop_nest:
    
    spec_dims: OrderedDict[str,int]
    shapes: OrderedDict[str,tuple[int]]
    name: str
    
    dims: OrderedDict[str,int]
    map_dims: OrderedDict[str,list[str]]
    perm: list[int]

    payload: dict[AbsExpr,set[str]]
    
    count = 0

    def __init__(
            self,
            dims,
            shapes,
            payload,
            spec_dims=None,
            map_dims=None,
            perm=None
    ):
        
        self.dims = dims
        
        self.spec_dims = self.dims if spec_dims == None else spec_dims
        
        self.shapes = shapes

        self.payload = payload
        for ds in payload.values():
            assert(ds.issubset(set(self.dims.keys())))
        
        if map_dims == None:
            self.map_dims = OrderedDict()
            for d in dims.keys():
                self.map_dims[d] = [d]
        else:
            self.map_dims = map_dims
            
        self.perm = list(range(len(self.dims))) if perm == None else perm
        
        self.name = "loop" + str(loop_nest.count)
        
        loop_nest.count += 1

    def check_consistency(self):
        assert(len(self.dims) == len(self.perm))
        
    def __eq__(self,other):
        return (self.payload == other.payload
                and list(self.dims.values()) == list(other.dims.values()))

    def __hash__(self):
        return hash((
            tuple(self.dims.values()),
            frozenset(self.payload)
        ))
        
    def clone(self):
        return loop_nest(
            dims = copy.copy(self.dims),
            shapes = copy.copy(self.shapes),
            payload = copy.deepcopy(self.payload),
            spec_dims = copy.copy(self.spec_dims),
            map_dims = copy.copy(self.map_dims),
            perm = copy.copy(self.perm)
        )

    def is_tiled(self,dim):
        return len(self.map_dims[dim]) > 1
    
    def tile_dimension(self,dim,tile_size):

        dim_size = self.spec_dims[dim]
        nindex0,nindex1 = dim+"0",dim+"1"
        
        self.check_consistency()
        assert(dim in self.spec_dims)
        
        assert(
            dim_size % tile_size == 0
            and tile_size > 0
            and tile_size <= dim_size
        )
        
        
        if nindex0 not in self.dims and nindex1 not in self.dims:
            assert(dim in self.dims)
            # Break the dimension d into 2 new dimensions
            mid1 = {key: value for i,(key, value) in enumerate(self.dims.items())
                    if i < list(self.dims.keys()).index(dim)}
            mid2 = {key: value for i,(key, value) in enumerate(self.dims.items())
                    if i > list(self.dims.keys()).index(dim)}
            mid1[nindex0] = int(dim_size // tile_size)
            mid1[nindex1] = int(tile_size)
            mid1.update(mid2)
            self.dims = mid1
            # Add a new dimension to the permutations buffer
            self.perm.append(max(self.perm) + 1)
            # Update the code
            self.map_dims[dim] = [nindex0,nindex1]
            eold = Var(name=dim)
            enew = Add(left=Var(nindex0),right=Var(nindex1))
            npayload = {}
            for code,dims in self.payload.items():
                code.replace(eold,enew)
                if dim in dims:
                    dims.remove(dim)
                    dims.add(nindex0)
                    dims.add(nindex1)
                npayload[code] = dims
            self.payload = npayload
        else:
            self.dims[nindex0] = int(dim_size // tile_size)
            self.dims[nindex1] = int(tile_size)

        self.check_consistency()

    def permutate_dimensions(self,a,b):
        self.check_consistency()

        # a = list(self.dims.keys()).index(i1)
        # b = list(self.dims.keys()).index(i2)
        self.perm[a], self.perm[b] = self.perm[b], self.perm[a]

        self.check_consistency()
        
    def hamming_distance(self,other):
        
        if self.dims == other.dims:
            dist = 1 if self.perm != other.perm else 0
        else:
            dist = (
                max(len(self.dims),len(other.dims))
                - min(len(self.dims),len(other.dims))
            )

        rem = set(self.dims.keys()).intersection(set(other.dims.keys()))
        for r in rem:
            if self.dims[r] != other.dims[r]:
                dist += 1

        return dist
    
    def to_c_loop(self,init_ident=0,ident_step=2,braces=True):
        assert(len(self.dims) == len(self.perm))
        c = ""
        ident = init_ident*ident_step
        p_dims = set([])
        p_code = set([])
        for d in self.perm:
            k = list(self.dims.keys())[d]
            v = self.dims[k]
            c += ident*" " + f"for (int {k} = 0; {k} < {v}; {k}++)"
            c += " {\n" if braces else "\n"
            ident += ident_step
            p_dims.add(k)
            for code,dims in self.payload.items():
                if dims.issubset(p_dims) and code not in p_code:
                    c += ident*" " + str(code) + ";\n"
                    p_code.add(code)
        while braces and (ident - ident_step) > init_ident:
            c += (ident - ident_step)*" " + "}\n"
            ident -= ident_step
        return c

    def to_c_function(
            self,
            name,
            ident_step=2,
            braces=True,
            gen_main=False,
            instrument=True
    ):
        
        instrument = gen_main and instrument
        c = "#include <stdint.h>\n#include <stdio.h>\n"
        c = gen_timing_function(tim_func,tim_ty,ident_step) if instrument else c

        # Generate the function embedding the loop

        data_list = {}
        for n,s in self.shapes.items():
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
        c += self.to_c_loop(init_ident=1,ident_step=ident_step,braces=braces)
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

    def evaluate(self):
        #
        f = open(f"/tmp/{self.name}.c","w")
        f.write(self.to_c_function(name=self.name,gen_main=True))
        f.close()
        #
        c_path = f"/tmp/{self.name}.c"
        bin_path = f"/tmp/{self.name}"
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
    
    def __str__(self):
        s =  f"loop_nest {self.name}\n"
        # s += 'spec_dims -> ' + str(self.spec_dims) + "\n"
        s += 'dims -> ' + str(self.dims) + "\n"
        # s += 'map_dims -> ' + str(self.map_dims) + "\n"
        s += 'perm -> ' + str(self.perm) + "\n"

        # s += 'payload -> {\n'
        # for (k,v) in self.payload.items():
        #     s+= str(k) + ": " + str(v) + ",\n"
        # s += "}\n"

        s += 'code ->\n' + self.to_c_loop(ident_step=0,braces=False)

        return s

