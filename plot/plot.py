# This file is part of CELADRO, Copyright (C) 2016-17, Romain Mueller
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

#
# Plotting routines
#

import numpy as np
import matplotlib.pyplot as plt
from math import sqrt, pi, copysign, atan2
from matplotlib.colors import LinearSegmentedColormap
from scipy import ndimage
from itertools import product

def get_velocity_field(phases, Qxx, Qxy):
    """Compute the collective velocity field from a collection of phase-fields
     and their velocities"""
    v = []
    for k in range(len(phases[0])):
        v = v + [ [ sum([ vel[n][0]*phases[n][k] for n in range(len(phases)) ]),
                    sum([ vel[n][1]*phases[n][k] for n in range(len(phases)) ]) ] ]
    return np.array(v)

def get_Qtensor(phases, Qxx, Qxy, size):
    """Compute the coarse grained tissue nematic field from individual cells"""
    # glue all Q-tensors together
    QQxx = np.zeros(phases[0].shape)
    QQxy = np.zeros(phases[0].shape)
    for n in range(len(phases)):
        QQxx += Qxx[n]*phases[n]
        QQxy += Qxy[n]*phases[n]

    # coarse grain
    QQxx = ndimage.filters.uniform_filter(QQxx, size=size, mode='wrap')
    QQxy = ndimage.filters.uniform_filter(QQxy, size=size, mode='wrap')

    return (QQxx, QQxy)


def get_director(phases, Qxx, Qxy, size):
    # get coarse grained Q-tensor
    (QQxx, QQxy) = get_Qtensor(phases, Qxx, Qxy, size)

    # obtain S, nx, and ny
    S = np.vectorize(sqrt)(QQxy**2 + QQxx**2)
    nx = np.vectorize(sqrt)((1 + QQxx/S)/2)
    ny = np.sign(QQxy)*np.vectorize(sqrt)((1 - QQxx/S)/2)

    return S, nx, ny

def get_defects(Q00, Q01):
    """Returns list of defects with format [ ((xpos,ypos), charge) ]"""

    #def wang(a, b):
    #    """Infamous chinese function"""
    #    ang = atan2(abs(a[0]*b[1]-a[1]*b[0]), a[0]*b[0]+a[1]*b[1])
    #    if ang>pi/2.:
    #        b = [ -i for i in b ]
    #    m = abs(a[0]*b[1]-a[1]*b[0])
    #    return copysign(m, 1.)*atan2(m, a[0]*b[0]+a[1]*b[1])

    #(LX, LY) = Q00.shape
    #w = np.zeros((LX, LY))

    #for i in range(LX):
    #    for j in range(LY):
    #        ax1 = [ Q00[(i+1)%LX,j],   Q01[(i+1)%LX,j]   ]
    #        ax2 = [ Q00[(i-1)%LX,j],   Q01[(i-1)%LX,j]   ]
    #        ax3 = [ Q00[i,(j-1)%LY],   Q01[i,(j-1)%LY]   ]
    #        ax4 = [ Q00[i,(j+1)%LY],   Q01[i,(j+1)%LY]   ]
    #        ax5 = [ Q00[(i+1)%LX,(j-1)%LY], Q01[(i+1)%LX,(j-1)%LY] ]
    #        ax6 = [ Q00[(i-1)%LX,(j-1)%LY], Q01[(i-1)%LX,(j-1)%LY] ]
    #        ax7 = [ Q00[(i+1)%LX,(j+1)%LY], Q01[(i+1)%LX,(j+1)%LY] ]
    #        ax8 = [ Q00[(i-1)%LX,(j+1)%LY], Q01[(i-1)%LX,(j+1)%LY] ]

    #        w[i,j]  = wang(ax1, ax5)
    #        w[i,j] += wang(ax5, ax3);
    #        w[i,j] += wang(ax3, ax6);
    #        w[i,j] += wang(ax6, ax2);
    #        w[i,j] += wang(ax2, ax8);
    #        w[i,j] += wang(ax8, ax4);
    #        w[i,j] += wang(ax4, ax7);
    #        w[i,j] += wang(ax7, ax1);
    #        w[i,j] /= 2.*pi
    #return w

    #
    # derivatives
    #
    dxQ00 = ndimage.convolve1d(Q00, [-.5, 0, .5], axis=0, mode='wrap')
    dyQ00 = ndimage.convolve1d(Q00, [-.5, 0, .5], axis=1, mode='wrap')
    dxQ01 = ndimage.convolve1d(Q01, [-.5, 0, .5], axis=0, mode='wrap')
    dyQ01 = ndimage.convolve1d(Q01, [-.5, 0, .5], axis=1, mode='wrap')

    S = np.vectorize(sqrt)(Q00**2 + Q01**2)

    # charge array
    #C = (dxQ00*dyQ01 - dyQ00*dxQ01)/S*8./9./pi
    C = (dxQ00*dyQ01 - dxQ01*dyQ00 - dxQ01*dyQ01 + dxQ00*dyQ01)/S/4./pi
    C = ndimage.filters.uniform_filter(C, size=3, mode='wrap')

    chop = lambda x: 0 if abs(x)<1e-6 else x
    C = np.vectorize(chop)(C)


    return C

def phasefields(frame, engine=plt):
    """Plot all phase fields"""
    for p in frame.phi:
        engine.contour(np.arange(0, frame.parameters['Size'][0]),
                       np.arange(0, frame.parameters['Size'][1]),
                       p.T,
                       #levels = [1e-10, 1e-5, .5])
                       levels = [.5],
                       #color='mediumblue'
                       colors='k')

def interfaces(frame, engine=plt):
    """Plot the interfaces density"""
    totphi = np.zeros(frame.parameters['Size'])
    for i in range(len(frame.phi)):
        totphi += frame.phi[i]*frame.parameters['walls']
        for j in range(i+1, len(frame.phi)):
            totphi += frame.phi[i]*frame.phi[j]

    cmap = LinearSegmentedColormap.from_list('mycmap', ['grey', 'white'])
    engine.imshow(totphi.T, interpolation='lanczos', cmap=cmap, origin='lower')

def solidarea(frame, engine=plt):
    """Plot all phase fields with solid colours corresponding to individual areas"""
    for i in range(len(frame.phi)):
        p = frame.phi[i]
        engine.contourf(np.arange(0, frame.parameters['Size'][0]),
                        np.arange(0, frame.parameters['Size'][1]),
                        frame.phi[i],
                        #levels = [1e-10, 1e-5, .5])
                        levels = [.5, 10.],
                        #color='mediumblue'
                        colors=str(frame.area[i]/(np.pi*frame.parameters['R']**2)))

def com(frame, engine=plt):
    """Plot the center-of-mass of each cell"""
    for c in frame.com:
        engine.plot(c[0], c[1], 'ro')

def shape(frame, engine=plt):
    """Print shape tensor of each cell"""
    for i in range(frame.nphases):
        Q00 = frame.S00[i]
        Q01 = frame.S01[i]
        S = sqrt(Q00**2 + Q01**2)
        nx = sqrt((1 + Q00/S)/2)
        ny = copysign(1, Q01)*sqrt((1 - Q00/S)/2)
        c = frame.com[i]
        a = S
        engine.arrow(c[0], c[1],  a*nx,  a*ny, color='k')
        engine.arrow(c[0], c[1], -a*nx, -a*ny, color='k')

def director(frame, Q00, Q01, size=15, avg=1, scale=False, engine=plt):
    """Plot director field associated with nematic tensor with components Q00, Q01"""
    S, nx, ny = get_director(frame.phi, Q00, Q01, size)
    S  = ndimage.generic_filter(S , np.mean, size=avg)
    nx = ndimage.generic_filter(nx, np.mean, size=avg)
    ny = ndimage.generic_filter(ny, np.mean, size=avg)
    x = []
    y = []
    for i, j in product(np.arange(frame.parameters['Size'][0], step=avg),
                        np.arange(frame.parameters['Size'][1], step=avg)):
        f = avg*(S[i,j] if scale else 1.)
        x.append(i + .5 - f*nx[i,j]/2.)
        x.append(i + .5 + f*nx[i,j]/2.)
        x.append(None)
        y.append(j + .5 - f*ny[i,j]/2.)
        y.append(j + .5 + f*ny[i,j]/2.)
        y.append(None)
    engine.plot(x, y, color='k', linestyle='-', linewidth=1)

def velc(frame, engine=plt):
    """Print contractile part of the velocity"""
    for i in range(frame.nphases):
        p = frame.phi[i].reshape(frame.parameters['Size'])
        c = frame.com[i]
        v = frame.velc[i]
        # correction factor
        a = frame.parameters['ninfo']*frame.parameters['nsubsteps']
        engine.arrow(c[0], c[1], a*v[0], a*v[1], color='g')


def velp(frame, engine=plt):
    """Print inactive part of the velocity"""
    for i in range(frame.nphases):
        p = frame.phi[i].reshape(frame.parameters['Size'])
        c = frame.com[i]
        v = frame.velp[i]
        # correction factor
        a = frame.parameters['ninfo']*frame.parameters['nsubsteps']
        engine.arrow(c[0], c[1], a*v[0], a*v[1], color='b')

def nematic(frame, engine=plt):
    """Print director of each cell"""
    for i in range(frame.nphases):
        Q00 = frame.Q00[i]
        Q01 = frame.Q01[i]
        S = sqrt(Q00**2 + Q01**2)
        nx = sqrt((1 + Q00/S)/2)
        ny = copysign(1, Q01)*sqrt((1 - Q00/S)/2)
        c = frame.com[i]
        a = frame.parameters['R'][i]/2.5*S
        #print S
        engine.arrow(c[0], c[1],  a*nx,  a*ny, color='k')
        engine.arrow(c[0], c[1], -a*nx, -a*ny, color='k')

def velf(frame, engine=plt):
    """Print active part of the velocity"""
    for i in range(frame.nphases):
        p = frame.phi[i].reshape(frame.parameters['Size'])
        c = frame.com[i]
        v = frame.velf[i]
        # correction factor
        a = frame.parameters['ninfo']*frame.parameters['nsubsteps']
        engine.arrow(c[0], c[1], a*v[0], a*v[1], color='brown')

def vela(frame, engine=plt):
    """Print active part of the velocity"""
    for i in range(frame.nphases):
        p = frame.phi[i].reshape(frame.parameters['Size'])
        c = frame.com[i]
        v = frame.pol[i]
        a = frame.parameters['alpha']/frame.parameters['xi']*frame.parameters['ninfo']*frame.parameters['nsubsteps']
        engine.arrow(c[0], c[1], a*v[0], a*v[1], color='r')

def vel(frame, engine=plt):
    """Print active part of the velocity"""
    for i in range(frame.nphases):
        p = frame.phi[i].reshape(frame.parameters['Size'])
        c = frame.com[i]
        v = frame.vela[i] + frame.veli[i] + frame.velf[i] + frame.velc[i]
        a = frame.parameters['ninfo']*frame.parameters['nsubsteps']
        engine.arrow(c[0], c[1], a*v[0], a*v[1], color='k', head_width=1, zorder=10)


def phase(frame, n, engine=plt):
    """Plot single phase as a density plot"""
    cax = engine.imshow(frame.phi[n].T, interpolation='lanczos', cmap='Greys', origin='lower'
                        #, clim=(0., 1.)
                        )
    cbar = plt.colorbar(cax)

def velocityfield(frame, size=15, engine=plt):
    """Plot the total veloctity field assiciated with the cells"""
    v = get_velocity_field(frame.phi, frame.parameters['alpha']*frame.pol+frame.velp)
    vx = np.array([ i[0] for i in v ])
    vy = np.array([ i[1] for i in v ])
    vx = ndimage.filters.uniform_filter(vx, size=size, mode='wrap')
    vy = ndimage.filters.uniform_filter(vy, size=size, mode='wrap')
    cax = engine.quiver(np.arange(0, frame.parameters['Size'][0]),
                        np.arange(0, frame.parameters['Size'][1]),
                        vx.T, vy.T,
                        pivot='tail', units='dots', scale_units='dots')

def walls(frame, engine=plt):
    """Plot the wall phase-field"""
    cax = engine.imshow(frame.parameters['walls'], cmap='Greys', origin='lower', clim=(0., 1.))

def patch(frame, n, engine=plt):
    """Plot the restricted patch of a single cell"""
    plot = lambda m, M: engine.fill([ m[0], M[0], M[0], m[0], m[0], None ],
                                    [ m[1], m[1], M[1], M[1], m[1], None ],
                                    color = 'b', alpha=0.04)
    LX, LY = frame.parameters['Size']
    m = frame.patch_min[n]
    M = frame.patch_max[n]

    if(m[0]==M[0]):
        m[0] += 1e-1
        M[0] -= 1e-1
    if(m[1]==M[1]):
        m[1] += 1e-1
        M[1] -= 1e-1

    if(m[0]>M[0] and m[1]>M[1]):
        plot(m, [ LX, LY ])
        plot([ 0, 0 ], M)
        plot([ m[0], 0 ], [ LX, M[1] ])
        plot([0, m[1] ], [ M[0], LY ])
    elif(m[0]>M[0]):
        plot(m, [ LX, M[1] ])
        plot([ 0, m[1] ], M)
    elif(m[1]>M[1]):
        plot(m, [ M[0], LY ])
        plot([ m[0], 0 ], M)
    else:
        plot(m, M)

def patches(frame, engine=plt):
    """Plot the restricted patches of each cell"""
    for n in range(frame.nphases):
        patch(frame, n, engine)

def masks(frame, engine=plt):
    """Plot division/death masks"""
    m1 = np.array([ 1 if i else 0 for i in frame.division_mask ])
    m2 = np.array([ 1 if i else 0 for i in frame.death_mask ])

    engine.contour(np.arange(0, frame.parameters['LX']),
                   np.arange(0, frame.parameters['LY']),
                   m1.reshape(frame.parameters['Size']).T,
                   levels = [.5], colors = ['b'])

    engine.contour(np.arange(0, frame.parameters['LX']),
                   np.arange(0, frame.parameters['LY']),
                   m2.reshape(frame.parameters['Size']).T,
                   levels = [.5], colors = [ 'r' ])
