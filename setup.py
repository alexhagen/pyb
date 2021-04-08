#!/usr/bin/env python
from setuptools import setup


REQUIREMENTS = ['matplotlib', 'numpy']

setup(name='pyb',
      version='1.0',
      description='Python Blender Rendering Utilities',
      author='Alex Hagen',
      author_email='alexhagen6@gmail.com',
      url='https://alexhagen.github.io/pyb',
      packages=['pyb'],
      install_requires=REQUIREMENTS,
     )