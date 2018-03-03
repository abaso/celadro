#
# Defect tracking script. Uses python2.
#
# Usage:
#
#   python2 defects-flowfields.py input
#
#  where
#
#    intput -- the input file or directory

import numpy as np
import matplotlib.pyplot as plt
import sys
sys.path.insert(0, "../plot/")
import plot
import archive
import animation
from scipy.ndimage import rotate, shift
from math import cos, sin, pi

##################################################
# Init

if len(sys.argv)<2:
    print "Please provide input file to me."
    exit(1)

##################################################
# Track defects

window_size = 100
charge      = 0.5

ar = archive.loadarchive(sys.argv[1])
tracker = plot.defect_tracker(max_dst=15)

# https://stackoverflow.com/questions/46657423/rotated-image-coordinates-after-scipy-ndimage-interpolation-rotate
def rot(image, xy, angle, crop):
    # shift, rotate, and shift
    org_center = (np.array(image.shape[:2][::-1])-1)/2.
    im_rot = shift (image, - xy + org_center, mode='wrap')
    im_rot = rotate(im_rot, np.rad2deg(angle), mode='wrap', reshape=False)
    im_rot = shift (im_rot, - org_center + 2*[crop/2], mode='wrap')
    # crop to window size
    return im_rot[0:crop, 0:crop]

c = 0
Q00_tot = np.zeros((window_size, window_size))
Q01_tot = np.zeros((window_size, window_size))
vx_tot  = np.zeros((window_size, window_size))
vy_tot  = np.zeros((window_size, window_size))

for i in np.arange(ar._nframes+1, step=5):
#for i in np.arange(300, 310):
    frame = ar.read_frame(i)
    print "{}/{}".format(i, ar._nframes)

    vx, vy   = plot.get_velocity_field(frame.phi, frame.velp + frame.velc + frame.velf, size=24)
    #Q00, Q01 = plot.get_Qtensor(frame.phi, frame.Q00, frame.Q01, size=24)
    Q00, Q01 = plot.get_Qtensor(frame.phi, frame.S00, frame.S01, size=24)

    defects = plot.get_defects(plot.charge_array(Q00, Q01), Q00, Q01)

    for d in defects:
        if d['charge']==charge:
            # rotation angle
            w = -d['angle']
            p = d['pos']

            # Q tensor
            Q00 = rot(Q00, p, w, window_size)
            Q01 = rot(Q01, p, w, window_size)
            Q00, Q01 = cos(2*w)*Q00 - sin(2*w)*Q01, sin(2*w)*Q00 + cos(2*w)*Q01
            Q00_tot += Q00
            Q01_tot += Q01

            # velocity field
            vx = rot(vx, p, w, window_size)
            vy = rot(vy, p, w, window_size)
            vx, vy = cos(w)*vx - sin(w)*vy, sin(w)*vx + cos(w)*vy
            vx_tot += vx
            vy_tot += vy

            c += 1

print "Averaged over", c, "instances"

avg = 4

################################################################################
# Q tensor

Q00_tot /= c
Q01_tot /= c

plot.director(Q00_tot, Q01_tot, avg=avg)
plt.show()

################################################################################
# stress (cheating)

#P   = Q00_tot + Q01_tot
#cax = plt.imshow(P.T, interpolation='lanczos', cmap='plasma', origin='lower')
#plt.show()

plot.director(Q00_tot, Q01_tot, avg=avg)
cax = plt.imshow(-Q00_tot.T, interpolation='lanczos', cmap='plasma', origin='lower')
plt.show()

plot.director(Q00_tot, Q01_tot, avg=avg)
cax = plt.imshow( Q01_tot.T, interpolation='lanczos', cmap='plasma', origin='lower')
plt.show()

################################################################################
# velocity

vx_tot /= c
vy_tot /= c

m = np.sqrt(vx_tot**2 + vy_tot**2)
cax = plt.imshow(m.T, interpolation='lanczos', cmap='plasma', origin='lower')
plt.colorbar(cax)

vx_tot = vx_tot.reshape((vx_tot.shape[0]//avg, avg, vx_tot.shape[1]//avg, avg))
vx_tot = np.mean(vx_tot, axis=(1,3))
vy_tot = vy_tot.reshape((vy_tot.shape[0]//avg, avg, vy_tot.shape[1]//avg, avg))
vy_tot = np.mean(vy_tot, axis=(1,3))

cax = plt.quiver(avg*np.arange(vx_tot.shape[0]),
                 avg*np.arange(vx_tot.shape[1]),
                 vx_tot.T, vy_tot.T,
                 pivot='tail', units='dots', scale_units='dots')
plt.show()


