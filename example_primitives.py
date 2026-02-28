#!/usr/bin/env python3
"""
Example file demonstrating bpwf primitives.

This script creates a scene with various geometric primitives:
- Sphere (sph)
- Box/Rectangular Parallelepiped (rpp)
- Cylinder (rcc)
- Cone (cone)
- Plane (plane)
"""

from bpwf import bpwf

# Create a new scene
scene = bpwf()

# Add a sphere
scene.sph(c=[0, 0, 0], r=1.0, name="sphere", color="#FF5733")

# Add a box/rectangular parallelepiped
scene.rpp(c=[3, 0, 0], l=[1.5, 1.5, 1.5], name="box", color="#3498DB")

# Add a cylinder
scene.rcc(c=[-3, 0, 0], r=0.75, h=2.0, direction='z', name="cylinder", color="#E74C3C")

# Add a cone
scene.cone(c=[0, 3, 0], r1=1.0, r2=0.2, h=2.0, name="cone", color="#2ECC71", direction='z')

# Add a plane as a ground
scene.plane(c=[0, 0, -2], l=[10, 10, 0], name="ground", color="#95A5A6")

# Add a sun lamp for lighting
scene.sun(strength=2.0)

# Add a point light for additional illumination
scene.point(location=[5, -5, 5], strength=500.0, name="point_light", color="#FFFFFF")

# Render the scene
print("Rendering scene with primitives...")
scene.render(
    camera_location=[8, -8, 6],
    c=[0, 0, 0],
    l=[5, 5, 5],
    samples=64,
    res=[1920, 1080],
    transparent=True
)

print(f"Render complete! Output saved to: {scene.filename}.png")
print(f"Blend file saved to: {scene.filename}.blend")
