#!/bin/bash -v
#
# move the ipynb files into the doc_notebooks folder
#
mkdir -p _build
#
# build the website
#
sphinx-build -N -v -b html . _build/html



