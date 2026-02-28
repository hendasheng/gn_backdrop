bl_info = {
    "name": "Geometry Nodes Backdrop",
    "author": "Your Name",
    "version": (1, 0, 0),
    "blender": (4, 5, 0),
    "location": "Node Editor > Geometry Nodes",
    "description": "Display 3D viewport in geometry nodes editor background",
    "category": "Node",
}

import bpy
from . import backdrop_draw


def register():
    print("→ __init__.py register() 被调用")
    backdrop_draw.register()
    print("✓ backdrop_draw.register() 完成")


def unregister():
    print("→ __init__.py unregister() 被调用")
    backdrop_draw.unregister()
    print("✓ backdrop_draw.unregister() 完成")


if __name__ == "__main__":
    register()
