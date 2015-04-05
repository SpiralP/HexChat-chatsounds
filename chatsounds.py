__module_name__ = 'chatsounds'
__module_author__ = 'SpiralP'
__module_version__ = '1'
__module_description__ = 'chatsounds'

import os, sys
import urllib2, json
import re

import hexchat


HEXCHAT_CONFIG_DIR=hexchat.get_info('configdir')
HEXCHAT_ADDONS_DIR=os.path.join(HEXCHAT_CONFIG_DIR,'addons')

CONFIG_DIR=os.path.join(HEXCHAT_CONFIG_DIR, 'chatsounds')
LISTS_DIR=os.path.join(CONFIG_DIR,'lists')

if not os.path.exists(LISTS_DIR):
	os.makedirs(LISTS_DIR)


if CONFIG_DIR not in sys.path:
	sys.path.insert(0, CONFIG_DIR) # for imports

os.environ['PATH'] = os.environ['PATH'] + ';' + CONFIG_DIR # for dlls


from pybass import *
from vpk2reader import *



CHATSOUNDS_DIR='D:\\music\\'
CHATSOUNDS_REPO='https://api.github.com/repos/Metastruct/garrysmod-chatsounds/contents/lua/chatsounds/'


LIST_REGEX='L\["(.+)"\]={{path="(.+)",length=(.+)}}'


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


def merge(a,b):
	c = a.copy()
	c.update(b)
	return c

def getLists(path=None):
	links = {}
	http = urllib2.urlopen('{}{}'.format(CHATSOUNDS_REPO,path))
	data = json.load(http)
	http.close()

	for a in data:
		link = "{}/{}".format(path,a['name'])
		hash = a['sha']
		if a['type']=='file':
			links[hash] = a['download_url']
		elif a['type']=='dir':
			links = merge(getLists(link),links)
	
	return links





indexes = {}
def getVpk(path):
	if path in indexes:
		return indexes[path]
	
	indexes[path] = VpkIndex(path)
	return indexes[path]


def loadVpks():
	return




channels = []
def command_callback(word, word_eol, userdata):
	name = word[1]
	
	
	if name=='sh':
		for chan in channels:
			BASS_ChannelStop(chan)
		del channels[:]
		return hexchat.EAT_ALL
	elif name=='downloadlists':
		
		info('Finding lists')
		lists = merge(getLists('lists_nosend'),getLists('lists_send'))
		
		deleted=0
		uptodate=0
		updated=0
		
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
			
			http = urllib2.urlopen(url)
			data = http.read()
			http.close()
			
			items = re.findall(LIST_REGEX,data)
			
			with open(filename,'wb') as file:
				for name,path,length in items:
					file.write(
						'\t'.join((name,path,length))
					)
					file.write('\n')
				file.close()
			
			updated+=1
		
		
		info('{} uptodate'.format(uptodate))
		warn('{} deleted'.format(deleted))
		success('{} updated'.format(updated))
		
		
		loadLists()
		
		return hexchat.EAT_ALL
		
		
	
	
	name = os.path.join(CHATSOUNDS_DIR,name)
	
	"""
	
	get path from lists
	check chatsounds if ^chatsounds/...
		chan = BASS_StreamCreateFile(False, path, 0, 0, 0)
	else vpks
		data = f.getData()
		chan = BASS_StreamCreateFile(True, data, 0, len(data), 0)
	
	"""
	
	
	if not os.path.exists(name):
		# check vpks
		return hexchat.EAT_ALL
	
	
	channels.append(chan)
	
	BASS_ChannelPlay(chan, False)
	
	return hexchat.EAT_ALL
hexchat.hook_command('chatsounds',command_callback)




def unload_callback(userdata):
	info('Unloading {}'.format(__module_name__))
	BASS_Free()
hexchat.hook_unload(unload_callback)


if BASS_Init(-1, 44100, 0, 0, 0):
	success("BASS loaded!")
else:
	warn("BASS COULD NOT BE LOADED! ({})".format(get_error_description(BASS_ErrorGetCode())))

	

print('%s version %s loaded.' % (__module_name__,__module_version__))


if False:
	pybass_path = os.path.join(CONFIG_DIR,'pybass.zip')
	print('getting pybass')
	http = urllib2.urlopen('http://sourceforge.net/projects/pybass/files/latest/download?source=files')
	with open(pybass_path,'wb') as file:
		file.write(http.read())
		file.close()
	http.close()


	import zipfile
	zip = zipfile.ZipFile(pybass_path,'r')

	zip.extractall(CONFIG_DIR)
	zip.close()
	with open(os.path.join(CONFIG_DIR,'pybass','__init__.py'),'wb') as file:
		file.write('from pybass import *\n') # compat
		file.close()



if False:
	bass_path = os.path.join(CONFIG_DIR,'bass.zip')
	print('getting bass')

	http = urllib2.urlopen('http://www.un4seen.com/files/bass24.zip')
	with open(bass_path,'wb') as file:
		file.write(http.read())
		file.close()
	http.close()

	import zipfile

	zip = zipfile.ZipFile(bass_path,'r')
	zip.extractall(os.path.join(CONFIG_DIR,'bass'),['bass.dll'])
	zip.close()






