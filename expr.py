from abc import ABC,abstractmethod

class AbsExpr(ABC):
    def contains_one(self,exprs):
        for e in exprs:
            if self.contains(e):
                return True
        return False
    @abstractmethod
    def contains(self,expr):
        pass
    @abstractmethod
    def replace(self,eold,enew):
        pass
    @abstractmethod
    def __eq__(self,other):
        pass
    @abstractmethod
    def to_c(self, vectorize=None):
        pass

class Expr(AbsExpr):
    expr: AbsExpr
    def __init__(self,expr):
        self.expr = expr
    def contains(self,expr):
        if self.expr == expr:
            return True
        else:
            self.expr.contains(expr)
    def replace(self,eold,enew):
        if self.expr == eold:
            self.expr = enew
        else:
            self.expr.replace(eold,enew)
    def __eq__(self,other):
        return self.__class__ == other.__class__ and self.expr == other.expr
    def __hash__(self):
        return hash((self.__class__,self.expr))
    def to_c(self, vectorize=None):
        return self.expr.to_c(vectorize=vectorize)

class Var(AbsExpr):
    name: str
    def __init__(self,name):
        self.name = name
    def contains(self,expr):
        return expr == self
    def replace(self,eold,enew):
        if eold == self:
            self.name = enew.var
    def __eq__(self,other):
        return isinstance(other,Var) and self.name == other.name
    def __hash__(self):
        return hash((self.__class__,self.name))
    def to_c(self, vectorize=None):
        return self.name

# class Call(AbsExpr):
#     name: str
#     args: list[AbsExpr]
#     def __init__(self,name,args):
#         self.name = name
#         self.args = args
#     def replace(self,eold,enew):
#         for i,a in enumerate(self.args):
#             if a == eold:
#                 self.args[i] = enew
#             else:
#                 self.replace(eold,enew)
#     def __eq__(self,other):
#         return (
#             isinstance(other,Call)
#             and self.name == other.name
#             and self.args == self.args
#         )
#     def __hash__(self):
#         return hash((self.__class__,self.name,tuple(self.args)))
#     def to_c(self,vectorize):
#         c = ""
#         c +=
    
class Decl(Var):
    ty: str
    def __init__(self,ty,name):
        super().__init__(name=name)
        self.ty = ty
    def __eq__(self,other):
        return super().__eq__(other) and self.ty == other.ty
    def __hash__(self):
        return hash((self.__class__,self.name,self.ty))
    def to_c(self, vectorize=None):
        return self.ty + " " + self.name

class IntLiteral(AbsExpr):
    lit: int
    def __init__(self,lit):
        self.lit = lit
    def replace(self,eold,enew):
        pass
    def contains(self,expr):
        return False
    def __eq__(self,other):
        return isinstance(other,IntLiteral) and self.lit == other.lit
    def __hash__(self):
        return hash((self.__class__,self.lit))
    def to_c(self, vectorize=None):
        return str(self.lit)

class Cell(AbsExpr):
    array: Var
    dims: list[AbsExpr]
    def __init__(self,array,dims):
        self.array = array
        self.dims = dims
    def contains(self,expr):
        for e in self.dims + [self.array]:
            if e == expr or e.contains(expr):
                return True
        return False
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
    
    def to_c(self, vectorize=None):
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
    def contains(self,expr):
        if self.left == expr or self.right == expr:
            return True
        else:
            return self.left.contains(expr) or self.right.contains(expr)
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
    def to_c_vect(self,vectorize):
        return None
    def __eq__(self,other):
        return (
            self.__class__ == other.__class__
            and self.left == other.left
            and self.right == other.right
        )
    def __hash__(self):
        return hash((self.__class__,self.left,self.right))
    def to_c(self, vectorize=None):
        c = None
        if vectorize:
            c = self.to_c_vect(vectorize=vectorize)
        if c == None:
            o = self.root()
            c = (
                self.left.to_c(vectorize=vectorize)
                + f" {o} "
                + self.right.to_c(vectorize=vectorize)
            )
        return c

class Add(BinOp):
    def root(self):
        return "+"
    def to_c_vect(self,vectorize):
        c = None
        # if vectorize == 'sse':
        #     c = "_mm_add_ps("
        #     c += self.left.to_c(vectorize=vectorize)
        #     c += ", " + self.right.to_c(vectorize=vectorize)
        #     c += ");"
        return c

class Mul(BinOp):
    def root(self):
        return "*"
    def to_c_vect(self,vectorize):
        c = None
        # if vectorize == 'sse':
        #     c = "_mm_mul_ps("
        #     c += self.left.to_c(vectorize=vectorize)
        #     c += ", " + self.right.to_c(vectorize=vectorize)
        #     c += ");"
        return c

class Affect(BinOp):
    def root(self):
        return "="
    def to_c_vect(self,vectorize):
        c = None
        if vectorize == 'sse':
            c = "_mm_storeu_ps(&"
            c += self.left.to_c(vectorize=vectorize)
            c += ", " + self.right.to_c(vectorize=vectorize)
            c += ");"
        return c

class FZero(Expr):
    def to_c(self,vectorize=None):
        init = Expr(Affect(
            left = self.expr,
            right = IntLiteral(lit=0)
        ))
        return init.to_c(vectorize=vectorize)

class FZeroInit(Expr):
    def to_c(self,vectorize=None):
        assert(isinstance(self.expr,Var))
        c = ""
        if vectorize == "sse":
            c += "__m128 " + self.expr.to_c(vectorize=vectorize)
            c += " = "
            c += "_mm_setzero_ps();"
        else:
            init = Expr(Affect(
                left = Decl(ty="float",name=self.expr.name),
                right = IntLiteral(lit=0)
            ))
            c += init.to_c(vectorize=vectorize)
        return c
        
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
    def contains(self,expr):
        for e in [
                self.dest,
                self.factor1,
                self.factor2,
                self.weight
        ]:
            if e == expr or e.contains(expr):
                return True
        return False
    def replace(self,eold,enew):
        self.dest = enew if self.dest == eold else self.dest
        self.factor1 = enew if self.factor1 == eold else self.factor1
        self.factor2 = enew if self.factor2 == eold else self.factor2
        self.weight = enew if self.weight == eold else self.weight
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
    def to_c(self,vectorize=None):
        c = ""
        if vectorize == "sse":
            c += (
                " __m128 a_row = _mm_loadu_ps(&"
                + self.factor1.to_c(vectorize=vectorize)
                + ");")
            c += (
                " __m128 b_col = _mm_loadu_ps(&"
                + self.factor2.to_c(vectorize=vectorize)
                + ");")
            c += (
                " "
                + self.dest.to_c(vectorize=vectorize)
                + "= _mm_add_ps("
                + self.weight.to_c(vectorize=vectorize)
                + ", _mm_mul_ps(a_row, b_col));"
            )
        else:
            mul = Mul(left=self.factor1,right=self.factor2)
            add = Add(left=self.weight,right=mul)
            e = Expr(Affect(
                left = self.dest,
                right = add
            ))
            c += e.to_c(vectorize=vectorize)
        return c
    
    
