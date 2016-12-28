import pyb

scene = pyb.pyb()
scene.rpp(c=(0., 0., 0.), l=(100., 100., 100.), name='cube')
scene.flat(color="#E3AE24", name='newgold')
scene.set_matl(obj='cube', matl='newgold')
scene.sun()
scene.run(target='cube')
scene.show()
