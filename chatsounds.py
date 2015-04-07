__module_name__ = 'chatsounds'
__module_author__ = 'SpiralP'
__module_version__ = '1'
__module_description__ = 'chatsounds'

import os, sys
import urllib2, json
import re
import random
import hashlib

import hexchat


HEXCHAT_CONFIG_DIR=hexchat.get_info('configdir')
HEXCHAT_ADDONS_DIR=os.path.join(HEXCHAT_CONFIG_DIR,'addons')

CONFIG_DIR=os.path.join(HEXCHAT_CONFIG_DIR, 'chatsounds')
LISTS_DIR=os.path.join(CONFIG_DIR,'lists')
PATHS_DIR=os.path.join(CONFIG_DIR,'paths.lua')

if not os.path.exists(LISTS_DIR):
	os.makedirs(LISTS_DIR)


if CONFIG_DIR not in sys.path:
	sys.path.insert(0, CONFIG_DIR) # for imports

os.environ['PATH'] = os.environ['PATH'] + ';' + CONFIG_DIR # for dlls


PYBASS_DOWNLOAD_URL='http://sourceforge.net/projects/pybass/files/latest/download?source=files'
BASS_DOWNLOAD_URL='http://www.un4seen.com/files/bass24.zip'
VPKREADER_URL='https://raw.githubusercontent.com/SpiralP/HexChat-chatsounds/master/vpk2reader.py'
SLPP_URL='https://raw.githubusercontent.com/SpiralP/slpp/master/slpp.py'

CHATSOUNDS_REPO='https://api.github.com/repos/Metastruct/garrysmod-chatsounds/contents/lua/chatsounds/'

PATHS = {'vpk':[''],'chatsounds':''}



CLEAR='\017'
BOLD='\002'
UNDERLINE='\037'
COLOR='\003'
RED=COLOR+'04'
GREEN=COLOR+'03'
BLUE=COLOR+'02'

def success(msg):
	hexchat.prnt(BOLD + GREEN + msg)
def info(msg):
	hexchat.prnt(BOLD + BLUE + msg)
def warn(msg):
	hexchat.prnt(BOLD + RED + msg)
def printh(h,msg):
	hexchat.prnt('['+GREEN+h+CLEAR+'] ' + BLUE + msg)

def _exists(name):
	return name in globals()

def merge(a,b):
	c = a.copy()
	c.update(b)
	return c

def goodpath(path,join=False):
	if not join:
		join = []
	if path!='' and path[-1]=='/':#  or path[-1]=='\\':
		path = path[:-1]
	
	split = os.path.split(path)
	
	if split[1]=='':
		return os.path.join(split[0],*join)
	
	join.insert(0,split[1])
	return goodpath(split[0],join)

def findFiles(path):
	list = []
	for root,dirs,files in os.walk(path):
		for file in files:
			list.append(os.path.join(root,file))
	return list

CANT_LOAD='{} could not be imported, try running ' + BLUE + '/chatsounds setup'

try:
	from pybass import *
except ImportError:
	warn(CANT_LOAD.format('pybass'))
except WindowsError, e:
	warn('bass.dll could not be loaded ({})'.format(e))

try:
	from vpk2reader import *
except ImportError:
	warn(CANT_LOAD.format('vpk2reader'))

try:
	from slpp import slpp as lua
except ImportError:
	warn(CANT_LOAD.format('slpp'))



class http():
	def __init__(self, url):
		self.web = urllib2.urlopen(url)
	
	def __enter__(self):
		return self.web
	def __exit__(self, type, value, traceback):
		self.web.close()
	
	def __str__(self):
		return str(self.web)


def setupPybass(force=False):
	from zipfile import ZipFile
	def msg(a):
		printh('pybass',a)
	
	if os.path.exists(os.path.join(CONFIG_DIR,'pybass','__init__.py')) and not force:
		msg('ALREADY EXISTS! (skipping)')
		return False
	
	
	archive_path = os.path.join(CONFIG_DIR,'pybass.zip')
	
	msg('downloading')
	with http(PYBASS_DOWNLOAD_URL) as web:
		with open(archive_path,'wb') as file:
			file.write(web.read())
	
	msg('extracting')
	with ZipFile(archive_path) as zip:
		zip.extractall(CONFIG_DIR)
	
	msg('cleaning up')
	os.remove(archive_path)
	
	with open(os.path.join(CONFIG_DIR,'pybass','__init__.py'),'wb') as file:
		file.write('from pybass import *\n') # compat
	
def setupBass(force=False):
	from zipfile import ZipFile
	def msg(a):
		printh('bass',a)
	
	out_path = os.path.join(CONFIG_DIR,'bass.dll')
	
	if os.path.exists(out_path) and not force:
		msg('ALREADY EXISTS! (skipping)')
		return False
	
	if _exists('BASS_Free'):
		BASS_Free() # attempt to unhook the .dll so we can touch it
	
	import platform
	if platform.system()=='Darwin': # OSX
		x64 = sys.maxsize > 2**32
	else: # all others
		x64 = platform.architecture()[0]=='64bit'
	
	msg("Looks like you {} using a 64 bit python!".format(UNDERLINE+(x64 and 'are' or 'are NOT')+CLEAR+BLUE))
	
	
	archive_path = os.path.join(CONFIG_DIR,'bass.zip')
	
	try:
		msg('downloading bass')
		with http(BASS_DOWNLOAD_URL) as web:
			with open(archive_path,'wb') as file:
				file.write(web.read())
		
		
		
		msg('extracting')
		with ZipFile(archive_path) as zip:
			zip.extractall(os.path.join(CONFIG_DIR,'bass'),[x64 and 'x64/bass.dll' or 'bass.dll'])
		
		dll_path=x64 and os.path.join(CONFIG_DIR,'bass','x64','bass.dll') or os.path.join(CONFIG_DIR,'bass','bass.dll')
		
		msg('moving bass.dll')
		if os.path.exists(out_path):
			os.remove(out_path)
		os.rename(dll_path,out_path)
		
	finally:
		msg('cleaning up')
		os.remove(archive_path)
		
		if x64:
			if os.path.exists(os.path.join(CONFIG_DIR,'bass','x64','bass.dll')):
				os.remove(os.path.join(CONFIG_DIR,'bass','x64','bass.dll'))
			os.rmdir(os.path.join(CONFIG_DIR,'bass','x64'))
		else:
			if os.path.exists(os.path.join(CONFIG_DIR,'bass','bass.dll')):
				os.remove(os.path.join(CONFIG_DIR,'bass','bass.dll'))
		os.rmdir(os.path.join(CONFIG_DIR,'bass'))
	
	return

def setupVpkReader(force=False):
	out_path = os.path.join(CONFIG_DIR,'vpk2reader.py')
	
	if os.path.exists(out_path) and not force:
		printh('vpk2reader.py','ALREADY EXISTS! (skipping)')
		return False
	
	printh('vpk2reader.py','downloading')
	with http(VPKREADER_URL) as web:
		with open(out_path,'wb') as file:
			file.write(web.read())
	return

def setupSlpp(force=False):
	out_path = os.path.join(CONFIG_DIR,'slpp.py')
	
	if os.path.exists(out_path) and not force:
		printh('slpp.py','ALREADY EXISTS! (skipping)')
		return False
	
	printh('slpp.py','downloading')
	with http(SLPP_URL) as web:
		with open(out_path,'wb') as file:
			file.write(web.read())
	return




indexes = {}
def getVpk(path):
	if path in indexes:
		return indexes[path]
	
	indexes[path] = VpkIndex(path)
	return indexes[path]


def downloadLists(path):
	links = {}
	with http(CHATSOUNDS_REPO+path) as web:
		data = json.load(web)

	for a in data:
		link = "{}/{}".format(path,a['name'])
		hash = a['sha']
		if a['type']=='file':
			links[hash] = a['download_url']
		elif a['type']=='dir':
			links = merge(downloadLists(link),links)
	
	return links


def savePaths():
	with open(PATHS_DIR,'wb') as file:
		file.write(lua.encode(PATHS))

def loadPaths(): # TODO say if path not found!
	global PATHS
	try:
		with open(PATHS_DIR,'rb') as file:
			PATHS = lua.decode(file.read())
	except IOError, e:
		pass
	
	
	for key,value in PATHS.iteritems():
		if type(value) is list:
			for path in value:
				if not os.path.isdir(path):
					warn('"{}" is not a valid folder! (paths {})'.format(path,key))
		elif type(value) is str:
			if not os.path.isdir(value):
				warn('"{}" is not a valid folder! (paths {})'.format(value,key))
	
	
	return PATHS


Lists = {}
def loadLists():
	for filename in os.listdir(LISTS_DIR):
		with open(os.path.join(LISTS_DIR,filename),'rb') as file:
			data = file.read()
		
		decoded = lua.decode(data)
		try:
			for name,paths in decoded.iteritems():
				for item in paths:
					if name not in Lists:
						Lists[name] = []
					
					list = Lists[name]
					list.append(item)
		except TypeError, e:
			warn('error loading list: {} ({})'.format(filename,e))
	
	return



def listToFile(data,filename):
	oldsize=len(data)
	data = re.sub('c\.StartList\(".*?"\)',	'{',	data)
	if len(data)==oldsize: # StartList not found
		return False
	
	data = re.sub('c\.EndList\(\)',			'}',	data)
	data = re.sub('L\["',					'["',	data)
	
	decoded = lua.decode(data)
	encoded = lua.encode(decoded)
	
	with open(filename,'wb') as file:
		file.write(encoded)
	
	return True


def randomSound(list):
	return random.choice(list)

channels = []
def playSound(path):
	print('playing {}'.format(path))
	
	
	path = os.path.join(PATHS['chatsounds'],'sound',goodpath(path))
	print(path)
	chan = BASS_StreamCreateFile(False, path, 0, 0, 0)
	if not chan:
		warn('BASS Error ({})'.format(get_error_description(BASS_ErrorGetCode())))
		return False
	
	channels.append(chan)
	BASS_ChannelPlay(chan, False)
	
	
	
	"""
	get path from lists
	check chatsounds if ^chatsounds/... (or check if path exists?)
		chan = BASS_StreamCreateFile(False, path, 0, 0, 0)
	else vpks
		data = f.getData()
		chan = BASS_StreamCreateFile(True, data, 0, len(data), 0)
	
	channels.append(chan)
	
	BASS_ChannelPlay(chan, False)
	"""
	

def updateLists():
	
	deleted=0
	uptodate=0
	updated=0
	errors=0
	
	
	if (PATHS['chatsounds']!='' and os.path.exists(PATHS['chatsounds'])): # use local
		printh('update','using local!')
		
		lists_path = os.path.join(PATHS['chatsounds'],'lua','chatsounds')
		if not os.path.isdir(lists_path):
			warn('chatsounds path does not exist!')
			return False
		
		lists = findFiles(os.path.join(lists_path,'lists_nosend'))+findFiles(os.path.join(lists_path,'lists_send'))
		
		hashs={}
		for filename in lists:
			with open(filename,'rb') as file:
				data = file.read()
				
				hash = hashlib.sha1(data).hexdigest()
				file_path = os.path.join(LISTS_DIR,hash)
				
				hashs[hash] = file_path
				
				
				if os.path.exists(file_path):
					uptodate+=1
				else:
					good = listToFile(data,file_path)
					if not good:
						warn('not good: '+filename)
						errors+=1
					else:
						updated+=1
		
		for filename in os.listdir(LISTS_DIR):
			if filename not in hashs:
				os.remove(os.path.join(LISTS_DIR,filename))
				deleted+=1
	
	
	
	else: # use remote
		printh('update','using remote!')
		
		info('Finding lists')
		try:
			lists = downloadLists('lists_send') # because assuming no local chatsounds
			# merge(downloadLists('lists_nosend'),downloadLists('lists_send'))
		except (urllib2.URLError, urllib2.HTTPError), e:
			warn('could not get lists!')
			return False
		
		for filename in os.listdir(LISTS_DIR):
			if filename not in lists:
				os.remove(os.path.join(LISTS_DIR,filename))
				deleted+=1
		
		info('Downloading lists')
		for hash,url in lists.iteritems():
			filename = os.path.join(LISTS_DIR,hash)
			if os.path.exists(filename):
				uptodate+=1
				continue
			
			try:
				with http(url) as web:
					data = web.read()
			except (urllib2.URLError, urllib2.HTTPError), e:
				warn('{} failed ({})'.format(url,e))
				errors+=1
			
			good = listToFile(data,filename) # not really original file hash, but whatever
			if not good:
				warn('not good: '+url)
				errors+=1
			else:
				updated+=1
	
	
	
	info('{} uptodate'.format(uptodate))
	warn('{} deleted'.format(deleted))
	success('{} updated'.format(updated))
	if errors>0:
		warn('{} ERRORS!'.format(UNDERLINE+str(errors)))
	
	return True


def load():
	
	if _exists('BASS_Init'):
		if BASS_Init(-1, 44100, 0, 0, 0):
			success("BASS loaded!")
		else:
			warn("BASS COULD NOT BE LOADED! ({})".format(get_error_description(BASS_ErrorGetCode())))
	else:
		warn("BASS COULD NOT BE LOADED! ({})".format("library missing"))
	
	
	if _exists('lua'):
		loadLists()



def command_callback(word, word_eol, userdata):
	name = word[1]
	
	
	if name=='sh':
		for chan in channels:
			BASS_ChannelStop(chan)
		del channels[:]
		return hexchat.EAT_ALL
	elif name=='setup':
		force = False
		if len(word)==3:
			force=word[2]=='force'
		
		
		setupSlpp(force)
		setupVpkReader(force)
		setupPybass(force)
		setupBass(force)

		
		success("Setup complete! Reload the plugin: "+BLUE+"/reload chatsounds.py")
		
		
		return hexchat.EAT_ALL
	elif name=='update':
		updateLists()
		return hexchat.EAT_ALL
	elif name=='load':
		loadPaths()
		load()
		return hexchat.EAT_ALL
	elif name=='paths':
		
		if len(word)>2:
			key = word[2]
			
			if key not in PATHS:
				warn('{} is not a valid key in paths!'.format(key))
				
			else:
				typ = type(PATHS[key])
				
				if typ is str:
					# set path
					if len(word)!=5:
						warn('incorrect usage: {}'.format(BLUE+'/chatsounds paths {} set (path)'.format(key)))
						return hexchat.EAT_ALL
					mode = word[3]
					path = word[4]
					
					if mode=='set':
						PATHS[key]=path
						
					else:
						warn('invalid mode!')
						return hexchat.EAT_ALL
					
				elif typ is list:
					# add path
					# del/remove path
					if len(word)!=5:
						warn('incorrect usage: {}'.format(BLUE+'/chatsounds paths {} (add/del/remove) (path)'.format(key)))
						return hexchat.EAT_ALL
					mode = word[3]
					path = word[4]
					
					if mode=='add':
						if len(PATHS[key])==1 and PATHS[key][0]=='':
							PATHS[key][0] = path
						else:
							PATHS[key].append(path)
						
					elif mode=='del' or mode=='delete' or mode=='remove': # if first and only element=='' then set that element
						if path not in PATHS[key]:
							warn('{} is not in {}!'.format(path,key))
							return hexchat.EAT_ALL
						
						PATHS[key].remove(path)
						
						if len(PATHS[key])==0:
							PATHS[key].append('')
							print'fixed'
						
					else:
						warn('invalid mode!')
						return hexchat.EAT_ALL
				
				
				savePaths()
				loadPaths()
				
				
		"""
		if mode=='set':
			if len(word)==5:
				
				key = word[3]
				value = word[4]
				
				if key=='vpk':
					paths['vpk'] = value
					success('vpk set')
				elif key=='chatsounds':
					paths['chatsounds'] = value
					success('chatsounds set')
				else:
					warn('wrong key (vpk|chatsounds)')
					return hexchat.EAT_ALL
				
				savePaths()
			else:
				warn('wrong syntax: {}'.format(BLUE+'/chatsounds paths set (vpk|chatsounds) path/to/folder'))
				return hexchat.EAT_ALL
			
			"""
			
			
		info('vpk: {}'.format('['+UNDERLINE+(', '.join(PATHS['vpk']))+CLEAR+BOLD+BLUE+']'))
		info('chatsounds: {}'.format(UNDERLINE+PATHS['chatsounds']))
		
		return hexchat.EAT_ALL
	
	
	try:
		_list = Lists[name]
	except KeyError:
		warn('{} not found in list'.format(name))
		return hexchat.EAT_ALL
	
	item = randomSound(_list)
	
	playSound(item['path']) # ,item['length'])
	
	
	return hexchat.EAT_ALL
hexchat.hook_command('chatsounds',command_callback)




def unload_callback(userdata):
	info('Unloading {}'.format(__module_name__))
	if _exists('BASS_Free'):
		BASS_Free()
	else:
		warn("BASS doesn't exist to unload!")
	
hexchat.hook_unload(unload_callback)

loadPaths()

print('%s version %s loaded.' % (__module_name__,__module_version__))

