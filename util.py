"""
    Utility functions
"""

import os
import logging
import re
from time import sleep


def atoi(text):
    return int(text) if text.isdigit() else text


def natural_keys(text):
    '''
    list.sort(key=natural_keys) sorts in human order
    http://nedbatchelder.com/blog/200712/human_sorting.html
    '''
    return [ atoi(c) for c in re.split('(\d+)', text) ]


def makedirs(path):
    """ Create directories for `path` (like 'mkdir -p'). """
    if not path:
        return
    folder = os.path.dirname(path)
    if folder and not os.path.exists(folder):
        os.makedirs(folder)


def setlog(name, logfile="", console_lvl='INFO', file_lvl='DEBUG',
        console_format=None, file_format=None):
    """ Set logging to file and console at the same time. """
    
    logger = logging.getLogger(name)
    
    # Check constant logging.<lvl> defined
    attrs = ('console_lvl', console_lvl), ('file_lvl', file_lvl)
    for name, value in attrs:
        if not hasattr(logging, value):
            raise ValueError("{} is one of 'INFO', 'DEBUG', 'WARNING'"
                    ", but '{}' given instead.".format(name, value)
                    )
    
    lvl_console = getattr(logging, console_lvl)
    lvl_file = getattr(logging, file_lvl)
    
    if not console_format:
        console_format = '%(message)s'
        
    if not file_format:
        file_format = '%(asctime)s %(levelname)s %(message)s'
    
    formatter_console = logging.Formatter(console_format)
    formatter_file = logging.Formatter(file_format)
    
    # Log to Console
    hdlr_console = logging.StreamHandler()
    hdlr_console.setFormatter(formatter_console)
    hdlr_console.setLevel(lvl_console) 
    logger.addHandler(hdlr_console)

    # Log to File at the same time
    if logfile:
        file_hdlr = logging.FileHandler(logfile)
        file_hdlr.setFormatter(formatter_file)
        file_hdlr.setLevel(logging.DEBUG)
        logger.addHandler(file_hdlr)
   
    logger.setLevel(logging.DEBUG)  # catch em all
    return logger

#https://gist.github.com/n1ywb/2570004
def retry(max_tries, delay=1, backoff=2, exceptions=(Exception,), hook=None):
    """Function decorator implementing retrying logic.
    delay: Sleep this many seconds * (backoff ** try number) after failure
    backoff: Multiply delay by this factor after each failure
    exceptions: A tuple of exception classes; default (Exception,)
    hook: A function with the signature myhook(tries_remaining, exception, delay);
          default None
    
    The decorator will call the function up to max_tries times if it raises an exception.
    
    By default it catches instances of the Exception class and subclasses.
    This will recover after all but the most fatal errors. You may specify a
    custom tuple of exception classes with the 'exceptions' argument; the
    function will only be retried if it raises one of the specified
    exceptions.
    
    Additionally you may specify a hook function which will be called prior
    to retrying with the number of remaining tries and the exception instance;
    see given example. This is primarily intended to give the opportunity to
    log the failure. Hook is not called after failure if no retries remain.
    """
    def dec(func):
        def f2(*args, **kwargs):
            mydelay = delay
            tries = reversed(range(max_tries))
            
            for tries_remaining in tries:
                try:
                   return func(*args, **kwargs)
                
                except exceptions as e:
                    if tries_remaining > 0:
                        if hook is not None:
                            hook(tries_remaining, e, mydelay)

                        sleep(mydelay)
                        mydelay = mydelay * backoff
                    else:
                        raise
                else:
                    break
        return f2
    return dec
import re
import numpy as np


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


