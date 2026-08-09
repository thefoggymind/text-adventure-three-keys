#!/usr/bin/env bash
#
# post_publish.sh - 公開後処理の自動化スクリプト
#
# itch.io への公開完了後に以下の処理を一括実行します。
#   1. README.md の公開前注意書きを削除
#   2. 配布ZIPを再生成（bash create_dist.sh）
#
# 使い方:
#   bash post_publish.sh
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== 公開後処理を開始 ==="

# --------------------------------------------------
# 1. README.md の公開前注意書きを削除
# --------------------------------------------------
echo ""
echo "[1/2] README.md から公開前注意書きを削除中..."

sed -i 's/（⚠ 公開前のURLです。itch.ioへのアップロード完了後に有効になります。アップロード後は本カッコ書きを削除し、ZIPを再生成してください）//' README.md

echo "  → 削除完了"

# --------------------------------------------------
# 2. 配布ZIPを再生成
# --------------------------------------------------
echo ""
echo "[2/2] 配布ZIPを再生成中..."

bash create_dist.sh

echo ""
echo "=== 公開後処理が完了しました ==="
echo "README.md の注意書き削除と配布ZIPの再生成が完了しました。"
echo "あとは再生成された dist/text-adventure-game.zip を itch.io にアップロードしてください。"