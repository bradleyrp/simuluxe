#!/bin/bash

#---requires sphinx_rtd_theme from readthedocs.com and numpydoc
#---install with: sudo pip install sphinx_rtd_theme
#---install with: sudo easy_install numpydoc

#---this script requires the base directory as an argument
basedir=$1
cd $basedir
rm -r $basedir/docs
sphinx-apidoc -F -o $basedir/docs $basedir/simuluxe
cp $basedir/sources/docs/conf-sphinx.py $basedir/docs/conf.py
cp $basedir/sources/docs/index.rst $basedir/docs/
cd $basedir/docs
make html
cwd=$(pwd)
cd $basedir
echo "documentation is ready at file://"$cwd"/_build/html/index.html"
