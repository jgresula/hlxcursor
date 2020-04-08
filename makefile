all:
	@rm -rf /tmp/hlcursor/cursors
	@mkdir -p /tmp/hlcursor/cursors
	@pyenv/bin/python hlcursor.py /tmp/hlcursor/cursors
