
test: clean nosetests local


clean:
	rm -rf tasks/
	rm -fv *.sqlite *.sqlite-journal *.csv
	rm -rf whtmp*
	rm -rf dist/
	rm -rf build/
	python setup.py clean

build:
	python setup.py build bdist_egg

local:
	time workhours -c ./local.ini -p -v 2>&1 | tee local.log

nosetests: 
	python setup.py nosetests

help:
	@echo "Usage: clean|build"

