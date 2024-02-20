from collections import OrderedDict
import subprocess
import sys

from ast import AbsExpr,Cell,Var,Expr,Affect,Add,Mul
from loops import loop_nest
from space import Space

class matmul:

    def __init__(self,A,B,C,i,j,k):
        self.A = A
        self.B = B
        self.C = C
        self.i = i
        self.j = j
        self.k = k

    def loop_nest(self):
        
        dims = OrderedDict(i=self.i,j=self.j,k=self.k)

        shapes = {
            "C": (self.i,self.j),
            "A": (self.i,self.k),
            "B": (self.k,self.j)
        }
        
        cij = Cell(array=Var(self.C),dims=[Var("i"),Var("j")])
        aik = Cell(array=Var(self.A),dims=[Var("i"),Var("k")])
        bkj = Cell(array=Var(self.B),dims=[Var("k"),Var("j")])
        e = Expr(Affect(
            left = cij,
            right = Add(left = cij, right = Mul(left = aik, right = bkj))
        ))
        return loop_nest(dims=dims, kernel = e, shapes = shapes)

s = Space()
m = matmul(A="A",B="B",C="C",i=512,j=512,k=512)

ml = m.loop_nest()
mlt = s.min_tiling_of_untiled_dims(ml)
# rml = s.random_implementation(mlt)
# rml1 = s.mutate(rml)
# rml2 = s.mutate(rml1)
rmls = [s.random_implementation(mlt) for i in range(5)]
for c,l in enumerate(rmls):
    nl = l
    d = s.difference_eval(ml,nl)
    print(f"seed {c}\n")
    print(f"{d}% better")
    print(nl)
    for i in range(3):
        nl = s.mutate(nl)
        d = s.difference_eval(ml,nl)
        print(f"{d}% better")
        print(nl)

