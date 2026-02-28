# 使用说明

## 快速开始

### 1. 打包插件

**重要提示：**
- 必须在 `gn_backdrop` 文件夹内运行打包脚本
- 生成的 zip 文件会在父目录
- zip 内部必须包含 `gn_backdrop` 文件夹，而不是直接包含文件

**使用打包脚本（推荐）：**

**macOS/Linux:**
```bash
cd gn_backdrop
./package.sh
```

**Windows (PowerShell):**
```powershell
cd gn_backdrop
.\package.ps1
```

**手动打包：**

在项目的**父目录**执行：
```bash
zip -r gn_backdrop.zip gn_backdrop -x "*.git*" -x "*__pycache__*" -x "*.DS_Store" -x "*.claude*"
```

**验证 zip 结构：**
```bash
unzip -l gn_backdrop.zip
```

应该看到：
```
gn_backdrop/
gn_backdrop/__init__.py
gn_backdrop/backdrop_draw.py
...
```

而**不是**：
```
__init__.py  ← 错误！
backdrop_draw.py
...
```

### 2. 安装插件

1. 打开 Blender
2. 编辑 > 偏好设置 > 插件
3. 点击右上角的 `安装...` 按钮
4. 选择 `gn_backdrop.zip` 文件
5. 搜索 "Geometry Nodes Backdrop"
6. 勾选启用插件

### 3. 使用

1. 打开几何节点编辑器
2. 在节点编辑器的头部（顶部工具栏）找到 **Backdrop** 按钮
3. 点击按钮即可开启/关闭背景显示

**提示：**
- 按钮按下（高亮）时表示 Backdrop 已启用
- 确保 3D 视图和几何节点编辑器同时可见才能看到效果
- 可以通过分屏或多窗口方式同时显示两个编辑器

## 工作原理

1. 插件在 3D 视图的绘制回调中捕获 framebuffer 内容
2. 将捕获的内容存储为 GPU 纹理
3. 在几何节点编辑器的背景中绘制这个纹理

## 注意事项

1. **性能影响**：实时捕获和绘制会消耗一定的 GPU 资源
2. **同步问题**：3D 视图和节点编辑器需要同时可见才能正常工作
3. **API 限制**：由于 Blender Python API 的限制，某些高级渲染特性可能无法完全捕获

## 故障排除

### 背景不显示

- 确保同时打开了 3D 视图和几何节点编辑器
- 确保已经执行了 toggle 命令启用功能
- 检查 Blender 控制台是否有错误信息

### 性能问题

- 降低视口的采样数
- 关闭不必要的叠加层
- 使用较小的窗口尺寸

### 显示不正确

- 尝试重新 toggle（关闭再打开）
- 重启 Blender
- 检查 Blender 版本是否为 4.5+

## 开发

如果你想修改或扩展这个插件：

1. 主要逻辑在 `backdrop_draw.py` 中
2. `capture_view3d_framebuffer()` 负责捕获 3D 视图
3. `draw_backdrop()` 负责在节点编辑器中绘制

## 已知问题

1. framebuffer 读取在某些情况下可能失败
2. 纹理格式可能需要根据不同的 GPU 调整
3. 多窗口支持可能不完善

## 未来改进

- [ ] 添加 UI 面板
- [ ] 添加缩放和平移控制
- [ ] 优化性能
- [ ] 支持多窗口
- [ ] 添加更多配置选项
