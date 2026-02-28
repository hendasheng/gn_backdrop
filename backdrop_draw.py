import bpy
import gpu
from gpu_extras.batch import batch_for_shader
from mathutils import Matrix
import bgl


# 全局变量
_draw_handler_node = None
_enabled = False
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


def get_view3d_matrices():
    """获取 3D 视图的视图和投影矩阵"""
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            for space in area.spaces:
                if space.type == 'VIEW_3D':
                    for region in area.regions:
                        if region.type == 'WINDOW':
                            # 获取 3D 视图的视图矩阵和投影矩阵
                            view_matrix = space.region_3d.view_matrix.copy()
                            projection_matrix = space.region_3d.window_matrix.copy()
                            return view_matrix, projection_matrix, space.region_3d
    return None, None, None


def draw_scene_objects(view_matrix, projection_matrix):
    """绘制场景中的所有对象"""
    # 启用深度测试
    gpu.state.depth_test_set('LESS_EQUAL')
    gpu.state.depth_mask_set(True)

    # 使用内置的 3D 着色器
    shader = gpu.shader.from_builtin('UNIFORM_COLOR')

    # 遍历场景中的所有对象
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH' and obj.visible_get():
            # 获取对象的世界矩阵
            model_matrix = obj.matrix_world

            # 计算 MVP 矩阵
            mvp_matrix = projection_matrix @ view_matrix @ model_matrix

            # 获取网格数据
            mesh = obj.data
            if len(mesh.vertices) == 0:
                continue

            # 创建顶点位置列表
            vertices = [(v.co.x, v.co.y, v.co.z) for v in mesh.vertices]

            # 创建索引列表（三角形）
            indices = []
            for poly in mesh.polygons:
                if len(poly.vertices) >= 3:
                    # 简单的三角形扇形分割
                    for i in range(1, len(poly.vertices) - 1):
                        indices.append((poly.vertices[0], poly.vertices[i], poly.vertices[i + 1]))

            if not indices:
                continue

            # 创建批次
            batch = batch_for_shader(
                shader, 'TRIS',
                {"pos": vertices},
                indices=indices,
            )

            # 设置着色器
            shader.bind()

            # 使用对象的材质颜色，如果没有则使用默认颜色
            if obj.active_material and obj.active_material.diffuse_color:
                color = obj.active_material.diffuse_color
                shader.uniform_float("color", (color[0], color[1], color[2], 1.0))
            else:
                shader.uniform_float("color", (0.8, 0.8, 0.8, 1.0))

            # 设置 MVP 矩阵
            gpu.matrix.push()
            gpu.matrix.load_matrix(mvp_matrix)

            # 绘制
            batch.draw(shader)

            gpu.matrix.pop()

    # 禁用深度测试
    gpu.state.depth_test_set('NONE')
    gpu.state.depth_mask_set(False)


def draw_backdrop():
    """在几何节点编辑器背景绘制 3D 场景"""
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

    # 获取 3D 视图的矩阵
    view_matrix, projection_matrix, region_3d = get_view3d_matrices()

    if view_matrix is None or projection_matrix is None:
        # 如果找不到 3D 视图，显示提示信息
        return

    try:
        # 保存当前的矩阵状态
        gpu.matrix.push()
        gpu.matrix.push_projection()

        # 加载 3D 视图的矩阵
        gpu.matrix.load_matrix(Matrix.Identity(4))
        gpu.matrix.load_projection_matrix(Matrix.Identity(4))

        # 绘制场景对象
        draw_scene_objects(view_matrix, projection_matrix)

        # 恢复矩阵状态
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
            print("背景将实时显示 3D 场景（约 30 FPS）")
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
    global _draw_handler_node

    # 安全注册类（避免重复注册错误）
    try:
        bpy.utils.register_class(GEONODE_OT_toggle_backdrop)
    except ValueError:
        # 类已经注册，先注销再重新注册
        bpy.utils.unregister_class(GEONODE_OT_toggle_backdrop)
        bpy.utils.register_class(GEONODE_OT_toggle_backdrop)

    # 在节点编辑器头部添加按钮
    bpy.types.NODE_HT_header.append(draw_header_button)

    # 在节点编辑器中注册绘制回调（使用 WINDOW 区域，PRE_VIEW 阶段确保在背景绘制）
    _draw_handler_node = bpy.types.SpaceNodeEditor.draw_handler_add(
        draw_backdrop, (), 'WINDOW', 'PRE_VIEW'
    )


def unregister():
    global _draw_handler_node, _update_timer

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

    if _draw_handler_node:
        bpy.types.SpaceNodeEditor.draw_handler_remove(_draw_handler_node, 'WINDOW')
        _draw_handler_node = None

    try:
        bpy.utils.unregister_class(GEONODE_OT_toggle_backdrop)
    except RuntimeError:
        # 类未注册，忽略错误
        pass
