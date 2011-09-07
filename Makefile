help:
	@echo "Usage: clean|build"

clean:
	rm -fv *.sqlite *.sqlite-journal *.csv
	rm -rfv dist/
	rm -rfv build/
	python setup.py clean

test:
	python setup.py nosetests

build:
	python setup.py build bdist_egg

