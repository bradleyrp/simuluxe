#!/usr/bin/python

import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

def generate_axes(nrows=1,ncols=1,figsize=None):
	fig = plt.figure(figsize=figsize)
	gs = gridspec.GridSpec(nrows,ncols)
	axes = [[fig.add_subplot(gs[r,c]) for c in range(ncols)] for r in range(nrows)]
	return fig,gs,axes

