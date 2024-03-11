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
ml = matmul(A="A",B="B",C="C",i=512,j=512,k=512)

mlt = b.min_tiling_of_untiled_dims(ml)
mlt.tile_dimension('i',32)
mlt.tile_dimension('j',4)
mlt.tile_dimension('k',4)
mlt.perm = [3,2,1,0,4,5]
mlt.vectorize_sse()

print(mlt.vectorizable_dims)

print(mlt)
print(mlt.to_c_loop())
