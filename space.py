from loops import loop_nest
import random
import copy
import math
from pandas import DataFrame

from expr import Var,Add
from evaluate import evaluate

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
        
    def get_measure(self,loop):
        if loop not in self.prior:
            e = evaluate(loop)
            self.prior[loop] = e
        return self.prior[loop]
