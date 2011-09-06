from setuptools import setup, find_packages

version = '0.5'

setup(name='workhours',
      version=version,
      description="Aggregates events from firefox places.sqlite and trac timeline.html files",
      long_description="""\
""",
      classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='',
      author='Wes Turner',
      author_email='wes@wrd.nu',
      url='',
      license='New BSD',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          # -*- Extra requirements: -*-
          'SQLAlchemy>=0.6beta1',
          'pytz>=2010e',
          'BeautifulSoup',
          'pyutmp'
      ],
      entry_points={
      # -*- Entry points: -*-
         'console_scripts': [
        'workhours = workhours.main:main',
     ]
      }
)
