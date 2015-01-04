#!/usr/bin/python

#---imports
from os.path import expanduser
execfile(expanduser('~/.simuluxe_config.py'))
from smx.codetools import *
import smx

def computer(focus,function,headerdat,get_slices=True):
	
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
				grofile,trajfile = smx.get_slices(ts,
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
					metadat=metadat,focus=focus,panel=panel)
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

