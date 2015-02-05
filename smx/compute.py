#!/usr/bin/python

#---imports
from os.path import expanduser
execfile(expanduser('~/.simuluxe_config.py'))
from smx.codetools import *
import smx

def computer(focus,function,headerdat,simdict,get_slices=True,**kwargs):
	
	"""
	Universal procedure for running a function over simulation slices.
	"""

	#---unload data from the header
	calculations = headerdat['calculations']
	compsign = headerdat['compsign']
	dropspot = headerdat['dropspot']
	metadat = headerdat['metadat']

	#---compute
	for panel in focus:
		for ts in focus[panel]:
			status(' '.join(['[CHECK]',compsign,ts]))
			timestamp = focus[panel][ts]['time']
			#---get slice information
			if get_slices:
				grofile,trajfile = smx.get_slices(ts,simdict,
					timestamp=timestamp,
					wrap=calculations[compsign]['wrap'],
					groupname=calculations[compsign]['groupname'])
			else: grofile,trajfile = None,None
			#---get unique filename
			name = 'postproc.'+compsign+'.'+ts+'.'+timestamp+'.dat'
			#---check the repo and if absent compute and store the result
			if not smx.lookup(name,dropspot):
				status(' '.join(['[COMPUTE]',compsign,ts]))
				result,attrs = function(simname=ts,grofile=grofile,trajfile=trajfile,
					metadat=metadat,focus=focus,panel=panel,headerdat=headerdat,**kwargs)
				smx.store(result,name,dropspot,attrs=attrs)

def loader(focus,headerdat):

	"""
	Universal procedure for unloading saved postprocessing data from the dropspot.
	"""

	#---unload data from the header
	compsign = headerdat['compsign']
	dropspot = headerdat['dropspot']
	
	#---retrieve	
	datlist = {}
	for panel in focus:
		for ts in focus[panel]:
			status(' '.join(['[CHECK]',compsign,ts]))
			timestamp = focus[panel][ts]['time']	
			name = 'postproc.'+compsign+'.'+ts+'.'+timestamp+'.dat'
			datlist[ts] = smx.load(name,dropspot)
	return datlist
	
def i2s(*items):

	"""
	Concisely join arguments in order to perform a lookup on an h5py dictionary when storing frames with
	objects that might not equal numpy array sizes. Note that a quick test showed that storing many frames
	with different sizes gave almost the exact same size on disk compared to loading a giant 1D array. The i2s 
	function is particularly useful when storing e.g. the neighborlist and simplex list for different frames of
	a bilayer simulation. In this case, the objects could be stored as "FRAME.MONO.neighborlist". We use the dot
	because it cannot be found in a python variable name anyway.
	"""

	return '.'.join([str(i) for i in items])
