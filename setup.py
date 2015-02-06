# workhours setup.py file
from setuptools import setup, find_packages
import os
import os.path as osp
version = '0.5.01'

def rel_path(path_):
    return osp.join(osp.dirname(osp.abspath(__file__)), path_)


from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'README.rst')) as f:
    README = f.read()
with open(os.path.join(here, 'CHANGES.rst')) as f:
    CHANGES = f.read()

requires = [
    'pytz',
    'BeautifulSoup',
    'pyutmp',
    'pyes',


    'pyramid',
    'waitress',
    'sqlalchemy',
    'alembic',
    'pyramid_jinja2',
    'passlib',
    'colander',
    'pyramid_marrowmailer',
    'html2text',
    'pyramid_tm',
     #'zope.sqlalchemy',
    'sqlalchemy-utils',
    ]

setup(name='workhours',
    version=version,
    description="Aggregates events from various sources",
    long_description='\n'.join( (README, CHANGES) ),
    classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
    keywords='',
    author='Wes Turner',
    author_email='wes@wrd.nu',
    url='',
    license='New BSD',
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    package_data={
        'workhours': [
            'README.rst',
            'CHANGES.rst',
            'scripts/*.sh',] },
    include_package_data=True,
    zip_safe=False,
    entry_points={
        # -*- Entry points: -*-
        'paste.app_factory': [
            'main = workhours:main'
        ],
        'console_scripts': [
            'workhours = workhours.climain:main',
        ]
    },
      install_requires=requires,
      #tests_require=requires + ['nose', 'fixture'],
      test_suite="test",
      )
