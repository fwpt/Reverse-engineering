# Extract files from CSR VM app DFU firmware partitions
# Please note DFU firmware format is proprietary Qualcomm software. Use this script only for research and educational purposes.  
# Current status: experimental - achieved by reverse engineering the partition files. Far from perfect, but works to extract the raw files from the partition/filesystem.
# Existing firmware extraction tools and binwalk don't recognise this format.
# Todo: extract to subdirectories (directory names are currently blank files without extension)
# Todo: some files do not have a proper length (missing a few bytes) which could make them corrupt if they were not padded (need to improve length calculation)
# Input partition files need to be extracted from OTAU single-file format first; there's scripts out there already for this.

import sys, struct, math
#from collections import namedtuple

outDir = './extract/' #V0411-s0/'
validMagic = b'File'
curPos = 0
verbose = True

if (len(sys.argv) <= 1):
	print('Usage: ' + sys.argv[0] + ' filename.bin')
	sys.exit(1)

if (len(sys.argv) == 3):
	outDir = sys.argv[2]

if (not outDir.endswith('/')):
	outDir = outDir + '/'

with open(sys.argv[1], 'rb') as binfile:
	binfile.seek(0, 0) # Go to beginning of file
	magic = binfile.read(4)
	if (magic != validMagic):
		print('Invalid file, unrecognised magic header')
		binfile.close()
		sys.exit(1)
	elif (verbose):
		print('Valid magic:', magic.decode('utf-8'))

	#dataT = struct.unpack('>IH', header) # read as big-endian
	#print(dataT)

	# The following could also be achieved using (un)pack but current reading in chunks allowed me to debug/develop the script 
	binSize = int.from_bytes(binfile.read(4), byteorder='big')
	binSizeUnix = 2 * binSize
	
	if (verbose):
		print('Filesize:', binSizeUnix)

	#tmp = binfile.read(2+4+4)
	#print(ord(tmp[0:4]))
	fileCountHeader = int.from_bytes(binfile.read(2), byteorder='big')
	if (verbose):
		print('fileCountHeader:', fileCountHeader)
	##fileCount = fileCountHeader - 1
	#unused1 = readbytes(10, 4)
	unused1 = int.from_bytes(binfile.read(4), byteorder='big')
	if (verbose):
		print('unused1', unused1)
	unsureType = int.from_bytes(binfile.read(4), byteorder='big')
	if (verbose):
		print('unsureType', unsureType)
	unused2 = int.from_bytes(binfile.read(2), byteorder='big')
	if (verbose):
		print('unused2', unused2)
	ignore = int.from_bytes(binfile.read(2), byteorder='big')
	fileCount = fileCountHeader - 1;
	if (verbose):
		print('fileCount', fileCount)
	curPos = binfile.tell()
	if (verbose):
		print('curPos', curPos)
	for i in range(fileCount):

		ignore = int.from_bytes(binfile.read(2), byteorder='big') # ignore now; could be 00 or 80; 80 means directory?
		offsetName = 2 * int.from_bytes(binfile.read(2), byteorder='big') # read 2 instead of 4 (see prev line)
		# 2*offsetName = start address filename
		offsetData = 2 * int.from_bytes(binfile.read(4), byteorder='big')
		#print('offsetData', offsetData)
		fileSize = int.from_bytes(binfile.read(4), byteorder='big')
		
		# save curPos for reading next file meta data
		curPos = binfile.tell()
		
		binfile.seek(offsetName)
		fileNameLen = int.from_bytes(binfile.read(2), byteorder='big')		
		fileName = binfile.read(fileNameLen * 2)
		#print(type(fileName), fileName)
		fileName = fileName.decode('ascii') #.lstrip('\x00')
		#fileName = fileName.split('\x00', 1)[0]
		fileName = fileName.replace('\x00', '')
		#print(type(fileName), bytes(fileName.encode('utf-8')))
		
		#readSize = math.ceil(fileSize / 2)
		readSize = fileSize
		print('Writing file', (i+1), 'of', fileCount, ':', fileName, '(', readSize, 'b )')
		#if ((file.size % 2) == 1) {
			# if not even (odd) eg 59 bytes > should read 30 and last byte is zero
			# check if we need adjustements
		#}
		binfile.seek(offsetData)
		fileData =  binfile.read(readSize)
		if (False and verbose):
			print('len', sys.getsizeof(fileData))
			print('datasize', fileSize)
			print('readSize', readSize)
		
		# write file
		with open(outDir + fileName, 'wb') as writefile:
			bytesWritten = writefile.write(fileData)
			#print('written', bytesWritten)
			writefile.close()

		# limit to max 100 files currently; don't expect more files (fail safe when we misread header)
		if (i >= 100):
			break	

		binfile.seek(curPos, 0)

	binfile.close()
