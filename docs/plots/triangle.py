from pylab import *
import matplotlib.pyplot as plt
import math
from matplotlib.patches import Ellipse, Polygon
import numpy as np
# delta = 45.0 # degrees
# angles = arange(0, 360+delta, delta)
# ells = [Ellipse((1, 1), 4, 2, a) for a in angles]

e_l = 1

triangle = np.array([(0, 0), (e_l, 0), (1/2 * e_l, math.sqrt(3)/2 * e_l)])

trids = []
for j in range(4, 0, -1):
    for i in range(0, 4, 1):
        tri = np.array(triangle)
        tri[:, 0] += i * 2
        tri[:, 1] += j * 2
        print(tri)
        trids.append(tri)


ax = plt.subplot(111, aspect='equal')
def plot_arrow():
    pass

t1 = '++--' * 4
t2 = '+-+-' * 4
func = lambda x: r'$\plus$' if x == '+' else r'$\minus$'
text1 = [func(i) for i in t1]
text2 = [func(i) for i in t2]
color_func = lambda x: 'green' if x=='+' else 'red'

color1 = [color_func(i) for i in t1]
color2 = [color_func(i) for i in t2]


for ind, tri in enumerate(trids):

    p = Polygon(tri, fill=None)
    ax.add_artist(p)

    # not change
    dx = tri[1][0] - tri[0][0]
    dy = tri[1][1] - tri[0][1]
    ax.arrow(tri[0][0], tri[0][1], dx, dy, head_width=0.2, length_includes_head=True)

    
    sign = ((ind // 8) * 2 -1 ) * -1
    dx = sign * (tri[2][0] - tri[0][0])
    dy = sign * (tri[2][1] - tri[0][1])
    x = tri[0][0] if sign == 1 else tri[2][0]
    y = tri[0][1] if sign == 1 else tri[2][1]
    ax.arrow(x, y, dx, dy, head_width=0.2, length_includes_head=True, color=color1[ind])
    ax.text(tri[0][0],tri[0][1], 'i', ha='left', va='top')
    ax.text(tri[1][0],tri[1][1], 'j', ha='right', va='top')
    ax.text(tri[2][0],tri[2][1], 'k', ha='center', va='bottom')
    
    sign = (ind // 4)
    sign = 1 if sign == 1 or sign == 2 else -1
    dx = sign * (tri[2][0] - tri[0][0])
    dy = sign * (tri[2][1] - tri[0][1])
    x = tri[1][0] if sign == 1 else tri[2][0]
    y = tri[1][1] if sign == 1 else tri[2][1]

    dx = sign * (tri[2][0] - tri[1][0])
    dy = sign * (tri[2][1] - tri[1][1])
    ax.arrow(x, y, dx, dy, head_width=0.2, length_includes_head=True, color=color2[ind])

    p = (tri[0] + tri[1])/2
    ax.annotate(r"$\plus / \minus$", xy=p, ha="center", va="top")

    p = (tri[0] + tri[2])/2
    ax.annotate(text1[ind], xy=p, ha="right", va="center")

    p = (tri[1] + tri[2])/2
    ax.annotate(text2[ind], xy=p, ha="left", va="center")


# for e in ells:
#     e.set_clip_box(a.bbox)
#     e.set_alpha(0.1)
#     a.add_artist(e)

plt.xlim(-e_l, 8 * e_l )
plt.ylim(e_l, 8 * e_l + 2 )
plt.axis('off')
plt.tight_layout()
plt.show()