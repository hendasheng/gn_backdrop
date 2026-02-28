import bpy
import gpu
from gpu_extras.batch import batch_for_shader
from bpy.app.handlers import persistent

# 全局变量
_draw_handler_node = None
_enabled = False
_update_timer = None
_batch_cache = {}  # 缓存批处理数据 {obj_name: batch}
_cached_shader = None

def get_shader():
    """获取或创建着色器"""
    global _cached_shader
    if _cached_shader is None:
        try:
            # 尝试使用新的着色器名称 (Blender 4.0+)
            _cached_shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
        except Exception:
            try:
                # 回退到旧名称
                _cached_shader = gpu.shader.from_builtin('UNIFORM_COLOR')
            except Exception as e:
                print(f"无法创建着色器: {e}")
                return None
    return _cached_shader

@persistent
def depsgraph_update_handler(scene, depsgraph):
    """当场景更新时清理缓存"""
    global _batch_cache
    # 如果有几何体更新，清理缓存
    for update in depsgraph.updates:
        if update.is_updated_geometry:
            _batch_cache.clear()
            break

def update_timer_callback():
    """定时器回调，仅重绘节点编辑器以实现实时更新"""
    if not _enabled:
        return None  # 停止定时器

    # 仅重绘几何节点编辑器，避免全界面重绘带来的性能损耗
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == 'NODE_EDITOR':
                # 检查是否是几何节点编辑器
                if area.spaces.active.tree_type == 'GeometryNodeTree':
                    area.tag_redraw()

    return 0.033  # 继续定时器 (约 30 FPS)

def get_view3d_matrices():
    """获取 3D 视图的视图和投影矩阵"""
    # 优先查找当前屏幕下的 3D 视图
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            region = area.spaces.active.region_3d
            if region:
                return region.view_matrix.copy(), region.window_matrix.copy()
    
    # 如果当前屏幕没有，查找所有窗口
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == 'VIEW_3D':
                region = area.spaces.active.region_3d
                if region:
                    return region.view_matrix.copy(), region.window_matrix.copy()
                    
    return None, None

def get_object_batch(obj, shader):
    """获取对象的 GPU 批处理数据（带缓存）"""
    if obj.name in _batch_cache:
        return _batch_cache[obj.name]
    
    mesh = obj.data
    
    # 确保计算了三角面（处理多边形）
    mesh.calc_loop_triangles()
    
    if len(mesh.loop_triangles) == 0:
        return None

    # 获取顶点坐标
    vertices = [v.co[:] for v in mesh.vertices]
    
    # 获取三角形索引
    indices = [lt.vertices[:] for lt in mesh.loop_triangles]
    
    if not indices:
        return None

    # 创建批次
    batch = batch_for_shader(
        shader, 'TRIS',
        {"pos": vertices},
        indices=indices,
    )
    
    _batch_cache[obj.name] = batch
    return batch

def draw_scene_objects(view_matrix, projection_matrix):
    """绘制场景中的所有对象"""
    shader = get_shader()
    if not shader:
        return

    # 启用深度测试
    gpu.state.depth_test_set('LESS_EQUAL')
    gpu.state.depth_mask_set(True)
    
    shader.bind()

    # 遍历场景中的所有对象
    # 优化：仅遍历可见的网格对象
    for obj in bpy.context.scene.objects:
        if obj.type != 'MESH' or not obj.visible_get():
            continue
            
        batch = get_object_batch(obj, shader)
        if not batch:
            continue

        # 使用对象的材质颜色，如果没有则使用默认颜色
        if obj.active_material and obj.active_material.diffuse_color:
            color = obj.active_material.diffuse_color
            shader.uniform_float("color", (color[0], color[1], color[2], 1.0))
        else:
            shader.uniform_float("color", (0.8, 0.8, 0.8, 1.0))

        # 设置模型矩阵（对象的世界变换）
        gpu.matrix.push()
        gpu.matrix.load_matrix(obj.matrix_world)

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
    view_matrix, projection_matrix = get_view3d_matrices()

    if view_matrix is None or projection_matrix is None:
        return

    try:
        # 保存当前的 GPU 状态
        gpu.matrix.push()
        gpu.matrix.push_projection()

        # 设置视口为节点编辑器的区域大小
        gpu.state.viewport_set(0, 0, region.width, region.height)

        # 设置投影矩阵为 3D 视图的投影矩阵
        gpu.matrix.load_projection_matrix(projection_matrix)

        # 设置视图矩阵为 3D 视图的视图矩阵
        gpu.matrix.load_matrix(view_matrix)

        # 绘制场景对象
        draw_scene_objects(view_matrix, projection_matrix)

        # 恢复矩阵状态
        gpu.matrix.pop_projection()
        gpu.matrix.pop()

    except Exception as e:
        # 避免在绘制循环中频繁打印错误，可以考虑限制打印频率
        pass


class GEONODE_OT_toggle_backdrop(bpy.types.Operator):
    """Toggle geometry nodes backdrop display"""
    bl_idname = "node.toggle_geonode_backdrop"
    bl_label = "Backdrop"
    bl_options = {'REGISTER'}

    def execute(self, context):
        global _enabled, _update_timer
        _enabled = not _enabled

        if _enabled:
            # 注册定时器回调
            if not bpy.app.timers.is_registered(update_timer_callback):
                bpy.app.timers.register(update_timer_callback)

            self.report({'INFO'}, "Geometry Nodes Backdrop enabled")
        else:
            # 注销定时器回调
            if bpy.app.timers.is_registered(update_timer_callback):
                bpy.app.timers.unregister(update_timer_callback)

            self.report({'INFO'}, "Geometry Nodes Backdrop disabled")

        # 强制重绘一次以立即更新状态
        for window in context.window_manager.windows:
            for area in window.screen.areas:
                if area.type == 'NODE_EDITOR':
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

    # 注册类
    try:
        bpy.utils.register_class(GEONODE_OT_toggle_backdrop)
    except ValueError:
        bpy.utils.unregister_class(GEONODE_OT_toggle_backdrop)
        bpy.utils.register_class(GEONODE_OT_toggle_backdrop)

    # 注册头部按钮
    bpy.types.NODE_HT_header.append(draw_header_button)

    # 注册绘制回调
    _draw_handler_node = bpy.types.SpaceNodeEditor.draw_handler_add(
        draw_backdrop, (), 'WINDOW', 'PRE_VIEW'
    )
    
    # 注册依赖图更新回调（用于缓存清理）
    bpy.app.handlers.depsgraph_update_post.append(depsgraph_update_handler)


def unregister():
    global _draw_handler_node, _cached_shader

    # 清理缓存
    _batch_cache.clear()
    _cached_shader = None

    # 注销定时器
    if bpy.app.timers.is_registered(update_timer_callback):
        bpy.app.timers.unregister(update_timer_callback)

    # 移除依赖图更新回调
    if depsgraph_update_handler in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(depsgraph_update_handler)

    # 移除头部按钮
    try:
        bpy.types.NODE_HT_header.remove(draw_header_button)
    except:
        pass

    # 移除绘制回调
    if _draw_handler_node:
        bpy.types.SpaceNodeEditor.draw_handler_remove(_draw_handler_node, 'WINDOW')
        _draw_handler_node = None

    # 注销类
    try:
        bpy.utils.unregister_class(GEONODE_OT_toggle_backdrop)
    except RuntimeError:
        pass
