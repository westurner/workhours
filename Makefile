

_ETC?=.

test: clean pytest local

clean:
	rm -rf tasks/
	rm -fv *.sqlite
	rm -fv *.sqlite-journal
	rm -fv *.csv
	rm -rf whtmp*
	rm -rf dist/
	rm -rf build/
	python setup.py clean

build:
	python setup.py build bdist_egg

local:
	rm -rf ~/.ve/workhours/var/cache/events
	workhours -c ${_ETC}/cli.ini -P  2>&1 && echo $# | tee local.log

nosetests:
	python setup.py nosetests

pytest:
	pytest

tags:
	cd ${VIRTUAL_ENV}
	grind --follow '*.py' | ctags -L -

help:
	echo "Usage: clean|build"

