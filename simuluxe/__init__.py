#!/usr/bin/python

import os,sys

#---conditional simuluxe imports
import os
if os.path.isfile(os.path.expanduser('~/.simuluxe_config.py')):
	execfile(os.path.expanduser('~/.simuluxe_config.py'))
	#---execute all configuration files on import
	for setfile in setfiles: execfile(setfile)

#---autocomplete and other bells and whistles
if os.path.isfile('/etc/pythonstart'): execfile('/etc/pythonstart')

#---universal imports
import numpy as np
from numpy import array,shape
import matplotlib as mpl
import pylab as plt

#---json to format dictionaries (note that this is fairly trivial)
import json
