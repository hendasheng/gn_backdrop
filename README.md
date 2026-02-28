# Geometry Nodes Backdrop

将 3D 视图显示在几何节点编辑器的背景中，类似于合成模块的 Backdrop 功能。

## 功能

- 在几何节点编辑器背景显示 3D 视图的内容
- 实时更新（约 30 FPS）
- 简单的开关控制

## 安装

### 方法一：使用打包脚本（推荐）

1. 在项目目录下运行打包脚本：

**macOS/Linux:**
```bash
./package.sh
```

**Windows (PowerShell):**
```powershell
.\package.ps1
```

2. 脚本会自动读取 `__init__.py` 中的版本号，并在**项目父目录**下生成 `gn_backdrop_vX.X.X.zip` 文件。

3. 在 Blender 中：
   - 编辑 > 偏好设置 > 插件
   - 点击右上角的 `安装...` 按钮
   - 选择生成的 zip 文件
   - 搜索 "Geometry Nodes Backdrop"
   - 勾选启用插件

### 方法二：手动打包

**重要：必须打包整个文件夹，而不是文件夹内的文件！**

在项目的**父目录**执行：
```bash
zip -r gn_backdrop.zip gn_backdrop -x "*.git*" -x "*__pycache__*" -x "*.DS_Store" -x "*.claude*"
```

确保 zip 文件内部结构为：
```
gn_backdrop.zip
  └── gn_backdrop/
      ├── __init__.py
      ├── backdrop_draw.py
      └── ...
```

而**不是**：
```
gn_backdrop.zip
  ├── __init__.py  ← 错误！不应该在顶层
  ├── backdrop_draw.py
  └── ...
```

## 使用方法

1. 打开几何节点编辑器
2. 在节点编辑器的头部（顶部工具栏）找到 **Backdrop** 按钮
3. 点击按钮即可开启/关闭背景显示

按钮状态：
- 按下状态（高亮）：Backdrop 已启用
- 未按下状态：Backdrop 已禁用

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
