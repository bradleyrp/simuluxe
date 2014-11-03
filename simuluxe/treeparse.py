#!/usr/bin/python

#---imports
from os.path import expanduser
execfile(expanduser('~/.simuluxe_config.py'))
from simuluxe import *

#---libraries
import glob,re

#---classic python argsort
def argsort(seq): return [x for x,y in sorted(enumerate(seq), key = lambda x: x[1])]

def findsims(top_prefixes=None,valid_suffixes=None,key_files=None):

	'''
	Parses all paths in datapaths to search for simulation data and returns a dictionary of base directories
	and valid subdirectories (of the form "basename-vNUM/xNUM-descriptor" e.g. "membrane-v567/s8-sim".
	'''

	#--dictionary to hold simulation paths
	simtree = dict()

	#---defaults to specify valid simulation folder prefixes of the form "name-vNUM"
	if top_prefixes == None: top_prefixes = ['membrane','mesomembrane'][:1]
	if valid_suffixes == None: valid_suffixes = ['trr','xtc','tpr']
	if key_files == None: key_files = ['system.gro']
	traj_suf = ['trr','xtc']

	#---search all datapaths for simulations
	for dp in datapaths:
		tops = [f for f in os.listdir(dp+'/') for top in top_prefixes if re.search(r'^'+top+'\-v.+', f)]
		for top in tops:
			for (dirpath, dirnames, filenames) in os.walk(dp+'/'+top):
				#---only parse one level
				if dirpath == dp+'/'+top:
					simtree[top] = dict()
					simtree[top]['root'] = dp
					steplist = [dn for dn in dirnames if re.search(r'^[s-z][0-9]\-.+',dn)]
					steplist = [steplist[j] for j in argsort([int(i[1:].split('-')[0]) for i in steplist])]
					simtree[top]['steps'] = [{'dir':step} for step in steplist]
					#---loop over subdirectories
					for stepnum,sd in enumerate(steplist):
						#---grab selected file types that match a regex for files on the simulation timeline
						for suf in valid_suffixes:
							valids = [fn for fn in os.listdir(dp+'/'+top+'/'+sd) 
								if re.search(r'^md\.part[0-9]{4}\.'+suf+'$',fn)]
							if valids != []: simtree[top]['steps'][stepnum][suf] = list(valids)
						#---grab key files
						for kf in key_files:
							valids = [fn for fn in os.listdir(dp+'/'+top+'/'+sd) if fn == kf]
							if valids != []: simtree[top]['steps'][stepnum]['key_files'] = list(valids)
						#---grab concatenated trajectory files
						for suf in traj_suf:
							valids = [fn for fn in os.listdir(dp+'/'+top+'/'+sd) 
								if re.search(r'^md\.part[0-9]{4}\.[0-9]+\-[0-9]+\-[0-9]+\.'+suf+'$',fn)]
							if valids != []: simtree[top]['steps'][stepnum]['trajs'] = list(valids)							
	
	#---send dictionary back to controller to write to file
	return simtree
