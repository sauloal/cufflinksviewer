find . -type f -name '*.pyc' -exec rm {} \;
find . -type f -name '*.pyo' -exec rm {} \;

venvlin/bin/python server.py
