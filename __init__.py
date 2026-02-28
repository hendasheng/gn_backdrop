bl_info = {
    "name": "Geometry Nodes Backdrop",
    "author": "Your Name",
    "version": (1, 0, 0),
    "blender": (5, 0, 0),
    "location": "Node Editor > Geometry Nodes",
    "description": "Display 3D viewport in geometry nodes editor background",
    "category": "Node",
}

import bpy
from . import backdrop_draw


def register():
    backdrop_draw.register()


def unregister():
    backdrop_draw.unregister()


if __name__ == "__main__":
    register()
