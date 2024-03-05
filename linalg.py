from collections import OrderedDict
from loops import loop_nest
from expr import AbsExpr,Cell,Var,Expr,Affect,Add,Mul,IntLiteral,FMA,FZero

class matmul:

    def __init__(self,A,B,C,i,j,k):
        self.A = A
        self.B = B
        self.C = C
        self.i = i
        self.j = j
        self.k = k

    def loop_nest(self,initialize_C):
        
        dims = OrderedDict(i=self.i,j=self.j,k=self.k)

        shapes = {
            "C": (self.i,self.j),
            "A": (self.i,self.k),
            "B": (self.k,self.j)
        }
        
        cij = Cell(array=Var(self.C),dims=[Var("i"),Var("j")])
        aik = Cell(array=Var(self.A),dims=[Var("i"),Var("k")])
        bkj = Cell(array=Var(self.B),dims=[Var("k"),Var("j")])
        e = FMA(dest=cij,factor1=aik,factor2=bkj,weight=cij)
        init = FZero(dest=cij)
        # init = Expr(Affect(
        #     left = cij,
        #     right = IntLiteral(lit=0)
        # ))
        
        # e = Expr(Affect(
        #     left = cij,
        #     right = Add(left = cij, right = Mul(left = aik, right = bkj))
        # ))

        payload = {
                e: {'i','j','k'},
        }
        if initialize_C:
            payload[init] = {'i','j'}
        
        return loop_nest(
            dims=dims,
            payload=payload,
            shapes = shapes
        )
