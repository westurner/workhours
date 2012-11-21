# workhours setup.py file
from setuptools import setup, find_packages
import os.path as osp
version = '0.5'

def rel_path(path_):
    return osp.join(osp.dirname(osp.abspath(__file__)), path_)


from setuptools.command.test import test as TestCommand

class PyTest(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True
    def run_tests(self):
        #import here, cause outside the eggs aren't loaded
        import pytest
        pytest.main(self.test_args)

setup(name='workhours',
    version=version,
    description="Aggregates events from various sources",
    long_description='\n'.join( (
        file(rel_path('README.rst'),'rb').read(),
        file(rel_path('CHANGES.rst'), 'rb').read(),) ),
    classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
    keywords='',
    author='Wes Turner',
    author_email='wes@wrd.nu',
    url='',
    license='New BSD',
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    package_data={
        'workhours': ['scripts/*.sh',] },
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        # -*- Extra requirements: -*-
        'SQLAlchemy>=0.6beta1',
        'pytz>=2010e',
        'BeautifulSoup',
        'pyutmp',
        'pyes'
        ],
    entry_points={
        # -*- Entry points: -*-
        'paste.app_factory': [
            'main = workhours:main'
        ],
        'console_scripts': [
            'workhours = workhours.climain:main',
            ]
        },
    tests_require=['pytest','pytest-cov'],
    cmdclass = {'test': PyTest},
)
