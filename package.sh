#!/bin/bash

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 读取版本号
VERSION=$(grep '"version":' __init__.py | sed -E 's/.*: \(([0-9]+), ([0-9]+), ([0-9]+)\),/\1.\2.\3/')
ADDON_NAME="gn_backdrop"
# 输出到父级目录
PARENT_DIR="$(dirname "$SCRIPT_DIR")"
OUTPUT_FILE="$PARENT_DIR/${ADDON_NAME}_v${VERSION}.zip"

# 定义需要打包的文件列表（白名单模式）
FILES_TO_PACKAGE=(
    "__init__.py"
    "backdrop_draw.py"
    "LICENSE"
    "README.md"
)

# 创建临时构建目录
BUILD_DIR="$SCRIPT_DIR/build_temp"
rm -rf "$BUILD_DIR"
TARGET_DIR="$BUILD_DIR/$ADDON_NAME"
mkdir -p "$TARGET_DIR"

echo "正在打包 $ADDON_NAME v$VERSION ..."
echo "输出文件: $OUTPUT_FILE"

# 复制文件到临时目录
for file in "${FILES_TO_PACKAGE[@]}"; do
    if [ -e "$file" ]; then
        cp -r "$file" "$TARGET_DIR/"
    else
        echo "⚠️ 警告: 文件 $file 未找到，跳过"
    fi
done

# 打包
cd "$BUILD_DIR"
# 删除旧文件
if [ -f "$OUTPUT_FILE" ]; then
    rm "$OUTPUT_FILE"
fi
zip -r "$OUTPUT_FILE" "$ADDON_NAME" > /dev/null

# 清理
cd "$SCRIPT_DIR"
rm -rf "$BUILD_DIR"

echo ""
if [ -f "$OUTPUT_FILE" ]; then
    echo "✅ 打包成功: $OUTPUT_FILE"
    echo "文件大小: $(du -h "$OUTPUT_FILE" | cut -f1)"
    echo "包含文件:"
    unzip -l "$OUTPUT_FILE" | grep "$ADDON_NAME/"
else
    echo "❌ 打包失败"
    exit 1
fi
