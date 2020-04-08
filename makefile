PYTHON = pyenv/bin/python

all:
	@rm -rf /tmp/hlcursor/cursors
	@mkdir -p /tmp/hlcursor/cursors
	@$(PYTHON) hlcursor.py /tmp/hlcursor/cursors

pydep:
	@rm -rf pyenv
	@virtualenv -p python3 pyenv
	@pyenv/bin/pip install -r python3-requirements.txt

pack-theme:
	@tar -czf DMZ-JaGHighlight.tar.gz -C ~/.icons/ DMZ-JaGHighlight
