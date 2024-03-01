import sys
from space import Space
from builder import LoopBuilder
from linalg import matmul

initialize_C=False

b = LoopBuilder()
s = Space()
m = matmul(A="A",B="B",C="C",i=512,j=512,k=512)

ml = m.loop_nest(initialize_C=initialize_C)
mlcy = s.get_measure(ml)
mlflops = int(((512*512*512)/mlcy)*100)/100

mlt = b.min_tiling_of_untiled_dims(ml)

# sys.exit(0)
# rml = s.random_implementation(mlt)
# rml1 = s.mutate(rml)
# rml2 = s.mutate(rml1)
rmls = [b.random_implementation(mlt) for i in range(5)]
for c,l in enumerate(rmls):
    nl = l
    cy = s.get_measure(nl)
    flops = int(((512*512*512)/cy)*100)/100
    rel = int((flops/mlflops)*100)/100
    print(f"seed {c}\n")
    print(f"{flops} flops/cycle ({mlflops} before: x{rel})")
    print(nl)
    for i in range(3):
        nl = b.mutate(nl)
        cy = s.get_measure(nl)
        flops = int(((512*512*512)/cy)*100)/100
        rel = int((flops/mlflops)*100)/100
        print(f"{flops} flops/cycle ({mlflops} before: x{rel})")
        print(nl)

