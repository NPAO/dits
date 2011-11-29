import hashlib
from functools import partial
import os
import pyfits
import fnmatch
import re

class ImageTypeError(Exception):
	pass
	
	
def md5sum(filename):
    with open(filename, mode='rb') as f:
        d = hashlib.md5()
        for buf in iter(partial(f.read, 128), b''):
            d.update(buf)
    return d.hexdigest()



def get_filter_id(filter_name, conn):
	return conn.execute('select ID from FILTERS where NAME=?', 
						(filter_name.lower(),)).fetchone()[0]

def get_flipstat(header):
	flipstat = header['flipstat']
	if flipstat == ' ':
		return 0
	elif flipstat == 'Flip/Mirror':
		return 1
	else:
		raise KeyError('Flipstat not understood: %s' % flipstat)

def coord_fromstr(coordstr):
	coord_match = re.match('([+-]?)(\d{2})\s+(\d{2})\s+(\d{2}\.\d+)', coordstr)
	if coord_match != None:
		sign = coord_match.groups()[0]
		degrees, minutes, seconds = map(float, coord_match.groups()[1:])
		return int(sign+'1')*(degrees + minutes/60. + seconds/3600.)
	else:
		raise ValueError('Coordinate is not encoded in the standard way: %s' % coordstr)

def get_coord(header):
#get coordinates from header and convert to degrees
	try:
		ra = header['ra']
		dec = header['dec']
		return coord_fromstr(ra)*15., coord_fromstr(dec)
	except KeyError:
		return None, None


def get_objcoord(header):
#get coordinates from header and convert to degrees
	try:
		ra = header['obj_ra']
		dec = header['obj_dec']
		return ra, dec
	except KeyError:
		return None, None


def get_fwhm(header):
	try:
		fwhm = header['fwhm']
		return fwhm
	except KeyError:
		return None

def get_zmag(header):
	try:
		zmag = header['zmag']
		return zmag
	except KeyError:
		return None

def get_airmass(header):
	try:
		airmass = header['airmass']
		return airmass
	except KeyError:
		return None
		
def get_obstype_id(header):
	image_type = header['imagetyp']
	if image_type == 'Bias Frame':
		return 0
	elif image_type == 'Dark Frame':
		return 1

	elif image_type == 'Flat Field':
		return 2
	elif image_type == 'Light Frame':
		return 3
	else:
		raise ImageTypeError('Not a Bias, Dark, Flat or Science')

def get_pierside(header):
	try:
		pierside = header['pierside']
	except KeyError:
		return None
	if pierside.strip().lower() == 'west':
		return 1
	if pierside.strip().lower() == 'east':
		return 0

#def get_geoloc_id(	
						
def ingest_file(file_name, conn):
	curs = conn.cursor()
	header = pyfits.getheader(file_name)
	obstype_id = get_obstype_id(header)
	try:
		filter_id = get_filter_id(header['filter'], conn)
	except KeyError:
		filter_id = -1
	flip = get_flipstat(header)
	fwhm = get_fwhm(header)
	zmag = get_zmag(header)
	airmass = get_airmass(header)
	pierside = get_pierside(header)
	ra, dec = get_coord(header)
	obj_ra, obj_dec = get_objcoord(header)
	curs.execute('insert into OBSERVATIONS(OBS_TYPE_ID,'
		'GEO_LOC_ID, FILTER_ID, TARGET_ID, PROGRAM_ID, OBSERVER_ID, '
		'FLIP, NAXIS1, NAXIS2, SUBFX, SUBFY, BINNING, EXPTIME, MJD, '
		'RA, DEC, SET_TEMP, CCD_TEMP, FWHM, AIRMASS, ZMAG, PIERSIDE)'
		'values(%s)' % ','.join(22*'?'), 
		(obstype_id, 0, filter_id, 0, 0, 0, flip, header['naxis1'], header['naxis2'],
		header['xorgsubf'], header['yorgsubf'], header['xbinning'], header['exptime'],
		header['jd'] - 2400000.5, ra, dec,
		header['set-temp'], header['ccd-temp'], fwhm, airmass,
		zmag, pierside))
	obs_id = curs.lastrowid
	md5hash = md5sum(file_name)
	file_size = os.path.getsize(file_name)
	file_abspath = os.path.abspath(file_name)
	
	curs.execute('insert into FILES(OBS_ID, NAME, PATH, SIZE, MD5) '
				'values(?, ?, ?, ?, ?)',
				(obs_id, os.path.basename(file_abspath), os.path.dirname(file_abspath), file_size, md5hash))
	
	print "Read File %s" % file_abspath
	 
def ingest_tree(root_path, conn, pattern='*.fts'):

	for root, dirs, files in os.walk(root_path):
	    for filename in fnmatch.filter(files, pattern):
	        file_name = os.path.join(root, filename)
	        ingest_file(file_name, conn)

