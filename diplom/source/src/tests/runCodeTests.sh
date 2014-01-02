#!/bin/bash

pyflakes app *.py >tests/reports/checkstyle.txt
pep8 app *.py >>tests/reports/checkstyle.txt
pylint main.py  -f html >>tests/reports/pylint.html
google-chrome tests/reports/pylint.html
