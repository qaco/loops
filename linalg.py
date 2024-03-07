from collections import OrderedDict
from loops import loop_nest
from expr import Cell,Var,Affect,FMA,FZero,FZeroInit

class matmul(loop_nest):
    
    def __init__(self,A,B,C,i,j,k,vectorize):
        
        dims = OrderedDict(i=i,j=j,k=k)

        shapes = {
            "C": (i,j),
            "A": (i,k),
            "B": (k,j)
        }

        cij = Cell(array=Var(C),dims=[Var("i"),Var("j")])
        aik = Cell(array=Var(A),dims=[Var("i"),Var("k")])
        bkj = Cell(array=Var(B),dims=[Var("k"),Var("j")])
        tmpvar = Var("sum")
        init = FZeroInit(dest=tmpvar)
        e = FMA(dest=tmpvar,factor1=aik,factor2=bkj,weight=tmpvar)
        load = Affect(left=cij,right=tmpvar)

        prefix_payload = {
            e: {'i','j','k'},
            init: {'i','j'}
        }
        suffix_payload = {
            load: {'i','j'}
        }
        
        super().__init__(
            dims=dims,
            shapes=shapes,
            prefix_payload=prefix_payload,
            suffix_payload=suffix_payload,
            vectorizable_dims=['j']
        )
