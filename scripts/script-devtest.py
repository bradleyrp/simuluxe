#!/usr/bin/python

'''
Script which tests controller functions.
Development only.
'''

#---imports
from os.path import expanduser
execfile(expanduser('~/.simuluxe_config.py'))
import simuluxe
import controller

#---TESTS
#-------------------------------------------------------------------------------------------------------------

#---three ways to call the function
#---from simuluxe directory run "make avail membrane-v509 membrane-v630"
if 0: avail = controller.makeface(['avail','membrane-v509'])
if 0: avail = simuluxe.avail(simname='membrane-v509')

#---alternately "make timeslice membrane-v700-exo70-dilute s8-trestles 85000-95000-1000"
if 0:
	simuluxe.timeslice(
		simname='membrane-v700-exo70-dilute',
		step='s8-trestles',
		time='85000-95000-1000',
		form='xtc')

#---DEV
#-------------------------------------------------------------------------------------------------------------

'''
In the following section I attempt to reset the whole simuluxe system from scratch.
But the imports are far too complex and clumsy.
Deploy the system to ~/worker/simuluxe for code, ~/worker/simuluxe-work for development,
	and ~/worker/simuluxe-data/simdict.py for storing the simdict using the following:

rm ~/.simuluxe.config; make addpath ~/compbio; make catalog ~/simuluxe-data/simdict.py
'''

#---reset the system
#---alternately "make catalog ~/worker/simuluxe-data/simdict.py"
#---note that this is deprecated
if 0:

	#---bootstrap imports for testing
	import os,sys
	confpath = os.path.expanduser('~/.simuluxe_config.py')
	if os.path.isfile(confpath): execfile(os.path.expanduser('~/.simuluxe_config.py'))
	else:
		print 'no simuluxe config file so assuming location is ~/worker/simuluxe'
		sys.path.append(os.path.expanduser('~/worker/simuluxe'))
		import controller

	#---reset
	if os.path.isfile(confpath): os.remove(confpath)
	controller.addpath('~/compbio')
	controller.catalog(infofile='~/worker/simuluxe-data/simdict.py',edrtime=True)

