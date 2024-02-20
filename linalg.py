from collections import OrderedDict
from loops import loop_nest
from expr import AbsExpr,Cell,Var,Expr,Affect,Add,Mul,IntLiteral

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
        init = Expr(Affect(
            left = cij,
            right = IntLiteral(lit=0)
        ))
        aik = Cell(array=Var(self.A),dims=[Var("i"),Var("k")])
        bkj = Cell(array=Var(self.B),dims=[Var("k"),Var("j")])
        e = Expr(Affect(
            left = cij,
            right = Add(left = cij, right = Mul(left = aik, right = bkj))
        ))

        
        return loop_nest(
            dims=dims,
            payload = {e: {'i','j','k'}},
            # payload = {e: {'i','j','k'}, init: {'i','j'}},
            shapes = shapes
        )
