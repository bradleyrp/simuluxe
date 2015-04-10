#!/usr/bin/python

#---imports
from os.path import expanduser
execfile(expanduser('~/.simuluxe_config.py'))
from smx import*

#---imports
from numpy import *
import scipy

class SimSetMembrane(SimSet):

	def identify_monolayers_deprecated(self,atomdirectors,startframeno=1):
		'''General monolayer identifier function. Needs: names of outer, inner atoms on lipids.'''
		status('status: moving to frame '+str(startframeno))
		status('status: identifying monolayers')
		self.gotoframe(startframeno)
		pointouts = self.universe.selectAtoms(atomdirectors[0])
		pointins = [self.universe.selectAtoms(atomdirectors[j]).coordinates() 
			for j in range(1,len(atomdirectors))]
		whichlayer = [0 if i > 0.0 else 1 for i in pointouts.coordinates()[:,2] - mean(pointins,axis=0)[:,2]]
		monos = []
		#---monos separates the lipids by absolute index into monolayers from index zero
		monos.append([pointouts.resids()[i]-1 for i in range(len(whichlayer)) if whichlayer[i] == 0])
		monos.append([pointouts.resids()[i]-1 for i in range(len(whichlayer)) if whichlayer[i] == 1])
		#---monolayer rerack hack if some residue IDs are missing
		#---Nb this may affect the tilter, mesher, identify_residues, and batch_gr functions so beware
		if (max(monos[0]+monos[1])-min(monos[0]+monos[1])) != len(monos[0]+monos[1])-1:
			print 'warning: resorting the monolayer indices because there is a mismatch'
			#---reracker is a sorted list of all of the absolute indices
			reracker = list(sort(monos[0]+monos[1]))
			#---monos_rerack is a copy of reracker in relative indices which is separated into monolayers 
			monos_rerack = [[reracker.index(i) for i in monos[m]] for m in range(2)]
			self.monolayer_residues_abs = monos
			#---resids_reracker is in absolute units
			self.resids_reracker = reracker
			#---monolayer_residues is in relative units
			self.monolayer_residues = monos_rerack
		else: 
			self.monolayer_residues = monos
			self.resids_reracker = []
		if len(monos[0]) != len(monos[1]):
			print 'warning: there is a difference in the number of lipids per monolayer'

	def identify_monolayers(self,atomdirectors,startframeno=1):
		'''General monolayer identifier function. Needs: names of outer, inner atoms on lipids.'''
		status('status: moving to frame '+str(startframeno))
		status('status: identifying monolayers')
		self.gotoframe(startframeno)
		pointouts = self.universe.selectAtoms(atomdirectors[0])
		pointins = [self.universe.selectAtoms(atomdirectors[j]).coordinates() 
			for j in range(1,len(atomdirectors))]
		whichlayer = [0 if i > 0.0 else 1 for i in pointouts.coordinates()[:,2] - mean(pointins,axis=0)[:,2]]
		monos = []
		#---monos separates the lipids by absolute index into monolayers from index zero
		monos.append([pointouts.resids()[i]-1 for i in range(len(whichlayer)) if whichlayer[i] == 0])
		monos.append([pointouts.resids()[i]-1 for i in range(len(whichlayer)) if whichlayer[i] == 1])
		#---monolayer rerack hack if some residue IDs are missing
		#---Nb this may affect the tilter, mesher, identify_residues, and batch_gr functions so beware
		if (max(monos[0]+monos[1])-min(monos[0]+monos[1])) != len(monos[0]+monos[1])-1:
			print 'warning: resorting the monolayer indices because there is a mismatch'
			#---reracker is a sorted list of all of the absolute indices
			reracker = list(sort(monos[0]+monos[1]))
			#---monos_rerack is a copy of reracker in relative indices which is separated into monolayers 
			monos_rerack = [[reracker.index(i) for i in monos[m]] for m in range(2)]
			self.monolayer_residues_abs = monos
			#---resids_reracker is in absolute units
			self.resids_reracker = reracker
			#---monolayer_residues is in relative units
			self.monolayer_residues = monos_rerack
		else: 
			self.monolayer_residues = monos
			self.resids_reracker = []
		if len(monos[0]) != len(monos[1]):
			print 'warning: there is a difference in the number of lipids per monolayer'
			
	def identify_residues(self,selector):
		'''General monolayer identifier function. Needs: names of outer, inner atoms on lipids.'''
		self.monolayer_by_resid = []
		self.resnames = []
		self.resids = []
		#---selector holds the proposed resnames
		for sel in selector:
			selection = self.universe.selectAtoms('resname '+sel)
			if len([i-1 for i in selection.resids()]):
				#---resids holds the absolute residue numbers
				self.resids.append([i-1 for i in selection.resids()])
				self.resnames.append(sel)
		#---when re-racker has been defined by identify_monolayers then provide distinct residue numberings
		if self.resids_reracker != []: 
			self.resids_abs = self.resids
			newresids = [[self.resids_reracker.index(i) for i in j] for j in self.resids]
			self.resids = newresids
			#self.resids = [[flatten(self.monolayer_residues).index(i) for i in j] for j in self.resids]

		else:
			self.resids_abs = self.resids
		#---monolayer_residues is in relative indices
		for monolayer in self.monolayer_residues:
			monolayer_resids = []
			#for resids in residue_ids:
			#---self.resids is in relative indices
			for resids in self.resids:
				monolayer_resids.append(list(set.intersection(set(monolayer),set(resids))))
			#---monolayer_by_resid is in relative indices
			self.monolayer_by_resid.append(monolayer_resids)
		if self.resids_reracker == []:
			self.monolayer_by_resid_abs = self.monolayer_by_resid
		else:
			#---pack absolute residue indices into monolayer_by_resid_abs
			self.monolayer_by_resid_abs = \
				[[[self.resids_reracker[r] for r in restype] 
				for restype in mono] for mono in self.monolayer_by_resid]
				
	def wrappbc(self,points,vecs,dims=[0,1],mode=None,growsize=0.2):
		'''Adjusts input points to wrap or reflect over periodic boundaries in multiple ways.'''
		#---Takes anything outside the box, and adds it to the other side. Useful for non-rectangular meshes.
		if mode == 'add_oversteps':
			ans = []
			for p in points:
				if sum([(int(p[i]/vecs[i])%2) for i in dims]) > 0:
					ans.append([p[i]-((int(p[i]/vecs[i])%2)*vecs[i] if i in dims else 0) \
						for i in range(shape(points)[1])])
			return concatenate((points,array(ans)))
		#---Increases system size by the specified growsize percentage.
		elif mode == 'grow':
			ans = []
			over = [[0,1],[1,0],[-1,0],[0,-1],[-1,1],[1,-1],[1,1],[-1,-1]]
			for p in points:
				for move in over:
					ptmove = list([p[i]+vecs[i]*move[i] if i in dims else p[i] for i in range(3)])
					if ((ptmove[0] >= -vecs[0]*growsize) and (ptmove[0] <= vecs[0]*(1.+growsize)) \
						and (ptmove[1] >= -vecs[1]*growsize) and (ptmove[1] <= vecs[1]*(1.+growsize))):
						ans.append(ptmove)
			return concatenate((points,array(ans)))
		#---Includes adjacent (but not corner) meshes.
		elif mode == 'embiggen':
			ans = []
			for p in points:
				for tr in [[1,0],[0,1],[-1,0],[0,-1]]:
					ans.append([p[i]+tr[i]*vecs[i] if i in dims else p[i] for i in range(3)])
			return concatenate((points,array(ans)))
		elif mode == 'nine':
			ans = []
			for p in points:
				for tr in [[1,0],[0,1],[-1,0],[0,-1],[-1,1],[-1,-1],[1,1],[1,-1]]:
					ans.append([p[i]+tr[i]*vecs[i] if i in dims else p[i] for i in range(3)])
			return concatenate((points,array(ans)))
		else:
			return array([\
				[p[i]-((int(p[i]/vecs[i])%2)*vecs[i] if i in dims else 0) \
				for i in range(shape(points)[1])] for p in points])
				
	def midplaner(self,selector,rounder=4.0,framecount=None,start=None,end=None,skip=None,
		interp='best',protein_selection=None,residues=None,timeslice=None,thick=False,fine=None):
		
		'''Interpolate the molecular dynamics bilayers.'''
		
		#---additions to initialization
		self.monolayer1 = []
		self.monolayer2 = []
		self.surf = []
		self.protein = []
		self.surf_position = []
		self.surf_index = []
		self.surf_time = []
		self.protein_index = []
		
		self.rounder = rounder*self.lenscale
		self.griddims = [int(round(self.vec(1)[0]/self.rounder)),int(round(self.vec(1)[1]/self.rounder))]
		starttime = time.time()
		for k in range(self.nframes):
			status('status: calculating midplane ',i=k,looplen=self.nframes,start=starttime)
			self.calculate_midplane(selector,k,rounder=rounder,interp=interp,residues=residues,
				thick=thick,fine=fine)
			if protein_selection != None:
				self.protein.append(self.universe.selectAtoms(protein_selection).coordinates())
				self.protein_index.append(k)
		checktime()

	def calculate_midplane(self,selector,frameno,pbcadjust=1,rounder=4.0,interp='best',
		residues=None,thick=False,fine=None):

		'''Find the midplane of a molecular dynamics bilayer.'''

		lenscale = self.lenscale
		self.gotoframe(frameno)
		#---check for non-redundant residue numbers
		protein_atom_resid = list([i.resid for i in self.universe.selectAtoms('name BB or name CA')])
		#if list(set(protein_atom_resid)) != protein_atom_resid:
		#	raise Exception('except: redundant residue indices in the structure file!')
		if residues == None:
			topxyz = array([mean(self.universe.residues[i].selectAtoms(selector).coordinates(),axis=0) 
				for i in self.monolayer_residues[0]])
			botxyz = array([mean(self.universe.residues[i].selectAtoms(selector).coordinates(),axis=0) 
				for i in self.monolayer_residues[1]])
		else:
			topxyz = array([mean(self.universe.residues[i].selectAtoms(selector).coordinates(),axis=0) 
				for r in residues for i in self.monolayer_by_resid[0][self.resnames.index(r)]])
			botxyz = array([mean(self.universe.residues[i].selectAtoms(selector).coordinates(),axis=0) 
				for r in residues for i in self.monolayer_by_resid[1][self.resnames.index(r)]])

		#---First we wrap PBCs
		topxyzwrap = self.wrappbc(topxyz,vecs=self.vec(frameno),mode='grow')
		botxyzwrap = self.wrappbc(botxyz,vecs=self.vec(frameno),mode='grow')

		#---Triangulate the surface on a regular grid
		topmesh = self.makemesh(topxyzwrap,self.vec(frameno),self.griddims,method=interp,fine=fine)
		botmesh = self.makemesh(botxyzwrap,self.vec(frameno),self.griddims,method=interp,fine=fine)

		#---Take the average surface
		topzip = self.rezipgrid(topmesh,frameno=frameno)
		botzip = self.rezipgrid(botmesh,frameno=frameno)

		#---Convert from points in 3-space to heights on a grid
		self.monolayer1.append(array(topzip))
		self.monolayer2.append(array(botzip))
		surfz = [[1./2*(topzip[i][j]+botzip[i][j]) for j in range(self.griddims[1])] 
			for i in range(self.griddims[0])]
		if thick:
			surf_thick = [[(topzip[i][j]-botzip[i][j]) for j in range(self.griddims[1])] 
				for i in range(self.griddims[0])]
			self.surf_thick.append(surf_thick)
		self.surf_position.append(mean(surfz))
		surfz = surfz - mean(surfz)
		self.surf.append(surfz)
		self.surf_index.append(frameno)
		self.surf_time.append(self.universe.trajectory[frameno].time)

	def makemesh(self,data,vecs,grid,method='best',fine=None):
		'''Approximates an unstructured mesh with a regular one.'''
		if method == 'best': method = 'bilinear_cubic'
		if method == 'bilinear_triangle_interpolation':
			dat1 = self.wrappbc(data,vecs,mode='grow')
			dat2 = Delaunay(dat1[:,0:2])
			xypts = array([[i,j] for i in linspace(0,vecs[0],grid[0]) for j in linspace(0,vecs[1],grid[1])])
			results = []
			for i in range(len(xypts)):
				print 'status: interpolating point: '+str(i)
				dat2 = Delaunay(dat1[:,0:2])
				mytripts = dat1[dat2.simplices[dat2.find_simplex(xypts[i])]]
				height = scipy.interpolate.griddata(mytripts[:,0:2],mytripts[:,2],[xypts[i]],method='linear')
				results.append([xypts[i][0],xypts[i][1],height])
			return array(results)
		elif method == 'bilinear_triangle_interpolation_manual':
			#---Manual bilinear interpolation. Same speed as griddata in method 1 (above).
			dat1 = self.wrappbc(data,vecs,mode='grow')
			dat2 = Delaunay(dat1[:,0:2])
			xypts = array([[i,j] for i in linspace(0,vecs[0],grid[0]) for j in linspace(0,vecs[1],grid[1])])
			results = []
			for i in range(len(xypts)):
				print 'status: interpolating point: '+str(i)
				dat2 = Delaunay(dat1[:,0:2])
				t = dat1[dat2.simplices[dat2.find_simplex(xypts[i])]]
				det = t[0][0]*t[1][1]-t[1][0]*t[0][1]+t[1][0]*t[2][1]-t[2][0]*t[1][1]+t[2][0]*t[0][1]\
					-t[0][0]*t[2][1]
				a = (((t[1][1]-t[2][1])*t[0][2]+(t[2][1]-t[0][1])*t[1][2]+(t[0][1]-t[1][1])*t[2][2]))/det
				b = (((t[2][0]-t[1][0])*t[0][2]+(t[0][0]-t[2][0])*t[1][2]+(t[1][0]-t[0][0])*t[2][2]))/det 
				c = (((t[1][0]*t[2][1]-t[2][0]*t[1][1])*t[0][2]+(t[2][0]*t[0][1]-t[0][0]*t[2][1])*t[1][2]\
					+(t[0][0]*t[1][1]-t[1][0]*t[0][1])*t[2][2]))/det
				height = a*xypts[i][0]+b*xypts[i][1]+c
				results.append([xypts[i][0],xypts[i][1],height])
			return array(results)
		elif method == 'bilinear':
			starttime = time.time()
			xypts = array([[i,j] for i in linspace(0,vecs[0],grid[0]) for j in linspace(0,vecs[1],grid[1])])
			interp = scipy.interpolate.LinearNDInterpolator(data[:,0:2],data[:,2],fill_value=0.0)
			return array([[i[0],i[1],interp(i[0],i[1])] for i in xypts])
		elif method == 'bilinear_cubic':
			starttime = time.time()
			xypts = array([[i,j] for i in linspace(0,vecs[0],grid[0]) for j in linspace(0,vecs[1],grid[1])])
			interp = scipy.interpolate.LinearNDInterpolator(data[:,0:2],data[:,2],fill_value=0.0)
			bilinear_pts = array([[i[0],i[1],interp(i[0],i[1])] for i in xypts])
			result = scipy.interpolate.griddata(bilinear_pts[:,0:2],bilinear_pts[:,2],bilinear_pts[:,0:2],
				method='cubic')
			return array([[bilinear_pts[i,0],bilinear_pts[i,1],result[i]] for i in range(len(result))])
		elif method == 'rbf':
			subj = self.wrappbc(data,vecs,mode='grow')
			print 'status: generating radial basis function object'
			rbfobj = scipy.interpolate.Rbf(subj[:,0],subj[:,1],subj[:,2],epsilon=1.2,function='gaussian')
			ti1 = linspace(0,vecs[0],grid[0]);ti2 = linspace(0,vecs[1],grid[1])
			XI, YI = meshgrid(ti1, ti2)
			print 'status: surfacing on a regular grid'
			ZI = rbfobj(XI,YI)
			return self.unzipgrid(transpose(ZI),vecs=vecs,reverse=0)
		elif method == 'sharp_cubic_spline':
			'''
			Added this method on 2014.08.14 in order to dramatically increase the resolution of the mesh.
			Currently the sharpness parameter is hard-coded but this should eventually become an argument.
			'''
			if fine == None: fineness = 500*1j,500*1j
			else: fine = fine*1j,fine*1j
			
			gridx,gridy = mgrid[0:vecs[0]:fine[0],0:vecs[1]:fine[1]]
			points = data[:,:2]
			values = data[:,2]
			heights = scipy.interpolate.griddata(points,values,(gridx,gridy),method='cubic')
			unzip = self.unzipgrid(transpose(heights),vecs=vecs,reverse=0)
			return unzip
		
	def unzipgrid(self,surf,vecs=None,grid=None,rounder_vecs=[1.0,1.0],reverse=0):
		'''Turns a 2D array into a set of points in 3-space.'''
		if type(surf) != ndarray:
			surf = array(surf)
		grid = [shape(surf)[i] for i in range(2)]
		if reverse != 0: grid = grid[::-1];
		if vecs != None:
			rounder_vecs = [vecs[i]/(grid[i]-1) for i in range(2)]
		replotin = surf
		surfreplot = []
		for i in range(grid[0]):
				for j in range(grid[1]):
					surfreplot.append([i*rounder_vecs[0],j*rounder_vecs[1],replotin[i,j]])
		surfreplot = array(surfreplot)
		return surfreplot
		
	def rezipgrid(self,xyz,vecs=None,frameno=0,grid=None,rounder_vecs=[1.0,1.0],
		reverse=0,diff=False,whichind=2):
		'''Turns a regular set of points in 3-space into a 2D matrix.'''
		#---Nb this is the source of the transpose error, which needs fixed.
		#---Nb it looks like I fixed this but didn't write it down until afterwards.
		#---Modifications in the following section for compatibility with the general interpolation function.
		#---Nb "diff" describes whether we are handling redundant points. Needs explained.
		#---Nb I removed all references to diff in the process of fixing script-meso-coupling code.
		if grid == None and diff != True: grid = self.griddims
		elif grid == None and diff == True: grid = self.griddims[0],self.griddims[1]
		if vecs == None: vecs = self.vec(frameno)
		steps = ([vecs[i]/(grid[i]-1) for i in range(2)] 
			if diff == False else [vecs[i]/(grid[i]) for i in range(2)])
		poslookup = [[xyz[i][j]/steps[j] for j in range(2)] for i in range(len(xyz))]
		surfgrid = [[0. for i in range(grid[1])] for j in range(grid[0])]
		for i in range(len(xyz)): 
			#---Note: added the round command below changes calculate_midplane time from 0.25 to 0.35!
			if int(poslookup[i][0]) < grid[0] and int(poslookup[i][1]) < grid[1]:
				surfgrid[int(round(poslookup[i][0]))][int(round(poslookup[i][1]))] = xyz[i][whichind]
		return surfgrid
		
	def wrappbc(self,points,vecs,dims=[0,1],mode=None,growsize=0.2):
		'''Adjusts input points to wrap or reflect over periodic boundaries in multiple ways.'''
		#---Takes anything outside the box, and adds it to the other side. Useful for non-rectangular meshes.
		if mode == 'add_oversteps':
			ans = []
			for p in points:
				if sum([(int(p[i]/vecs[i])%2) for i in dims]) > 0:
					ans.append([p[i]-((int(p[i]/vecs[i])%2)*vecs[i] if i in dims else 0) \
						for i in range(shape(points)[1])])
			return concatenate((points,array(ans)))
		#---Increases system size by the specified growsize percentage.
		elif mode == 'grow':
			ans = []
			over = [[0,1],[1,0],[-1,0],[0,-1],[-1,1],[1,-1],[1,1],[-1,-1]]
			for p in points:
				for move in over:
					ptmove = list([p[i]+vecs[i]*move[i] if i in dims else p[i] for i in range(3)])
					if ((ptmove[0] >= -vecs[0]*growsize) and (ptmove[0] <= vecs[0]*(1.+growsize)) \
						and (ptmove[1] >= -vecs[1]*growsize) and (ptmove[1] <= vecs[1]*(1.+growsize))):
						ans.append(ptmove)
			return concatenate((points,array(ans)))
		#---Includes adjacent (but not corner) meshes.
		elif mode == 'embiggen':
			ans = []
			for p in points:
				for tr in [[1,0],[0,1],[-1,0],[0,-1]]:
					ans.append([p[i]+tr[i]*vecs[i] if i in dims else p[i] for i in range(3)])
			return concatenate((points,array(ans)))
		elif mode == 'nine':
			ans = []
			for p in points:
				for tr in [[1,0],[0,1],[-1,0],[0,-1],[-1,1],[-1,-1],[1,1],[1,-1]]:
					ans.append([p[i]+tr[i]*vecs[i] if i in dims else p[i] for i in range(3)])
			return concatenate((points,array(ans)))
		else:
			return array([\
				[p[i]-((int(p[i]/vecs[i])%2)*vecs[i] if i in dims else 0) \
				for i in range(shape(points)[1])] for p in points])

	def get_points(self,frameno,selection_index=-1):
		'''Shell function that returns coordinates for a pre-defined selection.'''
		if self.universe.trajectory.frame-1 != frameno:
			self.gotoframe(frameno)
		return self.selections[selection_index].coordinates()
