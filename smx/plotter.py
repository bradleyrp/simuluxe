#!/usr/bin/python

import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.colors import LinearSegmentedColormap
import numpy as np

def generate_axes(nrows=1,ncols=1,figsize=None,no_plot=None,polar=False):

	"""
	Generate axes via gridspec in a consistent format.
	"""

	if no_plot == None: no_plot = []
	fig = plt.figure(figsize=figsize)
	gs = gridspec.GridSpec(nrows,ncols)
	axes = [[(fig.add_subplot(gs[r,c],polar=polar) if [r,c] not in no_plot else None)
		for c in range(ncols)] for r in range(nrows)]
	return fig,gs,axes
	
def colorscale(name='RdBu',count=10,cmap=None,cmap_segname=None,reverse=False):

	"""
	Divide a matplotlib color map into discrete colors.
	"""

	cdict1 = {
		'red':((0.0, 0.0, 0.0),(0.5, 0.0, 0.1),(1.0, 1.0, 1.0)),
		'green': ((0.0, 0.0, 0.0),(1.0, 0.0, 0.0)),
		'blue':  ((0.0, 0.0, 1.0),(0.5, 0.1, 0.0),(1.0, 0.0, 0.0))
		}
	if cmap != None: thiscmap = cmap
	elif cmap_segname != None: thiscmap = LinearSegmentedColormap(cmap_segname,cdict1)	
	else: thiscmap = plt.cm.get_cmap(name)

	return [thiscmap(i) for i in np.array(range(0,count)[::(-1 if reverse else 1)])/float(count)]


