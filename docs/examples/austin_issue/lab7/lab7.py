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
#       jupytext_version: 1.3.3
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
# ## Objectives ##
#
# ### Sections 4 through 7
#
# When you have completed these sections you will be able to:
#
# -   find the dispersion relation for a set of differential equations
#     (the “real” dispersion relation).
#
# -   find the dispersion relation for a set of difference equations (the
#     numerical dispersion relation).
#
# -   describe a leap-frog scheme
#
# -   construct a predictor-corrector method
#
# -   use the given differential equations to determine unspecified
#     boundary conditions as necessary
#
# -   describe a staggered grid
#
# -   state one reason why staggered grids are used
#
# -   explain the physical principle behind the CFL condition
#
# -   find the CFL condition for a linear, explicit, numerical scheme
#
# -   state one criteria that should be considered when choosing a grid
#

# %% [markdown]
# ## Readings
#
# These are the suggested readings for this lab. For more details about
# the books and papers, click on the reference link.
#
# -   **Rotating Navier Stokes Equations**
#
#     -    [Pond and Pickard, 1983](#Ref:PondPickard), Chapters 3,4 and 6
#
# -   **Shallow Water Equations**
#
#     -    [Gill, 1982](#Ref:Gill), Section 5.6 and 7.2 (not 7.2.1 etc)
#
# -   **Poincaré Waves**
#
#     -    [Gill, 1982](#Ref:Gill), Section 7.3 to just after equation (7.3.8), section 8.2
#         and 8.3
#
# -   **Introduction to Numerical Solution of PDE’s**
#
#     -    [Press et al, 1992](#Ref:Pressetal), Section 17.0
#
# -   **Waves**
#
#     -    [Cushman-Roision, 1994](#Ref:Cushman-Roisin), Appendix A

# %%
import context
from IPython.display import Image
import IPython.display as display
# import plotting package and numerical python package for use in examples later
import matplotlib.pyplot as plt
# make the plots happen inline
# %matplotlib inline  
# import the numpy array handling library
import numpy as np
# import the quiz script
from numlabs.lab7 import quiz7 as quiz
# import the pde solver for a simple 1-d tank of water with a drop of rain
from numlabs.lab7 import rain
# import the dispersion code plotter
from numlabs.lab7 import accuracy2d
# import the 2-dimensional drop solver
from numlabs.lab7 import interactive1
# import the 2-dimensional dispersion relation plotter
from numlabs.lab7 import dispersion_2d

# %% [markdown]
# ## Physical Example, Poincaré Waves
#
# One of the obvious examples of a physical phenomena governed by a
# partial differential equation is waves. Consider a shallow layer of
# water and the waves on the surface of that layer. If the depth of the
# water is much smaller than the wavelength of the waves, the velocity of
# the water will be the same throughout the depth. So then we can describe
# the state of the water by three variables: $u(x,y,t)$, the east-west
# velocity of the water, $v(x,y,t)$, the north-south velocity of the water
# and $h(x,y,t)$, the height the surface of the water is deflected. As
# specified, each of these variables are functions of the horizontal
# position, $(x,y)$ and time $t$ but, under the assumption of shallow
# water, not a function of $z$.
#
# In oceanographic and atmospheric problems, the effect of the earth’s
# rotation is often important. We will first introduce the governing
# equations including the Coriolis force ([Full Equations](#Full-Equations)). However,
# most of the numerical concepts can be considered without all the
# complications in these equations. We will also consider two simplier
# sets; one where we assume there is no variation of the variables in the
# y-direction ([No variation in y](#No-variation-in-y)) and one where, in addition, we assume
# that the Coriolis force is negligible ([Simple Equations](#Simple-Equations)).
#
# The solution of the equations including the Coriolis force are Poincaré
# waves whereas without the Coriolis force, the resulting waves are called
# shallow water gravity waves.
#
# The remainder of this section will present the equations and discuss the
# dispersion relation for the two simplier sets of equations. If your wave
# theory is rusty, consider reading Appendix A in [Cushman-Roisin, 1994](#Ref:Cushman-Roisin).

# %% [markdown]
# ### Introduce Full Equations 
# [full-equations]:(#Introduce-Full-Equations)
#
# The linear shallow water equations on an f-plane over a flat bottom are
# <div id='lab7:eq:swea'>
# (Full Equations, Eqn 1)
# $$\frac{\partial u}{\partial t} - fv = -g\frac{\partial h}{\partial x}$$
# </div><div id='lab7:eq:sweb'>
# (Full Equations, Eqn 2)
# $$\frac{\partial v}{\partial t} + fu = -g\frac{\partial h}{\partial y} $$
# </div><div id='lab7:eq:swec'>
# (Full Equations, Eqn 3)
# $$\frac{\partial h}{\partial t} + H\frac{\partial u}{\partial x} + H\frac{\partial v}{\partial y} = 0$$ 
# </div>
# where
#
# -   $\vec{u} = (u,v)$ is the horizontal velocity,
#
# -   $f$ is the Coriolis frequency,
#
# -   $g$ is the acceleration due to gravity,
#
# -   $h$ is the surface elevation, and
#
# -   $H$ is the undisturbed depth of the fluid.
#
# We will return to these equations in section [Full Equations](#Full-Equations).

# %% [markdown]
# ### No variation in y
# [no-variation-in-y.unnumbered]: (#No-variation-in-y)
#
# To simplify the problem assume there is no variation in y. This
# simplification gives:
# <div id='lab7:sec:firsteq'>
# (No variation in y, first eqn)
# $$\frac{\partial u}{\partial t} - fv = -g\frac{\partial h}{\partial x}$$ 
# </div><div id='lab7:sec:secondeq'>
# (No variation in y, second eqn)
# $$\frac{\partial v}{\partial t} + fu = 0$$
# </div><div id='lab7:sec:thirdeq'>
# (No variation in y, third eqn)
# $$\frac{\partial h}{\partial t} + H\frac{\partial u}{\partial x} = 0$$
# </div>

# %% [markdown]
# ### Introduce Simple Equations
# [simple-equations]:(#Simple-Equations)
#
# If we consider waves in the absence of the earth’s rotation, $f=0$,
# which implies $v=0$ and we get
# <div id='lab7:sec:simple_eq1'>
# $$\frac{\partial u}{\partial t} = -g\frac{\partial h}{\partial x}$$
# </div><div id='lab7:sec:simple_eq2'>
# $$\frac{\partial h}{\partial t} + H\frac{\partial u}{\partial x} = 0$$
# </div>
#
# These simplified equations give shallow water gravity waves. For
# example, a solution is a simple sinusoidal wave:
# <div id='lab7:sec:hwave'>
# (wave solution- h)
# $$h = h_{0}\cos{(kx - \omega t)}$$
# </div><div id='lab7:sec:uwave'>
# (wave solution- u)
# $$u = \frac{h_{0}\omega}{kH}\cos{(kx - \omega t)}$$ 
# </div>
# where $h_{0}$ is the amplitude, $k$ is the
# wavenumber and $\omega$ is the frequency (See [Cushman-Roisin, 1994](#Ref:Cushman-Roisin) for a nice
# review of waves in Appendix A).
#
# Substitution of ([wave solution- h](#lab7:sec:hwave)) and ([wave solution- u](#lab7:sec:uwave)) back into
# the differential equations gives a relation between $\omega$ and k.
# Confirm that 
# <div id='lab7:eq:disp'>
# (Analytic Dispersion Relation)
# $$\omega^2 = gHk^2,$$
# </div>
# which is the dispersion relation for these waves.

# %% [markdown]
# ### No variation in y
# [no-variation-in-y-1.unnumbered]:(#No-variation-in-y)
#
# Now consider $f\not = 0$.
#
# By assuming $$h= h_{0}e^{i(kx - \omega t)}$$
# $$u= u_{0}e^{i(kx - \omega t)}$$ $$v= v_{0}e^{i(kx - \omega t)}$$
#
# and substituting into the differential equations, eg, for [(No variation in y, first eqn)](#lab7:sec:firsteq)
# $$-iwu_{0}e^{i(kx - \omega t)} - fv_{0}e^{i(kx - \omega t)} + ikgh_{0}e^{i(kx - \omega t)} = 0$$
# and cancelling the exponential terms gives 3 homogeneous equations for
# $u_{0}$, $v_{0}$ and $h_{0}$. If the determinant of the matrix derived
# from these three equations is non-zero, the only solution is
# $u_{0} = v_{0} = h_{0} = 0$, NO WAVE! Therefore the determinant must be
# zero.

# %% [markdown]
# ### Quiz: Find the Dispersion Relation
#
# What is the dispersion relation for 1-dimensional Poincare waves?
#
# A) $\omega^2 = f^2 + gH (k^2 + \ell^2)$
#
# B) $\omega^2 = gH k^2$
#
# C) $\omega^2 = f^2 + gH k^2$
#
# D) $\omega^2 = -f^2 + gH k^2$
#
# In the following, replace 'x' by 'A', 'B', 'C' or 'D' and run the cell.

# %%
print (quiz.dispersion_quiz(answer = 'A'))

# %% [markdown]
# ## Numerical Solution
#
# ### Simple Equations
# [simple-equations]:(#Simple-Equations)
#
# Consider first the simple equations with $f = 0$. In order to solve
# these equations numerically, we need to discretize in 2 dimensions, one
# in space and one in time. Consider first the most obvious choice, shown
# in Figure [Unstaggered Grid](#lab7:fig:nonstagger).

# %%
Image(filename='images/nonstagger.png',width='40%') 

# %% [markdown]
# <div id='lab7:fig:nonstagger'>
# <b>Figure Unstaggered Grid.</b>
# </div>
#
# We will use centred difference schemes in both $x$ and $t$. The
# equations become:
# <div id='lab7:eq:nonstaggerGrid1'>
# (Non-staggered, Eqn One)
# $$\frac {u(t+dt, x)-u(t-dt, x)}{2 dt} + g \frac {h(t, x+dx) - h(t, x-dx)}{2dx} = 0$$
# </div><div id='lab7:eq:nonstaggerGrid2'>
# (Non-staggered, Eqn Two)
# $$\frac {h(t+dt, x)-h(t-dt, x)}{2 dt} + H \frac {u(t, x+dx) - u(t, x-dx)}{2dx} = 0$$
# </div>
# We can rearrange these equations to
# give $u(t+dt, x)$ and $h(t+dt, x)$. For a small number of points, the
# resulting problem is simple enough to solve in a notebook.
#
# For a specific example, consider a dish, 40 cm long, of water 1 cm deep.
# Although the numerical code presented later allows you to vary the
# number of grid points, in the discussion here we will use only 5 spatial
# points, a distance of 10 cm apart. The lack of spatial resolution means
# the wave will have a triangular shape. At $t=0$ a large drop of water
# lands in the centre of the dish. So at $t=0$, all points have zero
# velocity and zero elevation except at $x=3dx$, where we have
# $$h(0, 3dx) = h_{0} = 0.01 cm$$
#
# A centred difference scheme in time, such as defined by equations
# ([Non-staggered, Eqn One](#lab7:eq:nonstaggerGrid1)) and ([Non-staggered, Eqn Two](#lab7:eq:nonstaggerGrid2)), is
# usually refered to as a *Leap frog scheme*. The new values, $h(t+dt)$
# and $u(t+dt)$ are equal to values two time steps back $h(t-dt)$ and
# $u(t-dt)$ plus a correction based on values calculated one time step
# back. Hence the time scheme “leap-frogs” ahead. More on the consequences
# of this process can be found in section [Computational Mode](#Computational-Mode).
#
# As a leap-frog scheme requires two previous time steps, the given
# conditions at $t=0$ are not sufficient to solve
# ([Non-staggered, Eqn One](#lab7:eq:nonstaggerGrid1)) and ([Non-staggered, Eqn Two](#lab7:eq:nonstaggerGrid2)). We
# need the solutions at two time steps in order to step forward.

# %% [markdown]
# ### Predictor-Corrector to Start
# [lab7:sec:pred-cor]:(#Predictor-Corrector-to-Start)
#
# In section 4.2.2 of Lab 2, predictor-corrector methods were introduced.
# We will use a predictor-corrector based on the forward Euler scheme, to
# find the solution at the first time step, $t=dt$. Then the second order
# scheme ([Non-staggered, Eqn One](#lab7:eq:nonstaggerGrid1)), ([Non-staggered, Eqn Two](#lab7:eq:nonstaggerGrid2)) can be used.
#
# Using the forward Euler Scheme, the equations become
# <div id='lab7:eq:newnonstaggerGrid1'>
# $$\frac {u(t+dt, x)-u(t, x)}{dt} + g \frac {h(t, x+dx) - h(t, x-dx)}{2dx} = 0$$
# </div><div id='lab7:eq:newnonstaggerGrid2'>
# $$\frac {h(t+dt, x)-h(t, x)}{dt} + H \frac {u(t, x+dx) - u(t, x-dx)}{2dx} = 0$$
# </div>
#
# 1.  Use this scheme to predict $u$ and $h$ at $t=dt$.
#
# 2.  Average the solution at $t=0$ and that predicted for $t=dt$, to
#     estimate the solution at $t=\frac{1}{2}dt$. You should confirm that
#     this procedure gives: $$u(\frac{dt}{2}) = \left\{ \begin{array}{ll}
#     0 & { x = 3dx}\\
#     \left({-gh_{0}dt}\right)/\left({4dx}\right) & { x = 2dx}\\
#     \left({gh_{0}dt}\right)/\left({4dx}\right) & { x = 4dx}
#     \end{array}
#     \right.$$
#
#     $$h(\frac{dt}{2}) = \left\{ \begin{array}{ll}
#     h_{0} & { x = 3dx}\\
#     0 & { x \not= 3dx}
#     \end{array}
#     \right.$$
#
# 3.  The corrector step uses the centred difference scheme in time (the
#     leap-frog scheme) with a time step of ${dt}/{2}$ rather than dt. You
#     should confirm that this procedure gives:
#     $$u(dt) = \left\{ \begin{array}{ll}
#     0 & { x = 3dx}\\
#     \left({-gh_{0}dt}\right)/\left({2dx}\right) & { x = 2dx}\\
#     \left({gh_{0}dt}\right)/\left({2dx}\right) & { x = 4dx}
#     \end{array}
#     \right.$$
#
#     $$h(dt) = \left\{ \begin{array}{ll}
#     0 & { x = 2dx, 4dx}\\
#     h_{0} - \left({gHdt^2 h_{0}}\right)/\left({4dx^2}\right) & { x = 3dx}
#     \end{array}
#     \right.$$
#
# Note that the values at $x=dx$ and $x=5dx$ have not been specified.
# These are boundary points and to determine these values we must consider
# the boundary conditions.

# %% [markdown]
# ### Boundary Conditions
#
# If we are considering a dish of water, the boundary conditions at
# $x=dx, 5dx$ are those of a wall. There must be no flow through the wall.
# $$u(dx) = 0$$ $$u(5dx) = 0$$ But these two conditions are not
# sufficient; we also need $h$ at the walls. If $u=0$ at the wall for all
# time then $\partial u/\partial t=0$ at the wall, so $\partial h/\partial x=0$ at the wall. Using a
# one-sided difference scheme this gives
# $$\frac {h(2dx) - h(dx)}{dx} = 0$$ or$$h(dx) = h(2dx)$$
# and$$\frac {h(4dx) - h(5dx)}{dx} = 0$$ or$$h(5dx) = h(4dx)$$ which gives
# the required boundary conditions on $h$ at the wall.

# %% [markdown]
# ### Simple Equations on a Non-staggered Grid
#
# 1.  Given the above equations and boundary conditions, we can find the
#     values of $u$ and $h$ at all 5 points when $t = 0$ and $t = dt$.
#
# 2.  From ([Non-staggered, Eqn One](#lab7:eq:nonstaggerGrid1)) and ([Non-staggered, Eqn Two](#lab7:eq:nonstaggerGrid2)), we can find the values of $u$ and
#     $h$ for $t = 2dt$ using $u(0, x)$, $u(dt, x)$, $h(0, x)$, and
#     $h(dt, x)$.
#
# 3.  Then we can find the values of $u$ and $h$ at $t = 3dt$ using
#     $u(dt, x)$, $u(2dt, x)$, $h(dt, x)$, and $h(2dt, x)$.
#
# We can use this approach recursively to determine the values of $u$ and
# $h$ at any time $t = n * dt$. The python code that solves this problem
# is provided in the file rain.py. It takes two arguments, the first is the
# number of time steps and the second is the number of horizontal grid
# points. 
#
# The output is two coloured graphs.  The color represents time with black
# the earliest times and red later times.  The upper plot shows the water
# velocity (u) and the lower plot shows the water surface.  To start with
# the velocity is 0 (black line at zero across the whole domain) and the
# water surface is up at the mid point and zero at all other points (black
# line up at midpoint and zero elsewhere)
#
# Not much happens in 6 time-steps.  Do try longer and more grid points.

# %%
rain.rain([6, 5])

# %% [markdown]
# If you want to change something in the script (say the colormap I've chosen, viridis, doesn't work for you), you can edit rain.py in an editor or spyder.  To make it take effect here though, you have to reload rain.  See next cell for how to.  You will also need to do this if you do problem one or other tests changing rain.py but running in a notebook.

# %%
import importlib
importlib.reload(rain)

# %% [markdown]
# ### Staggered Grids
# [lab7:sec:staggered]:(#Staggered-Grids)
#
# After running the program with different numbers of spatial points, you
# will discover that the values of $u$ are always zero at the odd numbered
# points, and that the values of $h$ are always zero at the even numbered
# points. In other words, the values of $u$ and $h$ are zero in every
# other column starting from $u(t, dx)$ and $h(t, 2dx)$, respectively.
#
# A look at ([Non-staggered, Eqn One](#lab7:eq:nonstaggerGrid1)) and ([Non-staggered, Eqn Two](#lab7:eq:nonstaggerGrid2)) can help us understand why this is the
# case:
#
# $u(t + dt, x)$ is dependent on $h(t , x + dx)$ and $h(t , x - dx)$,
#
# but $h(t , x + dx)$ is in turn dependent on $u$ at $x + 2dx$ and at
# $x$,
#
# and $h(t , x - dx)$ is in turn dependent on $u$ at $x - 2dx$ and at
# $x$.
#
# Thus, if we just look at $u$ at a particular $x$, $u(x)$ will depend on
# $u(x + 2dx)$, $u(x - 2dx)$, $u(x + 4dx)$, $u(x - 4dx)$, $u(x + 6dx)$,
# $u(x - 6dx),$ ... but not on $u(x + dx)$ or $u(x - dx)$. Therefore, the
# problem is actually decoupled and consists of two independent problems:
# one problem for all the $u$’s at odd numbered points and all the $h$’s
# at even numbered points, and the other problem for all the $u$’s at even
# numbered points and all the $h$’s at odd numbered points, as shown in
# Figure [Unstaggered Dependency](#lab7:fig:dependency).

# %%
Image(filename='images/dependency.png',width='50%') 

# %% [markdown]
# <div id='lab7:fig:dependency'>
# <b>Figure Unstaggered Dependency</b>
# </div>
#
# In either problem, only the variable that is relevant to that problem
# will be considered at each point. So for one problem, if at point $x$ we
# consider the $u$ variable, at $x + dx$ and $x -dx$ we consider $h$. In
# the other problem, at the same point $x$, we consider the variable $h$.
#
# Now we can see why every second $u$ point and $h$ point are zero for
# *rain*. We start with all of
# $u(dx), h(2dx), u(3dx), h(4dx), u(5dx) = 0$, which means they remain at
# zero.
#
# Since the original problem can be decoupled, we can solve for $u$ and
# $h$ on each decoupled grid separately. But why solve two problems?
# Instead, we solve for $u$ and $h$ on a single staggered grid; whereas
# before we solved for $u$ and $h$ on the complete, non-staggered grid.
# Figure [Decoupling](#lab7:fig:decoupling) shows the decoupling of the grids.

# %% scrolled=true
Image(filename='images/decoupling.png',width='50%') 

# %% [markdown]
# <div id='lab7:fig:decoupling'>
# <b>Figure Decoupling</b>: The two staggered grids and the unstaggered grid. Note that the
# unstaggered grid has two variables at each grid/time point whereas the
# staggered grids only have one.
# </div>

# %% [markdown]
# Now consider the solution of the same problem on a staggered grid. The
# set-up of the problem is slightly different this time; we are
# considering 4 spatial points in our discussion instead of 5, shown in
# Figure [Staggered Grid](#lab7:fig:stagger). We will also be using $h_{i}$ and $u_{i}$ to
# denote the spatial points instead of $x = dx * i$.

# %%
Image(filename='images/stagger.png',width='50%') 

# %% [markdown]
# <div id='lab7:fig:stagger'>
# <b>Figure Staggered Grid</b>: The staggered grid for the drop in the pond problem.
# </div>
#
# The original equations, boundary and initial conditions are changed to
# reflect the staggered case. The equations are changed to the following:
# <div id='lab7:eq:staggerGrid1'>
# (Staggered, Eqn 1)
# $$\frac {u_{i}(t+dt)-u_{i}(t-dt)}{2 dt} + g \frac {h_{i + 1}(t) - h_{i}(t)}{dx} = 0$$
# </div><div id='lab7:eq:staggerGrid2'>
# (Staggered, Eqn 2)
# $$\frac {h_{i}(t+dt)-h_{i}(t-dt)}{2 dt} + H \frac {u_{i}(t) - u_{i - 1}(t)}{dx} = 0$$
# </div>
#
# The initial conditions are: At $t = 0$ and $t = dt$, all points have
# zero elevation except at $h_{3}$, where $$h_{3}(0) = h_{0}$$
# $$h_{3}(dt) = h_{3}(0) - h_{0} Hg \frac{dt^2}{dx^2}$$ At $t = 0$ and
# $t = dt$, all points have zero velocity except at $u_{2}$ and $u_{3}$,
# where $$u_{2}(dt) = - h_{0} g \frac{dt}{dx}$$
# $$u_{3}(dt) = - u_{2}(dt)$$ This time we assume there is a wall at
# $u_{1}$ and $u_{4}$, so we will ignore the value of $h_{1}$. The
# boundary conditions are: $$u_{1}(t) = 0$$ $$u_{4}(t) = 0$$
#
# ### Problem One
# [lab7:prob:staggered]:(#Problem-One) 
# > Modify *rain.py* to solve this problem (Simple
# equations on a staggered grid). Submit your code and a final plot for
# one case.
#
# %% [markdown]
# <div id='lab7:fig:sepmag'>
# <b>Figure Separate Roots</b>: Magnitude of the four roots of $\lambda$ as a function of $q dt$ (not $\omega dt$).
# </div>
#
# Now for stability
# $\lambda$ must have a magnitude less than or equal to one. From
# Figure [Separate Roots](#lab7:fig:sepmag), it is easy to see that this is the same as
# requiring that $|q dt|$ be less than 1.0.
#
# Substituting for $q$
# $$1 > q^2 dt^2 =  \frac {4gH}{d^2} \sin^2(kd/2) dt^2$$ for all $k$.

# %% [markdown]
# The maximum wavenumber that can be resolved by a grid of size $d$ is
# $k = \pi/d$. At this wavenumber, the sine takes its maximum value of 1.
# So the time step 
# <div id='lab7:eq:dt'>
# $$dt^2 < \frac { d^2}{4 g H}$$
# </div>
#
# For this case ($f = 0$) the ratio of the space step to the time step
# must be greater than the wave speed $\sqrt
# {gH}$, or $$d / dt > 2  \sqrt{gH}.$$ This stability condition is known
# as **the CFL condition** (named after Courant, Friedrich and Levy).
#
# On a historical note, the first attempts at weather prediction were
# organized by Richardson using a room full of human calculators. Each
# person was responsible for one grid point and passed their values to
# neighbouring grid points. The exercise failed dismally, and until the
# theory of CFL, the exact reason was unknown. The equations Richardson
# used included fast sound waves, so the CFL condition was
# $$d/dt > 2 \times 300 {\rm m/s}.$$ Richardson’s spatial step, $d$, was
# too small compared to $dt$ and the problem was unstable.
#
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


