import random
import math

from loops import loop_nest

def divisors(n):
    divs = [1]
    for i in range(2,int(math.sqrt(n))+1):
        if n%i == 0:
            divs.extend([i,n/i])
    divs.extend([n])
    return list(set(divs))

class LoopBuilder:

    def min_tiling_of_untiled_dims(self,loop):

        loop.check_consistency()

        nloop = loop.clone()
        for dim in nloop.spec_dims.keys():
            if not nloop.is_tiled(dim):
                nloop.tile_dimension(dim,1)

        nloop.check_consistency()
        return nloop

    def slice_permutations(self,loop):
        
        offsets = []
        for code,dims in (
                list(loop.prefix_payload.items())
                # + list(loop.suffix_payload.items())
        ):
            # The closest parent of the payload (innermost dimension)
            dmax = max(map(
                lambda n:list(loop.dims.keys()).index(n) + 1,
                dims
            ))
            if not dmax in offsets:
                offsets.append(dmax)
        offsets.sort()

        # Break the permutations into len(offsets) parts
        slices = []
        acc = 0
        for o in offsets:
               perm_slice = loop.perm[acc:o]
               acc = o
               slices.append(perm_slice)

        return slices
               
    def randomly_permutate(self,loop):

        loop.check_consistency()
        
        slices = self.slice_permutations(loop)
        # Randomly permutate each slice
        nperm = []
        for s in slices:
            random.shuffle(s)
            nperm += s

        assert(nperm.index(5) >= 4)
        assert(nperm.index(4) >= 4)
            
        nloop = loop.clone()
        nloop.perm = nperm
        
        nloop.check_consistency()
        return nloop

    def randomly_permutate_n(self,loop,n):

        nloop = loop.clone()
        slices = self.slice_permutations(loop)

        pairs = []
        for s in slices:
            p = [(a, b) for idx,a in enumerate(s) for b in s[idx + 1:]]
            pairs.append(p)

        for i in range(n):
            s = slices[i]
            ps = pairs[i]
            p = random.choice(ps)
            nloop.permutate_index_dimensions(p[0],p[1])

        nloop.check_consistency()
        assert(nloop.perm.index(5) >= 4)
        assert(nloop.perm.index(4) >= 4)
        return nloop
    
    def randomly_tile_dimensions(self, loop, dims):

        nloop = loop.clone()
        
        for d in dims:
            tile_sizes = divisors(loop.spec_dims[d])
            tile_sizes.remove(1)
            tile_sizes.remove(loop.spec_dims[d])
            n = random.choice(tile_sizes)
            nloop.tile_dimension(d,n)

        return nloop
            
    def randomly_tile_dimension(self, loop, dim):
        return self.randomly_tile_dimensions(loop,[dim])
    
    def randomly_permutate_1(self, loop):
        return self.randomly_permutate_n(loop, 1)
        
    def mutate(self,loop):
        d = random.choice(range(len(loop.spec_dims) + 1))

        if d == len(loop.spec_dims):
            nloop = self.randomly_permutate_1(loop)
        else:
            nloop = self.randomly_tile_dimension(loop,list(loop.spec_dims.keys())[d])

        if loop.hamming_distance(nloop) > 0:
            return nloop
        else:
            return self.mutate(loop)
                                             
    def random_implementation(self,loop):
        #
        to_tile = []
        for k in loop.spec_dims.keys():
            if random.choice([True,False]):
                to_tile.append(k)
        l2 = self.randomly_tile_dimensions(loop,to_tile)
        #
        l3 = self.randomly_permutate(l2)
        #
        return l3
