# Geometry Nodes Backdrop

将 3D 视图显示在几何节点编辑器的背景中，类似于合成模块的 Backdrop 功能。

## 功能

- 在几何节点编辑器背景显示 3D 视图的内容
- 实时更新（约 30 FPS）
- 简单的开关控制

## 安装

1. 将整个 `gn_backdrop` 文件夹复制到 Blender 的插件目录：
   - Windows: `%APPDATA%\Blender Foundation\Blender\4.5\scripts\addons\`
   - macOS: `~/Library/Application Support/Blender/4.5/scripts/addons/`
   - Linux: `~/.config/blender/4.5/scripts/addons/`

2. 在 Blender 中打开 `编辑 > 偏好设置 > 插件`
3. 搜索 "Geometry Nodes Backdrop"
4. 勾选启用插件

## 使用方法

1. 打开几何节点编辑器
2. 在 Blender 中运行命令：`bpy.ops.node.toggle_geonode_backdrop()`
3. 或者在 Python 控制台中输入：
   ```python
   import bpy
   bpy.ops.node.toggle_geonode_backdrop()
   ```

## 当前限制

由于 Blender Python API 的限制，当前版本无法完整捕获 3D 视图的所有渲染细节（材质、光照、后期处理等）。这需要访问 Blender 的内部 C/C++ 渲染引擎。

### 可能的解决方案

1. **使用 Blender 的 C API**：需要编写 C/C++ 扩展来直接访问渲染引擎
2. **使用截图方法**：定期截取 3D 视图的屏幕截图并显示
3. **等待 Blender API 更新**：希望未来的 Blender 版本提供更好的 Python API 支持

## 系统要求

- Blender 4.5 或更高版本

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！
