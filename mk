#!/bin/bash

PATH=/usr/texbin:$PATH
#/usr/texbin/latexmk -pdflatex=lualatex -pdf $*
/usr/texbin/latexmk -pdflatex="lualatex %O %S" -pdf -dvi- -ps- $*
# clean up
rm -f *.snm
rm -f *.nav
