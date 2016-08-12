import re
import numpy as np

def atoi(text):
    return int(text) if text.isdigit() else text

def natural_keys(text):
    '''
    alist.sort(key=natural_keys) sorts in human order
    http://nedbatchelder.com/blog/200712/human_sorting.html
    '''
    return [ atoi(c) for c in re.split('(\d+)', text) ]

def movingaverage(interval, window_size=3):
    window = np.ones(int(window_size))/float(window_size)
    return np.convolve(interval, window, 'same')


def accumulate(vals):
    total = 0
    for x in vals:
        total += x
        yield total


def common_start(*strings):
    """ Returns the longest common substring
        from the beginning of the `strings`
    """
    def _iter():
        for z in zip(*strings):
            if z.count(z[0]) == len(z):  # check all elements in `z` are the same
                yield z[0]
            else:
                return

    return ''.join(_iter())


# extrema
