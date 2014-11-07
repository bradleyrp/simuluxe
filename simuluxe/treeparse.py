#!/usr/bin/python

#---imports
from os.path import expanduser
try: execfile(expanduser('~/.simuluxe_config.py'))
except: print 'config file is absent'
from simuluxe import *

#---imports 
import re,subprocess

#---classic python argsort
def argsort(seq): return [x for x,y in sorted(enumerate(seq), key = lambda x: x[1])]

def bashrun(cmd):
	'''Basic bash interface with no logfiles or cwd.'''
	p = subprocess.Popen(cmd,stdout=subprocess.PIPE,stdin=subprocess.PIPE,stderr=subprocess.PIPE,shell=True)
	return p.communicate(input=None)

def findsims(top_prefixes=None,valid_suffixes=None,key_files=None,
	spider=False,timecheck_types=None):

	'''
	Parses all paths in datapaths to search for simulation data and returns a dictionary of base directories
	and valid subdirectories (of the form "basename-vNUM/xNUM-descriptor" e.g. "membrane-v567/s8-sim".
	'''
	
	#--dictionary to hold simulation paths
	simtree = dict()

	#---defaults to specify valid simulation folder prefixes of the form "name-vNUM"
	if top_prefixes == None: top_prefixes = ['membrane','mesomembrane'][:1]
	if valid_suffixes == None: valid_suffixes = ['trr','xtc','tpr','edr']
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
						'''
						#---grab selected file types that match a regex for files on the simulation timeline
						for suf in valid_suffixes:
							valids = [fn for fn in os.listdir(dp+'/'+top+'/'+sd) 
								if re.search(r'^md\.part[0-9]{4}\.'+suf+'$',fn)]
							#---sort by part number
							valids = [valids[k] for k in argsort([int(j[7:11]) for j in valids])]
							if valids != []: simtree[top]['steps'][stepnum][suf] = list(valids)
						#---grab key files
						for kf in key_files:
							valids = [fn for fn in os.listdir(dp+'/'+top+'/'+sd) if fn == kf]
							if valids != []: simtree[top]['steps'][stepnum]['key_files'] = list(valids)
						#---grab concatenated trajectory files
						for suf in traj_suf:
							valids = [fn for fn in os.listdir(dp+'/'+top+'/'+sd) 
								if re.search(r'^md\.part[0-9]{4}\.[0-9]+\-[0-9]+\-[0-9]+\.'+suf+'$',fn)]
							#---sort by part number
							valids = [valids[k] for k in argsort([int(j[7:11]) for j in valids])]
							if valids != []: simtree[top]['steps'][stepnum]['trajs'] = list(valids)							
						'''
						#---find all possible part numbers
						filenames = os.listdir(dp+'/'+top+'/'+sd)
						partfiles = [fn for fn in filenames if re.search(r'^md\.part[0-9]{4}\.',fn)]
						parts = list(set([int(i[7:11]) for i in partfiles]))
						parts = [parts[j] for j in argsort(parts)]
						if len(parts) > 0: simtree[top]['steps'][stepnum]['parts'] = []
						#---for each part number check for available files
						for pn in parts:
							newpart = dict()
							prefix = 'md.part'+'{:04d}'.format(pn)+'.'
							for suf in ['xtc','trr','edr']:
								if prefix+suf in filenames: newpart[suf] = prefix+suf
							simtree[top]['steps'][stepnum]['parts'].append(newpart)
							if spider:
								#---gmxcheck
								typecheck = 'edr'
								if typecheck == 'edr':
									command = ['gmxcheck',
										{'trr':'-f','xtc':'-f','edr':'-e'}[typecheck],
										simtree[top]['root']+'/'+top+'/'+\
										simtree[top]['steps'][stepnum]['dir']+'/'+prefix+typecheck]
									if type(command) == list: command = ' '.join(command)
									p = subprocess.Popen(command,stdout=subprocess.PIPE,
										stdin=subprocess.PIPE,stderr=subprocess.PIPE,shell=True)
									catch = p.communicate(input=None)
									#---only check edr files for time stamps because fast
									if not re.search(
										'WARNING: there may be something wrong with energy file',
										'\n'.join(catch)):
										starttime = perfectregex(catch,r'(index\s+0)',split=None)
										if starttime != -1: starttime = float(starttime.split('t:')[-1])
										endtime = perfectregex(catch,r'^Last energy frame read',split=None)
										if endtime != -1: endtime = float(endtime.split('time')[-1])
										if not any([i == -1 for i in [starttime,endtime]]): 
											stamp = '-'.join([
												str((int(i) if round(i) == i else float(i))) 
												for i in [starttime,endtime]])
											simtree[top]['steps'][stepnum]['parts'][-1]['edrstamp'] = stamp
								elif typecheck == 'trr' or typecheck == 'xtc':
									#---legacy code but this feature is disabled
									starttime = float(perfectregex(catch,
										r'^Reading frame\s+0\s+time\s+[0-9]+\.[0-9]+',num=1,split=4))
									nframes = int(perfectregex(catch,
										r'^Step\s+[0-9]+\s+[0-9]+$',split=1))
									timestep = int(perfectregex(catch,
										r'^Coords\s+[0-9]+\s+[0-9]+$',split=2))
									if any([i == -1 for i in [starttime,nframes,timestep]]): break
									if typecheck+'stamp' not in step.keys(): step[typecheck+'stamp'] = []
									step[typecheck+'stamp'].append('-'.join([
										str((int(i) if round(i) == i else float(i))) for i in 
										[starttime,starttime+nframes*timestep,timestep]]))

						#---grab key files
						for kf in key_files:
							valids = [fn for fn in os.listdir(dp+'/'+top+'/'+sd) if fn == kf]
							if valids != []: simtree[top]['steps'][stepnum]['key_files'] = list(valids)
						#---grab concatenated trajectory files
						for suf in traj_suf:
							valids = [fn for fn in os.listdir(dp+'/'+top+'/'+sd) 
								if re.search(r'^md\.part[0-9]{4}\.[0-9]+\-[0-9]+\-[0-9]+\.'+suf+'$',fn)]
							#---sort by part number
							valids = [valids[k] for k in argsort([int(j[7:11]) for j in valids])]
							if valids != []: simtree[top]['steps'][stepnum]['trajs'] = list(valids)							
							
	#---send dictionary back to controller to write to file
	return simtree
	
def latest_simdat(simname,traj,tpr):

	'''
	Retrieve the latest TPR, TRR, and GRO file for a particular simulation name.
	'''
	
	#---find latest files
	calcfiles = {'trr':None,'tpr':None,'gro':None}
	for si,step in reversed(list(enumerate(simdict[simname]['steps']))):
		if calcfiles['trr'] == None and 'trr' in step.keys() and step['trr'] != []: 
			calcfiles['trr'] = simdict[simname]['root']+'/'+simname+'/'+step['dir']+'/'+step['trr'][0]
		if calcfiles['tpr'] == None and 'tpr' in step.keys() and step['tpr'] != []: 
			calcfiles['tpr'] = simdict[simname]['root']+'/'+simname+'/'+step['dir']+'/'+step['tpr'][0]
		for groname in ['system-input.gro','system.gro']:
			if calcfiles['gro'] == None and 'key_files' in step.keys() \
				and groname in step['key_files']:
				calcfiles['gro'] = simdict[simname]['root']+'/'+simname+'/'+step['dir']+'/'+groname
	return calcfiles
	
def wrap_trjconv(simname,form,stepdir,partfile,start,end,timestep):

	'''
	Function to run trjconv for the make_timeslice function.
	'''
	
	cmd = ' '.join(['trjconv',
		'-f '+simdict[simname]['root']+'/'+simname+'/'+stepdir+'/'+partfile,
		'-o '+simdict[simname]['root']+'/'+simname+'/'+stepdir+'/'+\
			partfile.strip('.'+form)+'_slice.'+form,
		'-b '+str(start),
		'-e '+str(end),
		'-dt '+str(timestep)])
	return bashrun(cmd)
	
def wrap_trjcat(simname,form,timeline):
	
	'''
	Wrapper for trjcat to concatenate trajectory files.
	'''
	
	slicefiles = [simdict[simname]['root']+'/'+simname+'/'+s[0]+\
		'/'+s[1].strip('.'+form)+'_slice.'+form for s in timeline]
	outname = timeline[0][1].strip('.'+form)+'.'+'-'.join([str(i) 
		for i in [timeline[0][2],timeline[-1][3],timeline[0][4]]])+'.'+form
	cmd = ' '.join(['trjcat',
		'-f '+' '.join(slicefiles),
		'-o '+simdict[simname]['root']+'/'+simname+'/'+timeline[0][0]+'/'+outname])
	logdat = bashrun(cmd)
	for s in slicefiles: 
		print 'cleaning up '+str(s)
		os.remove(s)
	return logdat
	
def make_timeslice(simname,stepname,timeseg,form):

	'''
	Make a time slice.\n
	By default it writes the slice to the earliest step directory that holds the trajectory.
	'''
	#---unpack the time segment
	start,end,timestep = [int(i) for i in timeseg.split('-')]
	#---find the correct files
	tl = []
	stepnums = [j['dir'] for j in simdict[simname]['steps']].index(stepname)
	for stepnum in range(stepnums,len(simdict[simname]['steps'])):
		step = simdict[simname]['steps'][stepnum]
		if 'parts' in step.keys():
			for part in step['parts']:
				if form in part.keys() and 'edrstamp' in part.keys():
					seg = [step['dir']]+[part[form]]+[float(i) 
						for i in part['edrstamp'].split('-')]
					if (start <= seg[3] and start >= seg[2]) or (end <= seg[3] and end >= seg[2]):	
						tl.append(seg)
	#---check if the time span is big enough
	if not any([j[2] <= start for j in tl]): raise Exception('except: time segment runs too early')
	if not any([j[3] >= end for j in tl]): raise Exception('except: time segment runs too late')
	#---check continuity, disabled because edr files are sampled more frequently
	if not all([tl[i][3]==tl[i+1][2] for i in range(len(tl)-1)]) and 0: 
		print 'timeline = '+str(tl)
		raise Exception('except: timeline must be seamless')
	#---note that we would normally include a check to make sure that frames are not repeated
	#---...however gromacs covers this by checking for overlapping timestamps
	#---...and in my tests, only selects one copy of each timestep if there are redundancies
	#---...however it would be wise to use these slices with caution
	#---prepare segments
	tl_reduce = []
	if len(tl) > 1:
		tl_reduce.append((tl[0][0],tl[0][1],start,tl[0][3],timestep))
		for t in tl[1:-1]: tl_reduce.append((t[0],t[1],t[2],t[3],timestep))
		tl_reduce.append((tl[-1][0],tl[-1][1],tl[-1][2],end,timestep))
	else: tl_reduce.append((tl[0][0],tl[0][1],start,end,timestep))
	#---report
	print 'time slices = '+str(tl_reduce)
	#---make individual slices
	for t in tl_reduce: wrap_trjconv(simname,form,*t)
	#---concatenate the slices
	wrap_trjcat(simname,form,tl_reduce)


