"""
Shared pytest fixtures and configuration for bpwf test suite.
"""

import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
import pytest


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    tmpdir = tempfile.mkdtemp()
    yield tmpdir
    shutil.rmtree(tmpdir, ignore_errors=True)


@pytest.fixture
def mock_bpy():
    """Mock the bpy module for testing without Blender installed."""
    with patch.dict('sys.modules', {'bpy': MagicMock()}):
        import sys
        bpy_mock = sys.modules['bpy']
        
        # Mock common bpy structures
        bpy_mock.data = MagicMock()
        bpy_mock.data.objects = {}
        bpy_mock.data.materials = {}
        bpy_mock.data.meshes = {}
        bpy_mock.data.lights = {}
        bpy_mock.data.cameras = {}
        bpy_mock.data.scenes = MagicMock()
        bpy_mock.data.collections = {}
        bpy_mock.data.worlds = MagicMock()
        
        bpy_mock.context = MagicMock()
        bpy_mock.context.scene = MagicMock()
        bpy_mock.context.object = MagicMock()
        bpy_mock.context.window = MagicMock()
        bpy_mock.context.view_layer = MagicMock()
        
        bpy_mock.ops = MagicMock()
        bpy_mock.ops.mesh = MagicMock()
        bpy_mock.ops.object = MagicMock()
        bpy_mock.ops.render = MagicMock()
        bpy_mock.ops.wm = MagicMock()
        
        yield bpy_mock


@pytest.fixture
def sample_scene(mock_bpy):
    """Create a basic bpwf scene for testing."""
    from bpwf import bpwf
    
    scene = bpwf(default_light=False)
    return scene


@pytest.fixture
def mock_mcp_scenes(monkeypatch):
    """Mock the global _scenes dictionary for MCP server tests."""
    mock_scenes = {}
    monkeypatch.setattr("bpwf.mcp_server._scenes", mock_scenes)
    return mock_scenes


@pytest.fixture
def has_bpy():
    """Check if bpy is actually available on the system."""
    try:
        import bpy
        return True
    except ImportError:
        return False


@pytest.fixture
def skip_if_no_bpy(has_bpy):
    """Skip test if bpy is not available."""
    if not has_bpy:
        pytest.skip("bpy not available - install with: pip install bpy")
