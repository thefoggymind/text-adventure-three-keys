#!/usr/bin/env bash
#
# create_dist.sh - 配布用パッケージングスクリプト
#
# game.py, README.md, LICENSE を zip 形式でまとめます。
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

DIST_DIR="dist"
ZIP_NAME="text-adventure-game.zip"

echo "=== 配布パッケージ作成開始 ==="

mkdir -p "$DIST_DIR"

# Python 標準ライブラリ zipfile で圧縮
python3 << EOF
import os
import zipfile

dist_dir = "$DIST_DIR"
zip_name = "$ZIP_NAME"
files = ["game.py", "README.md", "LICENSE", "ISSUE_TEMPLATE.md", "ROADMAP.md"]

zip_path = os.path.join(dist_dir, zip_name)
with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
    for f in files:
        zf.write(f, arcname=os.path.basename(f))

print()
print(f"  {'Name':<30} {'Size':>10}")
print(f"  {'-'*30} {'-'*10}")
with zipfile.ZipFile(zip_path, "r") as zf:
    for info in zf.infolist():
        print(f"  {info.filename:<30} {info.file_size:>10}")
EOF

echo ""
echo "✓ パッケージ作成完了: $DIST_DIR/$ZIP_NAME"
echo ""
echo "=== 完了 ==="