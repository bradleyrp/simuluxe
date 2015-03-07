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
import datetime
from smx import *

#---MONITORING FUNCTIONS
#-------------------------------------------------------------------------------------------------------------

#---record a global start time
global_start_time = time.time()

#---classic python argsort
def argsort(seq): return [x for x,y in sorted(enumerate(seq), key = lambda x: x[1])]

def call(command,logfile=None,cwd=None,silent=False,inpipe=None):

	"""
	Wrapper for system calls in a different directory with a dedicated log file.
	"""

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
			if str(sys.stdout.__class__) == "<class 'smx.codetools.tee'>": 
				stderr = sys.stderr.files[0]
				stdout = sys.stdout.files[0]
			else: 
				stderr = sys.stdout
				stdout = sys.stdout
			try: 
				subprocess.check_call(command,shell=True,
					stdout=stdout,stderr=stderr,cwd=cwd)
			except: raise Exception('except: execution error')

def niceblock(text,newlines=False):
	
	"""
	Remove tabs so that large multiline text doesn't awkwardly wrap in the code.
	"""

	return re.sub('\n([\t])+',(' ' if not newlines else '\n'),re.sub('^\n([\t])+','',text))
	
def status(string,start=None,i=None,looplen=None,blocked=False):
	
	"""
	Print status to the screen also allows for re-writing the line. Duplicated in the membrain library.
	"""

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

	"""
	Report the current time.
	"""
	
	status('[STATUS] time = %.2f'%(1./60*(time.time()-global_start_time))+' minutes')
	
def confirm(message=None):

	"""
	Generic function to check with the user.
	"""

	if message != None: status(message)
	go = True if raw_input("%s (y/N) " % 'continue?').lower() == 'y' else False
	if not go:
		print 'aborting' 
		return False
	sure = True if raw_input("%s (y/N) " % 'confirmed?').lower() == 'y' else False
	if go and sure: return True
	
def regcheck(chopped,regex,split=None,num=1):

	"""
	Searches a newline-split file in a list for a regex and makes sure there is only one match.
	"""

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

def banner(text,width=40):

	"""
	Print a nicely-formatted banner to the terminal. Useful for highlighting sections of output.
	"""

	if len(text)>width: width = len(text)+5
	print '\n+'.ljust(width-1,'-')+'+\n|'+text.center(width-3)+'|\n+'.ljust(width,'-')+'+'
	
def asciitree(obj,depth=0,wide=2,last=[],recursed=False):

	"""
	Print a dictionary as a tree to the terminal.
	Includes some simuluxe-specific quirks.
	"""

	spacer = {0:'\n',
		1:' '*(wide+1)*(depth-1)+'+'+'-'*wide,
		2:' '*(wide+1)*(depth-1)
		}[depth] if depth <= 1 else (
		''.join([('|' if d not in last else ' ')+' '*wide for d in range(1,depth)])
		)+'+'+'-'*wide
	if type(obj) == str: 
		if depth == 0: print spacer+str(obj)+'\n'+'-'*len(obj)
		else: print spacer+str(obj)
	#---in case there is only one dictionary we give it extra depth
	#elif type(obj) == dict and all([type(i)==str for i in obj.values()]) and depth==0:
	elif type(obj) == dict and all([type(i)==str for i in obj.values()]) and depth==0:
		asciitree({'HASH':obj},depth=1,recursed=True)
	elif type(obj) == list:
		for ind,item in enumerate(obj):
			if type(item)==str: print spacer+item
			elif item != {}:
				print spacer+'('+str(ind)+')'
				asciitree(item,depth=depth+1,
					last=last+([depth] if ind==len(obj)-1 else []),
					recursed=True)
	elif type(obj) == dict and obj != {}:
		for ind,key in enumerate(obj.keys()):
			if type(obj[key])==str: print spacer+key+' = '+str(obj[key])
			#---special: print single-item lists of strings on the same line as the key
			elif type(obj[key])==list and len(obj[key])==1 and type(obj[key][0])==str: 
				print spacer+key+' = '+str(obj[key])
			#---special: skip lists if blank dictionaries
			elif type(obj[key])==list and all([i=={} for i in obj[key]]): pass
			elif obj[key] != {}:
				#---fancy border for top level
				if depth == 0: 
					print '\n+'+'-'*(len(key)+0)+'+'+spacer+'|'+str(key)+'|\n+'+'-'*len(key)+'+\n|'
				else: print spacer+key
				asciitree(obj[key],depth=depth+1,
					last=last+([depth] if ind==len(obj)-1 else []),
					recursed=True)
	if not recursed: print '\n'
	
class tee(object):

	"""
	Routes print statements to the screen and a log file.
	
	Routes output to multiple streams, namely a log file and stdout, emulating the linux "tee" function. 
	Whenever a new log file is desired, use the following code to replace ``sys.stdout`` and route all print
	statements to both the screen and the log file. ::
		
		sys.stdout = tee(open(self.rootdir+'log-script-master','a',1))
		
	Initialize the object with a file handle for the new log file. It is possible to run ``tee`` multiple
	times in order to redirect ``print`` output to a new file. The new object checks to see if 
	``sys.stdout`` is a tee object or the "real" stream, and rolls both into the new object.
	"""

	def __init__(self, *files,**kwargs):

		#---if sys.stdout is already a tee object, then just steal its stdout member
		if str(sys.stdout.__class__) == "<class 'smx.codetools.tee'>": self.stdout = sys.stdout.stdout
		#---otherwise set stdout from scratch
		else: 
			if 'error' in kwargs.keys() and kwargs['error'] == True: self.stdout = sys.stderr
			else: self.stdout = sys.stderr
		self.files = files
		if 'error' in kwargs.keys() and kwargs['error'] == True: self.error = True
		else: self.error = False
		#---working on making this compatible with call
		if 0: self.fileno = self.files[0].fileno
		if 0: self.close = self.files[0].close

	def write(self, obj): 

		"""
		The write function here emulates the write functions for both files and the standard output stream
		so that the tee object will always write to both places.
		"""

		st = datetime.datetime.fromtimestamp(time.time()).strftime('%Y.%m.%d.%H%M') if not self.error else ''
		if obj != '\n': self.stdout.write(st+' ')
		self.stdout.write(obj)
		for f in self.files:
			if obj != '\n': f.write(st+' ')
			f.write(obj)
			
