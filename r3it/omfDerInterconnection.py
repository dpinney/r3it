''' perform analysis pertaining to the addition of a DER interconnection on a feeder. '''
import glob, json, os, tempfile, shutil, csv, math, warnings, random, copy, base64, platform
from os.path import join as pJoin
from os.path import split as pSplit
import networkx as nx
from networkx.drawing.nx_agraph import graphviz_layout
from functools import wraps, reduce
import time
import datetime
from contextlib import contextmanager
import traceback
import subprocess
import webbrowser
from copy import deepcopy
import sys
import re
import hashlib
import errno
try:
	import fcntl
except:
	#We're on windows, where we don't support file locking.
	fcntl = type('', (), {})()
	def flock(fd, op):
		return
	fcntl.flock = flock
	(fcntl.LOCK_EX, fcntl.LOCK_SH, fcntl.LOCK_UN, fcntl.LOCK_NB) = (0, 0, 0, 0)

# Hack: Agg backend doesn't work for interactivity. Switch to something we can use:
import matplotlib
if platform.system() == 'Darwin':
	matplotlib.use('TkAgg')
else:
	matplotlib.use('Agg')
from matplotlib import pyplot as plt
from jinja2 import Template

# dateutil imports
from dateutil import parser
from dateutil.relativedelta import *

# OMF imports 
# import feeder
# import gridlabd
# import __neoMetaModel__
# from __neoMetaModel__ import *

_myDir = os.path.dirname(os.path.abspath(__file__))

def metadata(fileUnderObject):
	''' Get the model name and template for a given model from its filename and associated .html file.
	The argument fileUnderObject should always be __file__.'''
	fileName = os.path.basename(fileUnderObject)
	modelName = fileName[0:fileName.rfind('.')]
	with open(pJoin(_myDir,'templates',modelName+".html")) as f:
		template = Template(f.read()) #HTML Template for showing output.
	return modelName, template
# Model metadata:

modelName, template = metadata(__file__)
tooltip = ('The derInterconnection model runs the key modelling and analysis steps involved '
	'in a DER Impact Study including Load Flow computations, Short Circuit analysis, '
	'and Effective Grounding screenings.')
#hidden = True

# Wireframe for new feeder objects:
newFeederWireframe = {
	"links":[],
	"hiddenLinks":[],
	"nodes":[],
	"hiddenNodes":[],
	"layoutVars":{"theta":"0.8","gravity":"0.01","friction":"0.9","linkStrength":"5","linkDistance":"5","charge":"-5"},
	"tree": {},
	"attachments":{}
}

def _seriesTranspose(theArray):
	''' Transpose every matrix that's a value in a dictionary. Yikes. '''
	return {i[0]:list(i)[1:] for i in zip(*theArray)}

def _strClean(x):
	''' Helper function that translates csv values to reasonable floats (or header values to strings). '''
	if x == 'OPEN':
		return 1.0
	elif x == 'CLOSED':
		return 0.0
	# Look for strings of the type '+32.0+68.32d':
	elif x == '-1.#IND':
		return 0.0
	if x.endswith('d'):
		matches = re.findall('^([+-]?\d+\.?\d*e?[+-]?\d+)[+-](\d+\.?\d*e?[+-]?\d*)d$',x)
		if len(matches)==0:
			return 0.0
		else:
			floatConv = map(float, matches[0])
			squares = [x**2 for x in floatConv]
			return math.sqrt(sum(squares))
	elif re.findall('^([+-]?\d+\.?\d*e?[+-]?\d*)$',x) != []:
		matches = re.findall('([+-]?\d+\.?\d*e?[+-]?\d*)',x)
		if len(matches)==0:
			return 0.0
		else:
			try: return float(matches[0])
			except: return 0.0 # Hack for crazy WTF occasional Gridlab output.
	else:
		return x

def csvToArray(fileName):
	''' Take a Gridlab-export csv filename, return a list of timeseries vectors.'''
	with open(fileName) as openfile:
		data = openfile.read()
	lines = data.splitlines()
	array = [x.split(',') for x in lines]
	cleanArray = [list(map(_strClean, x)) for x in array]
	# Magic number 8 is the number of header rows in each GridlabD csv.
	arrayNoHeaders = cleanArray[8:]
	# Drop the timestamp column:
	return arrayNoHeaders

def anaDataTree(studyPath, fileNameTest):
	''' Take a study and put all its data into a nested object {fileName:{metricName:[...]}} '''
	data = {}
	csvFiles = os.listdir(studyPath)
	for cName in csvFiles:
		if fileNameTest(cName) and cName.endswith('.csv'):
			arr = csvToArray(studyPath + '/' + cName)
			data[cName] = _seriesTranspose(arr)
	return data

def _phaseCount(phaseString):
	''' Return number of phases not including neutrals. '''
	return sum([phaseString.lower().count(x) for x in ['a','b','c']])

def _tokenizeGlm(inputStr, filePath=True):
	''' Turn a GLM file/string into a linked list of tokens.
	E.g. turn a string like this:
	clock {clockey valley;};
	object house {name myhouse; object ZIPload {inductance bigind; power newpower;}; size 234sqft;}; 
	Into a Python list like this:
	['clock','{','clockey','valley','}','object','house','{','name','myhouse',';',
		'object','ZIPload','{','inductance','bigind',';','power','newpower','}','size','234sqft','}']
	'''
	if filePath:
		with open(inputStr,'r') as glmFile:
			data = glmFile.read()
	else:
		data = inputStr
	# Get rid of http for stylesheets because we don't need it and it conflicts with comment syntax.
	data = re.sub(r'http:\/\/', '', data)  
	# Strip comments.
	data = re.sub(r'\/\/.*\n', '', data)
	# Also strip non-single whitespace because it's only for humans:
	data = data.replace('\n','').replace('\r','').replace('\t',' ')
	# Tokenize around semicolons, braces and whitespace.
	tokenized = re.split(r'(;|\}|\{|\s)',data)
	# Get rid of whitespace strings.
	basicList = [x for x in tokenized if x != '' and x != ' ']
	return basicList

def _parseTokenList(tokenList):
	''' Given a list of tokens from a GLM, parse those into a tree data structure. '''
	def currentLeafAdd(key, value):
		# Helper function to add to the current leaf we're visiting.
		current = tree
		for x in guidStack:
			current = current[x]
		current[key] = value
	def listToString(listIn):
		# Helper function to turn a list of strings into one string with some decent formatting.
		if len(listIn) == 0:
			return ''
		else:
			return reduce(lambda x,y:str(x)+' '+str(y),listIn[1:-1])
	# Tree variables.
	tree = {}
	guid = 0
	guidStack = []
	# Pop off a full token, put it on the tree, rinse, repeat.
	while tokenList != []:
		# Pop, then keep going until we have a full token (i.e. 'object house', not just 'object')
		fullToken = []
		while fullToken == [] or fullToken[-1] not in ['{',';','}']:
			fullToken.append(tokenList.pop(0))
		# Work with what we've collected.
		if fullToken[-1] == ';':
			# Special case when we have zero-attribute items (like #include, #set, module).
			if guidStack == [] and fullToken != [';']:
				tree[guid] = {'omftype':fullToken[0],'argument':listToString(fullToken)}
				guid += 1
			# We process if it isn't the empty token (';')
			elif len(fullToken) > 1:
				currentLeafAdd(fullToken[0],listToString(fullToken))
		elif fullToken[-1] == '}':
			if len(fullToken) > 1:
				currentLeafAdd(fullToken[0],listToString(fullToken))
			try:
				# Need try in case of zero length stack.
				guidStack.pop()
			except:
				pass
		elif fullToken[0] == 'schedule':
			# Special code for those ugly schedule objects:
			while fullToken[-1] not in ['}']:
				fullToken.append(tokenList.pop(0))
			tree[guid] = {'object':'schedule','name':fullToken[1], 'cron':' '.join(fullToken[3:-2])}
			guid += 1
		elif fullToken[0] == 'class':
			# Special code for the weirdo class objects:
			while fullToken[-1] not in ['}']:
				fullToken.append(tokenList.pop(0))
			tree[guid] = {'omftype':'class ' + fullToken[1],'argument':'{\n\t' + ' '.join(fullToken[3:-2]) + ';\n}'}
			guid += 1
		elif fullToken[-1] == '{':
			currentLeafAdd(guid,{})
			guidStack.append(guid)
			guid += 1
			# Wrapping this currentLeafAdd is defensive coding so we don't crash on malformed glms.
			if len(fullToken) > 1:
				# Do we have a clock/object or else an embedded configuration object?
				if len(fullToken) < 4:
					currentLeafAdd(fullToken[0],fullToken[-2])
				else:
					currentLeafAdd('omfEmbeddedConfigObject', fullToken[0] + ' ' + listToString(fullToken))
	return tree

def parse(inputStr, filePath=True):
	''' Parse a GLM into an omf.feeder tree. This is so we can walk the tree, change things in bulk, etc.
	Input can be a filepath or GLM string.
	'''
	tokens = _tokenizeGlm(inputStr, filePath)
	return _parseTokenList(tokens)

def findParentCoords(inTree, item, defaultCoords):
	nameRefTree = {}
	for key in inTree:
		itemOb = inTree[key]
		if 'name' in itemOb.keys():
			itemName = itemOb['name']
			nameRefTree[itemName] = key

	if 'parent' in item.keys():
		parentName = item['parent']
		#check to see if the parent object is in nameRefTree
		if parentName in nameRefTree.keys():
			parentKey = nameRefTree[parentName]
			parentItem = inTree[parentKey]
			try:
				parentCoords = (float(parentItem['latitude']), float(parentItem['longitude']))
				print("Coordinates found for " + parentName + ", parent of " + item['name'] + " : " + str(parentCoords))
			except KeyError:
				print("No coordinates for " + parentName + ", parent of " + item['name'] + ", looking for parent coordinates now...")
				parentCoords = findParentCoords(inTree, parentItem, defaultCoords)
		else:
			print(parentName + ", parent of " + item['name'] + ", was not found in nameRefTree, assigning default coordinates.")
			parentCoords = defaultCoords
	elif 'from' in item.keys():
		#case in which the parent of an object is an edge (transformers are represented this way sometimes)
		fromName = item['from']
		if fromName in nameRefTree.keys():
			fromKey = nameRefTree[fromName]
			fromItem = inTree[fromKey]
			try:
				parentCoords = (float(fromItem['latitude']), float(fromItem['longitude']))
				print("Coordinates found for " + fromName + ", \"from\" of " + item['name'] + " : " + str(parentCoords))
			except KeyError:
				print("No coordinates for " + fromName + ", \"from\" of " + item['name'] + ", looking for parent coordinates now...")
				parentCoords = findParentCoords(inTree, fromItem, defaultCoords)
	else:
		print("No parent found for " + item['name'] + ", assigning default coordinates.")
		parentCoords = defaultCoords
	return parentCoords

def calcDefaultCoords(inTree):
	lats = []
	lons = []
	for key in inTree:
		item = inTree[key]
		if 'latitude' in item.keys():
			lats.append(float(item['latitude']))
		if 'longitude' in item.keys():
			lons.append(float(item['longitude']))
	if len(lats) != 0:
		latitude_min = min(lats)
		latitude_max = max(lats)
	else:
		latitude_min = 0.0
		latitude_max = 0.0
	if len(lons) != 0:
		longitude_min = min(lons)
		longitude_max = max(lons)
	else:
		longitude_min = 0.0
		longitude_max = 0.0
	return (latitude_max, longitude_min)

def treeToNxGraph(inTree):
	''' Convert feeder tree to networkx graph. '''
	outGraph = nx.Graph()
	#TODO: make default coordinates change slightly each time they are assigned to a node to prevent multiple location-less nodes to just be stacked on top of each other
	defaultCoords = calcDefaultCoords(inTree)
	for key in inTree:
		item = inTree[key]
		# This check is why configuration objects never get coordinates. Or maybe this is intentional because configuration objects are added later?
		if 'name' in item.keys():
			if 'parent' in item.keys():
				outGraph.add_edge(item['name'], item['parent'], type='parentChild', phases=1)
				outGraph.nodes[item['name']]['type'] = item['object']
				# Note that attached houses via gridEdit.html won't have lat/lon values, so this try is a workaround.
				try:
					outGraph.nodes[item['name']]['pos'] = (float(item['latitude']), float(item['longitude']))
				except KeyError:
					#if the grid object doesn't have a lat/lon, give it a lat/lon close or same to that of its parent if it has one
					print("No coordinates found for " + item['name'] + ", looking for parent coordinates now...")
					outGraph.nodes[item['name']]['pos'] = findParentCoords(inTree, item, defaultCoords)
				except:
					outGraph.nodes[item['name']]['pos'] = defaultCoords
			elif 'from' in item.keys():
				myPhase = _phaseCount(item.get('phases','AN'))
				outGraph.add_edge(item['from'], item['to'], name=item.get('name',''), type=item['object'], phases=myPhase)
			elif item['name'] in outGraph:
				# Edge already led to node's addition, so just set the attributes:
				outGraph.nodes[item['name']]['type'] = item['object']
			else:
				outGraph.add_node(item['name'], type=item['object'])
			if 'latitude' in item.keys() and 'longitude' in item.keys():
				# Ignore lines that have "latitude" and "longitude" properties
				if 'from' not in item.keys():
					try:
						outGraph.nodes[item['name']]['pos'] = (float(item['latitude']), float(item['longitude'])) 
					except:
						outGraph.nodes[item['name']]['pos'] = defaultCoords
	return outGraph

def sortedWrite(inTree):
	''' Write out a GLM from a tree, and order all tree objects by their key. 
	Sometimes Gridlab breaks if you rearrange a GLM.
	'''
	sortedKeys = sorted(inTree.keys(), key=int)
	output = ''
	try:
		for key in sortedKeys:
			# print inTree[key]
			output += _dictToString(inTree[key]) + '\n'
	except ValueError:
		raise Exception
	return output

def _gatherKeyValues(inDict, keyToAvoid):
	''' Helper function: put key/value pairs for objects into the format Gridlab needs. '''
	otherKeyValues = ''
	for key in inDict:
		if type(inDict[key]) is dict:
			# WARNING: RECURSION HERE
			otherKeyValues += _dictToString(inDict[key])
		elif key != keyToAvoid:
			if key == 'comment':
				otherKeyValues += (inDict[key] + '\n')
			elif key == 'name' or key == 'parent':
				if len(inDict[key]) <= 62:
					otherKeyValues += ('\t' + key + ' ' + str(inDict[key]) + ';\n')
				else:
					warnings.warn("{:s} argument is longer that 64 characters. Truncating.".format(key), RuntimeWarning)
					otherKeyValues += ('\t' + key + ' ' + str(inDict[key])[0:62] + '; // truncated from {:s}\n'.format(inDict[key]))
			else:
				otherKeyValues += ('\t' + key + ' ' + str(inDict[key]) + ';\n')
	return otherKeyValues

def _dictToString(inDict):
	''' Helper function: given a single dict representing a GLM object, concatenate it into a string. '''
	# Handle the different types of dictionaries that are leafs of the tree root:
	if 'omftype' in inDict:
		return inDict['omftype'] + ' ' + inDict['argument'] + ';'
	elif 'module' in inDict:
		return 'module ' + inDict['module'] + ' {\n' + _gatherKeyValues(inDict, 'module') + '};\n'
	elif 'clock' in inDict:
		## This object has known property order issues writing it out explicitly
		clock_string = 'clock {\n'
		timezone = inDict.get('timezone')
		if timezone is not None:
			clock_string += '\ttimezone ' + timezone + ';\n'
		else:
			warnings.warn('clock object did not have a timezone property', RuntimeWarning)
		clock_string += '\tstarttime ' + inDict['starttime'] + ';\n' + '\tstoptime ' + inDict['stoptime'] + ';\n};\n'
		return clock_string
	elif 'object' in inDict and inDict['object'] == 'schedule':
		return 'schedule ' + inDict['name'] + ' {\n' + inDict['cron'] + '\n};\n'
	elif 'object' in inDict:
		return 'object ' + inDict['object'] + ' {\n' + _gatherKeyValues(inDict, 'object') + '};\n'
	elif 'omfEmbeddedConfigObject' in inDict:
		return inDict['omfEmbeddedConfigObject'] + ' {\n' + _gatherKeyValues(inDict, 'omfEmbeddedConfigObject') + '};\n'
	elif '#include' in inDict:
		return '#include ' + '"' + inDict['#include'] + '"' + '\n'
	elif '#define' in inDict:
		return '#define ' + inDict['#define'] + '\n'
	elif '#set' in inDict:
		return '#set ' + inDict['#set'] + '\n'
	#Following was made to help with gridballast gridlabd functionality, so that frequency player doesn't need to be reopened
	elif 'class' in inDict and inDict['class'] =='player':
		return 'class' + ' ' + inDict['class'] + ' {\n' + '     ' + 'double' + ' ' + inDict['double'] + ';' + '\n};\n'
	# elif 'collector' in inDict and 'group' in inDict and inDict['group'] =='class=ZIPload':
	# 	return 'object' + ' ' + inDict['object'] + ' {\n' + '	' + 'name' + ' ' + 'collector_ZIPloads' + ';'+'\n' +'group' + ' ' + inDict['group']+';'+'\n'+'property' +' '+inDict['property']+';'+'\n'+'interval'+' '+inDict['interval']+';'+'\n'+'file'+' '+inDict['file']+'\n};\n'

def runToCompletionForMacOS(feederTree, attachments=[], keepFiles=False, workDir=None, glmName=None, gldBinary=None):
	#TODO: port repeated running code from Kevin in here.
	MAX_ERROR_RUN = 12
	for i in range(MAX_ERROR_RUN):
		gridlabOut = runInFilesystem(
			feederTree, attachments=attachments, keepFiles=keepFiles, workDir=workDir, 
			glmName=glmName, gldBinary=gldBinary, mac_check=True)
		if 'error when setting parent' not in gridlabOut.get('stderr','OOPS'):
			break
	return gridlabOut

def runInFilesystem(feederTree, attachments=[], keepFiles=False, workDir=None, glmName=None, gldBinary=None, mac_check=False):
	''' Execute gridlab in the local filesystem. Return a nice dictionary of results. '''
	if sys.platform == 'darwin' and not mac_check:
		return runToCompletionForMacOS(feederTree, attachments=attachments, keepFiles=keepFiles, workDir=workDir, glmName=glmName, gldBinary=gldBinary)
	try:
		#Runs standard gridlabd binary if binary is not specified, runs gldBinary parameter path if specified. 
		#gldBinary must be path to binary
		if gldBinary is None:
			binaryName = "gridlabd"
		else:
			binaryName = str(gldBinary)
		# Create a running directory and fill it, unless we've specified where we're running.
		if not workDir:
			workDir = tempfile.mkdtemp()
			print("gridlabD runInFilesystem with no specified workDir. Working in", workDir)
		# Need to zero out lat/lon data on copy because it frequently breaks Gridlab.
		localTree = deepcopy(feederTree)
		for key in localTree.keys():
			try:
				del localTree[key]["latitude"]
				del localTree[key]["longitude"]
			except:
				pass # No lat lons.
		# Write attachments and glm.
		for attach in attachments:
			with open (pJoin(workDir,attach),'w') as attachFile:
				attachFile.write(attachments[attach])
		glmString = sortedWrite(localTree)
		if not glmName:
			glmName = "main." + datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S') + ".glm"
		with open(pJoin(workDir, glmName),'w') as glmFile:
			glmFile.write(glmString)
		# RUN GRIDLABD IN FILESYSTEM (EXPENSIVE!) 
		with open(pJoin(workDir,'stdout.txt'),'w') as stdout, open(pJoin(workDir,'stderr.txt'),'w') as stderr, open(pJoin(workDir,'PID.txt'),'w') as pidFile:
			# MAYBEFIX: turn standerr WARNINGS back on once we figure out how to supress the 500MB of lines gridlabd wants to write...
			proc = subprocess.Popen([binaryName, '-w', glmName], cwd=workDir, stdout=stdout, stderr=stderr)
			pidFile.write(str(proc.pid))
		returnCode = proc.wait()
		# Build raw JSON output.
		rawOut = anaDataTree(workDir, lambda x:True)
		with open(pJoin(workDir,'stderr.txt'),'r') as stderrFile:
			rawOut['stderr'] = stderrFile.read().strip()
		with open(pJoin(workDir,'stdout.txt'),'r') as stdoutFile:
			rawOut['stdout'] = stdoutFile.read().strip()
		# Delete the folder and return.
		if not keepFiles and not workDir:
			# NOTE: if we've specify a working directory, don't just blow it away.
			for attempt in range(5):
				try:
					shutil.rmtree(workDir)
					break
				except WindowsError:
					# HACK: if we don't sleep 1 second, windows intermittantly fails to delete things and an exception is thrown.
					# Probably cus dropbox is monkeying around in these folders on my dev machine. Disabled for now since it works when dropbox is off.
					time.sleep(2)
		return rawOut
	except:
		trace = traceback.format_exc()
		with open(pJoin(workDir, "stderr.txt"), "a+") as stderrFile:
			stderrFile.write(trace)
		return {"stderr":trace}


def getMaxKey(inTree):
	''' Find the largest key value in the tree. We need this because de-embedding causes noncontiguous keys. '''
	keys = [int(x) for x in inTree.keys()]
	return max(keys)

def insert(tree, gridlabdObject, index=None):
	''' Add an object to the tree; if index=None put it on the end.
	WARNING: the tree will be modified in-place. Consider making a copy.deepcopy of the original tree. '''
	if index == None:
		tree[str(getMaxKey(tree) + 1)] = gridlabdObject	
	elif tree.get(str(index), None) is None:
		tree[str(index)] = gridlabdObject
	else:
		swap = tree[str(index)]
		tree[str(index)] = gridlabdObject
		tree = insert(tree, swap, index + 1)

@contextmanager
def locked_open(filepath, mode='r', timeout=180, **io_open_args):
	'''
	Open a file and lock it depending on the file access mode. An IOError will be raised if the lock cannot be acquired within the timeout. If the
	filepath does not exist, this function should thrown the exception upwards and not try to handle it
	'''
	# __enter__()
	if 'r' in mode and '+' not in mode:
		lock_mode = fcntl.LOCK_SH # LOCK_SH == 1
	else:
		lock_mode = fcntl.LOCK_EX # LOCK_EX == 2
	f = open(filepath, mode, **io_open_args)
	start_time = time.time()
	while True:
		try:
			fcntl.flock(f, lock_mode | fcntl.LOCK_NB)
			break
		except IOError as e:
			# Ignore any IOError regarding the resource being unavailabe, but raise any other IOError
			if e.errno != errno.EACCES and e.errno != errno.EAGAIN:
				raise
		if time.time() >= start_time + timeout:
			raise IOError("{timeout}-second file lock timeout reached. Either a file-locking operation is taking more than {timeout} seconds "
				"or there was a programmer error that would have resulted in deadlock.".format(timeout=timeout))
	yield f
	# __exit___()
	fcntl.flock(f, fcntl.LOCK_UN)
	f.close() 

def getStatus(modelDir):
	''' Is the model stopped, running or finished? '''
	try:
		modFiles = os.listdir(modelDir)
	except:
		modFiles = []
	hasPID = "PPID.txt" in modFiles
	hasOutput = "allOutputData.json" in modFiles
	if hasPID:
		return 'running'
	elif hasOutput:
		return 'finished'
	else:
		return 'stopped'

def renderTemplate(modelDir, absolutePaths=False, datastoreNames={}):
	''' Render the model template to an HTML string.
	By default render a blank one for new input.
	If modelDir is valid, render results post-model-run.
	If absolutePaths, the HTML can be opened without a server. '''
	try:
		with locked_open(pJoin(modelDir, 'allInputData.json')) as f:
			inJson = json.load(f)
		modelPath, modelName = pSplit(modelDir)
		deepPath, modelOwner = pSplit(modelPath)
		inJson["modelName"] = modelName
		inJson["user"] = modelOwner
		modelType = inJson["modelType"]
		allInputData = json.dumps(inJson)
		# Get hashes for model python and html files 
		with open(pJoin(_myDir, 'templates', modelType+".html")) as f:
			htmlFile = f.read()
		currentHtmlHash = hashlib.sha256(htmlFile.encode('utf-8')).hexdigest()
		with open(pJoin(_myDir, modelType+".py")) as f:
			pythonFile = f.read()
		currentPythonHash = hashlib.sha256(pythonFile.encode('utf-8')).hexdigest()
	except IOError:
		allInputData = None
		inJson = None
	try:
		with locked_open(pJoin(modelDir,"allOutputData.json")) as f:
			allOutputData = f.read()
		with locked_open(pJoin(modelDir, "allOutputData.json")) as f:
			outJson = json.load(f)
		try:
			#Needed? Should this be handled a different way? Add hashes to the output if they are not yet present
			if ('pythonHash' not in outJson) or ('htmlHash' not in outJson):
				outJson['htmlHash'] = currentHtmlHash
				outJson['pythonHash'] = currentPythonHash
				outJson['oldVersion'] = False
			#If the hashes do not match, mark the model as an old version
			elif outJson['htmlHash'] != currentHtmlHash or outJson['pythonHash'] != currentPythonHash:
				outJson['oldVersion'] = True
			#If the hashes match, mark the model as up to date
			else:	
				outJson['oldVersion'] = False
		except (UnboundLocalError, KeyError) as e:
			print((traceback.print_exc()))
			print(('error:' + str(e)))
	except IOError:
		allOutputData = None
		outJson = None
	if absolutePaths:
		# Parent of current folder.
		pathPrefix = _myDir
	else:
		pathPrefix = ""
	# Generate standard raw output files.
	rawFilesTemplate = '''
		<p class="reportTitle">Raw Input and Output Files</p>
		<div id="rawOutput" class="content" style="margin-top:0px">
			{% for name in allOutputDataDict['fileNames'] %}
				{% if loop.index > 1 %}&mdash; {% endif %}<a href="/downloadModelData/{{allInputDataDict['user']}}/{{allInputDataDict['modelName']}}/{{name}}">{{name}}</a>
			{% endfor %}
		</div>
	'''
	rawOutputFiles = Template(rawFilesTemplate).render(allOutputDataDict=outJson, allInputDataDict=inJson)
	# Generate standard model buttons.
	omfModelButtonsTemplate = '''
		<div class="wideInput" style="text-align:right">
		{% if modelStatus != 'running' and (loggedInUser == modelOwner or loggedInUser == 'admin') %}
		<button id="deleteButton" type="button" onclick="deleteModel()">Delete</button>
		<button id="runButton" type="submit">Run Model</button>
		{% endif %}
		{% if modelStatus == "finished" %}
		<button id="shareButton" type="button" onclick="shareModel()">Share</button>
		<button id="duplicateButton" type="button" onclick="duplicateModel()">Duplicate</button>
		{% endif %}
		{% if modelStatus == "running" and (loggedInUser == modelOwner or loggedInUser == 'admin') %}
		<button id="cancelButton" type="button" onclick="cancelModel()">Cancel Run</button>
		{% endif %}
	</div>
	'''
	# Generate standard status content.
	loggedInUser = datastoreNames.get('currentUser', 'test')
	modelStatus = getStatus(modelDir)
	omfModelButtons = Template(omfModelButtonsTemplate).render(modelStatus=modelStatus, loggedInUser=loggedInUser, modelOwner=modelOwner)
	now = datetime.datetime.now()
	try:
		mod_start = datetime.datetime.fromisoformat(inJson.get('runStartTime'))
	except:
		mod_start = now
	elapsed_dt = now - mod_start
	elapsed_min = elapsed_dt.total_seconds() / 60.0
	model_estimate_min = float(inJson.get('runtimeEst_min', '2.0'))
	remain_min = model_estimate_min - elapsed_min 
	runDebugTemplate = '''
		{% if modelStatus == 'running' %}
		<div id ="runIndicator" class="content">
			Model has run for {{elapsed_min}} minutes. {{remain_min}} minutes estimated until completion. Results updated every 5 seconds.
		</div>
		{% endif %}
		{% if modelStatus == 'stopped' and stderr != '' %}
		<div id ="stopIndicator" class="content">
			<pre id='errorText' style='overflow-x:scroll'>MODEL ENCOUNTERED AN ERROR AS FOLLOWS:\n\n{{stderr}}</pre>
		</div>
		{% endif %}
		'''
	omfRunDebugBlock = Template(runDebugTemplate).render(modelStatus=modelStatus, stderr=inJson.get('stderr', ''), elapsed_min=round(elapsed_min,2), remain_min=round(remain_min,2))
	# Raw input output include.
	return template.render(allInputData=allInputData, allOutputData=allOutputData, modelStatus=modelStatus, pathPrefix=pathPrefix,
		datastoreNames=datastoreNames, modelName=modelType, allInputDataDict=inJson, allOutputDataDict=outJson, rawOutputFiles=rawOutputFiles, omfModelButtons=omfModelButtons, omfRunDebugBlock=omfRunDebugBlock)

def renderAndShow(modelDir, datastoreNames={}):
	''' Render and open a template (blank or with output) in a local browser. '''
	with tempfile.NamedTemporaryFile('w', suffix=".html", delete=False) as temp:
		temp.write(renderTemplate(modelDir, absolutePaths=True))
		temp.flush()
		webbrowser.open("file://" + temp.name)

def runForeground(modelDir):
	''' Run all model work immediately in the same thread. '''
	with locked_open(pJoin(modelDir, "PPID.txt"),"w+") as pPidFile:
		pPidFile.write('-999') # HACK: put in an invalid PID to indicate the model is running.
	print("FOREGROUND RUNNING", modelDir)
	heavyProcessing(modelDir)

def nmm_new(modelDir, defaultInputs):
	''' Create a new instance of a model. Returns true on success, false on failure. '''
	alreadyThere = os.path.isdir(modelDir) or os.path.isfile(modelDir)
	try:
		if not alreadyThere:
			os.makedirs(modelDir)
		else:
			defaultInputs["created"] = str(datetime.datetime.now())
			with locked_open(pJoin(modelDir, "allInputData.json"),"w") as inputFile:
				json.dump(defaultInputs, inputFile, indent = 4)
			return False
		defaultInputs["created"] = str(datetime.datetime.now())
		with locked_open(pJoin(modelDir, "allInputData.json"),"w") as inputFile:
			json.dump(defaultInputs, inputFile, indent = 4)
		return True
	except:
		return False

def neoMetaModel_test_setup(function):
	@wraps(function)
	def test_setup_wrapper(*args, **kwargs):
		heavyProcessing.__defaults__ = (True,)
		return function()
	return test_setup_wrapper

def heavyProcessing(modelDir, test_mode=False):
	''' Wrapper to handle model running safely and uniformly. '''
	try:
		# Start a timer.
		startTime = datetime.datetime.now()
		# Get the inputs.
		with locked_open(pJoin(modelDir, 'allInputData.json')) as f:
			inputDict = json.load(f)
		# Place run start time.
		inputDict['runStartTime'] = startTime.isoformat()
		with open(pJoin(modelDir, 'allInputData.json'), 'w') as f:
			json.dump(inputDict, f, indent=4)
		# Remove old outputs.
		try:
			os.remove(pJoin(modelDir,"allOutputData.json"))
		except Exception as e:
			pass
		# Estimate runtime if possible.
		try:
			inputDict['runtimeEst_min'] = derInterconnection.runtimeEstimate(modelDir)
		except: 
			pass
		# Get the function and run it.
		# work = work()
		#This grabs the new outData model
		outData = work(modelDir, inputDict)
		#print("!!!!!!! thing !!!!!!!!") # DEBUG
	except Exception as e:
		# cancel(modelDir)
		if test_mode == True:
			raise e
		# If input range wasn't valid delete output, write error to disk.
		thisErr = traceback.format_exc()
		print('ERROR IN MODEL', modelDir, thisErr)
		inputDict['stderr'] = thisErr
		with locked_open(os.path.join(modelDir,'stderr.txt'),'w') as errorFile:
			errorFile.write(thisErr)
	else:
		# No errors, so update the runTime in the input file.
		endTime = datetime.datetime.now()
		inputDict["runTime"] = str(datetime.timedelta(seconds=int((endTime - startTime).total_seconds())))
		# Write output.
		modelType = inputDict["modelType"]
		#Get current file hashes and dd to the output
		with open(pJoin(_myDir, 'templates', modelType+".html")) as f:
			htmlFile = f.read()
		currentHtmlHash = hashlib.sha256(htmlFile.encode('utf-8')).hexdigest()
		with open(pJoin(_myDir, modelType+".py")) as f:
			pythonFile = f.read()
		currentPythonHash = hashlib.sha256(pythonFile.encode('utf-8')).hexdigest()
		outData['htmlHash'] = currentHtmlHash
		outData['pythonHash'] = currentPythonHash
		outData['oldVersion'] = False
		# Raw input/output file names.
		outData['fileNames'] = os.listdir(modelDir)
		outData['fileNames'].append('allOutputData.json')
		with locked_open(pJoin(modelDir, "allOutputData.json"),"w") as outFile:
			json.dump(outData, outFile, indent=4)
	finally:
		# Clean up by updating input data.
		try:
			with locked_open(pJoin(modelDir,"allInputData.json"),"w") as inFile:
				json.dump(inputDict, inFile, indent=4)
		except: pass
		try: os.remove(pJoin(modelDir,"PPID.txt"))
		except: pass

def work(modelDir, inputDict):
	''' Run the model in its directory. '''
	
	outData = {}

	feederName = [x for x in os.listdir(modelDir) if x.endswith('.omd')][0][:-4]
	inputDict['feederName1'] = feederName
	
	with open(pJoin(modelDir,feederName + '.omd')) as f:
		omd = json.load(f)
	if inputDict.get('layoutAlgorithm', 'geospatial') == 'geospatial':
		neato = False
	else:
		neato = True 

	path = pJoin(modelDir,feederName + '.omd')
	if path.endswith('.glm'):
		tree = parse(path)
		attachments = []
	elif path.endswith('.omd'):
		with open(path) as f:
			omd = json.load(f)
		tree = omd.get('tree', {})
		attachments = omd.get('attachments',[])
	else:
		raise Exception('Invalid input file type. We require a .glm or .omd.')
	
	# dictionary to hold info on lines present in glm
	edge_bools = dict.fromkeys(['underground_line','overhead_line','triplex_line','transformer','regulator', 'fuse', 'switch'], False)
	# Get rid of schedules and climate and check for all edge types:
	for key in list(tree.keys()):
		obtype = tree[key].get('object','')
		if obtype == 'underground_line':
			edge_bools['underground_line'] = True
		elif obtype == 'overhead_line':
			edge_bools['overhead_line'] = True
		elif obtype == 'triplex_line':
			edge_bools['triplex_line'] = True
		elif obtype == 'transformer':
			edge_bools['transformer'] = True
		elif obtype == 'regulator':
			edge_bools['regulator'] = True
		elif obtype == 'fuse':
			edge_bools['fuse'] = True
		elif obtype == 'switch':
			edge_bools['switch'] = True
		if tree[key].get('argument','') == '\"schedules.glm\"' or tree[key].get('tmyfile','') != '':
			del tree[key]

	# print edge_bools
			
	# Make sure we have a voltDump:
	def safeInt(x):
		try: return int(x)
		except: return 0
	biggestKey = max([safeInt(x) for x in tree.keys()])
	tree[str(biggestKey*10)] = {'object':'voltdump','filename':'voltDump.csv'}
	tree[str(biggestKey*10 + 1)] = {'object':'currdump','filename':'currDump.csv'}
	
	# Line rating dumps
	tree[getMaxKey(tree) + 1] = {'module': 'tape'}
	for key in edge_bools.keys():
		if edge_bools[key]:
			tree[getMaxKey(tree) + 1] = {
				'object':'group_recorder', 
				'group':'"class='+key+'"',
				'limit':1000,
				'property':'continuous_rating',
				'file':key+'_cont_rating.csv'
			}

	if edge_bools['regulator']:
		tree[getMaxKey(tree) + 1] = {
			'object':'group_recorder', 
			'group':'"class=regulator"',
			'limit':1000,
			'property':'tap_A',
			'file':'tap_A.csv',
			'interval':0
		}

		tree[getMaxKey(tree) + 1] = {
			'object':'group_recorder', 
			'group':'"class=regulator"',
			'limit':1000,
			'property':'tap_B',
			'file':'tap_B.csv',
			'interval':0
		}

		tree[getMaxKey(tree) + 1] = {
			'object':'group_recorder', 
			'group':'"class=regulator"',
			'limit':1000,
			'property':'tap_C',
			'file':'tap_C.csv',
			'interval':0
		}

		tree[getMaxKey(tree) + 1] = {
			'object':'group_recorder', 
			'group':'"class=regulator"',
			'limit':1000,
			'property':'flow_direction',
			'file':'regulatorFlowDirection.csv',
			'interval':0
		}

	# get start and stop time for the simulation
	[startTime,stopTime] = ['','']
	for key in tree.keys():
		obname = tree[key].get('object','')
		starttime = tree[key].get('starttime','')
		stoptime = tree[key].get('stoptime','')
		if starttime!='' and stoptime!='':
			startTime = tree[key]['starttime']
			stopTime = tree[key]['stoptime']
			break	

	# gridlabd complains if sim and fault start at the same time so
	# add 1 sec to the fault start
	faultStartTime = parser.parse(starttime)
	faultStartTime = faultStartTime + relativedelta(seconds=+1)
	faultStartTime = str(faultStartTime)		

	# Map to speed up name lookups.
	nameToIndex = {tree[key].get('name',''):key for key in tree.keys()}
	
	# find the key of the relavant added DER components  
	addedDerKey = nameToIndex[inputDict['newGeneration']]
	addedDerInverterKey = nameToIndex[tree[addedDerKey]['parent']]
	addedBreakKey = nameToIndex[inputDict['newGenerationBreaker']]
	poi = tree[addedBreakKey]['to']

	# set solar generation to provided insolation value
	insolation = float(inputDict['newGenerationInsolation'])
	if insolation > 1000:
		insolation = 1000
	elif insolation < 0:
		insolation = 0
	# cant set insolation directly but without climate object it defaults to 1000
	# whilch is about 10x max sun output and we can set shading factor between 0 and 1
	# to effectively control insolation
	tree[addedDerKey]['shading_factor'] = insolation/1000
	
	# initialize variables
	flickerViolations = []
	flickerThreshold = float(inputDict['flickerThreshold'])
	voltageViolations = []
	[upperVoltThresh, lowerVoltThresh, lowerVoltThresh600] = [1.05,0.95,0.975]
	thermalViolations = []
	thermalThreshold = float(inputDict['thermalThreshold'])/100
	reversePowerFlow = []
	tapViolations = []
	tapThreshold = float(inputDict['tapThreshold'])
	faults = ['SLG-A','SLG-B','SLG-C','TLG']
	faultLocs = [inputDict['newGenerationBreaker']]
	faultBreaker = [[] for i in range(2*len(faults))] # the 2 is for the 2 load conditions
	faultStepUp = [[] for i in range(2*len(faults))]
	faultCurrentViolations = []
	faultCurrentThreshold = float(inputDict['faultCurrentThreshold'])
	faultPOIVolts = []
	faultVoltsThreshold = float(inputDict['faultVoltsThreshold'])

	# run analysis for both load conditions
	count = 0
	for loadCondition in ['Peak', 'Min']:

		# if a peak load file is provided, use it to set peak loads in the tree
		if (loadCondition == 'Peak') and (inputDict['peakLoadData'] != ''):
			peakLoadData = inputDict['peakLoadData'].split('\r\n')
			for data in peakLoadData:
				if str(data) != '':
					key = data.split(',')[0]
					val = data.split(',')[1]
					tree[key]['power_12'] = val
		
		elif (loadCondition == 'Min'):
			# if a min load file is provided use is to set the min loads
			if inputDict['minLoadData'] != '':
				minLoadData = inputDict['minLoadData'].split('\r\n')
				for data in minLoadData:
					if str(data) != '':
						key = data.split(',')[0]
						val = data.split(',')[1]
						tree[key]['power_12'] = val
		
			else: # if no min load file is provided set min load to be 1/3 of peak + noise				
				for key in tree.keys():
					obtype = tree[key].get('object','')
					if obtype == 'triplex_node':
						load = tree[key].get('power_12','')
						if load != '':
							load = float(load)
							minLoad = (load/3)+(load*0.1*random.triangular(-1,1))
							tree[key]['power_12'] = str(minLoad)

		# initialize variables
		flicker = {}
		[maxFlickerLocation, maxFlickerVal] = ['',0]

		# run analysis with DER on and off under both load conditions
		for der in ['On', 'Off']:


			# if der is Off set added DER offline, if its On set DER online
			if der is 'Off':
				tree[addedDerKey]['generator_status'] = 'OFFLINE'
				tree[addedDerInverterKey]['generator_status'] = 'OFFLINE'
			else: # der is on 
				tree[addedDerKey]['generator_status'] = 'ONLINE'
				tree[addedDerInverterKey]['generator_status'] = 'ONLINE'

			# run gridlab solver
			count += 1
			print('run num', count, 'der', der, 'load', loadCondition)
			data = runGridlabAndProcessData(tree, attachments, edge_bools, workDir=modelDir)
			# print(tree[addedDerKey]);
			# print(tree[addedDerInverterKey]);

			# generate voltage, current and thermal plots
			filename = 'voltageDer' + der + loadCondition
			chart = drawPlot(tree,nodeDict=data['percentChangeVolts'], neatoLayout=neato, nodeFlagBounds=[114, 126], defaultNodeVal=120)
			chart.savefig(pJoin(modelDir, filename + 'Chart.png'))
			with open(pJoin(modelDir,filename + 'Chart.png'),'rb') as inFile:
				outData[filename] = base64.standard_b64encode(inFile.read()).decode('ascii')

			filename = 'currentDer' + der + loadCondition
			chart = drawPlot(tree,nodeDict=data['edgeCurrentSum'], neatoLayout=neato)
			chart.savefig(pJoin(modelDir, filename + 'Chart.png'))
			with open(pJoin(modelDir,filename + 'Chart.png'),'rb') as inFile:
				outData[filename] = base64.standard_b64encode(inFile.read()).decode('ascii')

			filename = 'thermalDer' + der + loadCondition
			chart = drawPlot(tree,nodeDict=data['edgeValsPU'], neatoLayout=neato)
			chart.savefig(pJoin(modelDir, filename + 'Chart.png'))
			with open(pJoin(modelDir,filename + 'Chart.png'),'rb') as inFile:
				outData[filename] = base64.standard_b64encode(inFile.read()).decode('ascii')


			# calculate max and min voltage and track badwidth violations
			[maxVoltsLocation, maxVoltsVal] = ['',0]
			[minVoltsLocation, minVoltsVal] = ['',float('inf')]
			for key in data['nodeVolts'].keys():
				
				voltVal = float(data['nodeVolts'][key])
				nominalVoltVal = float(data['nominalVolts'][key])
				
				if maxVoltsVal <= voltVal:
					maxVoltsVal = voltVal
					maxVoltsLocation = key
				if minVoltsVal >= voltVal:
					minVoltsVal = voltVal
					minVoltsLocation = key

				change = 100*((voltVal-nominalVoltVal)/nominalVoltVal)
				if nominalVoltVal > 600:
					violation = (voltVal >= (upperVoltThresh*nominalVoltVal)) or \
						(voltVal <= (lowerVoltThresh600*nominalVoltVal))
				else:
					violation = (voltVal >= (upperVoltThresh*nominalVoltVal)) or \
						(voltVal <= (lowerVoltThresh*nominalVoltVal))
				content = [key, nominalVoltVal, voltVal, change, \
					loadCondition +' Load, DER ' + der,violation]
				voltageViolations.append(content)

			outData['maxVolts'+loadCondition+'Der'+der] = [maxVoltsLocation, maxVoltsVal]
			outData['minVolts'+loadCondition+'Der'+der] = [minVoltsLocation, minVoltsVal]

			# check for thermal violations
			for key in data['edgeValsPU'].keys():
				thermalVal = float(data['edgeValsPU'][key])
				content = [key, 100*thermalVal,\
					loadCondition+' Load, DER '+der,(thermalVal>=thermalThreshold)]
				thermalViolations.append(content)

			if edge_bools['regulator']:
				# check for reverse regulator powerflow
				for key in data['regulatorFlowDirection']:
					directions = data['regulatorFlowDirection'][key].split('|')
					reverseFlow = ('AR' in directions) or \
						('BR' in directions) or ('CR' in directions)
					powerVal = float(data['edgePower'][key])
					content = [key, powerVal,\
						loadCondition+' Load, DER '+der,reverseFlow]
					reversePowerFlow.append(content)

				# check for tap_position values and violations
				if der == 'On':
					tapPositions = copy.deepcopy(data['tapPositions'])
				else: # der off
					for tapType in ['tapA','tapB','tapC']:
						for key in tapPositions[tapType].keys():
							# calculate tapPositions
							tapDerOn = int(tapPositions[tapType][key])
							tapDerOff = int(data['tapPositions'][tapType][key])
							tapDifference = abs(tapDerOn-tapDerOff)
							# check for violations
							content = [loadCondition, key+' '+tapType, tapDerOn, \
								tapDerOff,tapDifference, (tapDifference>=tapThreshold)]
							tapViolations.append(content)

			#induce faults and measure fault currents
			for faultLocation in faultLocs:
				for faultNum, faultType in enumerate(faults):
					faultIndex = faultNum
					if loadCondition == 'Min':
						faultIndex = faultNum + len(faults)

					treeCopy =  createTreeWithFault( tree, \
						faultType, faultLocation, faultStartTime, stopTime )
					count += 1
					print('run num', count, 'der', der, 'load', loadCondition, \
						'fault Location', faultLocation, 'type', faultType, )
					faultData = runGridlabAndProcessData(treeCopy, attachments, \
						edge_bools, workDir=modelDir)
					faultVolts = faultData['nodeVolts']
					faultCurrents = faultData['edgeCurrentSum']

					# the fault is at the breaker
					if faultLocation == inputDict['newGenerationBreaker']:

						if der == 'On':
						
							# get fault current values at the breaker
							faultBreaker[faultIndex] = [loadCondition, faultType]
							faultBreaker[faultIndex].append(\
								float(faultCurrents[inputDict['newGenerationBreaker']]))
						
							# get fault current values at the transformer
							faultStepUp[faultIndex] = [loadCondition, faultType]
							faultStepUp[faultIndex].append(\
								float(faultCurrents[inputDict['newGenerationStepUp']]))
						
						else: #der off

							# get fault current values at the breaker
							faultBreaker[faultIndex].append(\
								float(faultCurrents[inputDict['newGenerationBreaker']]))
							faultBreaker[faultIndex].append(\
								faultBreaker[faultIndex][2] - \
								faultBreaker[faultIndex][3])

							# get fault current values at the transformer
							faultStepUp[faultIndex].append(\
								float(faultCurrents[inputDict[\
									'newGenerationStepUp']]))
							faultStepUp[faultIndex].append(\
								faultStepUp[faultIndex][2] - \
								faultStepUp[faultIndex][3])
						
						# get fault voltage values at POI
						preFaultval = data['nodeVolts'][poi]
						postFaultVal = faultVolts[poi]
						percentChange = 100*(postFaultVal/preFaultval)
						faultPOIVolts.append(['Der '+ der + ' ' + \
							loadCondition + ' Load', poi, faultType, preFaultval,\
								postFaultVal, percentChange, \
								(percentChange>=faultVoltsThreshold)])

					# get fault violations when der is on
					if der == 'On':
						for key in faultCurrents.keys():
							preFaultval = float(data['edgeCurrentSum'][key])
							postFaultVal = float(faultCurrents[key])
							difference = abs(preFaultval-postFaultVal)
							if preFaultval == 0:
								percentChange = 0
							else:
								percentChange = 100*(difference/preFaultval)

							content = [loadCondition, faultLocation, faultType, key, \
								preFaultval, postFaultVal, percentChange, \
								(percentChange>=faultCurrentThreshold)]
							faultCurrentViolations.append(content)

			# calculate flicker, keep track of max, and violations
			if der == 'On':
				flicker = copy.deepcopy(data['nodeVolts'])
			else: # der off
				for key in flicker.keys():
					# calculate flicker
					derOn = float(flicker[key])
					derOff = float(data['nodeVolts'][key])
					flickerVal = 100*(1-(derOff/derOn))
					flicker[key] = flickerVal
					# check for max
					if maxFlickerVal <= flickerVal:
						maxFlickerVal = flickerVal
						maxFlickerLocation = key
					# check for violations
					content = [key, flickerVal,loadCondition+' Load',\
					(flickerVal>=flickerThreshold)]
					flickerViolations.append(content)

		# plot flicker
		filename = 'flicker' + loadCondition
		chart = drawPlot(tree,nodeDict=flicker, neatoLayout=neato)
		chart.savefig(pJoin(modelDir,filename + 'Chart.png'))
		with open(pJoin(modelDir,filename + 'Chart.png'),"rb") as inFile:
			outData[filename] = base64.standard_b64encode(inFile.read()).decode('ascii')

		# save max flicker info to output dictionary
		outData['maxFlicker'+loadCondition] = [maxFlickerLocation, maxFlickerVal]

	outData['voltageViolations'] = voltageViolations
	outData['flickerViolations'] = flickerViolations
	outData['thermalViolations'] = thermalViolations
	outData['reversePowerFlow'] = reversePowerFlow	
	outData['tapViolations'] = tapViolations
	outData['faultBreaker']	 = faultBreaker
	outData['faultStepUp'] = faultStepUp
	outData['faultCurrentViolations'] = faultCurrentViolations
	outData['faultPOIVolts'] = faultPOIVolts
	
	plt.close('all')
	return outData

def createTreeWithFault( tree, faultType, faultLocation, startTime, stopTime ):
	
	treeCopy = copy.deepcopy(tree)

	# HACK: set groupid for all meters so outage stats are collected.
	noMeters = True
	for key in treeCopy:
		if treeCopy[key].get('object','') in ['meter', 'triplex_meter']:
			treeCopy[key]['groupid'] = "METERTEST"
			noMeters = False
	if noMeters:
		raise Exception("No meters detected on the circuit. \
			Please add at least one meter to allow for collection of outage statistics.")

	treeCopy[getMaxKey(treeCopy) + 1] = {
		'module': 'reliability ',
		'maximum_event_length': '300 s',
		'report_event_log': 'TRUE'
	}

	faultType = '"'+faultType+'"'
	outageParams = '"'+faultLocation+','+startTime.replace('\'','') + \
		','+stopTime.replace('\'','')+'"'
	treeCopy[getMaxKey(treeCopy) + 1] = {
		'object': 'eventgen',
		'name': 'ManualEventGen',
		'parent': 'RelMetrics',
		'fault_type': faultType,
		'manual_outages': str(outageParams)
	}

	treeCopy[getMaxKey(treeCopy) + 1] = {
		'object': 'fault_check ',
		'name': 'test_fault',
		'check_mode': 'ONCHANGE',
		'eventgen_object': 'ManualEventGen',
		'output_filename': 'Fault_check_out.txt'
	}

	treeCopy[getMaxKey(treeCopy) + 1] = {
		'object': 'metrics',
		'name': 'RelMetrics',
		'report_file': 'Metrics_Output.csv',
		'module_metrics_object': 'PwrMetrics',
		'metrics_of_interest': '"SAIFI,SAIDI,CAIDI,ASAI,MAIFI"',
		'customer_group': '"groupid=METERTEST"',
		'metric_interval': '5 h',
		'report_interval': '5 h'
	}
	
	treeCopy[getMaxKey(treeCopy) + 1] = {
		'object': 'power_metrics',
		'name': 'PwrMetrics',
		'base_time_value': '1 h'
	}

	return treeCopy

def readGroupRecorderCSV( filename ):

	dataDictionary = {}
	with open(filename, newline='') as csvFile:
		reader = csv.reader(csvFile)
		# loop past the header, 
		[keys,vals] = [[],[]]
		for row in reader:
			if '# timestamp' in row:
				keys = row
				i = keys.index('# timestamp')
				keys.pop(i)
				vals = next(reader)
				vals.pop(i)
		for pos,key in enumerate(keys):
			dataDictionary[key] = vals[pos]
			
	return dataDictionary	

def runGridlabAndProcessData(tree, attachments, edge_bools, workDir=False):
	
	# Run Gridlab.
	if not workDir:
		workDir = tempfile.mkdtemp()
	else:
		# print(workDir)
		folderContents = glob.glob(workDir+'/*')
		for item in folderContents:
			if (item[-3:] != 'omd') and (item[-4:] != 'json'):
				# os.remove(item)
				pass

	gridlabOut = runInFilesystem(tree, attachments=attachments, workDir=workDir)

	if os.stat(workDir+'/stderr.txt').st_size > 40:
		print('failed with stderr.txt size', os.stat(workDir+'/stderr.txt').st_size)
		print('--------------------------------------')
		print(gridlabOut['stderr'])
		print('--------------------------------------')
		
	else:
		print('passed with stderr.txt size', os.stat(workDir+'/stderr.txt').st_size)

	# read voltDump values into a dictionary.
	try:
		with open(pJoin(workDir,'voltDump.csv'), newline='') as dumpFile:
			reader = csv.reader(dumpFile)
			next(reader) # Burn the header.
			keys = next(reader)
			voltTable = []
			for row in reader:
				rowDict = {}
				for pos,key in enumerate(keys):
					rowDict[key] = row[pos]
				voltTable.append(rowDict)
	except:
		raise Exception('GridLAB-D failed to run with the following errors:\n' + gridlabOut['stderr'])

	# read currDump values into a dictionary
	with open(pJoin(workDir,'currDump.csv'), newline='') as currDumpFile:
		reader = csv.reader(currDumpFile)
		next(reader) # Burn the header.
		keys = next(reader)
		currTable = []
		for row in reader:
			rowDict = {}
			for pos,key in enumerate(keys):
				rowDict[key] = row[pos]
			currTable.append(rowDict)

	# read line rating values into a single dictionary
	lineRatings = {}
	for key1 in edge_bools.keys():
		if edge_bools[key1]:		
			with open(pJoin(workDir,key1+'_cont_rating.csv'), newline='') as ratingFile:
				reader = csv.reader(ratingFile)
				keys = []
				vals = []
				for row in reader:
					if '# timestamp' in row:
						keys = row
						i = keys.index('# timestamp')
						keys.pop(i)
						vals = next(reader)
						vals.pop(i)
				for pos,key2 in enumerate(keys):
					lineRatings[key2] = abs(float(vals[pos]))				

	# Calculate average node voltage deviation. First, helper functions.
	def digits(x):
		''' Returns number of digits before the decimal in the float x. '''
		return math.ceil(math.log10(x+1))
	def avg(l):
		''' Average of a list of ints or floats. '''
		if len(l) == 0:
			return 0
		return sum(l)/len(l)
	
	# Tot it all up.
	nodeVolts = {}
	for row in voltTable:
		allVolts = []
		for phase in ['A','B','C']:
			realVolt = abs(float(row['volt'+phase+'_real']))
			imagVolt = abs(float(row['volt'+phase+'_imag']))
			phaseVolt = math.sqrt((realVolt ** 2) + (imagVolt ** 2))
			if phaseVolt != 0.0:
				allVolts.append(phaseVolt)
		avgVolts = avg(allVolts)
		nodeVolts[row.get('node_name','')] = float("{0:.2f}".format(avgVolts))
		
	
	nominalVolts = {}
	percentChangeVolts = {}
	for key in nodeVolts.keys():
		for treeKey in tree:
			ob = tree[treeKey]
			obName = ob.get('name','')
			if obName==key:
				nominalVolts[key] = float(ob.get('nominal_voltage',1))
				percentChangeVolts[key] = (nodeVolts[key] / nominalVolts[key]) * 120

	# find edge currents by parsing currdump
	edgeCurrentSum = {}
	edgeCurrentMax = {}
	for row in currTable:
		allCurr = []
		for phase in ['A','B','C']:
			realCurr = abs(float(row['curr'+phase+'_real']))
			imagCurr = abs(float(row['curr'+phase+'_imag']))
			phaseCurr = math.sqrt((realCurr ** 2) + (imagCurr ** 2))
			allCurr.append(phaseCurr)
		edgeCurrentSum[row.get('link_name','')] = sum(allCurr)
		edgeCurrentMax[row.get('link_name','')] = max(allCurr)
	# When just showing current as labels, use sum of the three lines' current values, when showing the per unit values (current/rating), use the max of the three
	

	#edgeValsPU = current values normalized per unit by line ratings
	edgeValsPU = {}
	edgePower = {}

	for edge in edgeCurrentSum:
		for obj in tree.values():
			obname = obj.get('name','').replace('"','')
			if obname == edge:
				nodeFrom = obj.get('from')
				nodeTo = obj.get('to')
				currVal = edgeCurrentSum.get(edge)
				voltVal = avg([nodeVolts.get(nodeFrom), nodeVolts.get(nodeTo)])
				lineRatings[edge] = lineRatings.get(edge, 10.0**9)
				edgePerUnitVal = (edgeCurrentMax.get(edge))/lineRatings[edge]
				edgeValsPU[edge] = edgePerUnitVal
				edgePower[edge] = ((currVal * voltVal)/1000)

	tapPositions = {}
	regulatorFlowDirection = {}
	if edge_bools['regulator']:
		
		# read regulator tap position values values into a single dictionary
		tapPositions['tapA'] = readGroupRecorderCSV(pJoin(workDir,'tap_A.csv'))
		tapPositions['tapB'] = readGroupRecorderCSV(pJoin(workDir,'tap_B.csv'))
		tapPositions['tapC'] = readGroupRecorderCSV(pJoin(workDir,'tap_C.csv'))
		
		# read regulator flow direction values into a single dictionary
		regulatorFlowDirection = readGroupRecorderCSV(pJoin(workDir,'regulatorFlowDirection.csv'))


	return {'nominalVolts':nominalVolts, 'nodeVolts':nodeVolts, 'percentChangeVolts':percentChangeVolts, 
	'edgeCurrentSum':edgeCurrentSum, 'edgePower':edgePower, 'edgeValsPU':edgeValsPU, 'tapPositions':tapPositions,
	'regulatorFlowDirection': regulatorFlowDirection }

def drawPlot(tree, nodeDict=None, edgeDict=None, edgeLabsDict=None, displayLabs=False, customColormap=False, 
	perUnitScale=False, rezSqIn=400, neatoLayout=False, nodeFlagBounds=[-float('inf'), float('inf')], defaultNodeVal=1):
	''' Draw a color-coded map of the voltage drop on a feeder.
	path is the full path to the GridLAB-D .glm file or OMF .omd file.
	workDir is where GridLAB-D will run, if it's None then a temp dir is used.
	neatoLayout=True means the circuit is displayed using a force-layout approach.
	edgeLabs property must be either 'Name', 'Current', 'Power', 'Rating', 'PercentOfRating', or None
	nodeLabs property must be either 'Name', 'Voltage', 'VoltageImbalance', or None
	edgeCol and nodeCol can be set to false to avoid coloring edges or nodes
	customColormap=True means use a one that is nicely scaled to perunit values highlighting extremes.
	Returns a matplotlib object.'''
	# Be quiet matplotlib:
	# warnings.filterwarnings('ignore')

	# Build the graph.
	fGraph = treeToNxGraph(tree)
	# TODO: consider whether we can set figsize dynamically.
	wlVal = int(math.sqrt(float(rezSqIn)))

	chart = plt.figure(figsize=(wlVal, wlVal))
	plt.axes(frameon = 0)
	plt.axis('off')
	chart.gca().set_aspect('equal')
	plt.tight_layout()

	# Need to get edge names from pairs of connected node names.
	edgeNames = []
	for e in fGraph.edges():
		edgeNames.append((fGraph.edges[e].get('name','BLANK')).replace('"',''))
	
	#set axes step equal
	if neatoLayout:
		# HACK: work on a new graph without attributes because graphViz tries to read attrs.
		cleanG = nx.Graph(fGraph.edges())
		cleanG.add_nodes_from(fGraph)
		positions = graphviz_layout(cleanG, prog='neato')
	else:
		positions = {n:fGraph.nodes[n].get('pos',(0,0))[::-1] for n in fGraph}
	
	#create custom colormap
	if customColormap:
		custom_cm = matplotlib.colors.LinearSegmentedColormap.from_list('custColMap',[(0.0,'blue'),(0.15,'darkgray'),(0.7,'darkgray'),(1.0,'red')])
		custom_cm.set_under(color='black')
	else:
		custom_cm = plt.cm.get_cmap('viridis')
	
	drawColorbar = False
	emptyColors = {}
	
	#draw edges with or without colors
	if edgeDict != None:
		drawColorbar = True
		edgeList = [edgeDict.get(n,1) for n in edgeNames]
	else:
		edgeList = [emptyColors.get(n,.6) for n in edgeNames]

	edgeIm = nx.draw_networkx_edges(fGraph,
		pos = positions,
		edge_color = edgeList,
		width = 1,
		edge_cmap = custom_cm)

	#draw edge labels
	if displayLabs:
		edgeLabelsIm = nx.draw_networkx_edge_labels(fGraph,
			pos = positions,
			edge_labels = edgeLabsDict,
			font_size = 8)

	# draw nodes with or without color
	if nodeDict != None:
		nodeList = [nodeDict.get(n,defaultNodeVal) for n in fGraph.nodes()]
		drawColorbar = True
	else:
		nodeList = [emptyColors.get(n,.6) for n in fGraph.nodes()]
	
	if perUnitScale:
		vmin = 0
		vmax = 1.25
	else:
		vmin = None
		vmax = None

	edgecolors = ['None'] * len(nodeList)
	for i in range(len(nodeList)):
		if nodeList[i] < nodeFlagBounds[0]:
			edgecolors[i] = '#ffa500'
		if nodeList[i] > nodeFlagBounds[1]:
			edgecolors[i] = 'r'
	nodeIm = nx.draw_networkx_nodes(fGraph,
		pos = positions,
		node_color = nodeList,
		edgecolors = edgecolors,
		linewidths = 2,
		node_size = 30,
		vmin = vmin,
		vmax = vmax,
		cmap = custom_cm)

	#draw node labels
	if displayLabs and nodeDict != None:
		nodeLabelsIm = nx.draw_networkx_labels(fGraph,
			pos = positions,
			labels = nodeDict,
			font_size = 8)
	
	plt.sci(nodeIm)
	# plt.clim(110,130)
	if drawColorbar:
		plt.colorbar()
	return chart

def glmToModel(glmPath, modelDir):
	''' One shot model creation from glm. '''
	tree = parse(glmPath)
	# Run powerflow. First name the folder for it.
	# Remove old copy of the model.
	shutil.rmtree(modelDir, ignore_errors=True)
	# Create the model directory.
	new(modelDir)
	# Create the .omd.
	os.remove(modelDir + '/Olin Barre Geo.omd')
	with open(modelDir + '/Olin Barre Geo.omd','w') as omdFile:
		omd = dict(newFeederWireframe)
		omd['tree'] = tree
		json.dump(omd, omdFile, indent=4)

def new(modelDir):
	''' Create a new instance of this model. Returns true on success, false on failure. '''
	defaultInputs = {
		'feederName1': 'Olin Barre Geo Modified DER',
		'modelType': modelName,
		'runTime': '',
		'layoutAlgorithm': 'forceDirected',
		'flickerThreshold': '2',
		'newGeneration': 'addedDer',
		'newGenerationStepUp': 'addedDerStepUp',
		'newGenerationBreaker': 'addedDerBreaker',
		'thermalThreshold': '100',
		'peakLoadData': '',
		'minLoadData': '',
		'tapThreshold': '2',
		'faultCurrentThreshold': '10',
		'faultVoltsThreshold': '138',
		'newGenerationInsolation': '30'
	}
	creationCode = nmm_new(modelDir, defaultInputs)
	try:
		shutil.copyfile(f'{_myDir}/static/{defaultInputs["feederName1"]}.omd', pJoin(modelDir, defaultInputs["feederName1"]+'.omd'))
	except:
		return False
	return creationCode

def _testingPlot():
	PREFIX = os.path.join(os.path.dirname(__file__), '../scratch/CIGAR/')
	#PREFIX = omf.omfDir + '/scratch/CIGAR/'

	FNAME = 'test_base_R4-25.00-1.glm_CLEAN.glm'
	# FNAME = 'test_Exercise_4_2_1.glm'
	# FNAME = 'test_ieee37node.glm'
	# FNAME = 'test_ieee123nodeBetter.glm'
	# FNAME = 'test_large-R5-35.00-1.glm_CLEAN.glm'c
	# FNAME = 'test_medium-R4-12.47-1.glm_CLEAN.glm'
	# FNAME = 'test_smsSingle.glm'

	tree = parse(PREFIX + FNAME)
	chart = drawPlot(tree, neatoLayout=True, perUnitScale=False, rezSqIn=400)
	#chart = drawPlot(PREFIX + FNAME, neatoLayout=True, edgeCol=True, nodeLabs="Voltage", edgeLabs="Current", perUnitScale=False, rezSqIn=400)

	chart.savefig(PREFIX + "YO_WHATS_GOING_ON.png")
	plt.show()

@neoMetaModel_test_setup
def _tests():
	# Location
	modelLoc = pJoin("Automated Testing of " + modelName)
	# Blow away old test results if necessary.
	try:
		shutil.rmtree(modelLoc)
	except:
		# No previous test results.
		pass 
	# Create New.
	new(modelLoc)
	# Pre-run.
	# renderAndShow(modelLoc)
	# Run the model.
	runForeground(modelLoc)
	# Show the output.
	renderAndShow(modelLoc)

if __name__ == '__main__':
	_tests()
	#_testingPlot()
