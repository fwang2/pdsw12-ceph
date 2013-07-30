#!/bin/bash

PATH=/usr/texbin:$PATH
/usr/texbin/latexmk -pdflatex=lualatex -pdf $*

# clean up
rm -f *.snm
rm -f *.nav
