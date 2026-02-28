"""
MCP (Model Context Protocol) server for bpwf.

This module provides a FastMCP server that exposes bpwf functionality
for AI-assisted 3D scene creation and rendering.
"""

from typing import Optional, List, Dict, Any
import json
import os
import tempfile
from pathlib import Path

from fastmcp import FastMCP

# Import bpwf components
from .bpwf import bpwf


# Initialize FastMCP server
mcp = FastMCP("bpwf-server")

# Global scene storage (in-memory for now)
_scenes: Dict[str, bpwf] = {}


@mcp.tool()
def create_scene(
    scene_id: str,
    default_light: bool = True,
    scene_name: Optional[str] = None
) -> str:
    """
    Create a new bpwf scene.
    
    Args:
        scene_id: Unique identifier for the scene
        default_light: Whether to include default lighting
        scene_name: Optional Blender scene name for multi-scene support
    
    Returns:
        Success message with scene ID
    """
    if scene_id in _scenes:
        return f"Error: Scene '{scene_id}' already exists. Use a different ID or delete the existing scene."
    
    try:
        scene = bpwf(default_light=default_light, scene_name=scene_name)
        _scenes[scene_id] = scene
        return f"Scene '{scene_id}' created successfully."
    except Exception as e:
        return f"Error creating scene: {str(e)}"


@mcp.tool()
def list_scenes() -> str:
    """
    List all active scenes.
    
    Returns:
        JSON string with list of scene IDs
    """
    return json.dumps({
        "scenes": list(_scenes.keys()),
        "count": len(_scenes)
    }, indent=2)


@mcp.tool()
def delete_scene(scene_id: str) -> str:
    """
    Delete a scene.
    
    Args:
        scene_id: ID of the scene to delete
    
    Returns:
        Success or error message
    """
    if scene_id not in _scenes:
        return f"Error: Scene '{scene_id}' not found."
    
    del _scenes[scene_id]
    return f"Scene '{scene_id}' deleted successfully."


@mcp.tool()
def add_sphere(
    scene_id: str,
    x: float,
    y: float,
    z: float,
    radius: float,
    name: str,
    color: str = "#FFFFFF",
    alpha: float = 1.0,
    emissive: bool = False
) -> str:
    """
    Add a sphere to the scene.
    
    Args:
        scene_id: ID of the scene
        x, y, z: Center coordinates
        radius: Sphere radius
        name: Object name
        color: Hex color code (e.g., "#FF5733")
        alpha: Transparency (0.0-1.0)
        emissive: Whether the sphere emits light
    
    Returns:
        Success or error message
    """
    if scene_id not in _scenes:
        return f"Error: Scene '{scene_id}' not found."
    
    try:
        scene = _scenes[scene_id]
        scene.sph(c=[x, y, z], r=radius, name=name, color=color, alpha=alpha, emis=emissive)
        return f"Sphere '{name}' added to scene '{scene_id}'."
    except Exception as e:
        return f"Error adding sphere: {str(e)}"


@mcp.tool()
def add_cube(
    scene_id: str,
    x1: float,
    x2: float,
    y1: float,
    y2: float,
    z1: float,
    z2: float,
    name: str,
    color: str = "#FFFFFF",
    alpha: float = 1.0
) -> str:
    """
    Add a cube/box to the scene.
    
    Args:
        scene_id: ID of the scene
        x1, x2: X-axis bounds
        y1, y2: Y-axis bounds
        z1, z2: Z-axis bounds
        name: Object name
        color: Hex color code
        alpha: Transparency (0.0-1.0)
    
    Returns:
        Success or error message
    """
    if scene_id not in _scenes:
        return f"Error: Scene '{scene_id}' not found."
    
    try:
        scene = _scenes[scene_id]
        scene.rpp(x1=x1, x2=x2, y1=y1, y2=y2, z1=z1, z2=z2, name=name, color=color, alpha=alpha)
        return f"Cube '{name}' added to scene '{scene_id}'."
    except Exception as e:
        return f"Error adding cube: {str(e)}"


@mcp.tool()
def add_cylinder(
    scene_id: str,
    x: float,
    y: float,
    z: float,
    radius: float,
    height: float,
    name: str,
    direction: str = "z",
    color: str = "#FFFFFF",
    alpha: float = 1.0
) -> str:
    """
    Add a cylinder to the scene.
    
    Args:
        scene_id: ID of the scene
        x, y, z: Base center coordinates
        radius: Cylinder radius
        height: Cylinder height
        name: Object name
        direction: Axis direction ('x', 'y', or 'z')
        color: Hex color code
        alpha: Transparency (0.0-1.0)
    
    Returns:
        Success or error message
    """
    if scene_id not in _scenes:
        return f"Error: Scene '{scene_id}' not found."
    
    try:
        scene = _scenes[scene_id]
        scene.rcc(c=[x, y, z], r=radius, h=height, name=name, direction=direction, 
                  color=color, alpha=alpha)
        return f"Cylinder '{name}' added to scene '{scene_id}'."
    except Exception as e:
        return f"Error adding cylinder: {str(e)}"


@mcp.tool()
def add_cone(
    scene_id: str,
    x: float,
    y: float,
    z: float,
    base_radius: float,
    top_radius: float,
    height: float,
    name: str,
    direction: str = "z",
    color: str = "#FFFFFF",
    alpha: float = 1.0
) -> str:
    """
    Add a cone to the scene.
    
    Args:
        scene_id: ID of the scene
        x, y, z: Base center coordinates
        base_radius: Radius at base
        top_radius: Radius at top (0 for pointed cone)
        height: Cone height
        name: Object name
        direction: Axis direction ('x', 'y', or 'z')
        color: Hex color code
        alpha: Transparency (0.0-1.0)
    
    Returns:
        Success or error message
    """
    if scene_id not in _scenes:
        return f"Error: Scene '{scene_id}' not found."
    
    try:
        scene = _scenes[scene_id]
        scene.cone(c=[x, y, z], r1=base_radius, r2=top_radius, h=height, 
                   name=name, direction=direction, color=color, alpha=alpha)
        return f"Cone '{name}' added to scene '{scene_id}'."
    except Exception as e:
        return f"Error adding cone: {str(e)}"


@mcp.tool()
def add_point_light(
    scene_id: str,
    x: float,
    y: float,
    z: float,
    strength: float = 1000.0,
    name: str = "PointLight",
    color: str = "#FFFFFF"
) -> str:
    """
    Add a point light to the scene.
    
    Args:
        scene_id: ID of the scene
        x, y, z: Light position
        strength: Light intensity
        name: Light name
        color: Light color (hex code)
    
    Returns:
        Success or error message
    """
    if scene_id not in _scenes:
        return f"Error: Scene '{scene_id}' not found."
    
    try:
        scene = _scenes[scene_id]
        scene.point(location=[x, y, z], strength=strength, name=name, color=color)
        return f"Point light '{name}' added to scene '{scene_id}'."
    except Exception as e:
        return f"Error adding point light: {str(e)}"


@mcp.tool()
def add_sun_light(
    scene_id: str,
    strength: float = 1.0
) -> str:
    """
    Add a sun light to the scene.
    
    Args:
        scene_id: ID of the scene
        strength: Sun intensity
    
    Returns:
        Success or error message
    """
    if scene_id not in _scenes:
        return f"Error: Scene '{scene_id}' not found."
    
    try:
        scene = _scenes[scene_id]
        scene.sun(strength=strength)
        return f"Sun light added to scene '{scene_id}'."
    except Exception as e:
        return f"Error adding sun light: {str(e)}"


@mcp.tool()
def boolean_operation(
    scene_id: str,
    left_object: str,
    right_object: str,
    operation: str,
    unlink_right: bool = True
) -> str:
    """
    Perform boolean operation on two objects.
    
    Args:
        scene_id: ID of the scene
        left_object: Name of the first object
        right_object: Name of the second object
        operation: Operation type ('subtract', 'union', or 'intersect')
        unlink_right: Whether to remove the right object after operation
    
    Returns:
        Success or error message
    """
    if scene_id not in _scenes:
        return f"Error: Scene '{scene_id}' not found."
    
    try:
        scene = _scenes[scene_id]
        
        if operation == "subtract":
            scene.subtract(left_object, right_object, unlink=unlink_right)
        elif operation == "union":
            scene.union(left_object, right_object, unlink=unlink_right)
        elif operation == "intersect":
            scene.intersect(left_object, right_object, unlink=unlink_right)
        else:
            return f"Error: Invalid operation '{operation}'. Use 'subtract', 'union', or 'intersect'."
        
        return f"Boolean operation '{operation}' performed on '{left_object}' and '{right_object}'."
    except Exception as e:
        return f"Error performing boolean operation: {str(e)}"


@mcp.tool()
def render_scene(
    scene_id: str,
    camera_x: float = 5.0,
    camera_y: float = -5.0,
    camera_z: float = 3.0,
    target_x: float = 0.0,
    target_y: float = 0.0,
    target_z: float = 0.0,
    samples: int = 128,
    resolution_x: int = 1920,
    resolution_y: int = 1080,
    output_filename: Optional[str] = None
) -> str:
    """
    Render the scene to an image.
    
    Args:
        scene_id: ID of the scene to render
        camera_x, camera_y, camera_z: Camera position
        target_x, target_y, target_z: Point the camera looks at
        samples: Number of render samples (higher = better quality)
        resolution_x: Image width in pixels
        resolution_y: Image height in pixels
        output_filename: Optional output filename (without extension)
    
    Returns:
        Success message with output path or error message
    """
    if scene_id not in _scenes:
        return f"Error: Scene '{scene_id}' not found."
    
    try:
        scene = _scenes[scene_id]
        
        # Set output filename
        if output_filename:
            scene.filename = output_filename
        
        # Render the scene
        scene.run(
            camera_location=[camera_x, camera_y, camera_z],
            c=[target_x, target_y, target_z],
            l=[2, 2, 2],
            samples=samples,
            res=[resolution_x, resolution_y],
            block=True
        )
        
        output_path = f"{scene.filename}.png"
        return f"Scene '{scene_id}' rendered successfully to: {output_path}"
    except Exception as e:
        return f"Error rendering scene: {str(e)}"


@mcp.tool()
def get_bpy_status() -> str:
    """
    Check bpy availability and configuration.
    
    Returns:
        JSON string with bpy status information
    """
    try:
        import bpy
        
        return json.dumps({
            "available": True,
            "bpy_version": bpy.app.version_string if hasattr(bpy.app, 'version_string') else "unknown",
            "status": "ready"
        }, indent=2)
    except ImportError:
        return json.dumps({
            "available": False,
            "error": "bpy module not installed. Install with: pip install bpy",
            "status": "unavailable"
        }, indent=2)
    except Exception as e:
        return json.dumps({
            "available": False,
            "error": str(e),
            "status": "error"
        }, indent=2)


@mcp.tool()
def get_scene_info(scene_id: str) -> str:
    """
    Get information about a scene.
    
    Args:
        scene_id: ID of the scene
    
    Returns:
        JSON string with scene information
    """
    if scene_id not in _scenes:
        return f"Error: Scene '{scene_id}' not found."
    
    scene = _scenes[scene_id]
    
    return json.dumps({
        "scene_id": scene_id,
        "filename": scene.filename,
        "has_run": scene.has_run,
        "particles_count": len(scene.particles) if hasattr(scene, 'particles') else 0,
        "draft_mode": scene._draft
    }, indent=2)


def main():
    """Main entry point for the MCP server."""
    import sys
    
    # Run the FastMCP server
    print("Starting bpwf MCP server...")
    print("Checking bpy availability...")
    
    try:
        import bpy
        print("✓ bpy is available")
    except ImportError:
        print("✗ Warning: bpy not available. Install with: pip install bpy")
    
    print("\nServer ready. Available tools:")
    print("  - create_scene: Create a new 3D scene")
    print("  - add_sphere, add_cube, add_cylinder, add_cone: Add primitives")
    print("  - add_point_light, add_sun_light: Add lighting")
    print("  - boolean_operation: Perform boolean operations")
    print("  - render_scene: Render the scene to an image")
    print("  - get_bpy_status: Check bpy configuration")
    print("  - list_scenes, get_scene_info, delete_scene: Scene management")
    
    # Start the server
    mcp.run()


if __name__ == "__main__":
    main()
