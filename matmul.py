import sys
from space import Space
from linalg import matmul

s = Space()
m = matmul(A="A",B="B",C="C",i=512,j=512,k=512)

ml = m.loop_nest(initialize_C=True)
mlt = s.min_tiling_of_untiled_dims(ml)

# sys.exit(0)
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

