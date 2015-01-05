#!/usr/bin/python

import numpy as np
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt

def quickplot3d(dat):
	if len(np.shape(dat))==2: dat = np.array([dat])
	fig = plt.figure()
	ax = fig.add_subplot(111, projection='3d')
	colors = ['r','b','k','m']
	for di,d in enumerate(dat):
		ax.scatter(d[:,0],d[:,1],d[:,2],c=colors[di])
	ax.set_xlabel('X')
	ax.set_ylabel('Y')
	ax.set_zlabel('Z')
	plt.show()
