
.PHONY: clean upload venv install

venv:
	python3 -m venv venv

install: venv
	./venv/bin/pip install -e .

clean:
	rm -rf dist/ .eggs/ *.egg-info/

upload: clean install
	./venv/bin/python -m build
	./venv/bin/twine upload dist/*
