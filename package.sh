#!/bin/bash
# 打包 Blender 插件脚本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PARENT_DIR="$(dirname "$SCRIPT_DIR")"
ADDON_NAME="gn_backdrop"
OUTPUT_FILE="$PARENT_DIR/${ADDON_NAME}.zip"

echo "正在打包插件..."
echo "源目录: $SCRIPT_DIR"
echo "输出文件: $OUTPUT_FILE"

cd "$PARENT_DIR"

# 删除旧的 zip 文件（如果存在）
if [ -f "$OUTPUT_FILE" ]; then
    rm "$OUTPUT_FILE"
    echo "已删除旧的 zip 文件"
fi

# 打包，排除不必要的文件
zip -r "$OUTPUT_FILE" "$ADDON_NAME" \
    -x "*.git*" \
    -x "*__pycache__*" \
    -x "*.pyc" \
    -x "*.DS_Store" \
    -x "*package.sh" \
    -x "*package.ps1"

if [ $? -eq 0 ]; then
    echo "✓ 打包成功: $OUTPUT_FILE"
    echo "现在可以在 Blender 中安装此文件"
else
    echo "✗ 打包失败"
    exit 1
fi
