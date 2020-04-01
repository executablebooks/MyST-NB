# -*- coding: utf-8 -*-
# %% [markdown]
# # Tex parsing problem?
#
# ## Introduction
#
# <div id="Figure-Model-Ocean">
# <strong>Figure Model Ocean</strong> The rectangular ocean with flat bottom, ignoring curvature
# effects.
# </div>
#
# Let's see an unescaped apostrophe.
#
# More information on what is a $\beta$-plane and on the neglect of
# curvature terms in the $\beta$-plane approximation is given in the
# appendix.
#
# If we assume that the ocean is homogeneous (it has constant density
# throughout), then the equations governing the fluid motion on the
# $\beta$-plane are: 
#
# <div id="eq:xmom">(X-Momentum Eqn)</div>

# %% [markdown]
# $$
# \frac{\partial u}{\partial t} + u \frac {\partial u}{\partial x} + v \frac {\partial u}{\partial y} + w \frac{\partial u}{\partial z} - fv = - \, \frac{1}{\rho} \, \frac {\partial p}{\partial x}
# + A_v \, \frac{\partial^2 u}{\partial z^2} + A_h \, \nabla^2 u
# $$(eq:one)

# %% [markdown]
# <div id="eq:ymom">(Y-Momentum Eqn)</div>
#
# $$
# \frac{\partial v}{\partial t} + u \frac{\partial v}{\partial x} + v \frac{\partial v}{\partial y} + w \frac{\partial v}{\partial z} + fu = - \, \frac{1}{\rho} \, \frac{\partial p}{\partial y}
# + A_v \, \frac{\partial^2 v}{\partial z^2} + A_h \, \nabla^2 v
# $$

# %% [markdown]
# <div id="eq:hydrostatic">(Hydrostatic Eqn)</div>
#
# \begin{equation}
# \frac{\partial p}{\partial z} = - \rho g
# \end{equation}

# %% [markdown]
# <div id="eq:continuity">(Continuity Eqn)</div>
#
# $$
# \frac {\partial u}{\partial x} + \frac{\partial v}{\partial y} = - \, \frac{\partial w}{\partial z}
# $$

# %% [markdown]
# where
#
# -   ([X-Momentum Eqn](#eq:xmom)) and ([Y-Momentum Eqn](#eq:ymom)) are the lateral momentum equations,
#
# -   ([Hydrostatic Eqn](#eq:hydrostatic)) is the hydrostatic balance (and replaces the vertical momentum
#     equation), and
#
# -   ([Continuity Eqn](#eq:continuity)) is the continuity (or incompressibility or conservation of volume) condition.

# %% [markdown]
# The variables and parameters appearing above are:
#
# -   $(u,v,w)$, the fluid velocity components;
#
# -   $f(y)$, the Coriolis parameter (assumed to be a linear function of
#     $y$);
#
# -   $\rho$, the density (assumed constant for a homogeneous fluid);
#
# -   $A_v$ and $A_h$, the vertical and horizontal coefficients of
#     viscosity, respectively (constants);
#
# -   $g$, the gravitational acceleration (constant).
#
# Equations ([X-Momentum Eqn](#eq:xmom)), ([Y-Momentum Eqn](#eq:ymom)), ([Hydrostatic Eqn](#eq:hydrostatic)) and ([Continuity Eqn](#eq:continuity)) form a non-linear system of PDE’s, for which there are many
# numerical methods available. However, due to the complexity of the
# equations, the methods themselves are *very complex*, and
# consume a large amount of CPU time. It is therefore advantageous for us
# to reduce the equations to a simpler form, for which common, and more
# efficient numerical solution techniques can be used.
#
# ## Section new
#

# %%
