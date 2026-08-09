# デプロイ申請書 — Community Keeper (Discord Bot)

> **作成日**: 2026-08-09
> **プロジェクト種別**: Discord Bot（サーバー管理・コミュニティ活性化）
> **開発フェーズ**: Phase1〜Phase4 — 全実装完了・全268テスト通過・デプロイ準備完了

---

## 1. アプリケーション概要

**Community Keeper** は、Discord サーバーの管理とコミュニティ活性化を支援する多機能 Bot です。Python + discord.py で開発されており、SQLite をデータストアとして追加インフラ不要で動作します。

| 項目 | 内容 |
|------|------|
| **Bot名** | Community Keeper |
| **開発言語** | Python 3.10+ |
| **主要ライブラリ** | discord.py 2.3.0+ |
| **データベース** | SQLite3（標準ライブラリ、追加インストール不要） |
| **ホスティング想定** | Render 無料プラン（Web Service） |
| **収益モデル** | Freemium（無料 + Premium 月額500円、Phase2 実装済み） |
| **プレミアム機能** | リマインダー上限拡張・XP倍率カスタム・自動モデレーション・データエクスポート（全Phase2〜4実装済み） |
| **想定ユーザー** | 日本語圏の小〜中規模 Discord サーバー運営者（10〜500人） |

---

## 2. 機能一覧

### 2.1 ウェルカムメッセージ機能（実装済み）

| 機能 | 説明 |
|------|------|
| `on_member_join` | 新メンバー参加時にシステムチャンネルへ定型ウェルカムメッセージを送信 |
| `on_member_remove` | メンバー退出時にシステムチャンネルへ退出通知を送信 |
| 権限チェック | 送信権限がない場合は何も送信しない（安全設計） |

### 2.2 投票/アンケート機能（実装済み）

| コマンド | 説明 |
|---------|------|
| `/poll` | 質問と2〜10個の選択肢で投票を作成。リアクションで投票受付 |
| `/poll_result` | 投票IDを指定して結果を棒グラフ付き埋め込みで表示 |
| `/poll_list` | サーバー内のアクティブな投票一覧を表示 |

**オプション機能**:
- `--duration N` : 投票の有効期間を分単位で指定（期限切れ後は自動締切）
- `--anonymous` : 匿名投票モード（投票者を記録せず、リアクション数のみカウント）

### 2.3 リマインダー機能（実装済み）

| コマンド | 説明 |
|---------|------|
| `/remind` | 絶対日時指定でリマインダーを設定（例: `2026-08-10 15:00`） |
| `/remind_in` | 相対時間指定でリマインダーを設定（例: `30分`, `2時間`, `1日`） |
| `/reminders` | 自分のアクティブなリマインダー一覧を確認（本人のみ表示） |
| `/cancel_reminder` | 指定IDのリマインダーを削除（本人のみ、所有権チェック付き） |

**バックグラウンド動作**: 60秒間隔のループで期限切れリマインダーを検出し、DM または元チャンネルに通知を送信します。

### 2.4 XP/レベルシステム（実装済み）

| コマンド | 説明 |
|---------|------|
| `(自動)` | メッセージ送信時に XP を付与（15〜25 XP、60秒クールダウン） |
| `/rank` | 自分のレベル・XP・サーバー内順位を表示（他ユーザー指定可） |
| `/leaderboard` | サーバー内 XP トップ10 を表示 |

**レベル計算式**: `レベル = xp < 100 → 1, 以降 n² × 100 でレベルアップ`
- レベル1: 0〜99 XP
- レベル2: 100〜399 XP
- レベル3: 400〜899 XP
- レベル4: 900〜1599 XP
- ...

### 2.5 Premium 機能（Phase2〜4、全実装済み）

| 機能 | 区分 | 説明 |
|------|------|------|
| **Stripe購読管理** | Phase2 | `/premium` コマンドで Stripe Checkout Session を生成、Webhook で購読状態管理 |
| **プレミアム設定** | Phase2 | `/premium config` でリマインダー上限（max_reminders）・XP倍率（xp_rate_multiplier）をギルド単位で設定 |
| **自動モデレーション** | Phase3 | `/moderation` コマンドグループ: NGワードフィルター + スパム検出（Premium必須） |
| **データエクスポート** | Phase4 | `/export` コマンドで XP・リマインダー・モデレーション設定・購読情報を CSV/JSON/DM で出力 |

### 2.6 今後の拡張予定（未実装）

| フェーズ | 機能 | 時期 |
|---------|------|------|
| Phase5 | カスタムロール XP 連携 | 未着手 |
| Phase5 | Web 管理ダッシュボード | 未着手 |

---

## 3. ファイル構成

```
project/
├── bot.py                 # エントリーポイント（Bot 起動）
├── requirements.txt       # 依存関係（discord.py, aiosqlite）
├── .env.example           # 環境変数テンプレート（DISCORD_BOT_TOKEN, DATABASE_PATH）
├── data/                  # SQLite データベース格納ディレクトリ（自動生成）
│   ├── community_keeper.db     # 各種データ（レベル、reminder、moderation、premium 等）
│   └── moderation_logs.db      # モデレーションログDB
│
├── utils/
│   ├── __init__.py
│   ├── db.py              # DB接続管理
│   ├── levels.py          # レベル計算ロジック（XP→level変換）
│   └── roles.py           # ロール管理（手動付与ロール自動復元）
│
├── cogs/
│   ├── __init__.py
│   ├── greet.py           # 参加・退出メッセージ
│   ├── polls.py           # 投票作成・管理
│   ├── reminders.py       # リマインダー（繰り返し対応）
│   ├── xp.py              # XP 管理（音声・メッセージXP）
│   ├── levels.py          # レベル・ロール管理
│   ├── admin.py           # 管理コマンド（権限チェック）
│   └── errors.py          # エラーハンドリング
│
├── premium/
│   ├── __init__.py
│   ├── premium_cog.py     # Premium コマンド（/premium, /premium config）
│   ├── premium_db.py      # Premium 購読管理DB
│   ├── moderation_cog.py  # モデレーションコマンド（/moderation: ngword/spam）
│   ├── moderation_db.py   # モデレーション設定・ログDB
│   ├── export_cog.py      # エクスポートコマンド（/export: xp/reminders/moderation/subscription）
│   └── export_db.py       # エクスポート用データ取得
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py        # 共通テストフィクスチャ（Bot, guild, member, interaction モック）
│   ├── test_db.py         # DB接続テスト（4 tests）
│   ├── test_levels.py     # レベル計算テスト（6 tests）
│   ├── test_roles.py      # ロール管理テスト（6 tests）
│   ├── test_greet.py      # 参加退出メッセージ（23 tests）
│   ├── test_polls.py      # 投票管理テスト（26 tests）
│   ├── test_reminders.py  # リマインダーテスト（27 tests）
│   ├── test_xp.py         # XP管理テスト（18 tests）
│   ├── test_levels_cog.py # レベルCogテスト（18 tests）
│   ├── test_admin.py      # 管理コマンドテスト（27 tests）
│   ├── test_premium_db.py     # Premium DB テスト（13 tests）
│   ├── test_premium_cog.py    # Premium Cog テスト（37 tests）
│   ├── test_moderation_db.py  # モデレーションDBテスト（13 tests）
│   ├── test_moderation_cog.py # モデレーションCogテスト（18 tests）
│   ├── test_export_db.py      # エクスポートDBテスト（18 tests）
│   └── test_export_cog.py     # エクスポートCogテスト（14 tests）
│
├── README.md              # プロジェクト説明 + デプロイ手順
├── PROPOSAL_FOR_DEPLOY.md # 本デプロイ申請書
└── PUBLISH_GUIDE.md       # テキストアドベンチャー「3つの鍵」公開ガイド
```

---

## 4. 実行手順

### 4.1 前提条件

- Python 3.10 以上がインストールされていること
- Discord Developer Portal で Bot アプリケーションを作成し、トークンを発行済みであること
- Bot の Privileged Gateway Intents（`MEMBER INTENT`, `MESSAGE CONTENT INTENT`）が有効化されていること

### 4.2 セットアップ手順

```bash
# 1. 依存パッケージのインストール
pip install -r requirements.txt

# 2. 環境変数の設定
cp .env.example .env
# .env ファイルを編集し、DISCORD_BOT_TOKEN に発行されたトークンを設定

# 3. Bot の起動
python bot.py
```

### 4.3 期待される起動ログ

```
✅ Community Keeper 起動完了
   Bot名: Community Keeper
   BotID: 123456789012345678
   サーバー数: 1
   ✅ スラッシュコマンド同期完了
```

### 4.4 Bot 招待手順

1. Discord Developer Portal の `OAuth2 > URL Generator` で以下を選択:
   - Scopes: `bot`, `applications.commands`
   - Bot Permissions: `Send Messages`, `Read Message History`, `Add Reactions`, `Embed Links`
2. 生成された URL をブラウザで開き、導入したいサーバーを選択
3. サーバー内で `/poll`, `/remind`, `/rank`, `/leaderboard` が使用可能になる

### 4.5 Render デプロイ手順（推奨）

| 設定項目 | 値 |
|---------|-----|
| Runtime | Python 3 |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `python bot.py` |
| 環境変数 | `DISCORD_BOT_TOKEN`（必須） |

詳細は `README.md` の「Render（無料プラン）へのデプロイ手順」セクションを参照してください。

---

## 5. テスト結果

全 **268 テスト** がパス済みです（最終確認: 2026-08-09／タスク38c）。

| フェーズ | テストファイル | テスト数 | 結果 |
|---------|--------------|---------|------|
| **Phase1** | `test_db.py` — DB接続 | 4 | ✅ |
| | `test_levels.py` — レベル計算 | 6 | ✅ |
| | `test_roles.py` — ロール管理 | 6 | ✅ |
| | `test_greet.py` — 参加退出メッセージ | 23 | ✅ |
| | `test_polls.py` — 投票管理 | 26 | ✅ |
| | `test_reminders.py` — リマインダー | 27 | ✅ |
| | `test_xp.py` — XP管理 | 18 | ✅ |
| | `test_levels_cog.py` — レベルCog | 18 | ✅ |
| | `test_admin.py` — 管理コマンド | 27 | ✅ |
| | **Phase1 小計** | **155** | **✅** |
| **Phase2** | `test_premium_db.py` — Premium DB | 13 | ✅ |
| | `test_premium_cog.py` — Premium Cog | 37 | ✅ |
| | **Phase2 小計** | **50** | **✅** |
| **Phase3** | `test_moderation_db.py` — モデレーションDB | 13 | ✅ |
| | `test_moderation_cog.py` — モデレーションCog | 18 | ✅ |
| | **Phase3 小計** | **31** | **✅** |
| **Phase4** | `test_export_db.py` — エクスポートDB | 18 | ✅ |
| | `test_export_cog.py` — エクスポートCog | 14 | ✅ |
| | **Phase4 小計** | **32** | **✅** |
| **全Phases** | **総合計** | **268** | **✅ 全件パス** |

**テスト範囲（全Phase共通）**:
- データベース初期化・WALモード確認
- CRUD 全操作（作成・取得・更新・削除）
- バリデーション（存在確認・権限チェック・重複防止）
- クールダウン制御（XP重複付与防止）
- レベル計算ロジック（境界値テスト）
- リーダーボード・ランキング計算
- エッジケース（空データ・存在しないユーザー・二重削除など）
- E2E（全操作を組み合わせた一貫性テスト）
- Python コンパイルチェック（各モジュール）
- モック Discord 環境でのスラッシュコマンド実行テスト（conftest.py 共通フィクスチャ）
- Premium購読判定・Stripe Webhook 処理フロー
- NGワードフィルター・スパム検出ロジック
- CSV/JSON/DMエクスポート出力確認

---

## 6. 注意事項

### 6.1 データベース永続性

- 本 Bot は **SQLite** をデータストアとして使用します
- Render 無料プランは **エフェメラルストレージ**（再起動時にデータ消失）です
- **本番運用には Render Persistent Disk（$7/月）の追加、または外部データベースへの移行を推奨します**
- テスト・評価目的であれば無料プランでも十分です

### 6.2 スリープ問題

- Render 無料プランは **15分間の無アクセスで自動スリープ** します
- Bot は HTTP サーバーではないため、通常の uptime monitoring ではスリープ防止できません
- 回避策: 別途 Web エンドポイントを追加するか、有料プランへの移行を検討してください

### 6.3 月間稼働時間制限

- Render 無料プランは月間 **750時間** の制限があります
- 24時間稼働の場合、約31日（744時間）でほぼ上限に達します
- 複数サービスを同一アカウントで運用する場合は時間が共有される点に注意

### 6.4 環境変数とセキュリティ

- `DISCORD_BOT_TOKEN` は**必ず環境変数**から読み込んでください（`.env` やコードにハードコードしない）
- `DATABASE_PATH` は省略可能（デフォルト: `data/community_keeper.db`）。省略時は bot.py と同じディレクトリの `data/` が使われます
- Render ダッシュボードの Environment Variables 機能を使用してトークンを設定してください
- テスト用のダミートークンはコミットしないでください

### 6.5 Premium（Stripe）運用時の注意

- Premium 機能を本番運用するには、Stripe アカウント登録と Stripe API キーの取得が必要です
- Stripe Webhook エンドポイントを公開 URL（例: `https://your-app.onrender.com/webhook/stripe`）に設定してください
- Webhook 署名シークレット（`STRIPE_WEBHOOK_SECRET`）も環境変数に追加してください
- テストモードの Stripe キーで動作確認後、本番キーに切り替えることを推奨します
- 無料プランでは全機能（XP・リマインダー上限あり）が利用可能です。プレミアム特典として上限緩和・倍率設定・モデレーション・エクスポートが有効になります

### 6.6 Discord API 変更への対応

- discord.py のアップデートに追従するため、定期的なメンテナンスが必要です
- Discord の Gateway Intents や API 仕様が変更された場合、コードの修正が必要になる可能性があります

### 6.6 運用監視

- 標準エラー出力（stderr）にログが出力されます。Render ダッシュボードの Logs タブで確認可能
- 現在のバージョンでは専用の死活監視・エラー通知機能は未実装です
- 本番運用時は別途ログ監視・エラー通知の仕組みを導入することを推奨します

---

## 7. 参考リンク

- [discord.py ドキュメント](https://discordpy.readthedocs.io/)
- [Discord Developer Portal](https://discord.com/developers/applications)
- [Render Dashboard](https://dashboard.render.com)
- [SPEC.md](../SPEC.md) — 詳細設計書
- [README.md](README.md) — セットアップ手順・デプロイ手順