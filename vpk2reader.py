import os, struct, binascii

def get_int4(file):
	return int( struct.unpack("I",file.read(4))[0] )
def get_int2(file):
	return int( struct.unpack("H",file.read(2))[0] )
def get_sz(file):
	out = ""
	while True:
		cur = file.read(1)
		if cur == b'\x00': break
		out += struct.unpack("c",cur)[0].decode("ASCII")
	return out


class VpkIndex():
	path = ""
	signature = None
	version = None
	dirlength = None
	unknown1 = None
	unknown2 = None
	unknown3 = None
	unknown4 = None
	
	files = {}
	
	def __init__(self, path):
		print("loading",path)
		
		self.path = path
		
		self.file = open(path,'rb')
		self.signature = binascii.b2a_hex(self.file.read(4))
		self.version   = get_int4(self.file)
		self.dirlength = get_int4(self.file)
		
		self.unknown1 = get_int4(self.file)
		self.unknown2 = get_int4(self.file)
		self.unknown3 = get_int4(self.file)
		self.unknown4 = get_int4(self.file)
		
		self.Process()
		
		
	def Process(self):
		
		while True:
			extension = get_sz(self.file)
			if not extension: break
			
			while True:
				folder = get_sz(self.file)
				if not folder: break
				
				while True:
					filename = get_sz(self.file)
					if not filename: break
					
					
					path = "{}/{}.{}".format(folder,filename,extension)
					cur_file = VpkFile(path)
					self.files[path] = cur_file
					
					
					cur_file.CRC = get_int4(self.file)
					preload_bytes = get_int2(self.file)
					
					cur_file.archive_index = get_int2(self.file)
					if cur_file.archive_index == b'\x7fff':
						print("EMBED")
					
					cur_file.archive_path = self.path[:-7]+"{}.vpk".format(str(cur_file.archive_index).zfill(3))
					
					
					cur_file.offset = get_int4(self.file)
					cur_file.length = get_int4(self.file)
					
					get_int2(self.file)
					
					if preload_bytes:
						cur_file.preload = file.read(prelaod_bytes)
		
		self.close()
		
	def close(self):
		self.file.close()
	
	def __str(self):
		return '<VpkIndex: {}>'.format(self.path)
	
	
class VpkFile():
	path = ""
	CRC = -1
	archive_index = -1
	archive_path = ""
	offset = -1
	length = -1
	preload = bytes()
	
	def __init__(self, path):
		self.path = path
	
	def __str__(self):
		return '<VpkFile: {} {}>'.format(self.archive_path,self.path)
	
	
	def getData(self):
		data = self.preload
		
		vpk = open(self.archive_path,'rb')
		
		vpk.seek(self.offset)
		data += vpk.read(self.length)
		
		vpk.close()
		
		
		return data
	

