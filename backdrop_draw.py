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

    # 查找 3D 视图的视图设置
    view3d_space = None
    view3d_region = None

    for area in context.screen.areas:
        if area.type == 'VIEW_3D':
            for sp in area.spaces:
                if sp.type == 'VIEW_3D':
                    view3d_space = sp
                    break
            for reg in area.regions:
                if reg.type == 'WINDOW':
                    view3d_region = reg
                    break
            break

    if not view3d_space or not view3d_region:
        return

    try:
        # 保存当前的 GPU 状态
        gpu.matrix.push()
        gpu.matrix.push_projection()

        # 使用 3D 视图的视图矩阵和投影矩阵
        view_matrix = view3d_region.view_matrix.copy()
        projection_matrix = view3d_region.view_perspective_matrix.copy()

        gpu.matrix.load_matrix(view_matrix)
        gpu.matrix.load_projection_matrix(projection_matrix)

        # 设置视口
        gpu.state.viewport_set(0, 0, region.width, region.height)

        # 启用深度测试
        gpu.state.depth_test_set('LESS_EQUAL')
        gpu.state.depth_mask_set(True)

        # 绘制场景中的所有对象
        depsgraph = context.evaluated_depsgraph_get()

        for obj_eval in depsgraph.objects:
            if obj_eval.type == 'MESH':
                # 获取对象的世界矩阵
                matrix_world = obj_eval.matrix_world.copy()

                # 获取网格数据
                mesh = obj_eval.data

                if len(mesh.vertices) > 0 and len(mesh.polygons) > 0:
                    # 创建顶点和索引数据
                    vertices = [matrix_world @ v.co for v in mesh.vertices]

                    # 创建三角形索引
                    indices = []
                    for poly in mesh.polygons:
                        if len(poly.vertices) >= 3:
                            # 简单的三角形扇形分割
                            for i in range(1, len(poly.vertices) - 1):
                                indices.append((poly.vertices[0], poly.vertices[i], poly.vertices[i + 1]))

                    if indices:
                        # 创建着色器
                        shader = gpu.shader.from_builtin('UNIFORM_COLOR')
                        batch = batch_for_shader(
                            shader, 'TRIS',
                            {"pos": vertices},
                            indices=indices,
                        )

                        # 使用对象的颜色或默认颜色
                        if obj_eval.color:
                            color = (*obj_eval.color[:3], 1.0)
                        else:
                            color = (0.8, 0.8, 0.8, 1.0)

                        shader.bind()
                        shader.uniform_float("color", color)
                        batch.draw(shader)

        # 恢复 GPU 状态
        gpu.state.depth_test_set('NONE')
        gpu.state.depth_mask_set(False)
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

    # 在节点编辑器中注册绘制回调
    _draw_handler_node = bpy.types.SpaceNodeEditor.draw_handler_add(
        draw_3d_scene_as_backdrop, (), 'WINDOW', 'PRE_VIEW'
    )


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
