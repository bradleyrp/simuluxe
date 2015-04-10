#!/usr/bin/python

#---imports
from os.path import expanduser
execfile(expanduser('~/.simuluxe_config.py'))
from smx.codetools import *
import smx

#---imports
import numpy as np

def computer(focus,function,headerdat,simdict,get_slices=True,**kwargs):
	
	"""
	Universal procedure for running a function over simulation slices.
	"""

	#---unload data from the header
	calculations = headerdat['calculations']
	compsign = headerdat['compsign']
	dropspot = headerdat['dropspot']
	metadat = headerdat['metadat']
	
	#---sometimes we include a second computer call for a particular compsign but write to a different name
	compsign_store = kwargs['compsign_store'] if 'compsign_store' in kwargs else compsign

	#---compute
	for panel in focus:
		for sn in focus[panel]:
			status(' '.join(['[CHECK]',compsign,sn]))
			if type(focus[panel][sn])==list: timestamps = focus[panel][sn]
			else: timestamps = [focus[panel][sn]]
			status('[REPORT] timestamps = '+str(timestamps))
			for timestamp in timestamps:

				#---get unique filename (we omit step designations and this requires non-redundant times)
				#---we also drop any descriptors after the three-digit code
				sn_chop = re.findall('(^[a-z]+-v[0-9]+)-?',sn)[0]
				#---adding step code to the filename for future pickles 2015.3.4
				stepcode = re.findall('^([a-z][0-9]{1,2})',timestamp['step'])[0]
				name_step = 'postproc.'+compsign_store+'.'+sn_chop+'.'+stepcode+'.'+timestamp['time']+'.dat'
				#---retain backwards compatibility with pickles with no stepcode in the name
				name = 'postproc.'+compsign_store+'.'+sn_chop+'.'+timestamp['time']+'.dat'				
				#---check the repo and if absent compute and store the result
				if not smx.lookup(name,dropspot) and not smx.lookup(name_step,dropspot):

					#---get slice information
					if get_slices:
						#---omit step designation and only use time when getting the slices
						#---...because the step designation tells you how to find the slice in makeslices
						#---...we otherwise assume non-redundant time slices everywhere else
						#---...this saves the hassle of having to distinguish e.g. a02-postproc 
						#---...and s9-lonestar
						grofile,trajfile = smx.get_slices(sn,simdict,
							timestamp=timestamp['time'],
							step=timestamp['step'],
							wrap=calculations[compsign]['wrap'],
							groupname=calculations[compsign]['groupname'])
						#---beginning to add step designations here instead of get_slices
						if grofile==None and trajfile==None: 
							grofile,trajfile = smx.get_slices(sn,simdict,
								timestamp=timestamp['time'],
								wrap=calculations[compsign]['wrap'],
								groupname=calculations[compsign]['groupname'])
							if trajfile!=None:
								status('[NOTE] found old-school slice without sN designation '+trajfile)
						#---if clock file available then pass timestamps along to compute function
						if trajfile != None and os.path.isfile(trajfile[:-3]+'clock'):
							with open(trajfile[:-3]+'clock','r') as fp:
								kwargs['times'] = [float(i) for i in fp.readlines()]
						if grofile==None or trajfile==None:
							status('[ERRORNOTE] panel = '+str(panel))
							status('[ERRORNOTE] focus[panel] = '+str(focus[panel]))
							status('[ERRORNOTE] timestamp = '+str(timestamp))
							raise Exception('missing grofile/trajfile: '+str(grofile)+' '+str(trajfile))
					else: grofile,trajfile = None,None
					status(' '.join(['[COMPUTE]',compsign,sn,name_step]))
					result,attrs = function(simname=sn,grofile=grofile,trajfile=trajfile,
						metadat=metadat,focus=focus,panel=panel,headerdat=headerdat,**kwargs)
					#---intervene to include grofile and trajfile in the metadat
					#---...note that this is the sum total of our connection between slices and pickles
					#---...however the slice name should contain all of the information necessary to either
					#---...find the slice or figure out which time it came from via timestamp and clock file
					attrs['grofile'],attrs['trajfile'] = grofile,trajfile
					#---recently added more automatic metadata into attrs
					if get_slices:
						for key in ['wrap','groupname']: 
							attrs[key] = calculations[compsign][key]
					attrs['timestamp'] = timestamp
					smx.store(result,name_step,dropspot,attrs=attrs)

	#---reflect on how long this took
	checktime()

def loader(focus,headerdat,sn=None,compsign=None,check=False,compsign_original=None,**kwargs):

	"""
	Universal procedure for unloading saved postprocessing data from the dropspot.
	"""

	#---override timeslice names to label combinations of timeslices with timename
	timename = kwargs['timename'] if 'timename' in kwargs else False

	#---simple flag 
	
	if sn != None:
		focus = [dict([(sn,dict([(sn,focus[f][sn])]))]) 
			for f in focus if sn in focus[f]][0]

	#---unload data from the header
	dropspot = headerdat['dropspot']

	#---often require reference to the headerdat for an upstream compsign when doing post-post
	co = compsign_original if compsign_original != None else compsign
	
	#---alternate compsigns allow for multiple data objects
	#---check that these objects came from the same timeslices
	if compsign == None: compsign = headerdat['compsign']
	else:
		status('[LOAD] alternate compsign = '+compsign)
		if not headerdat['calculations'][co]['timeslices']==\
			headerdat['calculations'][co]['timeslices']:
			raise Exception('you asked for an alternate compsign by supplying the compsign flag '+\
				'to the loader however the headerdat tells me that these computations were drawn '+\
				'from different timeslices therefore I cannot allow you to proceed')

	#---retrieve	
	datlist = {}
	picklelist = {'found':[],'missing':[]}
	for panel in focus:
		for sn in focus[panel]:
			if not check: status(' '.join(['[LOAD]',compsign,sn]))
			if type(focus[panel][sn])==list:
				datlist_parted = {}
				sn_chop = re.findall('(^[a-z]+-v[0-9]+)-?',sn)[0]
				if type(timename) != str:
					for ts in focus[panel][sn]:
						stepcode = re.findall('^([a-z][0-9]{1,2})',ts['step'])[0]
						name = 'postproc.'+compsign+'.'+sn_chop+'.'+stepcode+'.'+ts['time']+'.dat'
						name_step = str(name)
						#---retain backwards compatibility with pickles with no stepcode in the name
						if not os.path.isfile(dropspot+name): 
							name = 'postproc.'+compsign+'.'+sn_chop+'.'+ts['time']+'.dat'
						if check:
							if os.path.isfile(dropspot+name): picklelist['found'].append(name)
							else: picklelist['missing'].append(name_step)
						else: 
							datlist_parted[(sn,ts['time'],ts['step'])] = smx.load(name,dropspot)
				if type(timename)==str:
					#---when timename is used to label lists of timeslices it will not find them above
					name = 'postproc.'+compsign+'.'+sn_chop+'.'+timename+'.dat'
					datlist[sn] = smx.load(name,dropspot)
				elif len(focus[panel][sn])==1 and not check:
					#---if only one slice then we just pass it along
					datlist[sn] = datlist_parted[(sn,ts['time'],ts['step'])]
				elif not check: 
					datlist[sn] = loadcat(datlist_parted,focus,headerdat)[sn]
			else: 
				sn_chop = re.findall('(^[a-z]+-v[0-9]+)-?',sn)[0]
				stepcode = re.findall('^([a-z][0-9]{1,2})',focus[panel][sn]['step'])[0]
				name = 'postproc.'+compsign+'.'+sn_chop+'.'+stepcode+'.'+focus[panel][sn]['time']+'.dat'
				name_step = str(name)
				#---retain backwards compatibility with pickles with no stepcode in the name
				if not os.path.isfile(dropspot+name): 
					name = 'postproc.'+compsign+'.'+sn_chop+'.'+focus[panel][sn]['time']+'.dat'
				if check:
					if os.path.isfile(dropspot+name): picklelist['found'].append(name)
					else: picklelist['missing'].append(name_step)
				else:
					datlist[sn] = smx.load(name,dropspot)
	if check: return picklelist
	else: return datlist

def loadcat(datlist,focus,headerdat):

	"""
	This function intelligently concatenates a datlist which contains simulations with multiple 
	post-processed time slices.
	"""
	
	"""
	Broadly speaking, there are two kinds of data that ends up in a h5py file regardless of whether they
	are stored in results (numpy) or attrs (pythonic): data which are general to the simulation and those 
	that depend on time. Those that depend on time are usually stored in a dot-separated string. In bilayer 
	simulations, the other dimension is usually the monolayer. To combine slices, we stitch together the 
	frame-wise dimensions and check that all of the other parameters are the same.
	"""

	#---unpack
	comparisons = headerdat['comparisons']

	sns = list(set([i[0] for i in datlist.keys()]))
	slicekeys = [[i for i in datlist.keys() if i[0]==sn] for sn in sns]
	slicekeys = [i for i in slicekeys if i!=[]]
	status('[LOADING] concatenation')
	master_datlist = {}
	for snnum,sks in enumerate(slicekeys):
		status('[STITCH] '+str(sks))
		sn = sns[snnum]
		#---resort sks by starting time
		sks = [sks[j] for j in np.argsort([[int(k) for k in i[1].split('-')][0] for i in sks])]
		timelist = [[int(k) for k in i[1].split('-')] for i in sks]
		if not all([timelist[i][1]==timelist[i+1][0] for i in range(len(timelist)-1)]) or \
			not all([timelist[0][2]==timelist[i][2] for i in range(1,len(timelist))]):
			status('[WARNING] these simulations have un-synchronized times but we concatenate anyway')
			status('[NOTE] timelist='+str(timelist))
			stepnames = list(set([i[2] for i in sks]))
			stepnames = [stepnames[j] for j in np.argsort([int(re.findall('^[a-z]([0-9]+)',i)[0]) 
				for i in stepnames])]
			bystep = [[i for i in sks if i[2]==s] for s in stepnames]
			sks = [m for n in [[b[j] for j in np.argsort([[int(k) 
				for k in i[1].split('-')][0] for i in b])] for b in bystep] for m in n]
		else:
			#---reorder the datlist keys
			sks = [sks[j] for j in np.argsort([[int(k) for k in i[1].split('-')] 
				for i in slicekeys[0]],axis=0)[:,0]]
		#---find keys that lack the period, indicating that they are general to 
		#---...the calculation (and not frame-wise)
		if any([datlist[sk]=='fail' for sk in sks]): 
			raise Exception('missing sk pickle '+str([sk for sk in sks if datlist[sk]=='fail']))
		general_keys = [[i for i in datlist[sk].keys() if '.' not in i] for sk in sks]
		#---check that all pickles have the same list of general_keys
		if not all([set(general_keys[ii])==set(general_keys[(ii+1)%len(sks)]) 
			for ii,i in enumerate(general_keys)]):
			raise Exception('pickles cannot be combined because they have unequal general keys')
		#---identify the numbers of frames in each pickle
		nframes_list = [datlist[sk]['nframes'] for sk in sks]
		nframes_apparent = [(timelist[i][1]-timelist[i][0])/timelist[i][2] for i in range(len(timelist))]
		#---check for keys that have a dot implying that they are listed in a sequence
		if not all([any(['.' in i for i in datlist[sk]]) for sk in sks]): time_indices = [-1]
		else:
			#---find the index in the numbered keys (i.e. those with a period) that 
			#---...corresponds to the number of frames
			inds = [np.array([[int(j) for j in i.split('.') 
				if j.isdigit()] for i in datlist[sk] if '.' in i]) for sk in sks]
			time_indices = [np.where(inds[j].max(axis=0)==nframes_list[j]-1)[0][0] 
				for j in range(len(nframes_list))]
		if len(list(set(time_indices)))!=1:
			raise Exception('different time dimensions in framewise objects')
		timedim = time_indices[0]
		#---keys that must be present but not equivalent
		general_keys_that_change = ['nframes','vecs','grofile','trajfile','hqs']
		if 'sequenced' in datlist[sk]: general_keys_that_change += datlist[sk]['sequenced']
		#---keys which must be equal between pickles
		checklist = list(set([i for j in general_keys for i in j if (i not in general_keys_that_change and 
			i not in ['wrap','timesamp','groupname'])]))
		#---list of keys which are not equal
		for key in checklist:
			print key
			print [(k if type(k)==bool else all(k)) 
				for k in [datlist[sks[s]][key]==datlist[sks[(s+1)%len(sks)]][key] 
				for s in range(len(sks))]]
		nomatch_check = [[(k if type(k)==bool else all(k)) 
			for k in [datlist[sks[s]][key]==datlist[sks[(s+1)%len(sks)]][key] 
			for s in range(len(sks))]] for key in checklist]
		nomatch = [checklist[i] for i in np.where(nomatch_check==False)[0]]
		if nomatch != []: raise Exception('keys do not match between pickles: '+str(nomatch))
		#---combine datlist objects
		master_datlist[sn] = dict(datlist[sks[0]])
		#---need to fold in the general_keys_that_change
		master_datlist[sn]['nframes'] = sum(nframes_list)
		for si,sk in enumerate(sks[1:]):
			for key in [i for i in general_keys_that_change if i!='nframes' if i in datlist[sk]]:
				if type(master_datlist[sn][key]).__module__=='numpy':
					print np.shape(master_datlist[sn][key])
					print np.shape(datlist[sk][key])
					master_datlist[sn][key] = np.concatenate((master_datlist[sn][key],datlist[sk][key]))
				elif si==0: master_datlist[sn][key] = [master_datlist[sn][key],datlist[sk][key]]
				else: master_datlist[sn][key].append(datlist[sk][key])
			offset = sum(nframes_list[:si+1])
			newtimes = np.sort(np.array([[int(k) for k in i.split('.')] 
				for i in datlist[sk].keys() if '.' in i]),axis=0)
			#---renumber the dotted keys
			if timedim != -1:
				for fr in newtimes.take(timedim,axis=1):
					for sub in [i for i in datlist[sk].keys() 
						if ('.' in i and i.split('.')[timedim]==str(fr))]:
						newkey = '.'.join([str(int(i) if ii!=timedim else int(i)+offset)
							for ii,i in enumerate(sub.split('.'))])
						master_datlist[sn][newkey] = datlist[sk][sub]
	#---note that we need timestamp checking via nframes_apparent to be added here
	#---...but first we must ensure that the slicer gets the times right
	return master_datlist
	
def i2s(*items):

	"""
	Concisely join arguments in order to perform a lookup on an h5py dictionary when storing frames with
	objects that might not equal numpy array sizes. Note that a quick test showed that storing many frames
	with different sizes gave almost the exact same size on disk compared to loading a giant 1D array. The 
	i2s function is particularly useful when storing e.g. the neighborlist and simplex list for different 
	frames of a bilayer simulation. In this case, the objects could be stored as "FRAME.MONO.neighborlist". 
	We use the dot because it cannot be found in a python variable name anyway.
	"""
	
	return '.'.join([str(i) for i in items])

def i2s2(*items,**kwargs):

	"""
	Alternate delimiter for i2s function.
	"""
	
	delim = ':' if 'delim' not in kwargs else kwargs['delim']
	return delim.join([str(i) for i in items])
	
def compute_post_post_basic(compsign2,function,
	headerdat=None,focus=None,upstream=None,**kwargs):

	"""
	Post-post processing function which depends on a post-processing pickle.
	"""
	
	dropspot = headerdat['dropspot']
	comparisons = headerdat['comparisons']
	written_anything = False
	timename = kwargs['timename'] if 'timename' in kwargs else False

	for panel in focus:
		for sn in focus[panel]:
			
			#---previously we looped over a compacted list
			if 0: sns = list(np.unique([i for j in [comparisons[k] for k in focus] for i in j]))
			if 0: timestamps = [focus[f][sn] for sn in sns for f in focus if sn in focus[f]]

			status('[COMPUTE] post-post processing '+\
				(upstream if type(upstream)==str else '+'.join(upstream))+\
				' --> '+function.__name__+': '+sn)
			
			#---the timename flag ensures that the post-post-processing function is only run once for 
			#---...any set of timeslices, instead of once per slice, where the timename string contains
			#---...the name that describes the timeslices list in the filename
			if timename != False:

				sn_chop = re.findall('(^[a-z]+-v[0-9]+)-?',sn)[0]
				name = 'postproc.'+compsign2+'.'+sn_chop+'.'+timename+'.dat'
				if not smx.lookup(name,dropspot):
					if type(upstream) == list: 
						dats = [loader(focus,headerdat,sn=sn,compsign=u,
							compsign_original=kwargs['compsign_original'])[sn] 
							for u in upstream]
						result = function(sn,*dats,**kwargs)
					else: 
						dat = loader(focus,headerdat,sn=sn,compsign=upstream)[sn]
						result = function(sn,dat,**kwargs)
					if len(result) == 2 and all([type(i)==dict for i in result]): result,attrs = result
					else: attrs = {}
					nosave = [] if 'nosave' not in kwargs else kwargs['nosave']
					for k in [j for j in kwargs if j not in nosave]: attrs[k] = kwargs[k]
					smx.store(result,name,dropspot,attrs=attrs)
					written_anything = True
				else: status('[REPORT] found the post-post processing data')

			#---one computation per slice in timeslices
			else:

				if type(focus[panel][sn])==list: timestamps = focus[panel][sn]
				else: timestamps = [focus[panel][sn]]

				#---one computation per slice in timeslices
				for timestamp in timestamps:
				
					#---get unique filename (we omit step designations and this requires non-redundant times)
					#---we also drop any descriptors after the three-digit code
					sn_chop = re.findall('(^[a-z]+-v[0-9]+)-?',sn)[0]
					#---adding step code to the filename for future pickles 2015.3.4
					stepcode = re.findall('^([a-z][0-9]{1,2})',timestamp['step'])[0]
					name = 'postproc.'+compsign2+'.'+sn_chop+'.'+stepcode+'.'+timestamp['time']+'.dat'
					name_step = str(name)
					#---retain backwards compatibility with pickles with no stepcode in the name
					if not os.path.isfile(dropspot+name): 
						name = 'postproc.'+compsign2+'.'+sn_chop+'.'+timestamp['time']+'.dat'				
					if not smx.lookup(name,dropspot):
						focus_trim = dict(focus)
						focus_trim[panel][sn] = timestamp
						if type(upstream) == list: 
							dats = [loader(focus_trim,headerdat,sn=sn,compsign=u,
								compsign_original=kwargs['compsign_original'])[sn] for u in upstream]
							result = function(sn,*dats,**kwargs)
						else: 
							dat = loader(focus_trim,headerdat,sn=sn,compsign=upstream)[sn]
							result = function(sn,dat,**kwargs)
						if len(result) == 2 and all([type(i)==dict for i in result]): result,attrs = result
						else: attrs = {}
						nosave = [] if 'nosave' not in kwargs else kwargs['nosave']
						for k in [j for j in kwargs if j not in nosave]: attrs[k] = kwargs[k]
						smx.store(result,name_step,dropspot,attrs=attrs)
						written_anything = True
					else: status('[REPORT] found the post-post processing data')

	return written_anything
	
