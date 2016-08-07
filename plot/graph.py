from matplotlib import pyplot as plt


from matplotlib.lines import Line2D
from itertools import cycle
from util import natural_keys

filled_markers = Line2D.filled_markers

class Plot(object):
    def __init__(self, data, opts={}):
        self.fig = plt.figure()
        self.plt = self.plot(data, **opts)
        
    def plot(self, data, title="", **opts):
        markers=cycle(filled_markers)
        labels = sorted(data.keys(), key=lambda x: natural_keys(x[0]) )
        
        for label in labels:
            x, y = data[label]
            plt.plot(x, y, label=label, marker=next(markers), **opts)
        
        plt.title(title)
        plt.grid()
        plt.legend(title='ADC Threshold:', loc='upper left')
        return plt
    
    def show(self):
        self.plt.show()
    
    def save(self, filename):
        self.fig.savefig(filename)
