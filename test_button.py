"""
测试脚本：在 Blender 中运行此脚本来测试按钮是否正确添加

使用方法：
1. 在 Blender 的 Scripting 工作区打开此文件
2. 点击运行脚本
3. 查看控制台输出
"""

import bpy

print("\n=== 测试 Backdrop 按钮 ===")

# 检查操作符是否注册
if hasattr(bpy.ops.node, 'toggle_geonode_backdrop'):
    print("✓ 操作符已注册: node.toggle_geonode_backdrop")
else:
    print("✗ 操作符未注册")

# 检查头部是否有我们的绘制函数
header_funcs = bpy.types.NODE_HT_header._dyn_ui_initialize()
print(f"✓ 节点编辑器头部有 {len(header_funcs)} 个自定义函数")

# 检查当前上下文
context = bpy.context
print(f"\n当前区域类型: {context.area.type if context.area else 'None'}")

if context.area and context.area.type == 'NODE_EDITOR':
    space = context.space_data
    if hasattr(space, 'tree_type'):
        print(f"节点树类型: {space.tree_type}")
        if space.tree_type == 'GeometryNodeTree':
            print("✓ 当前在几何节点编辑器中，按钮应该可见")
        else:
            print("! 当前不在几何节点编辑器中")
    else:
        print("! space_data 没有 tree_type 属性")

print("\n如果按钮仍然不可见，请尝试：")
print("1. 切换到其他工作区再切换回来")
print("2. 重启 Blender")
print("3. 检查插件是否正确启用")
