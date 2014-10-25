#!/usr/bin/python

#---imports
import os
import numpy as np
from numpy import array,shape
from simuluxe.codetools import *

missing_libxdr = \
	"""
	Cannot load the libxdrfile package, which is
	necessary for directly reading the
	velocities. Get the libxdrfile package via wget
	ftp://ftp.gromacs.org/pub/contrib/xdrfile-1.1.4.tar.gz and navigate to
	http://www.gromacs.org/Developer_Zone/Programming_Guide/XTC_Library
	for details.
	"""

try:
	import MDAnalysis.coordinates.xdrfile.libxdrfile as libxdrfile
	from MDAnalysis.coordinates.xdrfile.libxdrfile import \
		xdrfile_open, xdrfile_close, read_trr_natoms, read_trr, DIM, exdrOK
except:
	try:
		import MDAnalysis.coordinates.xdrfile.libxdrfile2 as libxdrfile2
		from MDAnalysis.coordinates.xdrfile.libxdrfile2 import \
			xdrfile_open, xdrfile_close, read_trr_natoms, read_trr, DIM, exdrOK	
	except: status(missing_libxdr)
		
def trajectory_read(trrfile,get='velocities'):
	'''
	Wrapper for MDAnalysis/libxdrfile for reading velocities or positions from a TRR file.\n
	
	Parameters
	----------
	trrfile : path for the trr file to read
	requests : string explaining the requested data, ("x"/"positions" or "v"/"velocities")

	Returns
	-------
	A tuple containing arrays of the positions and/or velocities (in that order), depending on the request.
	'''
	#---parse
	if type(get) == list: get = [get]
	getv = True if ('v' in get or 'velocities' in get) else False
	getx = True if ('x' in get or 'positions' in get) else False	
	#---paths
	fullpath = os.path.abspath(os.path.expanduser(trrfile))
	traj = xdrfile_open(fullpath,'r')
	#---allocate
	xs,vs = [],[]
	natoms = read_trr_natoms(fullpath)
	x = np.zeros((natoms,DIM),dtype=np.float32)
	v = np.zeros((natoms,DIM),dtype=np.float32)
	f = np.zeros((natoms,DIM),dtype=np.float32)
	box = np.zeros((DIM,DIM),dtype=np.float32)
	status = exdrOK
	#---loop over the file
	while status == exdrOK:
		status,step,time,prec,has_x,has_v,has_f = read_trr(traj,box,x,v,f)
		if getx: xs.append(array(x))
		if getv: vs.append(array(v))
	xdrfile_close(traj)
	#---reformat and return
	xs,vs = array(xs),array(vs)
	if getv and getx: return xs,vs
	elif getv: return vs
	elif getx: return xs
