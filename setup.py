'''
Modum
=====

Modum is a modular, multi-server, asynchronous IRC bot written in python.
'''

from setuptools import setup, find_packages

setup(
    name='Modum',
    version='1.0dev',
    url='https://github.com/Ivoz/Modum',
    license='CC by-sa',
    author='Matthew Iversen',
    author_email='maxc@me.com',
    description='Modum is a modular, multi-server, asynchronous IRC bot written in python.',
    long_description=__doc__,
    packages=find_packages(),
    data_files=[('.', ['config-example.json'])]
)
