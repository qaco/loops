import random
import copy
import sys
import subprocess
import os

from collections import OrderedDict
from expr import AbsExpr,Var,Add

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

    def permutate_dimensions(self,i1,i2):
        a = list(self.dims.keys()).index(i1)
        b = list(self.dims.keys()).index(i2)
        self.permutate_index_dimensions(a,b)
        
    def permutate_index_dimensions(self,a,b):
        self.check_consistency()

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
        self.check_consistency()
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
                    c += ident*" " + code.to_c(vectorize=False) + ";\n"
                    p_code.add(code)
        while braces and (ident - ident_step) > init_ident:
            c += (ident - ident_step)*" " + "}\n"
            ident -= ident_step
        return c

    def __str__(self):
        s =  f"loop_nest {self.name}\n"
        s += "dims -> {"
        ldims = list(self.dims.items())
        for p in self.perm:
            k,v = ldims[p]
            s += f" {k}: {v},"
        s += " }"

        return s

