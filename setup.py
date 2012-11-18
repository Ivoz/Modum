'''Modum is a modular, multi-server, asynchronous (gevent-based) IRC bot written in python.'''

from setuptools import setup, find_packages
from lib.bot import __version__

readme = open('README.rst').read()
package_name = 'Modum'

setup(
    name=package_name,
    version=__version__,
    url='https://github.com/Ivoz/Modum',
    license='CC 3.0 by-sa',
    author='Matthew Iversen',
    author_email='teh.ivo@gmail.com',
    description=__doc__,
    long_description=readme,
    keywords='IRC bot gevent',
    packages=find_packages(),
    install_requires=['gevent'],
    zip_safe=False
)
