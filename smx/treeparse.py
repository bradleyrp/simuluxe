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
import datetime,time

#---import codetools
from codetools import *

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

	catted_re = r'^md\.part[0-9]{4}\.[0-9]+\-[0-9]+\-[0-9]+(\.[a-z,A-Z,0-9,_]+)(\.[a-z,A-Z,0-9,_]+)?\.'

	#---search all datapaths for simulations
	for dp in datapaths:
		tops = [f for f in os.listdir(dp+'/') for top in top_prefixes if re.search(r'^'+top+'\-v.+', f)]
		for top in tops:
			for (dirpath, dirnames, filenames) in os.walk(dp+'/'+top):
				#---only parse one level
				if dirpath == dp+'/'+top:
					simtree[top] = dict()
					simtree[top]['root'] = dp
					steplist = [dn for dn in dirnames if re.search(r'^[a-z][0-9]{1,2}\-.+',dn)]
					#---old method
					steplist = [steplist[j] for j in argsort([int(i[1:].split('-')[0]) for i in steplist])]
					#---the following ord hack will sort first by letter then by number
					#---...which allows backwards compatibility with directories 
					#---...named e.g. s8-kraken t1-trestles but is redundant for new simulations which
					#---...use 2-digits e.g. s12-walnut (this was necessary because step ordering matters in 
					#---...timeslice functions
					steplist = [steplist[j] for j in smx.argsort([(ord(i[0])-96)*26+int(i[1:].split('-')[0]) 
						for i in steplist])]
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
								if re.search(catted_re+suf+'$',fn)]
							#---sort by part number
							valids = [valids[k] for k in argsort([int(j[7:11]) for j in valids])]
							if valids != []: 
								if 'trajs' in simtree[top]['steps'][stepnum].keys():
									simtree[top]['steps'][stepnum]['trajs'].extend(list(valids))
								else:
									simtree[top]['steps'][stepnum]['trajs'] = list(valids)
						#---grab gro files for concatenated trajectory files
						for suf in ['gro']:
							valids = [fn for fn in os.listdir(dp+'/'+top+'/'+sd) 
								if re.search(catted_re+suf+'$',fn)]
							#---sort by part number
							valids = [valids[k] for k in argsort([int(j[7:11]) for j in valids])]
							if valids != []: 
								if 'trajs_gro' in simtree[top]['steps'][stepnum].keys():
									simtree[top]['steps'][stepnum]['trajs_gro'].extend(list(valids))
								else:
									simtree[top]['steps'][stepnum]['trajs_gro'] = list(valids)
						
	#---send dictionary back to controller to write to file
	return simtree
	
#---LOOKUPS
#-------------------------------------------------------------------------------------------------------------
	
def get_slices(simname,groupname=None,timestamp=None,unique=True,pbcmol=False,wrap=None):
	
	'''
	Return all post-processed slices of a simulation.
	'''
	
	#---note that this code is clumsy and needs reworked to be more general
	
	slist = []
	re_group_timestamp = '^md\.part[0-9]{4}\.([0-9]+)\-([0-9]+)\-([0-9]+)\.([a-z,A-Z,0-9,_]+)'+\
		'\.?([a-z,A-Z,0-9,_]+)?\.[a-z]{3}'
	for s in smx.simdict[simname]['steps']:
		rootdir = smx.simdict[simname]['root']
		if 'trajs' in s.keys():
			for t in s['trajs']:
				if 'trajs_gro' in s.keys() and t[:-3]+'gro' in s['trajs_gro']:
					add = False
					regex = re.compile(re_group_timestamp)
					if groupname == None and timestamp == None and wrap == None: add = True
					elif groupname != None and timestamp == None and wrap == None:
						if regex.match(t) and regex.findall(t)[3] == groupname: add = True
					elif groupname == None and timestamp != None and wrap == None:
						if regex.match(t) and '-'.join(regex.findall(t)[0][:3]) == timestamp: add = True
					elif groupname != None and timestamp != None and wrap == None:
						if regex.match(t) and regex.findall(t)[0][3]==groupname and \
						'-'.join(regex.findall(t)[0][:3])==timestamp: add = True
					elif groupname == None and timestamp != None and wrap != None:
						if regex.match(t) and '-'.join(regex.findall(t)[0][:3]) == timestamp and \
						regex.findall(t)[0][4] == wrap: add = True
					elif groupname != None and timestamp != None and wrap != None:
						if regex.match(t) and regex.findall(t)[0][3]==groupname and \
						'-'.join(regex.findall(t)[0][:3])==timestamp and \
						regex.findall(t)[0][4] == wrap: add = True
					if add: 
						slist.append((
							rootdir+'/'+simname+'/'+s['dir']+'/'+t[:-3]+'gro',
							rootdir+'/'+simname+'/'+s['dir']+'/'+t))
	if unique and len(slist) != 1: raise Exception('except: non-unique slices available: '+str(slist))
	elif unique: return slist[0]
	else: return slist
			
def avail(simname=None,slices=False,display=True):
	
	'''
	List available time slices for a simulation according to its root name.
	'''

	#---argument handling
	if simname == None or simname == []: simname = smx.simdict.keys()
	elif type(simname) == str: simname = [simname]

	#---result dictionary
	listing = []
	paths = {}
	if slices:
		#---specifically list the prepared slices
		for sn in simname:
			paths_sim = {}
			if 'steps' in smx.simdict[sn].keys():
				for step in smx.simdict[sn]['steps'][::-1]:
					if 'trajs' in step.keys():
						paths_sim['trajs'] = []
						for traj in step['trajs']:
							if display:
								print sn.ljust(30,'.')+step['dir'].ljust(20,'.')+traj.ljust(30)
							paths_sim['trajs'].append(sn+'/'+step['dir']+'/'+traj)							
					if 'key_files' in step.keys() and 'gro' not in paths_sim.keys():
						paths_sim['gro'] = sn+'/'+step['dir']+'/'+step['key_files'][0]
			if paths_sim != {}: paths[sn] = copy.deepcopy(paths_sim)
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
	return paths
	
#---TIME SLICE
#-------------------------------------------------------------------------------------------------------------
	
def timeslice(simname,step,time,form,path=None,pathletter='a',extraname='',selection=None,
	pbcmol=False):

	'''
	Make a time slice.\n
	By default it writes the slice to the earliest step directory that holds the trajectory.
	'''
	
	if selection != None and extraname == '': 
		raise Exception('must specify extraname for specific selection.')

	#---note currently set to do one slice at a time
	if type(step) == list and len(step) == 1 and len(step[0]) == 1: step = step[0][0]
	if type(simname) == list and len(simname) == 1: simname = simname[0]
	elif type(simname) == list and len(simname) != 1: print ('except: invalid selections')

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
	if not any([j[2] <= start for j in tl]): print ('except: time segment runs too early')
	if not any([j[3] >= end for j in tl]): print ('except: time segment runs too late')

	#---in some edge cases the simulation starts from an earlier time so we use the more recent slice
	for i in range(len(tl)-1):
		if tl[i][3] > tl[i+1][2]:
			tl[i][3] = tl[i+1][2]-timestep

	#---check for desired timestamps
	times_observed = np.concatenate([np.arange(i[2],i[3]+timestep,timestep) for i in tl])
	times_desired = np.arange(start,end+timestep,timestep)
	if not len(times_desired)==len(times_observed) or \
		not all([times_observed[i]==times_desired[i] for i in range(len(times_observed))]):
		print 'observed = '+str(list(times_observed))
		print 'desired = '+str(list(times_desired))
		if abs(len(times_observed)-len(times_desired)) <=3:
			print 'warning: timestamps not aligned but will try anyway (may be faulty edr file)'
		else: print ('except: timestamps not aligned')
		
	#---default final file is in the directory of the first relevant trajectory file
	outname = tl[0][1].strip('.'+form)+'.'+'-'.join([str(i)
		for i in [tl[0][2],tl[-1][3],tl[0][4]]])+\
		('.'+extraname if extraname != '' else '')+\
		('.pbcmol' if pbcmol else '')+'.'+form
	if path != None:
		if pathletter == None: regex = '^[a-z]([0-9]{1,2})-(.+)'
		else: regex = '^['+pathletter+']([0-9]{1,2})-(.+)'
		fulldirs = glob.glob(smx.simdict[simname]['root']+'/'+simname+'/*')
		dirs = [list(re.findall(regex,os.path.basename(i))[0])+[i] for i in fulldirs
			if re.match(regex,os.path.basename(i))]
		#---search for numbered directory with the desired path
		if any([i[1] == path for i in dirs]):
			cwd = os.path.abspath(dirs[argsort([int(i[0]) for i in dirs])[-1]][2])
			storedir = cwd
			final_name = cwd+outname
		#---otherwise search for the path directly in case the user has supplied an explicit number
		elif not re.match(regex,path):
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
		if not os.path.isdir(os.path.abspath(storedir)):
			print 'making directory: '+str(os.path.abspath(storedir))
			os.mkdir(os.path.abspath(storedir))
		final_name = storedir+'/'+outname
		cwd = storedir+'/'
	else: 
		final_name = smx.simdict[simname]['root']+'/'+simname+'/'+tl[0][0]+'/'+outname
		cwd = smx.simdict[simname]['root']+'/'+simname+'/'+tl[0][0]+'/'
	
	#---check if file already exists
	#---? check both gro and trajectory before continuing
	if os.path.isfile(final_name) or os.path.isfile(final_name[:-4]+'.gro'): 
		print 'ignoring target file which exists: '+final_name
		return

	#---generate system.gro file for the full system
	if selection != None:
		stepdir,partfile,start,end,timestep = tl[0]
		systemgro = cwd+final_name[:-4]+'.all.gro'
		cmd = ' '.join(['trjconv',
			'-f '+smx.simdict[simname]['root']+'/'+simname+'/'+stepdir+'/'+partfile,
			'-s '+smx.simdict[simname]['root']+'/'+simname+'/'+stepdir+'/'+partfile[:-4]+'.tpr',
			'-o '+systemgro,
			'-b '+str(start),
			'-e '+str(start),
			'-dt '+str(timestep)])
		call(cmd,logfile='log-timeslice-'+stepdir+'-'+partfile.strip('.'+form)+'-gro-all.log',
		    cwd=cwd,inpipe='0\n')
		#---create group file
		cmd = ' '.join(['make_ndx',
			'-f '+systemgro,
			'-o index-'+extraname+'.ndx'])
		call(cmd,logfile='log-timeslice-'+stepdir+'-'+partfile.strip('.'+form)+'-make-ndx',
		    cwd=cwd,inpipe='keep 0\n'+selection+'\nkeep 1\nq\n')
		os.remove(systemgro)
	
	#---report
	print 'time slices = '+str(tl)
	
	#---make individual slices
	for ti in range(len(tl)):
		stepdir,partfile,start,end,timestep = tl[ti]
		cmd = ' '.join(['trjconv',
			'-f '+smx.simdict[simname]['root']+'/'+simname+'/'+stepdir+'/'+partfile,
			'-o '+partfile.strip('.'+form)+'_slice.'+form,
			('-pbc mol' if pbcmol else ''),
			('-n index-'+extraname+'.ndx' if selection != None else ''),
			('-s '+smx.simdict[simname]['root']+'/'+simname+'/'+stepdir+'/'+partfile[:-4]+'.tpr'
				if selection != None or pbcmol else ''),
			'-b '+str(start),
			'-e '+str(end),
			'-dt '+str(timestep)])
		print "Running " + cmd
		print cwd
		call(cmd,logfile='log-timeslice-'+stepdir+'-'+partfile.strip('.'+form)+'.log',
			cwd=cwd,inpipe=(None if selection != None else '0\n'))
		#---save a gro file on the first part of the time slice
		if ti == 0:
			cmd = ' '.join(['trjconv',
				'-f '+smx.simdict[simname]['root']+'/'+simname+'/'+stepdir+'/'+partfile,
				'-o '+final_name[:-4]+'.gro',
				('-pbc mol' if pbcmol else ''),
				('-n index-'+extraname+'.ndx' if selection != None else ''),
				'-s '+smx.simdict[simname]['root']+'/'+simname+'/'+stepdir+'/'+partfile[:-4]+'.tpr',
				'-b '+str(start),
				'-e '+str(start),
				'-dt '+str(timestep)])
			call(cmd,logfile='log-timeslice-'+stepdir+'-'+partfile.strip('.'+form)+'-gro.log',
                cwd=cwd,inpipe=(None if selection != None else '0\n'))

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

