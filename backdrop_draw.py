import bpy
import gpu
from gpu_extras.batch import batch_for_shader
from mathutils import Matrix
import numpy as np


# 全局变量
_draw_handler_node = None
_draw_handler_view3d = None
_enabled = False
_captured_texture = None
_capture_width = 0
_capture_height = 0
_pixel_buffer = None
_update_timer = None


def update_timer_callback():
    """定时器回调，强制重绘所有区域以实现实时更新"""
    if not _enabled:
        return 0.033

    # 强制重绘所有区域
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if area.type in ('VIEW_3D', 'NODE_EDITOR'):
                area.tag_redraw()

    return 0.033  # 继续定时器


def capture_view3d_framebuffer():
    """在 3D 视图绘制后捕获 framebuffer"""
    global _captured_texture, _capture_width, _capture_height, _pixel_buffer

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

                # 读取颜色数据到 buffer - 使用 FLOAT 格式
                # 注意：读取的是最终渲染结果，应该包含所有光照和材质
                buffer = fb.read_color(0, 0, width, height, 4, 0, 'FLOAT')

                # 调试：检查 buffer 的内容
                if _captured_texture is None:
                    # 只在第一次打印
                    # 检查中心像素的值
                    center_idx = (height // 2 * width + width // 2) * 4
                    if center_idx + 4 <= len(buffer):
                        center_pixel = buffer[center_idx:center_idx+4]
                        print(f"✓ 创建纹理: {width}x{height}")
                        print(f"  中心像素 RGBA: {list(center_pixel)}")
                        print(f"  Framebuffer: {fb}")

                        # 检查是否所有值都接近 0（说明捕获的是空白或错误的数据）
                        if all(abs(v) < 0.01 for v in center_pixel[:3]):
                            print(f"  ⚠ 警告：捕获的像素值接近 0，可能没有捕获到正确的渲染内容")

                # 创建或更新纹理
                if (_captured_texture is None or
                    _capture_width != width or
                    _capture_height != height):

                    if _captured_texture:
                        del _captured_texture

                    # 创建新纹理，使用 data 参数直接初始化
                    _captured_texture = gpu.types.GPUTexture((width, height), format='RGBA32F', data=buffer)
                    _capture_width = width
                    _capture_height = height
                    _pixel_buffer = buffer
                else:
                    # 更新现有纹理 - 重新创建纹理（因为没有直接的更新方法）
                    del _captured_texture
                    _captured_texture = gpu.types.GPUTexture((width, height), format='RGBA32F', data=buffer)
                    _pixel_buffer = buffer

            except Exception as e:
                print(f"✗ 捕获错误: {e}")


def draw_backdrop():
    """在几何节点编辑器背景绘制捕获的内容"""
    global _enabled, _captured_texture

    if not _enabled:
        return

    if _captured_texture is None:
        # 绘制一个测试矩形来验证绘制是否工作
        context = bpy.context
        if hasattr(context, 'space_data') and context.space_data.type == 'NODE_EDITOR':
            space = context.space_data
            if hasattr(space, 'tree_type') and space.tree_type == 'GeometryNodeTree':
                region = context.region
                if region:
                    # 绘制红色测试矩形
                    shader = gpu.shader.from_builtin('UNIFORM_COLOR')
                    batch = batch_for_shader(
                        shader, 'TRI_FAN',
                        {"pos": [(100, 100), (300, 100), (300, 300), (100, 300)]},
                    )
                    shader.bind()
                    shader.uniform_float("color", (1, 0, 0, 0.5))
                    batch.draw(shader)
                    print("⚠ 纹理未捕获，显示红色测试矩形")
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

    # 计算纹理和窗口的宽高比
    texture_aspect = _capture_width / _capture_height if _capture_height > 0 else 1.0
    region_aspect = width / height if height > 0 else 1.0

    # 计算缩放后的尺寸，保持纹理的宽高比
    if texture_aspect > region_aspect:
        # 纹理更宽，以宽度为准
        scaled_width = width
        scaled_height = width / texture_aspect
        offset_x = 0
        offset_y = (height - scaled_height) / 2
    else:
        # 纹理更高，以高度为准
        scaled_height = height
        scaled_width = height * texture_aspect
        offset_x = (width - scaled_width) / 2
        offset_y = 0

    # 创建着色器 - 使用 IMAGE 着色器
    shader = gpu.shader.from_builtin('IMAGE')

    # 保持宽高比的四边形
    vertices = (
        (offset_x, offset_y),
        (offset_x + scaled_width, offset_y),
        (offset_x + scaled_width, offset_y + scaled_height),
        (offset_x, offset_y + scaled_height))

    # 正常的纹理坐标
    texcoords = (
        (0, 0), (1, 0),
        (1, 1), (0, 1))

    batch = batch_for_shader(
        shader, 'TRI_FAN',
        {"pos": vertices, "texCoord": texcoords},
    )

    # 绘制
    try:
        # 保存并重置变换矩阵，使用屏幕空间坐标
        gpu.matrix.push()
        gpu.matrix.push_projection()

        # 加载单位矩阵
        gpu.matrix.load_identity()

        # 设置正交投影矩阵，映射到屏幕像素坐标
        projection_matrix = Matrix([
            [2.0 / width, 0, 0, -1],
            [0, 2.0 / height, 0, -1],
            [0, 0, -1, 0],
            [0, 0, 0, 1]
        ])
        gpu.matrix.load_projection_matrix(projection_matrix)

        gpu.state.blend_set('ALPHA')
        shader.bind()
        shader.uniform_sampler("image", _captured_texture)
        batch.draw(shader)
        gpu.state.blend_set('NONE')

        # 恢复变换矩阵
        gpu.matrix.pop_projection()
        gpu.matrix.pop()
    except Exception as e:
        print(f"✗ 绘制错误: {e}")


class GEONODE_OT_toggle_backdrop(bpy.types.Operator):
    """Toggle geometry nodes backdrop display"""
    bl_idname = "node.toggle_geonode_backdrop"
    bl_label = "Backdrop"
    bl_options = {'REGISTER'}

    def execute(self, context):
        global _enabled, _update_timer
        _enabled = not _enabled

        if _enabled:
            # 启动定时器，每 0.033 秒（约 30 FPS）更新一次
            if _update_timer is None:
                _update_timer = context.window_manager.event_timer_add(0.033, window=context.window)
                # 注册定时器回调
                bpy.app.timers.register(update_timer_callback)

            self.report({'INFO'}, "Geometry Nodes Backdrop enabled")
            print("\n=== Backdrop 已启用 ===")
            print("背景将实时更新（约 30 FPS）")
            print("=====================\n")
        else:
            # 停止定时器
            if _update_timer is not None:
                context.window_manager.event_timer_remove(_update_timer)
                _update_timer = None
                # 注销定时器回调
                if bpy.app.timers.is_registered(update_timer_callback):
                    bpy.app.timers.unregister(update_timer_callback)

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

    # 在 3D 视图中注册捕获回调
    # 使用 POST_VIEW 而不是 POST_PIXEL，确保在所有渲染完成后捕获
    _draw_handler_view3d = bpy.types.SpaceView3D.draw_handler_add(
        capture_view3d_framebuffer, (), 'WINDOW', 'POST_VIEW'
    )

    # 在节点编辑器中注册绘制回调（使用 WINDOW 区域，PRE_VIEW 阶段确保在背景绘制）
    _draw_handler_node = bpy.types.SpaceNodeEditor.draw_handler_add(
        draw_backdrop, (), 'WINDOW', 'PRE_VIEW'
    )


def unregister():
    global _draw_handler_node, _draw_handler_view3d, _captured_texture, _update_timer

    # 停止定时器
    if _update_timer is not None:
        try:
            bpy.context.window_manager.event_timer_remove(_update_timer)
        except:
            pass
        _update_timer = None

    # 注销定时器回调
    if bpy.app.timers.is_registered(update_timer_callback):
        bpy.app.timers.unregister(update_timer_callback)

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
