.. simuluxe documentation master file, created by
   sphinx-quickstart on Mon Oct 13 22:42:20 2014.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Simuluxe Documentation
======================

Simuluxe is a collection of modeling and simulation analysis tools designed for biophysical simulations. "Simuluxe" is short for "luxurious simulations" or more specifically an everything-and-the-kitchen sink approach to analyzing biophysical simulation data from a variety of models. It is currently migrating from the ``membrain`` project written partly by Ryan Bradley, but will soon include the following functions.

1. Rapidly developing code for analysing molecular dynamics simulations.
2. Plotting across large datasets.
3. Hypotheses testing and large parameter sweeps.
4. Integration of fine-grained and coarse-grained simulation data.

Deployment
----------

The purpose of this code is to help researchers in computational biophysics analyze datasets quickly and easily, with a particular emphasis on analyzing large batches of simulations, possibly generated with [automacs](https://github.com/bradleyrp/automacs). The procedure for analyzing simulations is as follows.

1. Run a simulation and store the trajectory locally.
2. Download the ``simuluxe`` package.
3. Choose a script from ``simuluxe/scripts`` and copy it to a new folder for your calculation. Let's call that folder ``~/mycalc/`` and use the blank script called ``script-blank.py`` for our example.
4. Add simulation settings, including a ``trr`` or ``xtc`` entry and a ``gro`` entry to the ``simdict`` dictionary in a new file let's call it ``info.py``. Using the following code as a guide. Note that the following dictionary will always be loaded, and is meant to contain metadata about your simulation. ::

	simdict['my_simulation'] = {
		'gro':'path_to_my_gro_file',
		'trr':'path_to_my_trr_file',
		}

5. Return to the ``simuluxe`` folder run ``make addconfig <path to info.py>`` which will generate your local configuration, and add your trajectory paths to it.
6. In your calculation folder, you can modify and create new scripts to use both the ``simuluxe`` library as well as parse, catalog, and access your simulation trajectories. Run ``script-blank.py`` as a test.

When you are finished, you will have a local configuration file at ``~/.simuluxe_config.py`` which points to extra paths and descriptions of your simulations in ``~/mycalc/info.py``. Running a script e.g. ``~/mycalc/script-blank.py`` will automatically find and load the ``simuluxe`` code you downloaded earlier, and the extra configuration in ``info.py``. This will come in handy later.

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

