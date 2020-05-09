#!/bin/bash -v
#
#
mkdir -p ../_build/pyman
rm -rf ../_build/pyman/*
#
# build the website
#
sphinx-build  -N -v -b html . _build/html
rsync -avz _build/html/* ../_build/pyman/.





