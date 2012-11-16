'''Modum is a modular, multi-server, asynchronous IRC bot written in python.'''

from setuptools import setup, find_packages
from lib.bot import __version__

readme = open('README.rst').read()

setup(
    name='Modum',
    version=__version__,
    url='https://github.com/Ivoz/Modum',
    license='CC 3.0 by-sa',
    author='Matthew Iversen',
    author_email='teh.ivo@gmail.com',
    description=__doc__,
    long_description=readme,
    packages=find_packages(),
    zip_safe=False,
)
