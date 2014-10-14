#!/usr/bin/python

"""
Codetools for Simuluxe.

These tools aid in rapid development, debugging, and monitoring.
"""

#---LIBRARIES
#-------------------------------------------------------------------------------------------------------------

#---imports 
import sys, atexit, code, re, time, argparse

#---MONITORING FUNCTIONS
#-------------------------------------------------------------------------------------------------------------

#---record a global start time
global_start_time = time.time()

def niceblock(text,newlines=False):
	'''Remove tabs so that large multiline text doesn't awkwardly wrap in the code.'''
	return re.sub('\n([\t])+',(' ' if not newlines else '\n'),re.sub('^\n([\t])+','',text))
	
def status(string,start=None,i=None,looplen=None,blocked=False):
	'''Print status to the screen also allows for re-writing the line. Duplicated in the membrain library.'''
	#---note: still looking for a way to use the carriage return for dynamic counter without
	#---...having many newlines printed to the file. it seems impossible to use the '\r' + flush()
	#---...method with both screen and file output, since I can't stop the buffer from being written
	#---the blocked flag will remove tabs so that large multiline text doesn't awkwardly wrap in the code
	if blocked: string = niceds(text)
	#---display a refreshable string
	if start == None and looplen == None and i != None:		
		print '\r'+string+'  ...  '+str(i+1).rjust(7)+'/'+str(looplen).ljust(8)+'\n',
	elif start == None and looplen != None and i != None:		
		if i+1 == looplen:
			print '\r'+string+'  ...  '+str(i+1).rjust(7)+'/'+str(looplen).ljust(8)+'\n',
		#---if a logfile has been defined, this output is destined for a file in which case suppress counts
		elif i+1 != looplen and ('logfile' not in globals() or logfile == None):
			print '\r'+string+'  ...  '+str(i+1).rjust(7)+'/'+str(looplen).ljust(8),
			sys.stdout.flush()
	#---estimate the remaining time given a start time, loop length, and iterator
	elif start != None and i != None and looplen != None and ('logfile' not in globals() or logfile == None):
		esttime = (time.time()-start)/(float(i+1)/looplen)
		print '\r'+string.ljust(20)+str(abs(round((esttime-(time.time()-start))/60.,1))).ljust(10)+\
			'minutes remain',
		sys.stdout.flush()
	#---standard output
	else: print string
	
def checktime():
	'''Report the current time.'''
	status('status: time = '+str(1./60*(time.time()-global_start_time))+' minutes')
