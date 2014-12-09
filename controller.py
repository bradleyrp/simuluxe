#!/usr/bin/python

#---imports
import sys,os
import time
import copy
import json
import re

#---imports
import smx
from smx.codetools import niceblock,confirm

helpstring = """
	
	SIMULUXE simulation analysis tools
	
	operation
	---------
	addpath <path> .........: add a parent directory for a collection of
	                          simulations to the local config file
	addconfig <file> .......: add another local (python) settings file to
	                          be called by the local config file
	                          (~/.simuluxe_config.py)
	report .................: list environment variables
	
	configuration
	-------------
	Paths and settings are loaded from `~/.simuluxe_config.py` which will
	be created by default when you run addpath or addconfig. This file
	sets the paths for simulation data (`datapaths`), extra configuration
	descriptions of the simulations in a dictionary (`simdict`), and a list
	of additional configuration files to load (`addconfig`).

	quickstart
	----------
	Here is my favorite command for starting from scratch. You add a data path which
	holds simulations according to the "keyword-vNUMBER/xDIGIT-stepname" naming scheme.
	Then the catalog function searches for all edr files and uses them to quickly set the 
	time stamps. The paths and timestamps are stored in simdict for later.
	
	make addpath DATA
	make catalog ~/worker/simuluxe-data/simdict.py edrtime
	
	You can also list available timestamps for a simulation named e.g. keyword-v001
	from the edr files using this command. The only available keyword is "membrane" since
	this is the primary use for this analysis. Using the keyword 'slices' instead will
	return all prepared time slices.
	
	make avail membrane-v509 membrane-v510
	make avail slices

	To make a time slice from these trajectory use the following command. After suppling the
	simulation name (the top-level directory) and the step directory, you must also provide
	the format of the trajectory and a start-end-step string to indicate the time slice.
	
	make timeslice membrane-v612-enthx1-12800 s5-sim xtc 1000-6000-100
		
	documentation
	-------------
	"""+'see: file:///'+os.getcwd()+'/docs/_build/html/index.html'
	
initconfig = """#!/usr/bin/python

	import os,sys
	
	#---SIMULUXE LOCAL CONFIG FILE
	
	#---datapaths is a list of directories to search for simulation data
	datapaths = []
	
	#---additional settings files to load
	setfiles = []
	
	#---location of the simuluxe execute scripts
	"""

#---FUNCTIONS
#-------------------------------------------------------------------------------------------------------------

def docs(mods=None):

	'''
	Regenerate the documentation using sphinx-apidoc and code in simuluxe/script-make-docs.sh
	'''

	if mods != None and (mods == 'clean' or 'clean' in mods): os.system('cd docs/;make clean')
	else: os.system('./simuluxe/script-make-docs.sh '+os.path.abspath('.'))
	
def init_local_config():
	
	'''
	Check for a local configuration in the home directory and make a blank one if absent.
	'''
	
	confpath = os.path.expanduser('~/.simuluxe_config.py')
	if not os.path.isfile(confpath):
		print 'config file is absent so we will create it now and append paths.'
		with open(os.path.expanduser('~/.simuluxe_config.py'),'w') as fp:
			fp.write(niceblock(initconfig,newlines=True))
			slwd = os.path.abspath(os.path.expanduser(os.getcwd()))
			fp.write("slwd = '"+slwd+"'\n")
			fp.write("sys.path.append(slwd)\n")
			fp.write('\n#---customize below\n')
		return True
	else: return False

def addpath(datapath=None):

	'''
	Add extra paths to simulation data to the local configuration.
	'''

	new = init_local_config()
	if type(datapath) != list: datapath = [datapath]
	for n in datapath:
		fullpath = os.path.abspath(os.path.expanduser(n))
		if ((not new and fullpath not in smx.datapaths) or new) and os.path.isdir(fullpath):
			with open(os.path.expanduser('~/.simuluxe_config.py'),'a') as fp:
				fp.write("datapaths.append('"+fullpath+"')\n")

def addconfig(setfile=None):

	'''
	Add extra configuration and settings files to the local configuration.
	'''
	
	new = init_local_config()
	if type(setfile) != list: setfile = [setfile]
	for n in setfile:
		fullpath = os.path.abspath(os.path.expanduser(n))
		if ((not new and fullpath not in smx.setfiles) or new) and os.path.isfile(fullpath):
			with open(os.path.expanduser('~/.simuluxe_config.py'),'a') as fp:
				fp.write("setfiles.append('"+fullpath+"')\n")
			
def catalog(infofile=None,edrtime=False,xtctime=False,trrtime=False,sure=False):

	'''
	Parse simulation data directories, load paths into a new configuration file, and check that it's in
	the config file.
	'''
	
	new = init_local_config()
	#---note that checking time slices is only done via edr and the xtc/trr files are not consulted
	spider = True if any([xtctime,trrtime,edrtime]) else False
	infofile = os.path.abspath(os.path.expanduser(infofile))
	if os.path.isfile(infofile):
		print 'simdict file exists at '+infofile+' but I will overwrite'
		if not sure and not confirm():
			print 'cancel'
			return
	simdict = smx.findsims(spider=spider)
	with open(infofile,'w') as fp:
		#---note that we must define simdict here
		#---...simuluxe will execute the files in datapaths to create smx.simdict
		#---...execution of .simuluxe_config.py only loads paths while importing smx gets data
		fp.write('#!/usr/bin/env python\n\nsimdict = {}\n')
		for key in simdict.keys():
			fp.write("simdict['"+key+"'] = \\\n")
			formstring = json.dumps(simdict[key],indent=4)
			for line in formstring.split('\n'):
				fp.write('    '+line+'\n')
			fp.write('\n')
	if new or infofile not in smx.setfiles: addconfig(infofile)
	reload(smx)

#---INTERFACE
#-------------------------------------------------------------------------------------------------------------

'''
Functions exposed to makefile:
def avail
def timeslice
def catalog
'''

def makeface(arglist):
	'''
	Interface to makefile.
	'''

	#---print help if no arguments
	if arglist == []:
		print niceblock(helpstring,newlines=True)
		return
	
	#---we prepare a kwargs and an args variable to send to the next function
	#---note that we generally just use kwargs exclusively for clarity
	kwargs = dict()
	
	#---always get the function name from the first argument
	func = arglist.pop(0)
	
	#---define the arguments expected for each function
	argdict = {
		'avail':{'args':['simname','slices'],'module_name':'treeparse'},
		'timeslice':{'args':['simname','step','timerange','form'],'module_name':'treeparse'},
		'catalog':{'args':['infofile','xtctime','edrtime','trrtime','sure'],'module_name':None},
		'addpath':{'args':['datapath'],'module_name':None},
		'addconfig':{'args':['setfile'],'module_name':None},
		}
	
	#---make a copy of the dictionary for pruning
	if func not in argdict.keys():
		globals()[func]
		return
	else: argd = copy.deepcopy(argdict[func])
	
	#---special keywords are handled below
	if 'simname' in argd['args']:
		simnames = [a for a in arglist if any([re.match(kn,a) for kn in ['membrane','protein']])]
		for s in simnames: arglist.pop(arglist.index(s))
		argd['args'].remove('simname')
		kwargs['simname'] = simnames
	if 'step' in argd['args']:
		kwargs['step'] = [[i['dir'] for i in smx.simdict[sn]['steps'] if i['dir'] in arglist]
			for sn in simnames]
		for s in [j for i in kwargs['step'] for j in i]: 
			if s in arglist: arglist.remove(s)
	if 'timerange' in argd['args']:
		timerange = [i for i in arglist if len(i.split('-'))==3]
		if len(timerange) != 1: raise Exception('except: unclear time range')
		argd['args'].remove('timerange')
		for i in timerange: arglist.remove(i)
		kwargs['time'] = timerange[0]
	if 'form' in argd['args']:
		if 'xtc' in arglist and 'trr' in arglist: raise Exceptiopn('except: conflicting formats')
		elif 'trr' in arglist: kwargs['form'] = 'trr'
		else: kwargs['form'] = 'xtc'
	if 'infofile' in argd['args']:
		kwargs['infofile'] = arglist[0]
		argd['args'].remove('infofile')
		arglist.pop(0)
	for sig in ['datapath','setfile']:
		if sig in argd['args']:
			kwargs[sig] = arglist
			argd['args'].remove(sig)
			arglist = []
	
	#---all remaining keywords are handled as flags
	for a in list(arglist): 
		kwargs[a] = True if a in argd['args'] else False
		if a in argd['args']: arglist.remove(a)
	if arglist != []: raise Exception('except: unprocessed arguments')

	if argd['module_name'] == None and func != 'gitpush': target = globals()[func]
	else: target = getattr(getattr(smx,argd['module_name']),func)
	target(**kwargs)
	return	

#---MAIN
#-------------------------------------------------------------------------------------------------------------

if __name__ == "__main__": makeface(sys.argv[1:])
	
