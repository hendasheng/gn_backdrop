import bpy
import gpu
from gpu_extras.batch import batch_for_shader
from mathutils import Matrix


# 全局变量
_draw_handler_node = None
_draw_handler_view3d = None
_enabled = False
_captured_texture = None
_capture_width = 0
_capture_height = 0


def capture_view3d_framebuffer():
    """在 3D 视图绘制后捕获 framebuffer"""
    global _captured_texture, _capture_width, _capture_height

    if not _enabled:
        return

    context = bpy.context

    # 只在 3D 视图中捕获
    if context.area and context.area.type == 'VIEW_3D':
        region = context.region
        if region and region.type == 'WINDOW':
            width = region.width
            height = region.height

            if width <= 0 or height <= 0:
                return

            try:
                # 读取当前 framebuffer
                fb = gpu.state.active_framebuffer_get()

                # 读取颜色数据
                buffer = fb.read_color(0, 0, width, height, 4, 0, 'UBYTE')

                # 创建或更新纹理
                if (_captured_texture is None or
                    _capture_width != width or
                    _capture_height != height):

                    if _captured_texture:
                        del _captured_texture

                    _captured_texture = gpu.types.GPUTexture((width, height), format='RGBA8')
                    _capture_width = width
                    _capture_height = height

                # 更新纹理数据
                # 使用 bgl 来更新纹理
                import bgl
                bgl.glBindTexture(bgl.GL_TEXTURE_2D, _captured_texture.bind_code)
                bgl.glTexSubImage2D(
                    bgl.GL_TEXTURE_2D, 0, 0, 0, width, height,
                    bgl.GL_RGBA, bgl.GL_UNSIGNED_BYTE, buffer
                )
                bgl.glBindTexture(bgl.GL_TEXTURE_2D, 0)

            except Exception as e:
                print(f"Capture error: {e}")


def draw_backdrop():
    """在几何节点编辑器背景绘制捕获的内容"""
    global _enabled, _captured_texture

    if not _enabled or _captured_texture is None:
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

    width = region.width
    height = region.height

    # 创建着色器
    shader = gpu.shader.from_builtin('IMAGE')

    # 全屏四边形
    vertices = (
        (0, 0), (width, 0),
        (width, height), (0, height))

    texcoords = (
        (0, 0), (1, 0),
        (1, 1), (0, 1))

    indices = ((0, 1, 2), (0, 2, 3))

    batch = batch_for_shader(
        shader, 'TRIS',
        {"pos": vertices, "texCoord": texcoords},
        indices=indices,
    )

    # 设置正交投影矩阵
    projection_matrix = Matrix([
        [2.0 / width, 0, 0, -1],
        [0, 2.0 / height, 0, -1],
        [0, 0, -1, 0],
        [0, 0, 0, 1]
    ])

    # 绘制
    try:
        gpu.state.blend_set('ALPHA')
        shader.bind()
        shader.uniform_sampler("image", _captured_texture)
        shader.uniform_float("modelViewProjectionMatrix", projection_matrix)
        batch.draw(shader)
        gpu.state.blend_set('NONE')
    except Exception as e:
        print(f"Draw error: {e}")


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
        else:
            self.report({'INFO'}, "Geometry Nodes Backdrop disabled")

        # 强制重绘
        for window in context.window_manager.windows:
            for area in window.screen.areas:
                area.tag_redraw()

        return {'FINISHED'}


def draw_header_button(self, context):
    """在节点编辑器头部绘制 Backdrop 按钮"""
    layout = self.layout

    # 检查是否在节点编辑器中
    if not hasattr(context, 'area') or context.area.type != 'NODE_EDITOR':
        return

    space = context.space_data
    if space is None:
        return

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
    global _draw_handler_node, _draw_handler_view3d

    # 安全注册类（避免重复注册错误）
    try:
        bpy.utils.register_class(GEONODE_OT_toggle_backdrop)
    except ValueError:
        # 类已经注册，先注销再重新注册
        bpy.utils.unregister_class(GEONODE_OT_toggle_backdrop)
        bpy.utils.register_class(GEONODE_OT_toggle_backdrop)

    # 在节点编辑器头部添加按钮
    bpy.types.NODE_HT_header.append(draw_header_button)

    # 在 3D 视图中注册捕获回调（POST_PIXEL 确保在绘制完成后执行）
    _draw_handler_view3d = bpy.types.SpaceView3D.draw_handler_add(
        capture_view3d_framebuffer, (), 'WINDOW', 'POST_PIXEL'
    )

    # 在节点编辑器中注册绘制回调（使用 WINDOW 区域，PRE_VIEW 阶段确保在背景绘制）
    _draw_handler_node = bpy.types.SpaceNodeEditor.draw_handler_add(
        draw_backdrop, (), 'WINDOW', 'PRE_VIEW'
    )


def unregister():
    global _draw_handler_node, _draw_handler_view3d, _captured_texture

    # 移除头部按钮
    try:
        bpy.types.NODE_HT_header.remove(draw_header_button)
    except:
        pass

    if _draw_handler_view3d:
        bpy.types.SpaceView3D.draw_handler_remove(_draw_handler_view3d, 'WINDOW')
        _draw_handler_view3d = None

    if _draw_handler_node:
        bpy.types.SpaceNodeEditor.draw_handler_remove(_draw_handler_node, 'WINDOW')
        _draw_handler_node = None

    if _captured_texture:
        del _captured_texture
        _captured_texture = None

    try:
        bpy.utils.unregister_class(GEONODE_OT_toggle_backdrop)
    except RuntimeError:
        # 类未注册，忽略错误
        pass
