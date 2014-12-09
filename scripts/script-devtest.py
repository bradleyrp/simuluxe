#!/usr/bin/python -i

'''
Script which tests controller functions.
Development only.
'''

#---imports
import os,sys
execfile(os.path.expanduser('~/.simuluxe_config.py'))
import smx,controller

#---imports
from smx.io import trajectory_read
import matplotlib as mpl
import scipy
from scipy import linalg
from scipy import spatial
import pylab as plt
from numpy import fft

#---TESTS
#-------------------------------------------------------------------------------------------------------------

#---three ways to call the function
#---from simuluxe directory run "make avail membrane-v509 membrane-v630"
if 0: avail = controller.makeface(['avail','membrane-v509'])
if 0: avail = smx.avail(simname='membrane-v509')

#---make a time slice with the following code
#---alternately "make timeslice membrane-v700-exo70-dilute s8-trestles 85000-95000-1000"
if 0:
	smx.timeslice(
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
	and store the simdict in ~/worker/simuluxe-work/simdict.py using the following command:

	rm ~/.simuluxe.config; make addpath ~/compbio; make addpath ~/store-omicron/membrane-v5xx/; 
	make catalog ~/worker/simuluxe-work/simdict.py sure
	

If you skip making the catalog, you can run the following to do so, only if you have the 
	standard import given above:
	
	controller.catalog(infofile='~/worker/simuluxe-data/simdict.py',edrtime=True)
'''
