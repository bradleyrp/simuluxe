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
		for sn in focus[panel]:
			status(' '.join(['[CHECK]',compsign,sn]))
			if type(focus[panel][sn])==list: timestamps = focus[panel][sn]
			else: timestamps = [focus[panel][sn]]
			status('[REPORT] timestamps = '+str(timestamps))
			for timestamp in timestamps:
				#---get slice information
				if get_slices:
					#---omit step designation and only use time when getting the slices
					#---...because the step designation tells you how to find the slice in makeslices
					#---...we otherwise assume non-redundant time slices everywhere else
					#---...this saves the hassle of having to distinguish e.g. a02-postproc and s9-lonestar
					grofile,trajfile = smx.get_slices(sn,simdict,
						timestamp=timestamp['time'],
						wrap=calculations[compsign]['wrap'],
						groupname=calculations[compsign]['groupname'])
				else: grofile,trajfile = None,None
				#---get unique filename (we omit step designations and this requires non-redundant times)
				name = 'postproc.'+compsign+'.'+sn+'.'+timestamp['time']+'.dat'
				print name
				#---check the repo and if absent compute and store the result
				if not smx.lookup(name,dropspot):
					status(' '.join(['[COMPUTE]',compsign,sn]))
					result,attrs = function(simname=sn,grofile=grofile,trajfile=trajfile,
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
		for sn in focus[panel]:
			status(' '.join(['[LOAD]',compsign,sn]))
			if type(focus[panel][sn])==list:
				for ts in focus[panel][sn]:
					name = 'postproc.'+compsign+'.'+sn+'.'+ts['time']+'.dat'
					datlist[(sn,ts['time'])] = smx.load(name,dropspot)
			else: 
				name = 'postproc.'+compsign+'.'+sn+'.'+focus[panel][sn]['time']+'.dat'
				datlist[sn] = smx.load(name,dropspot)
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
