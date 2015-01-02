#!/usr/bin/python

#---imports
from os.path import expanduser
execfile(expanduser('~/.simuluxe_config.py'))
from smx.codetools import *
import smx,controller

def computer_standard(**kwargs):

	"""
	Universal procedure for running a function over simulation slices.\n
	This function is deprecated.
	"""

	#---unpack
	compsign = kwargs['compsign']
	target_timeslices = kwargs['target_timeslices']
	timeslices = kwargs['timeslices']
	metadat = kwargs['metadat']
	dropspot = kwargs['dropspot']
	function = kwargs['function']
	kw = {}
	otherkeys = [k for k in kwargs.keys() if k not in 
		['compsign','target_timeslices','timeslices','metadat','dropspot','function']]
	for key in otherkeys: kw[key] = kwargs[key]

	#---compute
	for sn in target_timeslices:
		status(' '.join(['[FETCH]',compsign,sn]))
		#---if no groupname is specified then do not retrieve slices
		if 'groupname' in kwargs.keys():
			groupname = kwargs['groupname']
			wrap = kwargs['wrap'] if 'wrap' in kwargs.keys() else 'pbcmol'
			grofile,trajfile = smx.get_slices(sn,timestamp=timeslices[sn]['time'],
				wrap=wrap,groupname=groupname)
			#---get unique filename
			name = 'postproc.'+compsign+'.'+sn+'.'+timeslices[sn]['time']+'.dat'
			#---check the repo and if absent compute and store the result
			if not smx.lookup(name,dropspot):
				status(' '.join(['[COMPUTE]',compsign,sn]))
				result,attrs = function(sn,grofile,trajfile,metadat,**kw)
				smx.store(result,name,dropspot,attrs=attrs)	
		#---unspecified groupname devolves get_slices to the function
		else:
			#---get unique filename
			name = 'postproc.'+compsign+'.'+sn+'.'+timeslices[sn]['time']+'.dat'
			#---check the repo and if absent compute and store the result
			if not smx.lookup(name,dropspot):
				status(' '.join(['[COMPUTE]',compsign,sn]))
				result,attrs = function(sn,metadat,**kw)
				smx.store(result,name,dropspot,attrs=attrs)	

def loader_standard(**kwargs):

	"""
	Universal procedure for unloading saved postprocessing data from the dropspot.\n
	This function is deprecated.
	"""

	target_timeslices = kwargs['target_timeslices']
	timeslices = kwargs['timeslices']
	dropspot = kwargs['dropspot']
	compsign = kwargs['compsign']
	#---retrieve
	datlist = {}
	for sn in target_timeslices:
		name = 'postproc.'+compsign+'.'+sn+'.'+timeslices[sn]['time']+'.dat'
		datlist[sn] = smx.load(name,dropspot)
	return datlist

def computer(focus,function,headerdat,get_slices=True):
	
	"""
	Universal procedure for running a function over simulation slices.
	"""

	#---unload data from the header
	calculations = headerdat['calculations']
	compsign = headerdat['compsign']
	dropspot = headerdat['dropspot']

	#---compute
	for panel in focus:
		for ts in focus[panel]:
			status(' '.join(['CHECK',compsign,ts]))
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
				status(' '.join(['COMPUTE',compsign,ts]))
				result,attrs = function(ts,grofile,trajfile,metadat)
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
			status(' '.join(['CHECK',compsign,ts]))
			timestamp = focus[panel][ts]['time']	
			name = 'postproc.'+compsign+'.'+ts+'.'+timestamp+'.dat'
			datlist[ts] = smx.load(name,dropspot)
	return datlist

