#!/usr/bin/python

import numpy as np
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt

def quickplot3d(dat):

	fig = plt.figure()
	ax = fig.add_subplot(111, projection='3d')
	ax.scatter(dat[:,0], dat[:,1], dat[:,2])
	ax.set_xlabel('X')
	ax.set_ylabel('Y')
	ax.set_zlabel('Z')
	plt.show()
