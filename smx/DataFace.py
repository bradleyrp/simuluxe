#!/usr/bin/python

import json
import sys,os,re
import psycopg2
import psycopg2.extras

#---CLASS
#-------------------------------------------------------------------------------------------------------------

class DataFace:

	def __init__(self,**kwargs):
		
		"""
		Postgresql database interface.
		"""
		
		#---specify
		if len(kwargs['dataspecs']) != 1: raise Exception('except: DataFace can only handle one object')
		else: self.map = kwargs['dataspecs'][0]['map']
		self.table = kwargs['dataspecs'][0]['table']
		
		#---connect
		try: self.conn = psycopg2.connect(kwargs['dbconnect_string'])
		except: raise Exception('except: unable to connect to database')
		self.cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
		for obj in kwargs['dataspecs']: self.table_exists(obj)
		
	def table_exists(self,obj):
		
		"""
		Make a table if it is absent.
		"""	
		
		self.cur.execute("select * from information_schema.tables where table_name=%s",
			('dataref_'+obj['table'],))
		if not bool(self.cur.rowcount): 
			cmd = 'CREATE TABLE '+('dataref_'+obj['table'])+' (id serial PRIMARY KEY'
			for key in (obj['map']): cmd += ', '+key+' '+obj['map'][key]
			self.ec(cmd+')')
				
	def ec(self,cmd):
		
		"""
		Execute and commit a change to the database.
		"""
		
		self.cur.execute(cmd)
		self.conn.commit()
		
	def query(self,qry):
		
		"""
		Return a database query using fetchall.
		"""
		
		self.cur.execute(qry)
		return self.cur.fetchall()

	def new(self,**obj):
		
		"""
		Simple function for adding values to a table.
		"""
		
		#---incoming object must match the map in dataspecs
		if set(obj.keys())!=set(self.map.keys()): raise Exception('incompatible object')
		#---convert dictionaries to json format
		for key in obj:
			if type(obj[key])==dict: obj[key] = json.dumps(obj[key])
		#---load object into new row
		self.cur.execute(
			'INSERT INTO dataref_'+self.table+' ('+\
			','.join(obj.keys())+') VALUES ('+\
			','.join(["%("+i+")s" for i in obj.keys()])+\
			') RETURNING id;',obj)		
		self.conn.commit()
		index = self.cur.fetchone()[0]
		return index		
		
	def lookup(self,**obj):
		
		"""
		Check for a record in the database.
		"""	
		
		unpackers = [key for key in obj if type(obj[key])==dict]
		lookup = self.query('SELECT * FROM dataref_'+self.table)
		matches = [dict(l) for li,l in enumerate(lookup) 
			if all([json.loads(l['meta'])[i]==obj['meta'][i] for i in obj['meta'].keys()])]
		if len(matches)!=1: return None
		else: return matches[0]
		
	def update(self,ind,**kwargs):
		
		"""
		Update a row.
		"""
		
		self.ec('UPDATE dataref_'+self.table+' SET ('+\
			','.join(kwargs.keys())+') = ('+\
			','.join(['\''+kwargs[key]+'\'' for key in kwargs.keys()])+\
			') WHERE id=\''+str(ind)+'\';')

if 0:
	'''
	Core database functionality in which generates a new entry with excess metadata.
	'''

	if type(extras) == dict:
		compact = dict()
		#---iterate one level to see if the extraspecs dictionary contains any dictionaries
		for key in extras:
			if type(extras[key]) == dict:
				compact[key] = '|'.join([subkey+':'+str(
					(extras[key][subkey] if type(extras[key][subkey])!= int 
					else float(extras[key][subkey])))
					for subkey in extras[key].keys()])
			else: compact[key] = str(extras[key])
		newrow = dict(compact.items()+specs.items())
	else: newrow = dict(specs)
	#---basic way to handle excludes
	if type(excludes) == list:
		for i in excludes:
			if i in newrow.keys(): del newrow[i]
	#---another way to handle excludes is to use refresh_mapping
	#---loop through refresh_mapping rules to prune the necessary metadata
	if 'refresh_mapping' in self.sets.keys():
		for key in self.sets['refresh_mapping']:
			if specs[key] in self.sets['refresh_mapping'][key]['vals']:
				for subkey in self.sets['refresh_mapping'][key].keys():
					for item in self.sets['refresh_mapping'][key][subkey]:
						if subkey == 'excludes': 
							if item in newrow.keys(): del newrow[item]
						elif subkey == 'vals': pass
						else: raise Exception('except: unclear rule') 		
	if 'calculation' in newrow.keys(): del newrow['calculation']
	self.cur.execute('INSERT INTO dataref_'+self.storename+' ('+\
		','.join(newrow.keys())+') VALUES ('+\
		','.join(["%("+i+")s" for i in newrow.keys()])+') RETURNING id;',
		newrow)
	index = self.cur.fetchone() [0]
	self.conn.commit()
	status('status: init row = '+str(index))
	return index

##############################################################################################################
#---CLASS !!!!!!!! DEPRECATED
#-------------------------------------------------------------------------------------------------------------

'''
Construct the tables necessary for the bookkeeping for one calculation.\n
Note that this is a one-time use database.

PSUEDOCODE
	1. get column names incoming from the script that instantiates this class
	2. make a table corresponding to pickle objects
	3. If this is a three-way calculation
		import functions for parsing the simulations
		parse the simulations
		use the results to load up other DOWNSTREAM tables
			i.e. the table for storing kappa values etc "mesosims_datastore" after the structure is 
				...computed and the simulation is identified
'''

class DataFace_deprecated:

	def __init__(self,**kwargs):
		'''
		Initiate a connection to the SQL database.
		'''
		
		#---catch settings
		bigkeylist = ['dbconnect_string','pickles']
		self.sets = dict()
		for key in bigkeylist: self.sets[key] = kwargs[key]
		
		#---connect
		try: self.conn = psycopg2.connect(self.sets['dbconnect_string'])
		except: raise Exception('except: unable to connect to database')
		self.cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
	
	def ec(self,cmd):
		'''Execute and commit a change to the database.'''
		self.cur.execute(cmd)
		self.conn.commit()

	def query(self,qry):
		'''Shortcut to return a database query.'''
		self.cur.execute(qry)
		return self.cur.fetchall()

	def scan_pklfiles(self):
		'''Return a list of files in the datastore (repo-pickles).'''
		rootdir = os.path.expanduser(self.sets['pickles'])
		pklfilenames = []
		for (dirpath, dirnames, filenames) in os.walk(rootdir):
			pklfilenames += filenames
			break
		return pklfilenames

	def unique(self,specs,extras=None,excludes=None):
		'''
		Function for looking up uniquely-named data files from a dictionary.
		'''	
		#---some parameters 
		#---mimics the new function which reduces a dictionary-within-a-dictionary to a string
		if type(extras) == dict:
			compact = dict()
			#---iterate one level to see if the extraspecs dictionary contains any dictionaries
			for key in extras:
				if type(extras[key]) == dict:
					compact[key] = '|'.join([subkey+':'+str(
						(extras[key][subkey] if type(extras[key][subkey])!= int 
						else float(extras[key][subkey])))
						for subkey in extras[key].keys()])
				else: compact[key] = str(extras[key])
			rowspecs = dict(compact.items()+specs.items())
		else: rowspecs = dict(specs)
		#---? handling excludes here but this needs checked
		if type(excludes) == list:
			for i in excludes:
				if i in rowspecs.keys(): del rowspecs[i]
				
		#---another way to handle excludes is to use refresh_mapping
		#---loop through refresh_mapping rules to prune the necessary metadata
		if 'refresh_mapping' in self.sets.keys():
			for key in self.sets['refresh_mapping']:
				if specs[key] in self.sets['refresh_mapping'][key]['vals']:
					for subkey in self.sets['refresh_mapping'][key].keys():
						for item in self.sets['refresh_mapping'][key][subkey]:
							if subkey == 'excludes': 
								if item in rowspecs.keys(): del rowspecs[item]
							elif subkey == 'vals': pass
							else: raise Exception('except: unclear rule') 
		#---pklname uses the letter 'i' instead of 'id'
		if 'i' in rowspecs.keys(): 
			rowspecs['id'] = rowspecs['i']
			del rowspecs['i']
		if 'calculation' in rowspecs.keys(): del rowspecs['calculation']
		#---check the database
		#---note that packing multiple values from a dictionary into a string makes this very difficult
		#---we check for subdictionaries and then filter multiple results
		dictkeys = [key for key in rowspecs.keys() 
			if type(rowspecs[key]) == str and re.search('\|',rowspecs[key])]
		subdicts = True if len(dictkeys) > 0 else False
		if 0 and subdicts: status('status: inferring rows for dictionaries')
		lookup = self.query('SELECT * FROM dataref_'+self.storename+' '+\
			' WHERE '+' AND '.join(['( '+key+'=\''+str(rowspecs[key])+'\' OR '+key+' IS NULL)' 
			for key in rowspecs.keys() if type(rowspecs[key]) == str and not re.search('\|',rowspecs[key])]))
		print 'SELECT * FROM dataref_'+self.storename+' '+\
			' WHERE '+' AND '.join(['( '+key+'=\''+str(rowspecs[key])+'\' OR '+key+' IS NULL)' 
			for key in rowspecs.keys() if type(rowspecs[key]) == str and not re.search('\|',rowspecs[key])])
		if lookup == []: return None
		elif len(lookup) > 0:
			print "LEN > 0"
			if subdicts:
				print "IN SUBDICTS"
				lookd = [dict(r) for r in lookup]
				matches = []
				for row in lookd:
					if all([
						set([tuple(i.split(':')) for i in row[d].split('|')]) == \
						set([tuple(i.split(':')) for i in rowspecs[d].split('|')])
						for d in dictkeys if d in row.keys()]):
						matches.append(row)
				print matches
				if len(matches) == 1: return matches[0]
				elif len(matches) > 1: raise Exception('multiple entries still match this query')
				else: return None
			else: 
				if len(lookup) == 1: return lookup[0]
				else: raise Exception('multiple entries match this query')
		else: return lookup[0]
		
	def pklsig(self,pklname):

		'''
		Function which decomposes a pickle file name into metadata required for entry into the database.\n
		Note that the filename may not code all of the metadata required to understand the object.
		In this case, the filename metadata must have a unique key necessary to pull the rest of the 
		information from the database. This should be assured by the namer function.
		'''

		sigs = dict()
		#---get callsign
		callsign = pklname.split('.')[2]
		if not re.match('^v[0-9]{3,4}\-[0-9]+\-[0-9]+\-[0-9]+$',callsign):
			raise Exception('except: invalid callsign in pickle file name')
		else: sigs['callsign'] = callsign
		#---set pickle file name
		sigs['pklname'] = pklname
		#---get other signifiers, which must come in key,value pairs separated by hyphens
		#---...located within the fourth dot-delimited section of the filename
		siglist = pklname.split('.')[3].split('-')
		if len(siglist)%2 != 0: 
			raise Exception('except: invalid number of extra signifiers in the filename')
		else:
			for i in range(len(siglist)/2): 
				sigs[siglist[i*2]] = siglist[i*2+1]
		return sigs
		
	def namer(self,specs,index=None,excludes=None):
		'''Makes a pickle name from specs and possibly an index if the database records other metadata.'''
		#---excludes is a list of keys to exclude from the name
		#---note that if this option is used then the database index is necessary to understand the pickles
		if excludes == None: excludes = []
		#---data type (calculation) and callsign are listed first by convention
		basename = 'pkl.'+specs['calculation']+'.'+specs['callsign']
		for key in ['calculation','callsign']:
			if key in specs.keys(): del specs[key]
		basename += ('.' if len(specs.keys())>0 else '')
		basename += '-'.join([key+'-'+specs[key] for key in specs.keys() if key not in excludes])
		if type(index) == int: basename += '-i-'+str(index)
		return basename
		
	def refresh_dataref(self,**dataspecs):

		'''
		Function which updates the dataref table for a particular calculation 
		by scanning for valid pickles.\n
		Note that this function handles a large part of the pickle-to-database interface.
		'''

		#---catch important settings
		self.storename = dataspecs['storename']
		for key in dataspecs.keys(): self.sets[key] = dataspecs[key]
		#---deprecated
		if 0:
			bigkeylist = ['pkl_metadata','refresh_mapping','calculation']
			for key in bigkeylist: 
				if key in dataspecs.keys():
					self.sets[key] = dataspecs[key]
			
		#---make the table if necessary
		self.cur.execute("select * from information_schema.tables where table_name=%s",
			('dataref_'+self.storename,))
		if not bool(self.cur.rowcount): 
			status('status: building dataref_'+self.storename+' table')
			self.make_dataref()

		#---get the tablenames for this calculation
		self.ec("SELECT relname AS table FROM pg_stat_user_tables WHERE schemaname = 'public'")
		self.tables = [i[0] for i in self.cur.fetchall()]
		
		#---find relevant pickles according to their prefix which must follow "pkl." in the filename
		pkllist = [fn for fn in self.scan_pklfiles() if re.match('^pkl.'+self.sets['calculation']+'.+',fn)]
		#---extract further signifiers from the filename according to simple rules
		#---...that is, the second dot delimited feature should be the call sign
		#---...then all subsequent parameters are explicitly listed as hyphen-delimited key-data pairs
		for pklname in pkllist:
			#---get metadata from the filename
			sigs = self.pklsig(pklname)
			#---if the pickle already has an ID, try to enter it in the database
			if 'i' in sigs.keys(): 
				sigs['id'] = sigs['i']
				del sigs['i']
			self.ec('SELECT * FROM '+','.join(self.tables)+' WHERE '+\
				' OR '.join(['('+' AND '.join([table+'.'+key+'=\''+sigs[key]+'\'' 
				for key in sigs.keys()])+')'
				for table in self.tables]))
			if not bool(self.cur.rowcount):				
				match = dict(self.sets['pkl_metadata'])
				#---loop through refresh_mapping rules to prune the necessary metadata
				if 'refresh_mapping' in self.sets.keys():
					for key in self.sets['refresh_mapping']:
						if sigs[key] in self.sets['refresh_mapping'][key]['vals']:
							for subkey in self.sets['refresh_mapping'][key].keys():
								for item in self.sets['refresh_mapping'][key][subkey]:
									if subkey == 'excludes': 
										if item in match.keys(): del match[item]
									elif subkey == 'vals': pass
									else: raise Exception('except: unclear rule') 
				if all([i in sigs.keys() for i in match.keys()]):
					status('status: adding pklfile to database: '+pklname)
					self.cur.execute('INSERT INTO dataref_'+self.storename+' ('+\
						','.join(sigs.keys())+') VALUES ('+\
						', '.join(["%("+i+")s" for i in sigs.keys()])+');',
						sigs)
					self.conn.commit()
				else:
					status('status: warning: found a pklfile = '+pklname+' not in the database '+\
						' but without all the necessary specs to add it back')
			del sigs
			
		#---perform the check in the opposite direction to confirm database pkl files still exist
		#---remove entries for missing pickle files
		self.cur.execute('SELECT * FROM dataref_'+self.storename)
		rows_to_delete = []
		for row in self.cur: 
			if row['pklname'] == None or not os.path.isfile(self.sets['pickles']+row['pklname']):
				status('error: missing pklname/id = '+\
					(str(row['id']) if row['pklname'] == None else row['pklname']))
				status('status: removing row ---> '+str(row))
				rows_to_delete.append(row['id'])
		if rows_to_delete != [] and \
			(not 'preserve_rows' in dataspecs.keys() or not dataspecs['preserve_rows']): 
			status('status: found rows not linked to data but the system may be computing now')
			status('status: please double-confirm row deletions if system is not computing elsewhere')
			go = True if raw_input("%s (y/N) " % 'delete rows?').lower() == 'y' else False
			if not go: status('status: no modifications to database')
			else: sure = True if raw_input("%s (y/N) " % 'confirmed?').lower() == 'y' else False
			if go and sure:
				status('status: removing rows')
				for rowid in rows_to_delete:
					self.ec('DELETE FROM dataref_'+self.storename+' WHERE id='+str(rowid))
			return
			
	def new(self,specs,extras=None,excludes=None):
	
		'''
		Core database functionality in which generates a new entry with excess metadata.
		'''

		if type(extras) == dict:
			compact = dict()
			#---iterate one level to see if the extraspecs dictionary contains any dictionaries
			for key in extras:
				if type(extras[key]) == dict:
					compact[key] = '|'.join([subkey+':'+str(
						(extras[key][subkey] if type(extras[key][subkey])!= int 
						else float(extras[key][subkey])))
						for subkey in extras[key].keys()])
				else: compact[key] = str(extras[key])
			newrow = dict(compact.items()+specs.items())
		else: newrow = dict(specs)
		#---basic way to handle excludes
		if type(excludes) == list:
			for i in excludes:
				if i in newrow.keys(): del newrow[i]
		#---another way to handle excludes is to use refresh_mapping
		#---loop through refresh_mapping rules to prune the necessary metadata
		if 'refresh_mapping' in self.sets.keys():
			for key in self.sets['refresh_mapping']:
				if specs[key] in self.sets['refresh_mapping'][key]['vals']:
					for subkey in self.sets['refresh_mapping'][key].keys():
						for item in self.sets['refresh_mapping'][key][subkey]:
							if subkey == 'excludes': 
								if item in newrow.keys(): del newrow[item]
							elif subkey == 'vals': pass
							else: raise Exception('except: unclear rule') 		
		if 'calculation' in newrow.keys(): del newrow['calculation']
		self.cur.execute('INSERT INTO dataref_'+self.storename+' ('+\
			','.join(newrow.keys())+') VALUES ('+\
			','.join(["%("+i+")s" for i in newrow.keys()])+') RETURNING id;',
			newrow)
		index = self.cur.fetchone()[0]
		self.conn.commit()
		status('status: init row = '+str(index))
		return index
		
	def update(self,ind,**kwargs):
		'''Update an entry.\n
		This function is designed primarily to insert the name of a data file that was created for a 
		pre-existing record.'''
		self.ec('UPDATE '+kwargs['table']+' SET ('+\
			','.join([key for key in kwargs.keys() if key != 'table'])+') = ('+\
			','.join(['\''+kwargs[key]+'\'' for key in kwargs.keys() if key != 'table'])+\
			') WHERE id=\''+str(ind)+'\';')
		status('status: updated row = '+str(ind))

	def make_dataref(self):

		'''
		Generate a "dataref" table in the database to store connections to pickle files in the repository.\n
		This function uses the storename passed to refresh_dataref to name the table while the column names 
		and corresponding types are provided via pkl_metadata defined in the calculation-specific header file
		which is also passed via keyword arguments to refresh_dataref and then filtered and stored as 
		self.sets for use here.
		'''

		#---create the table with columns
		status('status: creating table')
		cmd = 'CREATE TABLE '+('dataref_'+self.storename)+' (id serial PRIMARY KEY'
		for key in (self.sets['pkl_metadata']): cmd += ', '+key+' '+(self.sets['pkl_metadata'])[key]
		self.ec(cmd+')')
		
