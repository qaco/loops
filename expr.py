from abc import ABC,abstractmethod

class AbsExpr(ABC):
    @abstractmethod
    def replace(self,eold,enew):
        pass
    @abstractmethod
    def __eq__(self,other):
        pass
    @abstractmethod
    def to_c(self, vectorize):
        pass

class Expr(AbsExpr):
    expr: AbsExpr
    def __init__(self,expr):
        self.expr = expr
    def replace(self,eold,enew):
        if self.expr == eold:
            self.expr = enew
        else:
            self.expr.replace(eold,enew)
    def __eq__(self,other):
        return isinstance(other,Expr) and self.expr == other.expr
    def __hash__(self):
        return hash((self.__class__,self.expr))
    def to_c(self, vectorize):
        return self.expr.to_c(vectorize=vectorize)

class Var(AbsExpr):
    name: str
    def __init__(self,name):
        self.name = name
    def replace(self,eold,enew):
        if eold == self:
            assert(isinstance(enew,Var))
            self.name = enew.var
    def __eq__(self,other):
        return isinstance(other,Var) and self.name == other.name
    def __hash__(self):
        return hash((self.__class__,self.name))
    def to_c(self, vectorize):
        return self.name

class Decl(Var):
    ty: str
    def __init__(self,ty,name):
        super().__init__(name=name)
        self.ty = ty
    def __eq__(self,other):
        return super().__eq__(other) and self.ty == other.ty
    def __hash__(self):
        return hash((self.__class__,self.name,self.ty))
    def to_c(self, vectorize):
        return self.ty + " " + self.name

class IntLiteral(AbsExpr):
    lit: int
    def __init__(self,lit):
        self.lit = lit
    def replace(self,eold,enew):
        pass
    def __eq__(self,other):
        return isinstance(other,IntLiteral) and self.lit == other.lit
    def __hash__(self):
        return hash((self.__class__,self.lit))
    def to_c(self, vectorize):
        return str(self.lit)

class Cell(AbsExpr):
    array: Var
    dims: list[AbsExpr]
    def __init__(self,array,dims):
        self.array = array
        self.dims = dims
    def replace(self,eold,enew):
        self.array.replace(eold,enew)
        for i,d in enumerate(self.dims):
            if d == eold:
                self.dims[i] = enew
            else:
                d.replace(eold,enew)
    def __eq__(self,other):
        if (
                not isinstance(other,Cell)
                or self.array != other.array
                or len(self.dims) != len(other.dims)
        ):
            return False
        
        for m,o in zip(self.dims,other.dims):
            if m != o:
                return False

        return True

    def __hash__(self):
        return hash((self.__class__,self.array) + tuple(self.dims))
    
    def to_c(self, vectorize):
        s = self.array.to_c(vectorize=vectorize)
        for d in self.dims:
            e = d.to_c(vectorize=vectorize)
            s += f"[{e}]"
        return s

class BinOp(AbsExpr,ABC):
    left: AbsExpr
    right: AbsExpr
    def __init__(self,left,right):
        self.left = left
        self.right = right
    def replace(self,eold,enew):
        if self.left == eold:
            self.left = enew
        else:
            self.left.replace(eold,enew)
        if self.right == eold:
            self.right = enew
        else:
            self.right.replace(eold,enew)
    @abstractmethod
    def root(self):
        pass
    def __eq__(self,other):
        return (
            self.__class__ == other.__class__
            and self.left == other.left
            and self.right == other.right
        )
    def __hash__(self):
        return hash((self.__class__,self.left,self.right))
    def to_c(self, vectorize):
        o = self.root()
        return (
            self.left.to_c(vectorize=vectorize)
            + f" {o} "
            + self.right.to_c(vectorize=vectorize)
        )

class Add(BinOp):
    def root(self):
        return "+"

class Mul(BinOp):
    def root(self):
        return "*"

class Affect(BinOp):
    def root(self):
        return "="

class FZero(AbsExpr):
    dest: AbsExpr
    def __init__(self,dest):
        self.dest = dest
    def replace(self,eold,enew):
        self.dest.replace(eold,enew)
    def __eq__(self,other):
        return(
            isinstance(other,FZero)
            and self.dest == other.dest
        )
    def __hash__(self):
        return hash((
            self.__class__,
            self.dest
        ))
    def to_c(self,vectorize):
        if vectorize:
            assert(False)
        else:
            init = Expr(Affect(
                left = self.dest,
                right = IntLiteral(lit=0)
            ))
            return init.to_c(vectorize=vectorize)

class InitFZero(FZero):
    def to_c(self,vectorize):
        if vectorize:
            assert(False)
        else:
            assert(isinstance(self.dest,Var))
            init = Expr(Affect(
                left = Decl(ty="float",name=self.dest.name),
                right = IntLiteral(lit=0)
            ))
            return init.to_c(vectorize=vectorize)
        
class FMA(AbsExpr):
    dest: AbsExpr
    factor1: AbsExpr
    factor2: AbsExpr
    weight: AbsExpr
    def __init__(
            self,
            dest,
            factor1,
            factor2,
            weight,
    ):
        self.dest = dest
        self.factor1 = factor1
        self.factor2 = factor2
        self.weight = weight
    def replace(self,eold,enew):
        for e in [self.dest,self.factor1,self.factor2,self.weight]:
            e.replace(eold,enew)
    def __eq__(self,other):
        return(
            isinstance(other,FMA)
            and self.dest == other.dest
            and self.factor1 == other.factor1
            and self.factor2 == other.factor2
            and self.weight == other.weight
        )
    def __hash__(self):
        return hash((
            self.__class__,
            self.dest,
            self.factor1,
            self.factor2,
            self.weight
        ))
    def to_c(self,vectorize):
        if vectorize:
            assert(False)
        else:
            mul = Mul(left=self.factor1,right=self.factor2)
            add = Add(left=self.weight,right=mul)
            e = Expr(Affect(
                left = self.dest,
                right = add
            ))
            return e.to_c(vectorize=vectorize)
    
    
