import sys
from space import Space
from builder import LoopBuilder
from linalg import matmul

flops_per_iteration = 2 # because SSE does not have FMA
random_picks = 10
mutations = 10
initialize_C=True

b = LoopBuilder()
s = Space()
m = matmul(A="A",B="B",C="C",i=512,j=512,k=512)
ml = m.loop_nest(initialize_C=initialize_C)
mlcy = s.get_measure(ml).num_cycles
mlflops = int(((512*512*512*flops_per_iteration)/mlcy)*100)/100

def perform_measure(nl):

    measure = s.get_measure(nl)

    cy = measure.num_cycles

    if cy > mlcy:
        return
    
    cmisses = measure.cache_misses
    crefs = measure.cache_references
    cmisses_percent = measure.cache_misses_percent()
    flops = int(((512*512*512*flops_per_iteration)/cy)*100)/100
    rel = int((flops/mlflops)*100)/100

    l = ""
    l += str(nl) + "\n"
    l += f"{flops} flops/cycle (x{rel} perf against {mlflops})\n"
    l += f"{cmisses_percent}% cache misses ({cmisses}/{crefs})\n"
    
    vect = ""
    if measure.vect_sse:
        vect += " SSE"
    if measure.vect_avx2:
        vect += " AVX2"
    if measure.vect_avx512:
        vect += " AVX512"
    l += f"Vect:{vect}"
    
    l += "\n"

    print(l)

mlt = b.min_tiling_of_untiled_dims(ml)

# sys.exit(0)
# rml = s.random_implementation(mlt)
# rml1 = s.mutate(rml)
# rml2 = s.mutate(rml1)
rmls = [b.random_implementation(mlt) for i in range(random_picks)]
for c,l in enumerate(rmls):
    nl = l
    print(f"seed {c}\n")
    perform_measure(nl)
    for i in range(mutations):
        nl = b.mutate(nl)
        perform_measure(nl)

