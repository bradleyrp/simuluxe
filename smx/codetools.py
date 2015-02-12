#!/usr/bin/python

"""
Codetools for Simuluxe.

These tools aid in rapid development, debugging, and monitoring.
"""

#---LIBRARIES
#-------------------------------------------------------------------------------------------------------------

#---imports 
import sys,atexit,code,re
import time,subprocess
from smx import *

#---MONITORING FUNCTIONS
#-------------------------------------------------------------------------------------------------------------

#---record a global start time
global_start_time = time.time()

#---classic python argsort
def argsort(seq): return [x for x,y in sorted(enumerate(seq), key = lambda x: x[1])]

def call(command,logfile=None,cwd=None,silent=False,inpipe=None):
	'''
	Wrapper for system calls in a different directory with a dedicated log file.
	'''
	#---needs changed to match the lack of tee functionality in simuluxe
	if inpipe != None:
		output = open(('' if cwd == None else cwd)+logfile,'wb')
		if type(command) == list: command = ' '.join(command)
		p = subprocess.Popen(command,stdout=output,stdin=subprocess.PIPE,stderr=output,cwd=cwd,shell=True)
		catch = p.communicate(input=inpipe)[0]
	else:
		if type(command) == list: command = ' '.join(command)
		if logfile != None:
			output = open(('' if cwd == None else cwd)+logfile,'wb')
			if type(command) == list: command = ' '.join(command)
			if not silent: print 'executing command: "'+str(command)+'" logfile = '+logfile
			try:
				subprocess.check_call(command,
					shell=True,
					stdout=output,
					stderr=output,
					cwd=cwd)
			except: raise Exception('except: execution error')
			output.close()
		else: 
			if not silent: print 'executing command: "'+str(command)+'"'
			if str(sys.stdout.__class__) == "<class 'smx.tools.tee'>": stderr = sys.stdout.files[0]
			else: stderr = sys.stdout
			try: subprocess.check_call(command,shell=True,stderr=stderr,cwd=cwd)
			except: raise Exception('except: execution error')

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
		print '\r'+string.ljust((20 if len(string)<= 20 else len(string)+5))+\
			'  ...  '+str(i+1).rjust(7)+'/'+str(looplen).ljust(8)+\
			str(abs(round((esttime-(time.time()-start))/60.,1))).ljust(5)+\
			'minutes remain',
		if i!=looplen-1: sys.stdout.flush()
		else: print '\n',
	#---standard output
	else: print string
	
def checktime():
	'''Report the current time.'''
	status('status: time = %.2f'%(1./60*(time.time()-global_start_time))+' minutes')
	
def confirm(message=None):
	'''Generic function to check with the user.'''
	if message != None: status(message)
	go = True if raw_input("%s (y/N) " % 'continue?').lower() == 'y' else False
	if not go:
		print 'aborting' 
		return False
	sure = True if raw_input("%s (y/N) " % 'confirmed?').lower() == 'y' else False
	if go and sure: return True
	
def regcheck(chopped,regex,split=None,num=1):
	'''
	Searches a newline-split file in a list for a regex and makes sure there is only one match.
	'''
	chopped = '\n'.join([chopped] if type(chopped) == str else chopped)
	if re.search('error',chopped): return -1
	chopped = re.sub('\r','\n',chopped).split('\n')
	find = [j if split == None else j.split()[split] for j in chopped if re.search(regex,j)]
	if num == None: return find
	if len(find) != num: return -1
	else: return (find[0] if num == 1 else find)
	
def get_setfiles(namepart,multi=False):

	"""
	Return a settings file from the setfiles list that contains namepart.
	"""

	valid_names = [i for i in setfiles if re.search(namepart,i)]
	if len(valid_names) != 1 and not multi: raise Exception('except: search failed '+str(valid_names))
	elif multi: return valid_names
	else: return valid_names[0]

