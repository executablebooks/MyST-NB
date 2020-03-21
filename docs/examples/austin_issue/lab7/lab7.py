# -*- coding: utf-8 -*-
# ---
# jupyter:
#   jupytext:
#     cell_metadata_filter: all
#     formats: ipynb,py:percent
#     notebook_metadata_filter: all,-language_info,-toc,-latex_envs
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.4.1
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# %% [markdown]
# # Laboratory 7: Solving partial differential equations using an explicit, finite difference method.
#
# Lin Yang & Susan Allen & Carmen Guo

# %% [markdown]
# ## List of Problems ##
# - [Problem 1](#Problem-One): Numerical solution on a staggered grid.
# - [Problem 2](#Problem-Two): Stability of the difference scheme
# - [Problem 3](#Problem-Three): Dispersion relation for grid 2
# - [Problem 4](#Problem-Four): Choosing most accurate grid
# - [Problem 5](#Problem-Five): Numerical solution for no y variation
# - [Problem 6](#Problem-Six): Stability on the 2-dimensional grids
# - [Problem 7](#Problem-Seven): Finite difference form of equations
# - [Problem 8](#Problem-Eight): Dispersion relation for D-grid
# - [Problem 9](#Problem-Nine): Accuracy of the approximation on various grids


# %% [markdown]
# ### Problem One
# [lab7:prob:staggered]:(#Problem-One) 
# > Modify *rain.py* to solve this problem (Simple
# equations on a staggered grid). Submit your code and a final plot for
# one case.
#
#
# %% [markdown]
# ### Problem Two 
# [lab7:prob:stability]:(#Problem-Two)
# > a) Find the CFL condition (in seconds) for $dt$
# for the Python example in Problem One.
# <!--- [lab7:prob:staggered]---> Test your
# value. 
#
# > b) Find the CFL condition (in seconds) for $dt$ for the Python
# example in *rain.py*, ie., for the non-staggered grid. Test your value.
#


