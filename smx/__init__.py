#!/usr/bin/python

#---conditional simuluxe imports
import os
if os.path.isfile(os.path.expanduser('~/.simuluxe_config.py')):
	execfile(os.path.expanduser('~/.simuluxe_config.py'))
	simdict = {}
	#---execute all configuration files on import
	for setfile in setfiles: execfile(setfile)

#---autocomplete and other bells and whistles
if os.path.isfile('/etc/pythonstart'): execfile('/etc/pythonstart')
elif os.path.isfile(os.path.expanduser('~/.pythonstart')): execfile(os.path.expanduser('~/.pythonstart'))

#---load all submodules manually (note that sequence matters and this is safe but recursive)
from codetools import *
from quickplot import *
from SimSet import *
from SimSetMembrane import *
from treeparse import *
from datastore import *
from plotter import *
from compute import *
from io import *
