#!/bin/bash -v
#
# move the ipynb files into the doc_notebooks folder
#
mkdir -p _build
rm -rf _build/*
#
# build the website
#
sphinx-build -N -v -b html . _build/html
cp _build/html/equno.html equno_myst.html
cp -a _build/html/* _build/.





