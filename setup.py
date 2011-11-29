#setup script for DIT software
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

import glob

#version number
version = '0.01dev'

# Treat everything in scripts except README.rst as a script to be installed
scripts = glob.glob('scripts/*')
try:
	scripts.remove('scripts/README.rst')
except ValueError:
	pass


setup(name='dits',
	  description='DIT Software - Pipeline and operation software for the DIT (Arctic)',
	  author='The DIT collaboration',
      version=version,
      packages=['dits'],
      package_data={'dits': ['data/*']},
      scripts=scripts
      )
      
