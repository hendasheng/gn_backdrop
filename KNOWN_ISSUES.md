# 已知问题

## Blender 4.5 的 framebuffer 读取问题

在 Blender 4.5 中，`GPUFrameBuffer.read_color()` API 存在问题，无法正确读取完整的 framebuffer 数据。

### 问题表现

- 对于 1854×911 的视口，应该返回约 27 MB 的数据
- 但实际只返回 911 bytes（可能只是一行数据）
- 导致捕获的画面没有光影效果，只显示黑色轮廓

### 临时解决方案

由于这是 Blender 4.5 Python API 的限制，目前没有完美的解决方案。可能的选择：

1. **等待 Blender 4.5 API 修复**
2. **降级到 Blender 4.4**（如果该版本的 API 正常）
3. **使用 C/C++ 扩展**直接访问渲染引擎（需要编译）

### 技术细节

```python
# 期望的调用
buffer = fb.read_color(0, 0, width, height, 4, 0, 'FLOAT')

# 期望返回：width × height × 4 个 float 值
# 实际返回：height 个值（只有一行？）
```

这可能是 Blender 4.5 的 bug，或者 API 使用方式发生了变化但文档未更新。

### 相关链接

- Blender Python API 文档：https://docs.blender.org/api/current/
- 报告 bug：https://projects.blender.org/blender/blender/issues
