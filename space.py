from loops import loop_nest
import random
import copy
from pandas import DataFrame

from aux import divisors
from expr import Var,Add

class Space:

    prior: dict[loop_nest,int]

    def __init__(self):
        self.prior = {}

    def to_data_frame(self):

        ktime = "time"
        
        data = {ktime:[]}
        
        for (l,t) in self.prior.items():
            
            for (k,v),p in zip(l.dims.items(),l.perm):
                kp = k + "p"
                if k not in data:
                    data[k] = []
                    data[kp] = []
                data[k] = data[k] + [v]
                data[kp] = data[kp] + [p]

            data[ktime] = data[ktime] + [t]

        return DataFrame(data)
        
    def min_tiling_of_untiled_dims(self,loop):
        assert(len(loop.dims) == len(loop.perm))
        nloop = loop.clone()
        for dim in nloop.spec_dims.keys():
            if not nloop.is_tiled(dim):
                nloop.tile_dimension(dim,1)
        assert(len(nloop.dims) == len(nloop.perm))
        return nloop

    def slice_permutations(self,loop):
        # TODO
        
        offsets = []
        for code,dims in loop.payload.items():
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

        assert(len(loop.dims) == len(loop.perm))
        
        slices = self.slice_permutations(loop)
        # Randomly permutate each slice
        nperm = []
        for s in slices:
            random.shuffle(s)
            nperm += s

        nloop = loop.clone()
        nloop.perm = nperm
        assert(len(nloop.dims) == len(nloop.perm))
        return nloop

    def randomly_permutate_n(self,loop,n):

        nloop = loop.clone()
        slices = self.slice_permutations(loop)

        pairs = []
        for s in slices:
            p = [(a, b) for idx, a in enumerate(s) for b in s[idx + 1:]]
            pairs.append(p)

        for i in range(n):
            s = slices[i]
            ps = pairs[i]
            p = random.choice(ps)
            nloop.permutate_dimensions(p[0],p[1])

        assert(len(nloop.dims) == len(nloop.perm))
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

    def eval(self,loop):
        if loop not in self.prior:
            e = loop.evaluate()
            self.prior[loop] = e
        return self.prior[loop]

    def difference_eval(self,loop1,loop2):
        el1 = self.eval(loop1)
        el2 = self.eval(loop2)
        d = int(((el1 - el2)/el1)*10000)/100
        return d
