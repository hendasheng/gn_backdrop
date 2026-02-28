import bpy
import gpu
from gpu_extras.batch import batch_for_shader
from mathutils import Matrix


# 全局变量
_draw_handler_node = None
_enabled = False


def draw_3d_scene_as_backdrop():
    """在几何节点编辑器背景直接绘制 3D 场景"""
    global _enabled

    if not _enabled:
        return

    context = bpy.context

    # 确保当前是几何节点编辑器
    if not hasattr(context, 'space_data') or context.space_data.type != 'NODE_EDITOR':
        return

    space = context.space_data
    if not hasattr(space, 'tree_type') or space.tree_type != 'GeometryNodeTree':
        return

    region = context.region
    if not region:
        return

    try:
        # 简单绘制一个测试矩形，验证基本绘制是否工作
        shader = gpu.shader.from_builtin('UNIFORM_COLOR')

        width = region.width
        height = region.height

        # 绘制半透明蓝色背景
        vertices = [(0, 0), (width, 0), (width, height), (0, height)]

        batch = batch_for_shader(
            shader, 'TRI_FAN',
            {"pos": vertices},
        )

        # 保存并重置变换矩阵
        gpu.matrix.push()
        gpu.matrix.push_projection()

        gpu.matrix.load_identity()

        # 设置正交投影
        projection_matrix = Matrix([
            [2.0 / width, 0, 0, -1],
            [0, 2.0 / height, 0, -1],
            [0, 0, -1, 0],
            [0, 0, 0, 1]
        ])
        gpu.matrix.load_projection_matrix(projection_matrix)

        gpu.state.blend_set('ALPHA')
        shader.bind()
        shader.uniform_float("color", (0.2, 0.3, 0.5, 0.3))
        batch.draw(shader)
        gpu.state.blend_set('NONE')

        gpu.matrix.pop_projection()
        gpu.matrix.pop()

    except Exception as e:
        print(f"✗ 绘制错误: {e}")
        import traceback
        traceback.print_exc()


class GEONODE_OT_toggle_backdrop(bpy.types.Operator):
    """Toggle geometry nodes backdrop display"""
    bl_idname = "node.toggle_geonode_backdrop"
    bl_label = "Backdrop"
    bl_options = {'REGISTER'}

    def execute(self, context):
        global _enabled
        _enabled = not _enabled

        if _enabled:
            self.report({'INFO'}, "Geometry Nodes Backdrop enabled")
            print("\n=== Backdrop 已启用 ===")
            print("背景将显示 3D 场景")
            print("=====================\n")
        else:
            self.report({'INFO'}, "Geometry Nodes Backdrop disabled")
            print("\n=== Backdrop 已禁用 ===\n")

        # 强制重绘
        for window in context.window_manager.windows:
            for area in window.screen.areas:
                area.tag_redraw()

        return {'FINISHED'}


def draw_header_button(self, context):
    """在节点编辑器头部绘制 Backdrop 按钮"""
    layout = self.layout

    # 检查是否在节点编辑器中
    if context.area and context.area.type == 'NODE_EDITOR':
        space = context.space_data
        if space and space.type == 'NODE_EDITOR':
            # 只在几何节点编辑器中显示
            if hasattr(space, 'tree_type') and space.tree_type == 'GeometryNodeTree':
                layout.separator_spacer()

                # 使用图标按钮，根据状态改变图标
                icon = 'HIDE_OFF' if _enabled else 'HIDE_ON'
                layout.operator(
                    "node.toggle_geonode_backdrop",
                    text="Backdrop",
                    icon=icon,
                    depress=_enabled
                )


def register():
    global _draw_handler_node

    print("→ 注册 Backdrop 插件")

    # 安全注册类（避免重复注册错误）
    try:
        bpy.utils.register_class(GEONODE_OT_toggle_backdrop)
        print("✓ 操作符注册成功")
    except ValueError:
        # 类已经注册，先注销再重新注册
        bpy.utils.unregister_class(GEONODE_OT_toggle_backdrop)
        bpy.utils.register_class(GEONODE_OT_toggle_backdrop)
        print("✓ 操作符重新注册成功")

    # 在节点编辑器头部添加按钮
    bpy.types.NODE_HT_header.append(draw_header_button)
    print("✓ 头部按钮添加成功")

    # 在节点编辑器中注册绘制回调
    _draw_handler_node = bpy.types.SpaceNodeEditor.draw_handler_add(
        draw_3d_scene_as_backdrop, (), 'WINDOW', 'PRE_VIEW'
    )
    print("✓ 绘制回调注册成功")


def unregister():
    global _draw_handler_node

    # 移除头部按钮
    try:
        bpy.types.NODE_HT_header.remove(draw_header_button)
    except:
        pass

    if _draw_handler_node:
        bpy.types.SpaceNodeEditor.draw_handler_remove(_draw_handler_node, 'WINDOW')
        _draw_handler_node = None

    try:
        bpy.utils.unregister_class(GEONODE_OT_toggle_backdrop)
    except RuntimeError:
        # 类未注册，忽略错误
        pass
