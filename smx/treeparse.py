#!/usr/bin/python

#---imports
from os.path import expanduser
try: execfile(expanduser('~/.simuluxe_config.py'))
except: print 'config file is absent'
import smx

#---imports 
import copy,glob
import re,subprocess
import numpy as np

#---UTILITY FUNCTIONS
#-------------------------------------------------------------------------------------------------------------

#---classic python argsort
def argsort(seq): return [x for x,y in sorted(enumerate(seq), key = lambda x: x[1])]

def call(command,logfile=None,cwd=None,silent=False,inpipe=None):
	'''
	Wrapper for system calls in a different directory with a dedicated log file.\n
	Note that outsourcing call to codetools produces execution errors.
	'''
	#---needs changed to match the lack of tee functionality in simuluxe
	if inpipe != None:
		output = open(('' if cwd == None else cwd)+logfile,'wb')
		if type(command) == list: command = ' '.join(command)
		p = subprocess.Popen(command,stdout=output,stdin=subprocess.PIPE,stderr=output,cwd=cwd,shell=True)
		catch = p.communicate(input=inpipe)[0]
	else:
		if type(command) == list: command = ' '.join(command)
		if logfile != None:
			output = open(('' if cwd == None else cwd)+logfile,'wb')
			if type(command) == list: command = ' '.join(command)
			if not silent: print 'executing command: "'+str(command)+'" logfile = '+logfile
			try:
				subprocess.check_call(command,
					shell=True,
					stdout=output,
					stderr=output,
					cwd=cwd)
			except: raise Exception('except: execution error')
			output.close()
		else: 
			if not silent: print 'executing command: "'+str(command)+'"'
			if str(sys.stdout.__class__) == "<class 'smx.tools.tee'>": stderr = sys.stdout.files[0]
			else: stderr = sys.stdout
			try: subprocess.check_call(command,shell=True,stderr=stderr,cwd=cwd)
			except: raise Exception('except: execution error')

#---CATALOG
#-------------------------------------------------------------------------------------------------------------

def findsims(top_prefixes=None,valid_suffixes=None,key_files=None,
	spider=False,timecheck_types=None):

	'''
	Parses all paths in datapaths to search for simulation data and returns a dictionary of base directories
	and valid subdirectories (of the form "basename-vNUM/xNUM-descriptor" e.g. "membrane-v567/s8-sim".
	'''
	
	#--dictionary to hold simulation paths
	simtree = dict()

	#---defaults to specify valid simulation folder prefixes of the form "name-vNUM"
	if top_prefixes == None: top_prefixes = ['membrane','protein','mesomembrane'][:2]
	if valid_suffixes == None: valid_suffixes = ['trr','xtc','tpr','edr']
	if key_files == None: key_files = ['system.gro','system-input.gro']
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
							for suf in ['xtc','trr','edr','gro']:
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
										starttime = smx.regcheck(catch,r'(index\s+0)',split=None)
										if starttime != -1: starttime = float(starttime.split('t:')[-1])
										endtime = smx.regcheck(catch,r'^Last energy frame read',split=None)
										if endtime != -1: endtime = float(endtime.split('time')[-1])
										if not any([i == -1 for i in [starttime,endtime]]): 
											stamp = '-'.join([
												str((int(i) if round(i) == i else float(i))) 
												for i in [starttime,endtime]])
											simtree[top]['steps'][stepnum]['parts'][-1]['edrstamp'] = stamp
								elif typecheck == 'trr' or typecheck == 'xtc':
									#---legacy code but this feature is disabled
									starttime = float(smx.regcheck(catch,
										r'^Reading frame\s+0\s+time\s+[0-9]+\.[0-9]+',num=1,split=4))
									nframes = int(smx.regcheck(catch,
										r'^Step\s+[0-9]+\s+[0-9]+$',split=1))
									timestep = int(smx.regcheck(catch,
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
	
#---LOOKUPS
#-------------------------------------------------------------------------------------------------------------
	
def latest_simdat(simname,traj,tpr):

	'''
	Retrieve the latest TPR, TRR, and GRO file for a particular simulation name.
	'''
	
	#---find latest files
	calcfiles = {'trr':None,'tpr':None,'gro':None}
	for si,step in reversed(list(enumerate(smx.simdict[simname]['steps']))):
		if calcfiles['trr'] == None and 'trr' in step.keys() and step['trr'] != []: 
			calcfiles['trr'] = smx.simdict[simname]['root']+'/'+simname+'/'+step['dir']+'/'+step['trr'][0]
		if calcfiles['tpr'] == None and 'tpr' in step.keys() and step['tpr'] != []: 
			calcfiles['tpr'] = smx.simdict[simname]['root']+'/'+simname+'/'+step['dir']+'/'+step['tpr'][0]
		for groname in ['system-input.gro','system.gro']:
			if calcfiles['gro'] == None and 'key_files' in step.keys() \
				and groname in step['key_files']:
				calcfiles['gro'] = smx.simdict[simname]['root']+'/'+simname+'/'+step['dir']+'/'+groname
	return calcfiles
	
def avail(simname=None,slices=False,display=True):
	
	'''
	List available time slices for a simulation according to its root name.
	'''
	
	#---argument handling
	if simname == None or simname == []: simname = smx.simdict.keys()
	elif type(simname) == str: simname = [simname]

	#---result dictionary
	listing = []
	
	if slices:
		#---specifically list the prepared slices
		for sn in simname:
			if 'steps' in smx.simdict[sn].keys():
				for step in smx.simdict[sn]['steps']:
					if 'trajs' in step.keys():
						for traj in step['trajs']:
							if display: print sn.ljust(30,'.')+step['dir'].ljust(20,'.')+traj.ljust(30)
	else:
		#---list slices according to time slices
		dictlist = []
		for sn in simname:
			dictlist.append(copy.deepcopy(smx.simdict[sn]))
			thissim = dictlist[-1]
			for step in [s for s in smx.simdict[sn]['steps'] if 'parts' in s.keys()]:
				for part in step['parts']:
					if 'edrstamp' in part and 'trr' in part:
						ts = part['edrstamp'].split('-')
						listing.append(part)
						if display: 
							print sn.ljust(40,'.')+step['dir'].ljust(30,'.')+part['edr'].ljust(30,'.')+\
								re.sub('\s','.',re.compile(r'(\d)0+$').\
									sub(r'\1',"%16f" % float(ts[0])).ljust(20,'.'))+\
								re.sub('\s','.',re.compile(r'(\d)0+$').\
									sub(r'\1',"%16f" % float(ts[1])))

	#---print results but also return a dictionary
	#---? development note: the returned listing needs more data to specify simname and step
	return listing
	
def getslice(simname,trajslice):
	
	'''
	Return a structure and trajectory given the trajectory slice name.
	'''
	
	for step in smx.simdict[simname]['steps'][::-1]:
		if 'key_files' in step.keys() and 'system-input.gro' in step['key_files']:
			grofile = smx.simdict[simname]['root']+'/'+simname+'/'+step['dir']+'/system-input.gro'
			break 
	stepname = [step['dir'] for step in smx.simdict[simname]['steps']
		if 'trajs' in step.keys() and trajslice in step['trajs']][0]
	trajname = smx.simdict['membrane-v532']['root']+'/'+simname+'/'+stepname+'/'+trajslice
	return grofile,trajname


#---TIME SLICE
#-------------------------------------------------------------------------------------------------------------
	
def timeslice(simname,step,time,form,path=None,pathletter='a',extraname=''):

	'''
	Make a time slice.\n
	By default it writes the slice to the earliest step directory that holds the trajectory.
	'''

	#---note currently set to do one slice at a time
	if type(step) == list and len(step) == 1 and len(step[0]) == 1: step = step[0][0]
	if type(simname) == list and len(simname) == 1: simname = simname[0]
	elif type(simname) == list and len(simname) != 1: raise Exception('except: invalid selections')

	#---unpack the timestamp
	start,end,timestep = [int(i) for i in time.split('-')]

	#---generate timeline from relevant files
	tl = []
	stepnums = [j['dir'] for j in smx.simdict[simname]['steps']].index(step)
	for stepnum in range(stepnums,len(smx.simdict[simname]['steps'])):
		stepdict = smx.simdict[simname]['steps'][stepnum]
		if 'parts' in stepdict.keys():
			for part in stepdict['parts']:
				if form in part.keys() and 'edrstamp' in part.keys():
					seg = [stepdict['dir']]+[part[form]]+[float(i) 
						for i in part['edrstamp'].split('-')]+[timestep]
					if (start <= seg[3] and start >= seg[2]) or (end <= seg[3] and end >= seg[2]) or \
						(start <= seg[2] and end >= seg[3]):
						#---modifications to the timeline to match the request
						if start <= seg[3] and start >= seg[2]: t0 = start
						else: t0 = int(seg[2]/timestep+1)*timestep
						if end <= seg[3] and end >= seg[2]: t1 = end
						else: t1 = int(seg[3]/timestep)*timestep
						seg[2:4] = t0,t1
						tl.append(seg)
	#---check if the time span is big enough
	if not any([j[2] <= start for j in tl]): raise Exception('except: time segment runs too early')
	if not any([j[3] >= end for j in tl]): raise Exception('except: time segment runs too late')
	#---check that the target segments provide a range with the correct intervals
	if not all(np.concatenate([np.arange(i[2],i[3]+timestep,timestep) for i in tl]) == \
		np.arange(start,end+timestep,timestep)):
		raise Exception('except: timestamps not aligned')
		
	#---default final file is in the directory of the first relevant trajectory file
	outname = tl[0][1].strip('.'+form)+'.'+'-'.join([str(i) 
		for i in [tl[0][2],tl[-1][3],tl[0][4]]])+('.'+extraname if extraname != '' else '')+'.'+form
	if path != None:
		if pathletter == None: regex = '^[a-z]([0-9]{1,2})-(.+)'
		else: regex = '^['+pathletter+']([0-9]{1,2})-(.+)'
		#---if a path is given we write to the corresponding folder
		if not re.match(regex,path):
			#---if the path is not already available we mkdir with a new sequential number
			#---the following codeblock was taken from automacs/chain_step
			for root,dirnames,filenames in os.walk(smx.simdict[simname]['root']+'/'+simname): break
			stepdirs = [i for i in dirnames if re.match(regex,i)]
			stepnums = [int(re.findall(regex,i)[0][0]) for i in stepdirs]
			oldsteps = [stepdirs[i] for i in argsort(
				[int(re.findall(regex,i)[0][0]) for i in stepdirs])]
			if oldsteps != []: startstep = int(re.findall(regex,oldsteps[-1])[0][0])
			else: startstep = 0
			storedir = smx.simdict[simname]['root']+'/'+simname+'/'+\
				pathletter+str('%02d'%(startstep+1))+'-'+path
		else: storedir = smx.simdict[simname]['root']+'/'+simname+'/'+path
		if not os.path.abspath(storedir): 
			print 'making directory: '+str(os.path.abspath(storedir))
			os.mkdir(os.path.abspath(storedir))
		final_name = smx.simdict[simname]['root']+'/'+simname+'/'+path+'/'+outname
		cwd = smx.simdict[simname]['root']+'/'+simname+'/'+path+'/'
	else: 
		final_name = smx.simdict[simname]['root']+'/'+simname+'/'+tl[0][0]+'/'+outname
		cwd = smx.simdict[simname]['root']+'/'+simname+'/'+tl[0][0]+'/'
	
	#---check if file already exists
	if os.path.isfile(final_name): raise Exception('except: target file exists: '+final_name)
	if os.path.isfile(final_name[:-4]+'.gro'): raise Exception('except: target gro file exists: '+final_name)
	
	#---report
	print 'time slices = '+str(tl)
	#---make individual slices
	for ti in range(len(tl)):
		stepdir,partfile,start,end,timestep = tl[ti]
		cmd = ' '.join(['trjconv',
			'-f '+smx.simdict[simname]['root']+'/'+simname+'/'+stepdir+'/'+partfile,
			'-o '+partfile.strip('.'+form)+'_slice.'+form,
			'-b '+str(start),
			'-e '+str(end),
			'-dt '+str(timestep)])
		call(cmd,logfile='log-timeslice-'+stepdir+'-'+partfile.strip('.'+form)+'.log',cwd=cwd)
		#---save a gro file
		if ti == 0:
			cmd = ' '.join(['trjconv',
				'-f '+smx.simdict[simname]['root']+'/'+simname+'/'+stepdir+'/'+partfile,
				'-o '+final_name[:-4]+'.gro',
				'-b '+str(start),
				'-e '+str(start),
				'-dt '+str(timestep)])
			call(cmd,logfile='log-timeslice-'+stepdir+'-'+partfile.strip('.'+form)+'.log',cwd=cwd)

	#---concatenate the slices
	slicefiles = [cwd+s[1].strip('.'+form)+'_slice.'+form for s in tl]
	cmd = ' '.join(['trjcat',
		'-f '+' '.join(slicefiles),
		'-o '+final_name])
	call(cmd,logfile='log-timeslice-trjcat-'+\
		'-'.join([str(i) for i in [start,end,timestep]])+'.log',cwd=cwd)
	for s in slicefiles: 
		print 'cleaning up '+str(s)
		os.remove(s)

