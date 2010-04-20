from setuptools import setup, find_packages
import sys, os

version = '0.1'

setup(name='workhours',
      version=version,
      description="Reads work hours from firefox sqlite logs",
      long_description="""\
""",
      classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='',
      author='Wes Turner',
      author_email='wes.turner@gmail.com',
      url='',
      license='New BSD',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          # -*- Extra requirements: -*-
      ],
      entry_points="""
      # -*- Entry points: -*-
      """,
      )
