from abc import ABC,abstractmethod

class AbsExpr(ABC):
    @abstractmethod
    def replace(self,eold,enew):
        pass
    @abstractmethod
    def __eq__(self,other):
        pass
    @abstractmethod
    def __str__(self):
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
    def __str__(self):
        return str(self.expr)

class Var(AbsExpr):
    name: str
    def __init__(self,name):
        self.name = name
    def replace(self,eold,enew):
        pass
    def __eq__(self,other):
        return isinstance(other,Var) and self.name == other.name
    def __hash__(self):
        return hash((self.__class__,self.name))
    def __str__(self):
        return self.name

class Cell(AbsExpr):
    array: Var
    dims: list[AbsExpr]
    def __init__(self,array,dims):
        self.array = array
        self.dims = dims
    def replace(self,eold,enew):
        if isinstance(eold,Var) and eold.name == self.array.name:
            self.array = enew
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
    
    def __str__(self):
        s = str(self.array)
        for d in self.dims:
            e = str(d)
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
    def __str__(self):
        o = self.root()
        return str(self.left) + f" {o} " + str(self.right)

class Add(BinOp):
    def root(self):
        return "+"

class Mul(BinOp):
    def root(self):
        return "*"

class Affect(BinOp):
    def root(self):
        return "="
