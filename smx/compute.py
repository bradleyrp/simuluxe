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
					#---if clock file available then pass timestamps along to compute function
					if os.path.isfile(trajfile[:-3]+'clock'):
						with open(trajfile[:-3]+'clock','r') as fp:
							kwargs['times'] = [float(i) for i in fp.readlines()]
				else: grofile,trajfile = None,None
				#---get unique filename (we omit step designations and this requires non-redundant times)
				#---we also drop any descriptors after the three-digit code
				sn_chop = re.findall('(^[a-z]+-v[0-9]+)-?',sn)[0]
				#---adding step code to the filename for future pickles 2015.3.4
				stepcode = re.findall('^([a-z][0-9]{1,2})',timestamp['step'])[0]
				name = 'postproc.'+compsign+'.'+sn_chop+'.'+stepcode+'.'+timestamp['time']+'.dat'
				#---retain backwards compatibility with pickles with no stepcode in the name
				if not os.path.isfile(dropspot+name): 
					name = 'postproc.'+compsign+'.'+sn_chop+'.'+timestamp['time']+'.dat'				
				#---check the repo and if absent compute and store the result
				if not smx.lookup(name,dropspot):
					status(' '.join(['[COMPUTE]',compsign,sn]))
					result,attrs = function(simname=sn,grofile=grofile,trajfile=trajfile,
						metadat=metadat,focus=focus,panel=panel,headerdat=headerdat,**kwargs)
					#---intervene to include grofile and trajfile in the metadat
					#---...note that this is the sum total of our connection between slices and pickles
					#---...however the slice name should contain all of the information necessary to either
					#---...find the slice or figure out which time it came from via timestamp and clock file
					attrs['grofile'],attrs['trajfile'] = grofile,trajfile
					smx.store(result,name,dropspot,attrs=attrs)
	checktime()

def loader(focus,headerdat,sn=None,compsign=None,check=False,compsign_original=None):

	"""
	Universal procedure for unloading saved postprocessing data from the dropspot.
	"""
	
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
				for ts in focus[panel][sn]:
					datlist_parted = {}
					sn_chop = re.findall('(^[a-z]+-v[0-9]+)-?',sn)[0]
					stepcode = re.findall('^([a-z][0-9]{1,2})',ts['step'])[0]
					name = 'postproc.'+compsign+'.'+sn_chop+'.'+stepcode+'.'+ts['time']+'.dat'
					#---retain backwards compatibility with pickles with no stepcode in the name
					if not os.path.isfile(dropspot+name): 
						name = 'postproc.'+compsign+'.'+sn_chop+'.'+ts['time']+'.dat'
					if check:
						if os.path.isfile(dropspot+name): picklelist['found'].append(name)
						else: picklelist['missing'].append(name)
					else:
						datlist_parted[(sn,ts['time'])] = smx.load(name,dropspot)
						datlist[sn] = loadcat(datlist_parted,focus,headerdat)[sn]
			else: 
				sn_chop = re.findall('(^[a-z]+-v[0-9]+)-?',sn)[0]
				stepcode = re.findall('^([a-z][0-9]{1,2})',focus[panel][sn]['step'])[0]
				name = 'postproc.'+compsign+'.'+sn_chop+'.'+stepcode+'.'+focus[panel][sn]['time']+'.dat'
				#---retain backwards compatibility with pickles with no stepcode in the name
				if not os.path.isfile(dropspot+name): 
					name = 'postproc.'+compsign+'.'+sn_chop+'.'+focus[panel][sn]['time']+'.dat'
				if check:
					if os.path.isfile(dropspot+name): picklelist['found'].append(name)
					else: picklelist['missing'].append(name)
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

	sns = [i[0] for i in datlist.keys()]
	slicekeys = [[i for i in datlist.keys() if i[0]==sn] for sn in sns]
	slicekeys = [i for i in slicekeys if i!=[]]
	print str(slicekeys)
	print datlist.keys()
	raw_input('?')
	master_datlist = {}
	for snnum,sks in enumerate(slicekeys):
		sn = sns[snnum]
		#---make sure these pickles can be accurately stitched together by checking timestamp contiguity
		timelist = np.sort([[int(k) for k in i[1].split('-')] for i in slicekeys[0]],axis=0)
		if not all([timelist[i][1]==timelist[i+1][0] for i in range(len(timelist)-1)]):
			raise Exception('time stamps are non-contiguous: '+str(timelist))
		if not all([timelist[0][2]==timelist[i][2] for i in range(1,len(timelist))]):
			raise Exception('time stamps have unequal step sizes '+str(timelist))
		#---reorder the datlist keys
		sks = [sks[j] for j in np.argsort([[int(k) for k in i[1].split('-')] 
			for i in slicekeys[0]],axis=0)[:,0]]
		#---find keys that lack the period, indicating that they are general to 
		#---...the calculation (and not frame-wise)
		general_keys = [[i for i in datlist[sk].keys() if '.' not in i] for sk in sks]
		#---check that all pickles have the same list of general_keys
		if not all([set(general_keys[ii])==set(general_keys[(ii+1)%len(sks)]) 
			for ii,i in enumerate(general_keys)]):
			raise Exception('pickles cannot be combined because they have unequal general keys')
		#---identify the numbers of frames in each pickle
		nframes_list = [datlist[sk]['nframes'] for sk in sks]
		raw_input('sks='+str(sks))
		nframes_apparent = [(timelist[i][1]-timelist[i][0])/timelist[i][2] for i in range(len(timelist))]
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
		general_keys_that_change = ['nframes','vecs']
		#---keys which must be equal between pickles
		checklist = list(set([i for j in general_keys for i in j if i not in general_keys_that_change]))
		#---list of keys which are not equal
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
			for key in [i for i in general_keys_that_change if i!='nframes']:
				master_datlist[sn][key] = np.concatenate((master_datlist[sn][key],datlist[sk][key]))
			offset = nframes_list[si]
			newtimes = np.sort(np.array([[int(k) for k in i.split('.')] 
				for i in datlist[sk].keys() if '.' in i]),axis=0)
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
	
	delim = '.' if 'delim' not in kwargs else kwargs['delim']
	return delim.join([str(i) for i in items])
	
def compute_post_post_basic(compsign2,function,
	headerdat=None,focus=None,upstream=None,**kwargs):

	"""
	Post-post processing function which depends on a post-processing pickle.
	"""
	
	dropspot = headerdat['dropspot']
	comparisons = headerdat['comparisons']

	sns = list(np.unique([i for j in [comparisons[k] for k in focus] for i in j]))
	timestamps = dict(list(np.unique([(sn,focus[f][sn]['time']) 
		for sn in sns for f in focus if sn in focus[f]])))
	for sn in sns:
		status('[COMPUTE] post-post processing '+\
			(upstream if type(upstream)==str else '+'.join(upstream))+\
			' --> '+function.__name__+': '+sn)
		name = 'postproc.'+compsign2+'.'+sn+'.'+timestamps[sn]+'.dat'
		if not smx.lookup(name,dropspot):
			if type(upstream) == list: 
				dats = [loader(focus,headerdat,sn=sn,compsign=u,
					compsign_original=kwargs['compsign_original'])[sn] for u in upstream]
				result = function(sn,*dats,**kwargs)
			else: 
				dat = loader(focus,headerdat,sn=sn,compsign=upstream)[sn]
				result = function(sn,dat,**kwargs)
			print result.keys()
			smx.store(result,name,dropspot,attrs=kwargs)
		else: status('[REPORT] found the post-post processing data')
		