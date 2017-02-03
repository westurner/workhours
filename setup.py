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
 'BeautifulSoup',
 'alembic',
 'celery',
 'colander',
 'deform',
 'deform-jinja2',
 'fixture',
 'formencode',
 'html2text',
 'iso8601',
 'passlib',
 'peppercorn',
 'pyes',
 'pyparsing',
 'pyramid',
 'pyramid-celery',
 'pyramid-debugtoolbar',
 'pyramid-deform',
 'pyramid-jinja2',
 'pyramid-restler',
 'pyramid-simpleform',
 'pyramid-sqlalchemy',
 'pyramid_jinja2',
 'pyramid_marrowmailer',
 'pyramid_tm',
 'pytz',
 'pyutmp',
 'sqlalchemy',
 'sqlalchemy-utils',
 'waitress',
 'webhelpers',
]

try:
    from collections import OrderedDict
    requiresdict = OrderedDict()
    for name in requires:
        # TODO: parse (name, (ver, constraints))
        requiresdict.setdefault(name, ['setup.py:requires'])

    import pip.req
    requirementstxtfiles = ['requirements.txt',]
    rtxtdict = OrderedDict.fromkeys(requirementstxtfiles)
    for rtxtpath in rtxtdict:
        requirements = rtxtdict[rtxtpath] = list(
            pip.req.parse_requirements(
                rtxtpath, session='1'))
        for req in requirements:
            reqsrcs = requiresdict.setdefault(req.name, list)
            reqsrcs.append(rtxtpath)
    #import pprint
    #pprint.pprint(requiresdict.items())
    #raise Exception(requiresdict)
    requires = requiresdict.keys()

except ImportError:
    import warnings
    warnings.warn("Pip not found; skipping loading requirements files: %r" % requirementstxtfiles)

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
