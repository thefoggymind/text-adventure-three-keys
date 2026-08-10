# SPEC: Discord Bot「Community Keeper」

> 作成日: 2026-08-09
> 選定元: PROPOSAL.md 候補A（Discord Bot + プレミアム機能）
> 選定理由: 初期投資不要・Python完結・低コスト公開・サブスク課金で継続収益可能

---

## 1. プロジェクト概要

### 1.1 コンセプト
Discordサーバーの管理・コミュニティ活性化を支援する多機能Bot。
ウェルカムメッセージ、投票/アンケート、リマインダー、XP/レベルシステムを提供。
**Freemiumモデル**で基本機能は無料、高度なカスタマイズ機能を月額課金で提供する。

### 1.2 ターゲットユーザー
- **一次**: 日本語圏の小規模〜中規模Discordサーバー運営者（10〜500人規模）
  - ゲームコミュニティ、勉強会、サークル、趣味の集まり
- **二次**: 多サーバーを管理するパワーユーザー（プレミアム課金が見込める層）

### 1.3 差別化ポイント
| 観点 | 競合（汎用Bot） | Community Keeper |
|------|----------------|------------------|
| 言語 | 英語UI中心 | **日本語完全対応** |
| 設定 | 複雑な管理画面 | **シンプルなスラッシュコマンド** |
| 課金 | 高額プランあり | **低価格（月額500円〜）** |
| XP機能 | 独立Botが必要 | **内蔵で完結** |

---

## 2. 機能仕様

### 2.1 機能一覧（MVP）

| # | 機能 | 無料 | Premium | 説明 |
|---|------|------|---------|------|
| 1 | ウェルカムメッセージ | ✅ 定型文 | ✅ カスタム埋め込み | 新規メンバー参加時の自動メッセージ |
| 2 | 投票/アンケート | ✅ 基本投票 | ✅ 匿名・複数選択 | リアクション投票の作成・管理 |
| 3 | リマインダー | ✅ 1日3件まで | ✅ 無制限 | 指定日時・定期リマインダー |
| 4 | XP/レベルシステム | ✅ 基本表示 | ✅ カスタムロール | メッセージ活性度に応じたレベル |
| 5 | 自動モデレーション | — | ✅ ワードフィルター | スパム・NGワードの自動管理 |
| 6 | データエクスポート | — | ✅ CSV/JSON | サーバー統計の書き出し |

### 2.2 各機能の詳細

#### 2.2.1 ウェルカムメッセージ
- **トリガー**: 新メンバーがサーバーに参加したとき
- **動作**:
  - 指定チャンネルにメッセージを送信
  - 無料: 定型文「{ユーザー名}さん、ようこそ！{サーバー名}へ」
  - Premium: カスタムメッセージ + 埋め込み(Embed) + 画像設定可能
- **設定コマンド**: `/welcome set-channel`, `/welcome set-message`, `/welcome test`
- **データ保存**: サーバーIDごとに設定をSQLite保存

#### 2.2.2 投票/アンケート
- **コマンド**: `/poll "質問" "選択肢1" "選択肢2" [選択肢3...]`
- **機能**:
  - 最大10個の選択肢
  - 投票後、結果をリアルタイム集計
  - Premium: 匿名投票、複数選択可、期限設定可
- **出力**: Embed + リアクション（🇦🇧🇨...）

#### 2.2.3 リマインダー
- **コマンド**: `/remind set "内容" "2026-08-10 15:00"`
- **定期リマインダー**: `/remind repeat "内容" "daily" "09:00"`
- **制限**: 無料=3件/サーバー, Premium=無制限
- **保存**: SQLite（Bot再起動後も永続）

#### 2.2.4 XP/レベルシステム
- **仕組み**:
  - メッセージ1件につき XP +1（同一チャンネルでは60秒に1回まで）
  - レベル = floor(sqrt(total_xp / 10))
  - レベルアップ時にメンション通知（任意）
- **コマンド**: `/level`（自分のレベル表示）, `/leaderboard`（サーバーTOP10）
- **Premium**: レベルごとに自動付与ロール設定、XP付与率カスタマイズ

#### 2.2.5 自動モデレーション（Premium）
- **機能**: NGワードフィルター、スパム検知（同一メッセージ連投）
- **設定**: `/mod add-word`, `/mod remove-word`, `/mod list-words`
- **動作**: 該当メッセージを自動削除 + モデレーターチャンネルにログ送信

#### 2.2.6 データエクスポート（Premium）
- **コマンド**: `/export xp`（XPデータCSV）, `/export stats`（統計JSON）
- **形式**: CSV / JSON、DMでファイル送信

---

## 3. 技術仕様

### 3.1 技術スタック

| レイヤー | 技術 | バージョン | 備考 |
|---------|------|-----------|------|
| 言語 | Python | 3.10+ | 型ヒント活用 |
| Botライブラリ | discord.py | 2.4+ | スラッシュコマンド対応 |
| データベース | SQLite3 (標準ライブラリ) | — | 追加インストール不要 |
| 非同期 | asyncio | 標準 | discord.py標準のイベントループ |
| 決済 | Stripe | — | Premium購読管理（Phase2で実装） |
| ホスティング | Render / Koyeb 無料枠 | — | Phase1は無料枠で運用 |

### 3.2 システム構成

```
┌──────────────────────────────────┐
│         Discord API              │
└──────────┬───────────────────────┘
           │  Gateway Intents
┌──────────▼───────────────────────┐
│   Community Keeper Bot           │
│   (Python + discord.py)          │
│                                  │
│   ┌────────────────────────┐     │
│   │   Command Cog Layer    │     │
│   │  welcome / poll /     │     │
│   │  remind / level / mod │     │
│   └──────────┬─────────────┘     │
│              │                   │
│   ┌──────────▼─────────────┐     │
│   │   Service Layer        │     │
│   │  (ビジネスロジック)     │     │
│   └──────────┬─────────────┘     │
│              │                   │
│   ┌──────────▼─────────────┐     │
│   │   Data Layer (SQLite)  │     │
│   │  guilds.db / xp.db     │     │
│   └────────────────────────┘     │
└──────────────────────────────────┘
```

### 3.3 ディレクトリ構成

```
/workspace/community-keeper/
├── main.py                 # Botエントリポイント
├── config.py               # 設定・トークン管理
├── database.py             # SQLite操作 (接続・初期化・CRUD)
├── cogs/
│   ├── __init__.py
│   ├── welcome.py          # ウェルカムメッセージ機能
│   ├── poll.py             # 投票/アンケート機能
│   ├── remind.py           # リマインダー機能
│   ├── level.py            # XP/レベルシステム
│   └── moderation.py       # 自動モデレーション (Premium)
├── utils/
│   ├── __init__.py
│   ├── embeds.py           # Embed ヘルパー
│   └── checks.py           # 権限チェック・プレミアム判定
├── premium/
│   ├── __init__.py
│   └── stripe_webhook.py   # Stripe決済Webhook (Phase2)
├── requirements.txt        # discord.py のみ (最小構成)
└── README.md               # セットアップ・使い方
```

### 3.4 データベース設計（SQLite）

#### Table: guild_config
| カラム | 型 | 説明 |
|--------|------|------|
| guild_id | INTEGER PK | DiscordサーバーID |
| premium | INTEGER | 0=無料, 1=Premium |
| premium_since | TEXT | 課金開始日 (ISO8601) |
| welcome_channel_id | INTEGER | ウェルカムチャンネルID |
| welcome_message | TEXT | カスタムメッセージ (NULL=定型文) |
| welcome_embed_color | TEXT | Embed色 (#RRGGBB, Premium only) |
| mod_log_channel_id | INTEGER | モデレーションログ送信先 |
| created_at | TEXT | 設定作成日 |

#### Table: reminders
| カラム | 型 | 説明 |
|--------|------|------|
| id | INTEGER PK AUTO | — |
| guild_id | INTEGER | サーバーID |
| channel_id | INTEGER | 送信先チャンネル |
| author_id | INTEGER | 作成者 |
| content | TEXT | リマインダー内容 |
| remind_at | TEXT | 実行日時 (ISO8601) |
| repeat_interval | TEXT | 繰り返し間隔 (NULL=1回, 'daily', 'weekly') |
| done | INTEGER | 0=未, 1=完了 |

#### Table: xp_data
| カラム | 型 | 説明 |
|--------|------|------|
| guild_id | INTEGER PK | サーバーID |
| user_id | INTEGER PK | ユーザーID |
| total_xp | INTEGER | 累計XP |
| last_message_at | TEXT | 最終メッセージ日時 (クールダウン用) |

#### Table: ng_words
| カラム | 型 | 説明 |
|--------|------|------|
| guild_id | INTEGER PK | サーバーID |
| word | TEXT PK | NGワード |

### 3.5 主要コマンド一覧

| コマンド | 引数 | 権限 | 説明 |
|---------|------|------|------|
| `/welcome set-channel` | channel | Manage Server | ウェルカムチャンネル設定 |
| `/welcome set-message` | message | Manage Server | カスタムメッセージ設定 (Premium) |
| `/welcome test` | — | Manage Server | テスト送信 |
| `/poll` | question, options... | — | 投票作成 |
| `/remind set` | content, datetime | — | リマインダー設定 |
| `/remind list` | — | — | 自分のリマインダー一覧 |
| `/remind cancel` | id | — | リマインダー削除 |
| `/level` | [user] | — | レベル表示 |
| `/leaderboard` | — | — | サーバーランキング |
| `/mod add-word` | word | Manage Server | NGワード追加 (Premium) |
| `/mod remove-word` | word | Manage Server | NGワード削除 (Premium) |
| `/export xp` | — | Manage Server | XPデータ出力 (Premium) |
| `/help` | — | — | Bot使い方表示 |

---

## 4. 収益化設計

### 4.1 価格体系

| プラン | 価格 | 主要制限 |
|--------|------|---------|
| Free | 無料 | リマインダー3件まで、ウェルカム定型文のみ、モデレーションなし |
| Premium | 月額 **500円** | 全機能無制限、カスタム設定可能 |

### 4.2 決済フロー（Phase2実装）
1. ユーザーが `/premium` コマンドを実行
2. BotがStripe Checkout SessionのURLをDM送信
3. ユーザーがStripeページで決済
4. Stripe Webhook → Botが `guild_config.premium = 1` に更新
5. プレミアム機能が即時有効化

### 4.3 収益予測（楽観）
| サーバー数 | Premium転換率 | 月収 |
|-----------|-------------|------|
| 100 | 5% (5サーバー) | 2,500円 |
| 500 | 3% (15サーバー) | 7,500円 |
| 1,000 | 2% (20サーバー) | 10,000円 |
| 5,000 | 1% (50サーバー) | 25,000円 |

---

## 5. 開発ロードマップ

### Phase 1: MVP (1〜2週間)
- [ ] discord.py プロジェクトのセットアップ
- [ ] SQLiteデータベース層の実装
- [ ] ウェルカムメッセージ機能
- [ ] 投票/アンケート機能
- [ ] リマインダー機能（基本）
- [ ] XP/レベルシステム（基本）
- [ ] `/help` コマンド
- [ ] Render/Koyeb 無料枠へのデプロイ
- [ ] 動作確認・バグ修正

### Phase 2: 収益化 (3〜4週目)
- [ ] Premium判定システム
- [ ] Stripe Checkout Session 統合
- [ ] Stripe Webhook 実装
- [ ] プレミアム機能のゲート実装
- [ ] データエクスポート機能

### Phase 3: 拡充 (5〜8週目)
- [ ] 自動モデレーション機能
- [ ] カスタムロールXP連携
- [ ] Web管理ダッシュボード（任意）
- [ ] プロモーション・公開

---

## 6. 運用設計

### 6.1 ホスティング
- **Phase1**: Render無料枠（Web Service, 月750時間）または Koyeb無料枠
  - 軽量Botなら無料枠で十分動作可能
- **スケール時**: Render有料プラン（月額7USD〜）に移行

### 6.2 監視・ログ
- **ログ**: 標準出力にJSONログ出力（後日ログ集約サービスと連携可能）
- **死活監視**: Render/Koyebの自動ヘルスチェック（無料枠に内蔵）
- **エラー通知**: Discordの管理チャンネルにエラー内容を投稿

### 6.3 バックアップ
- SQLiteファイルの定期バックアップ（1日1回、cronでtar.gz圧縮）
- 復旧手順をREADME.mdに記載

### 6.4 コスト試算（月額）
| 項目 | Free運用時 | スケール時 |
|------|-----------|-----------|
| ホスティング | 0円 | 7USD (~1,050円) |
| ドメイン | 0円 | 0円（Discord Botに不要） |
| データベース | 0円（SQLite） | 0円（SQLite） |
| Stripe手数料 | — | 3.6% + 40円/件 |
| **合計** | **0円** | **〜1,100円 + 決済手数料** |

---

## 7. リスクと対策

| リスク | 確率 | 影響 | 対策 |
|--------|------|------|------|
| Discord API変更 | 低 | 大 | discord.pyのアップデート追従、公式ドキュメント監視 |
| ユーザー獲得難航 | 高 | 中 | 日本語コミュニティ向けに特化、Discord Botリストに登録 |
| サーバー負荷増大 | 低 | 中 | SQLite→PostgreSQL移行を視野、キャッシュ導入 |
| 決済トラブル | 低 | 中 | Stripeテスト環境で十分な事前検証、返金ポリシー明確化 |
| 競合Botの台頭 | 中 | 中 | ユーザーフィードバックを最優先、ニッチ機能で差別化継続 |

---

## 8. 公開計画

### 8.1 公開チャネル
- **一次**: Discord Bot List (DISBOARD, top.gg 等) に登録
- **二次**: 日本語フォーラム（Discord Bot 日本語サーバー、Qiita等）で紹介
- **三次**: GitHub公開（READMEに導入方法を記載）

### 8.2 導入手順（ユーザー視点）
1. [Bot招待リンク] をクリック
2. サーバーを選択し「許可」をクリック
3. サーバーで `/help` を実行して機能確認
4. 各機能を `/コマンド` で設定して利用開始

### 8.3 KPI目標
| 指標 | 1ヶ月後 | 3ヶ月後 | 6ヶ月後 |
|-----|---------|---------|---------|
| 導入サーバー数 | 50 | 200 | 500 |
| Premium契約数 | 3 | 10 | 20 |
| 月収 | 1,500円 | 5,000円 | 10,000円 |

---

## 9. 開発ルール

- **コーディング規約**: PEP 8準拠、型ヒント必須
- **コミットメッセージ**: `feat:` / `fix:` / `refactor:` プレフィックス
- **テスト**: 各Cogのユニットテスト（pytest）を作成
- **ドキュメント**: 全コマンドに `/help` 出力用の説明文を実装
- **セキュリティ**: Botトークンは環境変数から読み込み、Git管理しない

---

## 10. Phase2 収益化機能 詳細設計

### 10.1 概要

Phase2ではFreemiumモデルを実現するため、Stripe決済統合とプレミアム管理機能を実装する。
無料ユーザーには基本機能を提供し、月額500円のPremiumプランで全機能をアンロックする構造。

**設計方針**:
- Premiumは **サーバー単位** で契約（1サーバー = 1サブスクリプション）
- 支払いはサーバー管理者が行い、Stripe Customer + Subscription で管理
- 認可はサーバーID + 有効期限で判定し、コマンド実行時にチェック
- Stripeのテストモードを標準開発環境とし、本番はライブモードに切り替え

### 10.2 データベース設計（追加テーブル）

既存の `guild_config` テーブル（SPEC 3.4節）に加え、以下のテーブルを `premium.db` に作成する。

#### Table: premium_subscriptions

| カラム | 型 | 制約 | 説明 |
|--------|------|------|------|
| id | INTEGER | PK AUTO | 内部ID |
| guild_id | INTEGER | NOT NULL UNIQUE | DiscordサーバーID |
| owner_id | INTEGER | NOT NULL | 契約者（管理者）のDiscord User ID |
| stripe_customer_id | TEXT | NOT NULL | Stripe Customer ID (cus_xxx) |
| stripe_subscription_id | TEXT | NOT NULL | Stripe Subscription ID (sub_xxx) |
| status | TEXT | NOT NULL DEFAULT 'active' | 'active' / 'past_due' / 'canceled' / 'incomplete' |
| current_period_start | TEXT | — | 現在の契約開始日 (ISO8601) |
| current_period_end | TEXT | — | 現在の契約終了日 (ISO8601) |
| canceled_at | TEXT | — | 解約日 (ISO8601, NULL=有効) |
| created_at | TEXT | NOT NULL | レコード作成日 (ISO8601) |
| updated_at | TEXT | NOT NULL | レコード更新日 (ISO8601) |

**インデックス**:
- `idx_premium_guild_id` ON `premium_subscriptions(guild_id)`
- `idx_premium_stripe_customer` ON `premium_subscriptions(stripe_customer_id)`
- `idx_premium_status` ON `premium_subscriptions(status)`

#### Table: stripe_events

| カラム | 型 | 制約 | 説明 |
|--------|------|------|------|
| id | TEXT | PK | Stripe Event ID (evt_xxx) |
| type | TEXT | NOT NULL | イベント種別（例: checkout.session.completed）|
| processed_at | TEXT | NOT NULL | 処理日時 (ISO8601) |
| status | TEXT | NOT NULL DEFAULT 'processed' | 'processed' / 'failed' |

**目的**: Stripe Webhookの冪等性担保 — 同一イベントの重複処理を防止する。

#### Table: guild_premium_config

既存の `guild_config` に含まれるプレミアム関連カラムを拡張する形で、個別設定テーブルも用意する。

| カラム | 型 | 制約 | 説明 |
|--------|------|------|------|
| guild_id | INTEGER | PK | DiscordサーバーID |
| welcome_embed_json | TEXT | — | カスタムウェルカム埋め込み設定 (JSON, Premium only) |
| xp_role_mappings | TEXT | — | レベル→ロール自動付与マッピング (JSON, Premium only) |
| xp_rate_multiplier | REAL | DEFAULT 1.0 | XP付与率倍率 (Premium only) |
| max_reminders | INTEGER | DEFAULT 3 | リマインダー上限 (Premium=0で無制限) |
| anonymous_polls | INTEGER | DEFAULT 0 | 匿名投票利用可否 (Premium=1で許可) |
| multiple_vote_polls | INTEGER | DEFAULT 0 | 複数選択投票可否 (Premium=1で許可) |

`max_reminders=0` は「無制限」を意味する。無料サーバーは `max_reminders=3` 固定。

### 10.3 Stripe決済統合

#### 10.3.1 利用するStripe製品

| 項目 | 値 |
|------|-----|
| 製品名 | Community Keeper Premium |
| 価格 | 月額 500円 (price_live_xxx / price_test_xxx) |
| 通貨 | jpy |
| 課金周期 | 每月（月頭請求） |
| 支払い方法 | クレジットカード (Stripeデフォルト) |

Stripeダッシュボード上で以下の設定が必要:
1. Product作成: "Community Keeper Premium"
2. Price作成: 500 JPY / 月 (recurring)
3. Price ID (`price_xxx`) を環境変数 `STRIPE_PRICE_ID` に設定

#### 10.3.2 ディレクトリ構成

```
/workspace/project/
├── premium/
│   ├── __init__.py
│   ├── premium_db.py           # premium_subscriptions テーブル操作
│   ├── premium_cog.py          # /premium コマンド
│   ├── stripe_webhook.py       # Stripe Webhook エンドポイント (aiohttp)
│   └── checks.py               # プレミアム判定デコレータ・ユーティリティ
```

#### 10.3.3 決済フロー詳細

```
ユーザー (Discord)         Bot (premium_cog)         Stripe              Bot (Webhook)
     │                          │                      │                      │
     │  /premium                │                      │                      │
     │ ───────────────────────► │                      │                      │
     │                          │  Checkout Session    │                      │
     │                          │ 作成 (Stripe API)    │                      │
     │                          │ ──────────────────► │                      │
     │                          │ ←── session.url ─── │                      │
     │  DMでURL送信              │                      │                      │
     │ ◄─────────────────────── │                      │                      │
     │                          │                      │                      │
     │  URLを開く                │                      │                      │
     │ ──────────────────────────────────────────────► │                      │
     │                          │                      │  決済完了             │
     │                          │                      │  checkout.session    │
     │                          │                      │  .completed          │
     │                          │                      │ ──────────────────►  │
     │                          │                      │                      │  guild_config
     │                          │                      │                      │  .premium = 1
     │                          │                      │                      │
     │  /premium confirm        │                      │                      │
     │ ───────────────────────► │ 状態確認 → 有効化     │                      │
     │ ◄────── 完了通知 ──────── │                      │                      │
```

#### 10.3.4 Stripe Webhook 実装

**エンドポイント**: `POST /webhook/stripe`

**技術選定**: aiohttp を使用（discord.py の非同期イベントループと共存可能）

**処理するWebhookイベント**:

| イベント種別 | 処理内容 |
|-------------|---------|
| `checkout.session.completed` | subscription_id を取得、premium_subscriptions にレコード作成、guild_config.premium=1 に設定 |
| `invoice.paid` | 支払い成功 → current_period_end を更新（契約期間延長） |
| `invoice.payment_failed` | 支払い失敗 → status='past_due' に更新、管理者にDM通知 |
| `customer.subscription.updated` | 契約変更をDBに反映 |
| `customer.subscription.deleted` | status='canceled' に更新、guild_config.premium=0 に設定、管理者にDM通知 |

**冪等性**: `stripe_events` テーブルで event.id を記録し、同一イベントの再送を無視する。

**シークレット検証**: `stripe.Webhook.construct_event()` で署名検証を行う。

#### 10.3.5 環境変数

| 変数名 | 必須 | 説明 | テスト用デフォルト |
|--------|------|------|-------------------|
| `DISCORD_BOT_TOKEN` | ✅ | Discord Botトークン | — |
| `DATABASE_PATH` | — | DB保存先パス（省略時: ./data/） | `./data/` |
| `STRIPE_SECRET_KEY` | ✅ | Stripe Secret Key (sk_test_xxx / sk_live_xxx) | `sk_test_xxxxxxxx` |
| `STRIPE_PUBLISHABLE_KEY` | — | Stripe Publishable Key (フロントエンド用) | `pk_test_xxxxxxxx` |
| `STRIPE_WEBHOOK_SECRET` | ✅ | Webhook署名検証用シークレット (whsec_xxx) | `whsec_test_xxxx` |
| `STRIPE_PRICE_ID` | ✅ | Premium月額Price ID | `price_test_xxxx` |
| `WEBHOOK_HOST` | ✅ | Webhook公開URL（ngrok等）| `https://xxxx.ngrok.io` |
| `BOT_OWNER_ID` | — | Bot管理者のDiscord ID（緊急通知用） | — |

### 10.4 プレミアム機能ゲート

#### 10.4.1 判定ロジック（premium/checks.py）

```python
# 概念コード — 実装時に具体化

async def is_premium(guild_id: int) -> bool:
    """Return True if the guild has an active premium subscription."""
    sub = get_active_subscription(guild_id)
    if sub is None:
        return False
    if sub["status"] != "active":
        return False
    # Check period end
    period_end = datetime.fromisoformat(sub["current_period_end"])
    if period_end < datetime.now(timezone.utc):
        return False
    return True

async def require_premium(interaction: discord.Interaction) -> bool:
    """Send an ephemeral message if the guild is not premium. Return True if OK."""
    if interaction.guild_id is None:
        await interaction.response.send_message("❌ このコマンドはサーバー内でのみ使用できます。", ephemeral=True)
        return False
    if not await is_premium(interaction.guild_id):
        await interaction.response.send_message(
            "🌟 この機能は **Premiumプラン**（月額500円）限定です。\n"
            "`/premium` で詳細を確認してください。",
            ephemeral=True,
        )
        return False
    return True
```

#### 10.4.2 機能制限マトリクス（各Cogでの適用箇所）

| Cog | 制限対象 | 無料 | Premium |
|-----|---------|------|---------|
| `poll_cog` | 匿名投票 (`/poll --anonymous`) | 不可 (コマンド引数を無視) | 許可 |
| `poll_cog` | 複数選択投票 | 不可 | 許可 |
| `reminder_cog` | リマインダー上限 | 3件/ユーザー | 無制限 |
| `welcome_cog` (未実装) | カスタム埋め込みメッセージ | 定型文のみ | JSONカスタマイズ可 |
| `xp_cog` | レベルロール自動付与 | 不可 | 可 |
| `xp_cog` | XP倍率カスタマイズ | 不可 (1.0固定) | 0.5〜3.0で設定可 |
| `mod_cog` (Phase3) | 自動モデレーション | 不可 | 可 |
| — | データエクスポート | 不可 | 可 |

#### 10.4.3 実装パターン

各Cogでプレミアム制限を適用する際の実装パターン:

```python
# 概念コード

# パターンA: コマンド全体を制限
@app_commands.command(name="export", description="データをエクスポートします (Premium)")
async def export(self, interaction: discord.Interaction) -> None:
    if not await require_premium(interaction):
        return
    # ... 実装

# パターンB: 特定の引数を制限
@app_commands.command(name="poll", description="投票を作成します")
@app_commands.describe(anonymous="匿名投票 (Premium)")
async def poll(self, interaction: ..., anonymous: Optional[bool] = None) -> None:
    if anonymous and not await require_premium(interaction):
        anonymous = False  # Premiumでなければ強制解除
    # ... 実装

# パターンC: 利用数制限
async def _count_reminders(user_id: int) -> int:
    """Return current active reminder count."""
    ...

@app_commands.command(name="remind", description="リマインダーを設定")
async def remind(self, interaction: ..., ...) -> None:
    count = _count_reminders(interaction.user.id)
    guild_id = interaction.guild_id or 0
    max_rem = 0 if await is_premium(guild_id) else 3
    if max_rem > 0 and count >= max_rem:
        await interaction.response.send_message(
            f"❌ リマインダーは最大{max_rem}件までです。"
            f"（Premiumプランで無制限になります）",
            ephemeral=True,
        )
        return
    # ... 実装
```

### 10.5 コマンド設計

#### /premium (premium_cog.py)

| コマンド | 引数 | 権限 | 説明 | Ephemeral |
|---------|------|------|------|-----------|
| `/premium` | — | — | Premiumプランの案内 + 購入URL表示 | ✅ |
| `/premium status` | — | Manage Server | 自サーバーのPremium契約状態を表示 | ✅ |
| `/premium cancel` | — | Manage Server | Premium契約を解約（Stripe側にも反映） | ✅ |
| `/premium confirm` | — | Manage Server | 購入完了確認（Webhook受信後、手動トリガー） | ✅ |

**`/premium` レスポンス例**:
```
🌟 **Community Keeper Premium**
月額 **500円** で全機能が使い放題！

✨ Premium特典:
• ウェルカムメッセージを自由にカスタマイズ
• 匿名投票・複数選択投票
• リマインダー無制限
• レベル連動ロール自動付与
• XP倍率カスタマイズ
• 自動モデレーション（近日公開）

🔗 購入はこちら: [Stripe Checkout URL]

`/premium status` で契約状態を確認できます。
```

#### 既存コマンドへの変更点

| コマンド | 変更内容 |
|---------|---------|
| `/remind` | 無料=3件制限チェック追加、超過時はPremium案内 |
| `/poll --anonymous` | 無料サーバーでは `anonymous` 引数を無視し通常投票に |
| `/level` (将来) | ロール自動付与設定はPremium必須 |

### 10.6 Stripeテスト環境設計

#### 10.6.1 開発フェーズのテスト構成

| 環境 | Stripe Mode | 使用するキー | Webhook |
|------|------------|-------------|---------|
| ローカル開発 | テストモード | `sk_test_xxx` | Stripe CLI → `stripe listen` + ngrok |
| CI/CD | テストモード | `sk_test_xxx` | Stripe CLI (GitHub Actions) + モック |
| ステージング | テストモード | `sk_test_xxx` | ngrok + Stripe Dashboard Webhook設定 |
| 本番 | ライブモード | `sk_live_xxx` | 公開URL + Stripe Dashboard |

#### 10.6.2 ローカル開発手順

```bash
# 1. Stripe CLI インストール
#    macOS: brew install stripe/stripe-cli/stripe
#    Linux: 公式インストールスクリプト

# 2. Stripe ログイン
stripe login

# 3. Webhook転送開始（別ターミナルで実行）
stripe listen --forward-to localhost:8080/webhook/stripe

# 4. 出力された signing secret (whsec_xxx) を .env に設定
echo "STRIPE_WEBHOOK_SECRET=whsec_xxx" >> .env

# 5. ngrok でWebhook公開（別ターミナル）
ngrok http 8080

# 6. 生成された https://xxxx.ngrok.io を WEBHOOK_HOST に設定
echo "WEBHOOK_HOST=https://xxxx.ngrok.io" >> .env

# 7. Bot起動
python bot.py
```

#### 10.6.3 テスト用クレジットカード番号

Stripeテストモードで使用可能なカード番号:

| ブランド | 番号 | 結果 |
|---------|------|------|
| Visa (成功) | `4242 4242 4242 4242` | 支払い成功 |
| Visa (失敗: 認証不) | `4000 0000 0000 0002` | card_declined |
| 3Dセキュア認証必須 | `4000 0025 0000 3155` | authentication_required |

#### 10.6.4 テスト用Stripeイベント発生

```bash
# テスト用 checkout.session.completed イベントをトリガー
stripe trigger checkout.session.completed

# 特定のSubscription更新イベント
stripe trigger customer.subscription.updated

# 支払い失敗
stripe trigger invoice.payment_failed
```

### 10.7 プレミアムユーザー管理（Discord Bot内）

#### 10.7.1 管理ダッシュボード（Botコマンド）

| コマンド | 権限 | 説明 |
|---------|------|------|
| `/premium status` | Manage Server | 現在の契約状態、有効期限、次回請求日を表示 |
| `/premium cancel` | Manage Server | 即時解約（有効期限内は機能継続） |

#### 10.7.2 有効期限切れ・支払い失敗時の動作

| 状態 | API側の動作 | Discord Bot内の動作 |
|------|------------|-------------------|
| 有効期限内 | 全機能利用可 | — |
| 支払い失敗から3日以内 (past_due) | Premium機能維持 | サーバー管理チャンネルにDM + 通知 |
| 支払い失敗から3日超過 | Premium→Freeに自動Downgrade | 通知後、Premium機能停止 |
| 解約済み (canceled) | 即時Free扱い | 有効期限まではPremium維持（Stripeポリシー） |
| 有効期限切れ | 自動Free扱い | 期限切れ時にPremium機能停止 + 通知 |

#### 10.7.3 管理通知先

| イベント | 送信先 | 内容 |
|---------|--------|------|
| 購入完了 | 購入者DM | 購入完了と利用開始方法 |
| 支払い失敗 | 購入者DM | カード情報更新依頼 + Stripe Customer Portal URL |
| 有効期限切れ予告（7日前） | 購入者DM | 自動更新のお知らせ |
| 解約完了 | 購入者DM | 解約完了と有効期限日 |
| サーバー内通知 (任意) | guild_config.system_channel | 購入時・解約時の任意通知 |

#### 10.7.4 Stripe Customer Portal

StripeのCustomer Portalを利用して、ユーザー自身で以下を管理できる:

- サブスクリプションの管理（更新/解約）
- 支払い方法の変更
- 請求書のダウンロード

Customer Portalの設定はStripe Dashboardで事前に行う。

### 10.8 エラーハンドリングとリトライ戦略

| エラー種別 | 対応 |
|-----------|------|
| Stripe API一時エラー (500, timeout) | 最大3回リトライ (1s/5s/10s 間隔)、指数バックオフ |
| Webhook署名不一致 | 403返却、ログ出力（悪意あるリクエストの可能性） |
| Webhook重複イベント | stripe_events テーブルで冪等性チェック、重複時は200返却 |
| 存在しないサーバーへのWebhook | ログ出力のみ、エラーにしない |
| Stripe API key 未設定 | Bot起動時にチェックし、エラーログ出力、/premium でエラーメッセージ表示 |

### 10.9 セキュリティ考慮

| リスク | 対策 |
|--------|------|
| Stripe Secret Key漏洩 | 環境変数管理、.gitignoreに.env含む、CIではSecrets使用 |
| Webhook偽装 | `stripe.Webhook.construct_event()` で署名検証必須 |
| 不正なPremium有効化 | Webhook経由以外のpremiumフラグ更新は管理者コマンドのみ許可 |
| 他サーバーの契約情報閲覧 | コマンド実行時に guild_id を必ず検証、他サーバーの情報は見えない |
| ユーザー入力経由のStripe API操作 | Discordのインプットバリデーションを通過した安全な値のみ使用 |

### 10.10 Phase2 実装タスク一覧

| # | タスク | ファイル | 優先度 |
|---|-------|---------|--------|
| 1 | premium_db.py: premium_subscriptions/stripe_events/guild_premium_config テーブル作成 | `premium/premium_db.py` | P0 |
| 2 | checks.py: is_premium / require_premium ユーティリティ | `premium/checks.py` | P0 |
| 3 | premium_cog.py: /premium, /premium status, /premium cancel | `premium/premium_cog.py` | P0 |
| 4 | stripe_webhook.py: aiohttpサーバー + Webhook検証 + イベント処理 | `premium/stripe_webhook.py` | P0 |
| 5 | poll_cog.py: 匿名投票の制限チェック追加 | `poll_cog.py` | P1 |
| 6 | reminder_cog.py: 3件制限チェック追加 | `reminder_cog.py` | P1 |
| 7 | xp_cog.py: レベルロール設定の枠組み追加（実装はPhase3） | `xp_cog.py` | P2 |
| 8 | guild_config.py: サーバー設定管理テーブル操作リファクタ | — | P2 |
| 9 | テスト: premium_db.py ユニットテスト（6件以上） | `tests/test_premium_db.py` | P0 |
| 10 | テスト: checks.py ユニットテスト（4件以上） | `tests/test_premium_checks.py` | P0 |
| 11 | テスト: Webhook署名検証 + 冪等性テスト | `tests/test_webhook.py` | P1 |
| 12 | .env.example 更新: Stripe関連変数追加 | `.env.example` | P1 |
| 13 | requirements.txt 更新: aiohttp, stripe 追加 | `requirements.txt` | P0 |
| 14 | bot.py 更新: Webhookサーバー起動処理追加 | `bot.py` | P0 |
| 15 | SPEC.md 完了報告: 本セクション完了 | — | — |

### 10.11 追加依存パッケージ

| パッケージ | バージョン | 用途 |
|-----------|-----------|------|
| `stripe` | >=7.0.0 | Stripe API クライアント（Checkout Session作成、Webhook検証） |
| `aiohttp` | >=3.9.0 | 非同期HTTPサーバー（Webhookエンドポイント） |

`requirements.txt` に追記:
```
stripe>=7.0.0
aiohttp>=3.9.0
```

### 10.12 Phase2 開発ロードマップ（詳細）

| 週 | 作業 | 成果物 |
|----|------|--------|
| Week 1 | premium_db.py + checks.py + premium_cog.py 実装 | 購入フローの基本部分（実際の決済なし） |
| Week 2 | stripe_webhook.py 実装、Stripeテスト環境構築、E2Eテスト | テストモードでの購入→有効化→解約フロー完了 |
| Week 3 | 既存Cogへの制限実装、残りテスト、バグ修正 | Phase2完了 |
| Week 4 | バッファ期間（レビュー・追加テスト・本番準備） | 本番移行判断 |

---

## 11. Phase4: データエクスポート

### 11.1 機能概要

Premiumユーザー向けに、サーバーの各種データをCSV/JSON形式でエクスポートする機能を提供する。
対象データはXPデータ（ユーザー別累計XP）、リマインダー一覧、モデレーション設定、
プレミアム購読情報（Ownerのみ）の4種類。出力形式は全データでCSVとJSONの2形式をサポートする。

### 11.2 エクスポート対象と出力形式

| データ種別 | DBテーブル | CSV | JSON | アクセス制限 |
|-----------|-----------|-----|------|------------|
| XPデータ | `xp_data` | ✅ | ✅ | Manage Server権限 + Premium |
| リマインダー一覧 | `reminders` | ✅ | ✅ | Manage Server権限 + Premium |
| モデレーション設定 | `mod_config` + `moderation_keywords` | ✅ | ✅ | Manage Server権限 + Premium |
| プレミアム購読情報 | `premium_subscriptions` | ✅ | ✅ | Ownerのみ + Premium |

### 11.3 データベース層 API（`premium/export_db.py`）

#### 関数一覧

| 関数 | 引数 | 戻り値 | 説明 |
|------|------|--------|------|
| `export_xp_data(guild_id: int)` | guild_id | `list[dict]` | ギルドの全ユーザーXPデータ（user_id, guild_id, xp, level）を取得 |
| `export_reminders(guild_id: int)` | guild_id | `list[dict]` | ギルドの全リマインダー（id, user_id, channel_id, message, remind_at, created_at, triggered）を取得 |
| `export_moderation_config(guild_id: int)` | guild_id | `dict` | モデレーション設定（keywords一覧, spam_threshold, auto_mod_enabled）を取得 |
| `export_premium_info(guild_id: int)` | guild_id | `dict` | プレミアム購読情報（guild_id, owner_id, status, current_period_start, current_period_end）を取得 |

### 11.4 出力形式仕様

#### 11.4.1 XPデータ CSV/JSON

| 列名 | 型 | 説明 |
|------|-----|------|
| user_id | int | ユーザーID |
| guild_id | int | サーバーID |
| xp | int | 累計XP |
| level | int | 現在のレベル |

**CSV例**:
```csv
user_id,guild_id,xp,level
10001,20001,150,2
10002,20001,320,3
```

#### 11.4.2 リマインダー一覧 CSV/JSON

| 列名 | 型 | 説明 |
|------|-----|------|
| id | int | リマインダーID |
| user_id | int | 作成者ユーザーID |
| channel_id | int | 送信先チャンネルID |
| guild_id | int | サーバーID |
| message | text | リマインダー内容 |
| remind_at | real | 実行日時（UNIXタイムスタンプ） |
| created_at | real | 作成日時 |
| triggered | int | 0=未, 1=完了 |

#### 11.4.3 モデレーション設定 JSON

```json
{
  "guild_id": 20001,
  "keywords": ["badword1", "badword2"],
  "spam_threshold": 3,
  "auto_mod_enabled": true
}
```

#### 11.4.4 プレミアム購読情報 JSON

```json
{
  "guild_id": 20001,
  "owner_id": 10001,
  "status": "active",
  "current_period_start": "2026-08-01T00:00:00+00:00",
  "current_period_end": "2026-09-01T00:00:00+00:00"
}
```

### 11.5 コマンド設計（Phase4で実装予定）

| コマンド | 権限 | 説明 |
|---------|------|------|
| `/export xp` | Manage Server + Premium | XPデータをCSV/JSONで出力 |
| `/export reminders` | Manage Server + Premium | リマインダー一覧をCSV/JSONで出力 |
| `/export config` | Manage Server + Premium | モデレーション設定をJSONで出力 |
| `/export premium` | Owner + Premium | プレミアム購読情報をJSONで出力 |
| `/export all` | Manage Server + Premium | 全データをZIPで一括出力 |

### 11.6 アクセス制御

- **Premiumチェック**: 全てのエクスポートコマンドはPremium必須（`require_premium`使用）
- **権限チェック**: XP/リマインダー/モデレーション設定は `Manage Server` 権限が必要
- **Owner制限**: プレミアム購読情報は購読所有者（`owner_id`）のみアクセス可能
- **出力先**: ファイルはDMでユーザーに送信（サーバー公開チャンネルには送信しない）

### 11.7 ファイル構成

| ファイル | 役割 |
|---------|------|
| `premium/export_db.py` | データベース層（データ取得） |
| `premium/export_cog.py` | Cog: スラッシュコマンド + ファイル生成 + DM送信（Phase4b） |
| `test_export_db.py` | export_db.py の単体テスト |

---