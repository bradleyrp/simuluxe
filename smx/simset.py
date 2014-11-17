
'''A class which wraps data from a molecular dynamics simulation.'''

import MDAnalysis
from smx.codetools import *

class SimSet:

	def __init__(self):

		#---MDAnalysis universe
		self.universe = None
		#---time
		self.nframes = 0
		self.vecs,self.vecs_index = [],[]
		self.time_list = []
		#---files
		self.universe_structfile = ''
		self.universe_trajfile = ''
		
	def load_trajectory(self,files,resolution=None,lenscale=None):

		'''
		Load a molecular dynamics trajectory into the MembraneSet instance.

		This function takes a structure and trajectory file and creates a Universe instance from the
		MDAnalysis library which serves as a member of MembraneSet. The function also populates meta-data 
		inside the MembraneSet instance which keep track of the frames and timining of the trajectory.

		Args:
			files (tuple): A tuple containing the path to the structure (usually a GRO file) and trajectory 
			for the target simulation.

		Kwargs:
			resolution (str): Specify either "CGMD" or "AAMD" to denote the "graining" of simulation. This is
			only used in a few functions, for bookkeeping purposes.
		   
			lenscale (float): Set the natural lengthscale of the incoming data. Since this function uses the
			MDAnalysis package, the default value is 10, corresponding to 10 Angstroms, so that all 
			downstream units are in nanometers.
		   
		'''
		
		#---default lengthscale is 10 because many MD programs use Angstroms and we compute in nm
		self.lenscale = lenscale if lenscale != None else 10.
		if resolution != None: self.resolution = resolution
		if self.nframes != 0:
			status('status: clearing trajectory')
			self.vecs,self.vecs_index = [],[]
			self.nframes = 0
		self.universe = MDAnalysis.Universe(files[0],files[1])
		self.universe_structfile = files[0]
		self.universe_trajfile = files[1]
		self.nframes = len(self.universe.universe.trajectory)
		if hasattr(self.universe.trajectory[0],'time'): self.time_start = self.universe.trajectory[0].time
		if hasattr(self.universe.trajectory,'totaltime'): self.time_total = self.universe.trajectory.totaltime
		if hasattr(self.universe.trajectory,'dt'): self.time_dt = self.universe.trajectory.dt
		#---if trajectory is available check the timestamps
		if hasattr(self.universe,'trajectory'):
			self.time_list = [self.universe.trajectory[i].time 
				for i in range(len(self.universe.trajectory)) 
				if hasattr(self.universe.trajectory[i],'time')]
		status('status: the trajectory file has '+str(self.nframes)+' frames')

	def gotoframe(self,frameno):
		
		'''Iterate to another frame without delay.'''
		
		if len(self.universe.trajectory) == 1:
			print 'warning: only one frame is available'
		elif frameno == 0:
			frame = self.universe.trajectory[frameno]
		elif self.universe.trajectory.frame-1 < frameno:
			[self.universe.trajectory.next() for i in range(frameno-(self.universe.trajectory.frame-1))]
		elif self.universe.trajectory.frame-1 > frameno:
			frame = self.universe.trajectory[frameno]

	def vec(self,frameno):

		'''Returns box vectors and stores them for quicker retrieval.'''

		if frameno not in self.vecs_index:
			if self.universe.trajectory.frame-1 != frameno: self.gotoframe(frameno)
			vec = self.universe.dimensions[0:3]
			self.vecs.append(vec)
			self.vecs_index.append(frameno)
			return vec
		else: return self.vecs[self.vecs_index.index(frameno)]

