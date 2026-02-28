"""
bpwf - Blender for Publication-Worthy Figures
Programmatic 3D scene creation and rendering using Blender's bpy module.
"""

import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Import main classes
from .bpwf import bpwf, FileStringStream, PrincipledBSDF

__version__ = "3.0.0"
__all__ = ["bpwf", "FileStringStream", "PrincipledBSDF"]

# Log initialization
logger.info("bpwf initialized with direct bpy integration")
