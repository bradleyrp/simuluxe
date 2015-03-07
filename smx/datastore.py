#!/usr/bin/python

#---imports
from os.path import expanduser
try: execfile(expanduser('~/.simuluxe_config.py'))
except: print 'config file is absent'
from smx import *

#---imports 
import os
try: import h5py
except: print 'missing h5py package'
import json
import numpy
import matplotlib as mpl
import pylab as plt
try:
	from PIL import Image
	from PIL import PngImagePlugin
except: print 'missing python Image package'

def store(obj,name,path,attrs=None):
	"""
	Use h5py to store a dictionary of data.
	"""
	if type(obj) != dict: raise Exception('except: only dictionaries can be stored')
	if os.path.isfile(path+'/'+name): raise Exception('except: file already exists: '+path+'/'+name)
	path = os.path.abspath(os.path.expanduser(path))
	if not os.path.isdir(path): os.mkdir(path)
	fobj = h5py.File(path+'/'+name,'w')
	for key in obj.keys(): 
		if 0: print '[WRITING] '+key
		dset = fobj.create_dataset(key,data=obj[key])
	if attrs != None: fobj.create_dataset('meta',data=numpy.string_(json.dumps(attrs)))
	fobj.close()
	
def lookup(name,path):	
	"""
	Check if a viable h5py file is prsent in path/name.
	"""
	path = os.path.abspath(os.path.expanduser(path))
	return os.path.isfile(path+'/'+name)

def load(name,path,verbose=False,filename=False,exclude_slice_source=False):
	"""
	Load an h5py datastore.
	"""
	path = os.path.abspath(os.path.expanduser(path))
	if not os.path.isfile(path+'/'+name): return 'fail'
	data = {}
	rawdat = h5py.File(path+'/'+name,'r')
	for key in [i for i in rawdat if i!='meta']: 
		if verbose:
			print '[READ] '+key
			print '[READ] object = '+str(rawdat[key])
		data[key] = numpy.array(rawdat[key])
	if 'meta' in rawdat: attrs = json.loads(rawdat['meta'].value)
	else: 
		print '[WARNING] no meta in this pickle'
		attrs = {}
	if exclude_slice_source:
		for key in ['grofile','trajfile']:
			if key in attrs: del attrs[key]
	for key in attrs: data[key] = attrs[key]
	if filename: data['filename'] = path+'/'+name
	rawdat.close()
	return data
	
def trace_slice_source(name,path):

	"""
	Wrapper for load which gets the grofile and trajfile from a pickle (not loaded by default because it makes
	keys easier to handle). It then checks for a clock file and if it exists, returns the timestamps.
	"""
	dat = load(name,path,exclude_slice_source=False)
	grofile,trajfile = dat['grofile'],dat['trajfile']
	del dat
	if os.path.isfile(trajfile[:-3]+'clock'):
		with open(trajfile[:-3]+'clock','r') as fp:
			times = [float(i.strip('\n')) for i in fp.readlines()]
	return numpy.array(times)
	
def picturesave(directory,savename,meta=None):
	"""
	Function which saves the global matplotlib figure without overwriting.
	"""
	#---prevent overwriting the figure by making sequential backups
	if os.path.isfile(directory+savename):
		for i in range(1,100):
			base = directory+savename
			latestfile = '.'.join(base.split('.')[:-1])+'.bak'+('%02d'%i)+'.'+base.split('.')[-1]
			if not os.path.isfile(latestfile): break
		if i == 99 and os.path.isfile(latestfile):
			raise Exception('except: too many copies')
		else: 
			status('status: backing up '+directory+savename+' to '+latestfile)
			os.rename(directory+savename,latestfile)
	plt.savefig(directory+savename,dpi=300)
	plt.close()
	#---add metadata to png
	if meta != None:
		im = Image.open(directory+savename)
		imgmeta = PngImagePlugin.PngInfo()
		imgmeta.add_text('meta',json.dumps(meta))
		im.save(directory+savename,"png",pnginfo=imgmeta)
	
def picturedat(directory,savename,bank=False):
	"""
	Read metadata from figures with identical names.
	"""
	if not bank: 
		if os.path.isfile(directory+savename): return Image.open(directory+savename).info
		else: return
	else:
		dicts = {}
		if os.path.isfile(directory+savename):
			dicts[directory+savename] = Image.open(directory+savename).info
		for i in range(1,100):
			base = directory+savename
			latestfile = '.'.join(base.split('.')[:-1])+'.bak'+('%02d'%i)+'.'+base.split('.')[-1]
			if os.path.isfile(latestfile): dicts[latestfile] = Image.open(latestfile).info
		return dicts

