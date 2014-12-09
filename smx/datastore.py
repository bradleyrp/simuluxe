#!/usr/bin/python

#---imports
from os.path import expanduser
try: execfile(expanduser('~/.simuluxe_config.py'))
except: print 'config file is absent'
import smx

#---imports 
import os
import h5py
import json
import numpy

def store(obj,name,path,attrs=None):
	'''
	Use h5py to store a dictionary of data.
	'''
	if type(obj) != dict: raise Exception('except: only dictionaries can be stored')
	if os.path.isfile(path+'/'+name): raise Exception('except: file already exists: '+path+'/'+name)
	path = os.path.abspath(os.path.expanduser(path))
	if not os.path.isdir(path): os.mkdir(path)
	fobj = h5py.File(path+'/'+name,'w')
	for key in obj.keys(): dset = fobj.create_dataset(key,data=obj[key])
	if attrs != None: fobj.create_dataset('meta',data=numpy.string_(json.dumps(attrs)))
	fobj.close()
	
def lookup(name,path):	
	'''
	Check if a viable h5py file is prsent in path/name.
	'''
	path = os.path.abspath(os.path.expanduser(path))
	return os.path.isfile(path+'/'+name)

def load(name,path):
	'''
	Load an h5py datastore.
	'''
	path = os.path.abspath(os.path.expanduser(path))
	data = {}
	rawdat = h5py.File(path+'/'+name,'r')
	for key in rawdat.keys(): data[key] = numpy.array(rawdat[key])
	attrs = json.loads(rawdat['meta'].value)
	for key in attrs: data[key] = attrs[key]
	return data
