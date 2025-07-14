import random

class MetricRandomizer:
    def __init__(self, init_value_func, random_step_func):
        self.init_value =  init_value_func
        self.random_step = random_step_func

    def init(self):
        return round(self.init_value(), 2)
    
    def next(self, value):
        next_value = round(self.random_step(value), 2)
        if random.random() < 0.001: #0.1% for a spike
            next_value *= 2
        return next_value