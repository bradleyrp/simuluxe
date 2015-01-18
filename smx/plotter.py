#!/usr/bin/python

import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np

def generate_axes(nrows=1,ncols=1,figsize=None):
	fig = plt.figure(figsize=figsize)
	gs = gridspec.GridSpec(nrows,ncols)
	axes = [[fig.add_subplot(gs[r,c]) for c in range(ncols)] for r in range(nrows)]
	return fig,gs,axes
	
def colorscale(name='RdBu',count=10,reverse=False):
	return [plt.cm.get_cmap(name)(i) for i in np.array(range(0,count)[::(-1 if reverse else 1)])/float(count)]


