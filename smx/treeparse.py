#!/usr/bin/python

#---imports
from os.path import expanduser
try: execfile(expanduser('~/.simuluxe_config.py'))
except: print 'config file is absent'
from smx.codetools import *

#---imports 
import copy,glob
import re,subprocess
import numpy as np
import datetime,time

#---gromacs executable names
def gmxpaths(pname): return pname+''

#---CATALOG
#-------------------------------------------------------------------------------------------------------------

def findsims(top_prefixes=None,valid_suffixes=None,key_files=None,
	spider=False,timecheck_types=None,roots=None,no_slices=False):

	"""
	Parses all paths in datapaths to search for simulation data and returns a dictionary of base directories
	and valid subdirectories (of the form "basename-vNUM/xNUM-descriptor" e.g. "membrane-v567/s8-sim".
	"""
	
	#--dictionary to hold simulation paths
	simtree = dict()

	#---defaults to specify valid simulation folder prefixes of the form "name-vNUM"
	if top_prefixes == None: top_prefixes = ['membrane','protein','mesomembrane'][:2]
	if valid_suffixes == None: valid_suffixes = ['trr','xtc','tpr','edr']
	if key_files == None: key_files = ['system.gro','system-input.gro']
	traj_suf = ['trr','xtc']

	#catted_re = \
	#	r'^md\.part[0-9]{4}\.[0-9]+\-[0-9]+\-[0-9]+(\.[a-z,A-Z,0-9,_,-]+)?(\.[a-z,A-Z,0-9,_,-]+)?\.?'
	catted_re = '^md'+\
		'\.?([a-z][0-9]{1,2})?'+\
		'.part[0-9]{4}\.([0-9]+)\-([0-9]+)\-([0-9]+)'+\
		'\.?([a-z,A-Z,0-9,_,-]+)?'+\
		'\.?([a-z,A-Z,0-9,_,-]+)?'+\
		'\.?'
	#---search all datapaths for simulations
	if roots == None: roots = datapaths
	for dp in roots:
		tops = [f for f in os.listdir(dp+'/') for top in top_prefixes if re.search(r'^'+top+'\-v.+', f)]
		for top in tops:
			for (dirpath, dirnames, filenames) in os.walk(dp+'/'+top):
				#---only parse one level
				if dirpath == dp+'/'+top:
					simtree[top] = dict()
					#---devolve root to step: simtree[top]['root'] = dp
					steplist = [dn for dn in dirnames if re.search(r'^[a-z][0-9]{1,2}\-.+',dn)]
					#---old method
					steplist = [steplist[j] for j in argsort([int(i[1:].split('-')[0]) for i in steplist])]
					#---the following ord hack will sort first by letter then by number
					#---...which allows backwards compatibility with directories 
					#---...named e.g. s8-kraken t1-trestles but is redundant for new simulations which
					#---...use 2-digits e.g. s12-walnut (this was necessary because step ordering matters in 
					#---...timeslice functions
					steplist = [steplist[j] for j in argsort([(ord(i[0])-96)*26+int(i[1:].split('-')[0]) 
						for i in steplist])]
					#---devolve root to the level of dir
					simtree[top]['steps'] = [{'dir':step,'root':dp} for step in steplist]
					#---loop over subdirectories
					for stepnum,sd in enumerate(steplist):
						#---find all possible part numbers
						filenames = os.listdir(dp+'/'+top+'/'+sd)
						partfiles = [fn for fn in filenames 
							if re.search(r'^md\.?([a-z][0-9]{1,2})?\.part[0-9]{4}\.',fn)]
						parts = list(set([
							int(re.findall(r'^md\.?([a-z][0-9]{1,2})?\.part([0-9]{4})\.',i)[0][-1])
							for i in partfiles]))
						parts = [parts[j] for j in argsort(parts)]
						if len(parts) > 0: simtree[top]['steps'][stepnum]['parts'] = []
						#---for each part number check for available files
						for pn in parts:
							newpart = dict()
							prefix = 'md.part'+'%04d'%pn+'.'
							for suf in ['xtc','trr','edr','gro']:
								if prefix+suf in filenames: newpart[suf] = prefix+suf
							simtree[top]['steps'][stepnum]['parts'].append(newpart)
							if spider:
								#---gmxcheck
								typecheck = 'edr'
								if typecheck == 'edr':
									#---devolved root below
									command = [gmxpaths('gmxcheck'),
										{'trr':'-f','xtc':'-f','edr':'-e'}[typecheck],
										simtree[top]['steps'][stepnum]['root']+'/'+top+'/'+\
										simtree[top]['steps'][stepnum]['dir']+'/'+prefix+typecheck]
									if type(command) == list: command = ' '.join(command)
									p = subprocess.Popen(command,stdout=subprocess.PIPE,
										stdin=subprocess.PIPE,stderr=subprocess.PIPE,shell=True)
									catch = p.communicate(input=None)
									#---only check edr files for time stamps because fast
									if not re.search(
										'WARNING: there may be something wrong with energy file',
										'\n'.join(catch)):
										starttime = regcheck(catch,r'(index\s+0)',split=None)
										if starttime != -1: starttime = float(starttime.split('t:')[-1])
										endtime = regcheck(catch,r'^Last energy frame read',split=None)
										if endtime != -1: endtime = float(endtime.split('time')[-1])
										if not any([i == -1 for i in [starttime,endtime]]): 
											stamp = '-'.join([
												str((int(i) if round(i) == i else float(i))) 
												for i in [starttime,endtime]])
											simtree[top]['steps'][stepnum]['parts'][-1]['edrstamp'] = stamp
								elif typecheck == 'trr' or typecheck == 'xtc':
									#---legacy code but this feature is disabled
									starttime = float(regcheck(catch,
										r'^Reading frame\s+0\s+time\s+[0-9]+\.[0-9]+',num=1,split=4))
									nframes = int(regcheck(catch,
										r'^Step\s+[0-9]+\s+[0-9]+$',split=1))
									timestep = int(regcheck(catch,
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
						#---disable addition of slices when simdict-time and simdict-slices are separate
						if not no_slices:
							#---grab concatenated trajectory files
							for suf in traj_suf:
								valids = [fn for fn in os.listdir(dp+'/'+top+'/'+sd) 
									if re.search(catted_re+suf+'$',fn)]
								#---sort by part number
								valids = [valids[k] for k in argsort([
									int(re.findall(r'^md\.?([a-z][0-9]{1,2})?\.part([0-9]{4})\.',j)[0][-1])
									for j in valids])]
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
								valids = [valids[k] for k in argsort([
									int(re.findall(r'^md\.?([a-z][0-9]{1,2})?\.part([0-9]{4})\.',j)[0][-1])
									for j in valids])]
								if valids != []: 
									if 'trajs_gro' in simtree[top]['steps'][stepnum].keys():
										simtree[top]['steps'][stepnum]['trajs_gro'].extend(list(valids))
									else:
										simtree[top]['steps'][stepnum]['trajs_gro'] = list(valids)
						
	#---send dictionary back to controller to write to file
	return simtree
	
#---LOOKUPS
#-------------------------------------------------------------------------------------------------------------
	
def get_slices(simname,simdict,groupname=None,timestamp=None,
	step=None,unique=True,wrap=None,verbose=False,**kwargs):
	
	"""
	Find all post-processed slices of a simulation.
	"""
	
	slist = []
	re_group_timestamp = '^md'+\
		'\.?([a-z][0-9]{1,2})?'+\
		'.part[0-9]{4}\.([0-9]+)\-([0-9]+)\-([0-9]+)'+\
		'\.?([a-z,A-Z,0-9,_,-]+)?'+\
		'\.?([a-z,A-Z,0-9,_,-]+)?'+\
		'\.[a-z]{3}'
	nm = {'groupname':4,'timestamp':slice(1,4),'wrap':5,'step':0}
	regex = re.compile(re_group_timestamp)
	for s in simdict[simname]['steps']:
		#---devolved root: rootdir = simdict[simname]['root']
		rootdir = s['root']
		if 'trajs' in s.keys():
			for t in s['trajs']:
				if 'trajs_gro' in s.keys() and t[:-3]+'gro' in s['trajs_gro']:
					nd = regex.findall(t)[0]
					fits = [
						(wrap==None or nd[nm['wrap']]==wrap),
						(step==None or nd[nm['step']]==re.findall('^([a-z][0-9]{1,2})-',step)),
						(timestamp==None or timestamp=='-'.join(nd[nm['timestamp']])),
						((groupname in ['all','',None] and nd[nm['groupname']] in ['all','',None]) 
							or (groupname==nd[nm['groupname']])),
						]
					if all(fits):
						slist.append((rootdir+'/'+simname+'/'+s['dir']+'/'+t[:-3]+'gro',
							rootdir+'/'+simname+'/'+s['dir']+'/'+t))
	if slist == []: return (None,None)
	elif unique and len(slist) > 1: raise Exception('non-unique slices available: slist = '+str(slist))
	elif unique and len(slist) == 1: return slist[0]
	elif not unique and len(slist)>1: return slist

def find_missing_slices(simdict,calculations,comparisons,metadat,name=None,useful=False):

	"""
	Given a simdict and a calculations dictionary, return a list of slices which cannot be found.
	"""
	
	#---user must include project=project-NAME flag on the command line
	missing_slices,useful_slices = [],[]
	for compsign in calculations.keys():
		#---filter comparisons
		focus = dict([(comp,dict([(i,calculations[compsign]['timeslices'][i]) 
			for i in calculations[compsign]['timeslices'] 
			if i in comparisons[comp]])) 
			for comp in calculations[compsign]['comparisons']])
		for panel in focus:
			sns = focus[panel] if name == None else [i for i in focus[panel] if i==name]
			for sn in sns:
				if not 'multislice' in calculations[compsign].keys():
					multislices = [dict([(k,calculations[compsign][k]) 
						for k in ['groupname','wrap','select_ndx'] 
						if k in calculations[compsign]])]
				else: multislices = calculations[compsign]['multislice']
				if type(focus[panel][sn])==list: timestamps = [
					dict(time=t['time'],step=t['step']) for t in focus[panel][sn]]
				else: timestamps = [focus[panel][sn]]
				for ms in multislices:
					for timestamp in timestamps:
						#---check to be sure that there is no conflict between groupname and selection
						selection = ms['select_ndx'] if 'select_ndx' in ms.keys() else None
						if ms['groupname'] in ['all','',None] and 'select_ndx' in ms.keys() and \
							'select_ndx' != None:
							raise Exception('cannot have a groupname that asks for the entire system '+\
								'(e.g. \'\', None, or \'all\' without setting '+\
								'select_ndx to None')
						#---get slice information
						grofile,trajfile = get_slices(sn,simdict,
							timestamp=timestamp['time'],wrap=ms['wrap'],
							groupname=ms['groupname'],metadat=metadat[sn])
						if (grofile,trajfile) == (None,None) or useful:
							new_ms = dict(calc=compsign,simname=sn,
								timestamp=timestamp['time'],
								wrap=ms['wrap'],groupname=ms['groupname'],
								step=timestamp['step'])
							if 'select_ndx' in ms.keys(): new_ms['select_ndx'] = ms['select_ndx']						
						if (grofile,trajfile) == (None,None): missing_slices.append(new_ms)
						elif useful and (grofile,trajfile) != (None,None): 
							new_ms['grofile'] = grofile
							new_ms['trajfile'] = trajfile
							useful_slices.append(new_ms)
	if useful: return missing_slices,useful_slices
	else: return missing_slices

#---TIME SLICE
#-------------------------------------------------------------------------------------------------------------
	
def timeslice(simname,step,time,form,path=None,pathletter='a',extraname='',selection=None,
	pbcmol=False,wrap=None,simdict=None,disable_timecheck=True,infofile=None,metadat=None):

	"""
	Make a time slice.\n
	By default it writes the slice to the earliest step directory that holds the trajectory.
	"""
	
	print '\n+'.ljust(39,'-')+'+\n|'+'TIMESLICE'.center(37)+'|\n+'.ljust(40,'-')+'+'

	if infofile != None: 
		get_simdict = {}
		execfile(os.path.abspath(os.path.expanduser(infofile)),get_simdict)
		simdict = get_simdict['simdict']
	elif simdict == None: raise Exception('cannot locate simdict')
	
	if selection != None and extraname in ['','all',None]: 
		raise Exception('must specify extraname for specific selection.')
		
	#---handle wrap keyword for consistency with get_slices
	if wrap == 'pbcmol': pbcmol = True
	elif wrap == None: pbcmol = False

	#---note currently set to do one slice at a time
	if type(step) == list and len(step) == 1 and len(step[0]) == 1: step = step[0][0]
	if type(simname) == list and len(simname) == 1: simname = simname[0]
	elif type(simname) == list and len(simname) != 1: status('[WARNING] invalid selections')

	#---unpack the timestamp
	start,end,timestep = [int(i) for i in time.split('-')]
	
	#---generate timeline from relevant files
	tl = []
	stepnums = [j['dir'] for j in simdict[simname]['steps']].index(step)
	for stepnum in range(stepnums,len(simdict[simname]['steps'])):
		stepdict = simdict[simname]['steps'][stepnum]
		if 'parts' in stepdict.keys():
			for part in stepdict['parts']:
				if form in part.keys() and 'edrstamp' in part.keys():
					#---devolve root to step objects by adding root here 
					seg = [stepdict['dir']]+[part[form]]+[float(i) 
						for i in part['edrstamp'].split('-')]+[timestep]+[stepdict['root']]
					if (start <= seg[3] and start >= seg[2]) or (end <= seg[3] and end >= seg[2]) or \
						(start <= seg[2] and end >= seg[3]):
						#---modifications to the timeline to match the request
						if start <= seg[3] and start >= seg[2]: t0 = start
						else: t0 = int(seg[2]/timestep+1)*timestep
						if end <= seg[3] and end >= seg[2]: t1 = end
						else: t1 = int(seg[3]/timestep)*timestep
						seg[2:4] = t0,t1
						tl.append(seg)
					
	status('[REPORT] timeline = '+str(tl))
	#---check if the time span is big enough
	if not any([j[2] <= start for j in tl]): status('[WARNING] time segment runs too early')
	if not any([j[3] >= end for j in tl]): status('[WARNING] time segment runs too late')

	#---in some edge cases the simulation starts from an earlier time so we use the more recent slice
	for i in range(len(tl)-1):
		if tl[i][3] > tl[i+1][2]:
			tl[i][3] = tl[i+1][2]-timestep

	#---check for desired timestamps
	times_observed = np.concatenate([np.arange(i[2],i[3]+timestep,timestep) for i in tl])
	times_desired = np.arange(start,end+timestep,timestep)
	if not len(times_desired)==len(times_observed) or \
		not all([times_observed[i]==times_desired[i] for i in range(len(times_observed))]):
		if abs(len(times_observed)-len(times_desired)) <=3:
			status('[WARNING] timestamps not aligned but will try anyway (may be faulty edr file)')
		else: status('[WARNING] timestamps not aligned')
	for ti,t in enumerate(tl[:-1]):
		if tl[ti+1][2] <= tl[ti][3]: tl[ti+1][2] = tl[ti][3]+tl[ti][4]
	#---default final file is in the directory of the first relevant trajectory file
	#---updated naming scheme uses step directory code as a prefix to handle replicates
	stepcode = re.findall('^([a-z][0-9]{1,2})',tl[0][0])[0]
	partcode = re.findall('^md\.part([0-9]{4})',tl[0][1])[0]
	outname = 'md.'+stepcode+'.part'+partcode+'.'+'-'.join([str(i)
		for i in [tl[0][2],tl[-1][3],tl[0][4]]])+\
		('.'+extraname if extraname not in ['',None] else '')+\
		('.pbcmol' if pbcmol else '')+'.'+form

	#---decide write location
	if path != None:
		#---force a starting letter on the write path
		if pathletter == None: regex = '^[a-z]([0-9]{1,2})-(.+)'
		else: regex = '^['+pathletter+']([0-9]{1,2})-(.+)'
		#---we search for the desired path in the root that matches the first segment
		possible_roots = [tl[0][-1]]
		fulldirs = [i for j in [glob.glob(rd+'/'+simname+'/*') for rd in possible_roots] for i in j]
		dirs = [list(re.findall(regex,os.path.basename(i))[0])+[i] for i in fulldirs
			if re.match(regex,os.path.basename(i))]
		#---use exact path if any match
		if any([i[1] == path for i in dirs]):
			dirs_trim = [i for i in dirs if i[1] == path]
			cwd = os.path.abspath(dirs_trim[argsort([int(i[0]) for i in dirs_trim])[-1]][2])+'/'
			storedir = cwd
			final_name = cwd+outname
		#---otherwise search for the path directly in case the user has supplied an explicit number
		elif not re.match(regex,path):
			#---if the path is not already available we mkdir with a new sequential number
			#---the following codeblock was taken from automacs/chain_step
			#---search for the highest-numbered folder with the right path. we only perform this search
			#---...in the same root directory (e.g. an element of the global datapaths list) which also hosts
			#---...the step directory of the first step in the slice. This means that if you don't have a 
			#---...postproc directory and you send a path='postproc' to timeslice (the preferred convention)
			#---...then this function will make a new postproc directory under the same root/datapaths
			#---...directory as the step from which the slice starts. This makes the most sense because
			#---...the code currently cannot switch "root" directories to continue a slice hence you can
			#---...only make a slice entirely within one root (however the slice can continue across multiple)
			#---...step directories if you want. remember that the set of root directories is the datapaths
			rootdir = tl[0][-1]
			for root,dirnames,filenames in os.walk(rootdir+'/'+simname): break
			stepdirs = [i for i in dirnames if re.match(regex,i)]
			stepnums = [int(re.findall(regex,i)[0][0]) for i in stepdirs]
			oldsteps = [stepdirs[i] for i in argsort(
				[int(re.findall(regex,i)[0][0]) for i in stepdirs])]
			if oldsteps != []: startstep = int(re.findall(regex,oldsteps[-1])[0][0])
			else: startstep = 0
			storedir = rootdir+'/'+simname+'/'+\
				pathletter+str('%02d'%(startstep+1))+'-'+path
			final_name = storedir+'/'+outname
			cwd = storedir+'/'
		else: 
			#---if the path provided to timeslice explicitly matches the regex then we assume it's an 
			#---...absolute path in the same root as the step corresponding to the beginning of the slice
			rootdir = tl[0][-1]
			storedir = rootdir+'/'+simname+'/'+path
			final_name = storedir+'/'+outname
			cwd = storedir+'/'
		if not os.path.isdir(os.path.abspath(storedir)):
			status('[STATUS] making directory: '+str(os.path.abspath(storedir)))
			os.mkdir(os.path.abspath(storedir))
	else: 
		#---if no path is supplied then the slice goes in the same directory as the first timeline item
		#---devolve root to step
		rootdir = tl[0][-1]
		final_name = rootdir+'/'+simname+'/'+tl[0][0]+'/'+outname
		cwd = rootdir+'/'+simname+'/'+tl[0][0]+'/'

	#---check if file already exists
	#---? check both gro and trajectory before continuing
	if os.path.isfile(final_name) and os.path.isfile(final_name[:-4]+'.gro'): 
		status('[REPORT] ignoring target because it already exists: '+final_name)
		return

	#---generate system.gro file for the full system
	if selection != None:
		#---if selection is a string we assume it is in make_ndx syntax
		#---if selection is a dict with an 'atoms' entry, we reformat it for make_ndx
		if type(selection)==dict:
			selection_string = []
			if 'atoms' in selection.keys():
				selection_string.append(' | '.join(['a '+i for i in selection['atoms']]))
			if 'residues' in selection.keys():
				selection_string.append(' | '.join(['r '+i for i in selection['residues']]))
			if 'atoms_from_meta' in selection.keys() and metadat!=None:
				selection_string.append(' | '.join(['a '+i for j in selection['atoms_from_meta'] 
					for i in metadat[simname][j]]))
			elif 'atoms_from_meta' in selection.keys() and metadat==None:
				raise Exception('cannot find metadat to determine atom types')
			selection_string = ' | '.join(selection_string)
			if selection_string == '':
				raise Exception('unclear selection dictionary for make_ndx: '+str(selection))
			selection = selection_string
		status('[REPORT] make_ndx selection = "'+selection+'"')
		#---devolve root to the level of step so we replace all simdict[simname]['root'] with rootdir
		#---added rootdir as last item in tl to avoid having to change tl indices elsewhere
		stepdir,partfile,start,end,timestep,rootdir = tl[0]
		systemgro = final_name[:-4]+'.'+extraname+'.gro'
		cmd = ' '.join([gmxpaths('trjconv'),
			'-f '+rootdir+'/'+simname+'/'+stepdir+'/'+partfile,
			'-s '+rootdir+'/'+simname+'/'+stepdir+'/'+partfile[:-4]+'.tpr',
			'-o '+systemgro,
			'-b '+str(start),
			'-t0 '+str(start),
			'-e '+str(start),
			'-dt '+str(timestep)])
		call(cmd,logfile='log-slice-'+time+'-'+stepdir+'-'+partfile.strip('.'+form)+'-gro-'+extraname+'.log',
		    cwd=cwd,inpipe='0\n')
		#---create group file
		cmd = ' '.join([gmxpaths('make_ndx'),
			'-f '+systemgro,
			'-o index-'+extraname+'.ndx'])
		call(cmd,logfile='log-slice-'+time+'-'+stepdir+'-'+partfile.strip('.'+form)+'-make-ndx',
		    cwd=cwd,inpipe='keep 0\n'+selection+'\nkeep 1\nq\n')
		os.remove(systemgro)
	
	#---report
	status('[REPORT] time slices = '+str(tl))
	
	#---make individual slices
	tl_trimmed = []
	for ti in range(len(tl)):
		#---skip any slices that go backwards
		if tl[ti][2]<=tl[ti][3]: 
			tl_trimmed.append(tl[ti])
			stepdir,partfile,start,end,timestep,rootdir = tl[ti]
			#---save a gro file on the first part of the time slice
			if ti == 0:
				cmd = ' '.join([gmxpaths('trjconv'),
					'-f '+rootdir+'/'+simname+'/'+stepdir+'/'+partfile,
					'-o '+final_name[:-4]+'.gro',
					('-pbc mol' if pbcmol else ''),
					('-n index-'+extraname+'.ndx' if selection != None else ''),
					'-s '+rootdir+'/'+simname+'/'+stepdir+'/'+partfile[:-4]+'.tpr',
					'-b '+str(tl[ti][2]),
					'-t0 '+str(tl[ti][2]),
					'-e '+str(tl[ti][3]),
					'-dt '+str(timestep)])
				logfile = logfile='log-slice-'+stepdir+'-'+time+'-'+partfile.strip('.'+form)+'.gro.log'
				call(cmd,logfile,cwd=cwd,inpipe=(None if selection != None else '0\n'))
				#---make sure this is a valid start time
				with open(cwd+logfile,'r') as fp:
					for line in fp:
						if 'WARNING no output' in line:
							raise Exception('[ERROR] gro files gives no output '+\
								'so you might have an impossible start time. see '+\
								cwd+logfile)
			#---create trajectory slices
			cmd = ' '.join([gmxpaths('trjconv'),
				'-f '+rootdir+'/'+simname+'/'+stepdir+'/'+partfile,
				'-o '+partfile.strip('.'+form)+'_slice.'+form,
				('-pbc mol' if pbcmol else ''),
				('-n index-'+extraname+'.ndx' if selection != None else ''),
				('-s '+rootdir+'/'+simname+'/'+stepdir+'/'+partfile[:-4]+'.tpr'
					if selection != None or pbcmol else ''),
				'-b '+str(start),
				'-e '+str(end),
				'-dt '+str(timestep)])
			call(cmd,logfile='log-slice-'+stepdir+'-'+time+'-'+partfile+'.log',
				cwd=cwd,inpipe=(None if selection != None else '0\n'))
		elif ti==0: raise Exception('backwards timestep at the beginning skips gro')

	#---concatenate the slices
	slicefiles = [cwd+s[1].strip('.'+form)+'_slice.'+form for s in tl_trimmed]
	cmd = ' '.join([gmxpaths('trjcat'),
		'-f '+' '.join(slicefiles),
		'-o '+final_name])
	call(cmd,logfile='log-slice-'+stepdir+'-'+time+'-trjcat.log',cwd=cwd)
	for s in slicefiles: 
		status('[STATUS] cleaning up '+str(s))
		os.remove(s)

#---TIME CHECKING
#-------------------------------------------------------------------------------------------------------------
		
def scan_timestamps(trajfile):

	"""
	Given a trajfile check the available timestamps using MDAnalysis.
	"""

	import MDAnalysis,re
	from numpy import array,arange

	if 0: print('[CHECKING] '+trajfile)
	grofile = trajfile[:-3]+'gro'
	if not os.path.isfile(grofile):
		print('[WARNING] missing gro file: '+grofile)
		return
	uni = MDAnalysis.Universe(grofile,trajfile)
	supposed_times = [int(i) for i in 
		re.findall('^.*?/?md\.?([a-z][0-9]{1,2})?\.part[0-9]{4}\.([0-9]+)\-([0-9]+)\-([0-9]+)',
		trajfile)[0][1:4]]
	print('[REPORT] supposed times = '+str(supposed_times))
	timeseries = []
	for frnum,fr in enumerate(uni.trajectory):
		status('[SCAN] frame ',i=frnum,looplen=len(uni.trajectory))
		timeseries.append(int(uni.trajectory.ts.time))							
	timeseries = array(timeseries)
	desired_timeseries = arange(supposed_times[0],supposed_times[1]+supposed_times[2],supposed_times[2])
	return {'miss':[i for i in desired_timeseries if i not in timeseries],
		'grat':[i for i in timeseries if i not in desired_timeseries],
		'stamp':'-'.join([str(i) for i in supposed_times]),
		'times':timeseries}
		
def timelist(simdict,project=None,name=None,get_slices=True):
	
	"""
	Report timestamps for available simulations.
	"""
	
	#---imports avoid overwriting custom argsort
	from numpy import sort,array
	
	treechar = '|-----'.rjust(11)
	if name == None:
		for sn in simdict:
			times,stepnames,slices = [],[],[]
			for step in simdict[sn]['steps']:
				if 'parts' in step:
					for p in step['parts']:
						if 'edrstamp' in p:
							times.append(tuple([float(i) for i in p['edrstamp'].split('-')]))
							stepnames.append(step['dir'])
				if get_slices and 'trajs' in step:
					slices.append([step['dir']+'/'+t for t in step['trajs']])
			timesort = sort(array(times))
			timesort_arg = argsort(list(times))
			timestrings = [tuple(['%.f'%float(i) for i in j]) for j in timesort]
			steplist = [stepnames[i] for i in timesort_arg]
			if timestrings != [] and slices != []: status('\n[CATALOG] '+sn+'\n|')
			for ti,ts in enumerate(timestrings): 
				print '|-'+steplist[ti].ljust(30,'.')+('%.f'%float(ts[0])).rjust(10,'.')+\
					('%.f'%float(ts[1])).rjust(10,'.')
			if slices != []: 
				status('|-slices')
				for s in slices: 
					if type(s) == list:
						for i in s: print treechar+i
					else: print treechar+s
