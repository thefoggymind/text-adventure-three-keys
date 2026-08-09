> **公開準備完了** このゲームは itch.io にアップロードする準備が整っています。詳細な手順は [PUBLISH_GUIDE.md](PUBLISH_GUIDE.md) を参照してください。

# テキストベースアドベンチャーゲーム

森の中で目覚めたあなたは、二つの道の前に立っています。選択と運命が交差する、シンプルなテキストアドベンチャーゲームです。

## 遊び方

ゲームを起動すると、以下の選択肢が表示されます。

1. **左の道を進む** — きらめく川で休息。勝敗は運次第。
2. **右の道を進む** — 古い遺跡で発見。勝敗は運次第。
3. **冒険をあきらめて帰る** — 平穏な日常に戻ります。
4. **周辺を探索する** — （最初の1回のみ表示）隠しエンディングへの鍵を入手できます。

表示された番号を入力して Enter を押すだけです。

## 全6エンディング

| # | エンディング名 | 条件 | 説明 |
|---|---------------|------|------|
| 1 | **左の道 - 勝利** | 左の道で勝つ（50%） | 清らかな川で回復し、輝く宝石を手に入れる |
| 2 | **左の道 - 敗北** | 左の道で負ける（50%） | 毒された川の水で倒れる |
| 3 | **右の道 - 勝利** | 右の道で勝つ（50%） | 古代の宝具で富と名声を得る |
| 4 | **右の道 - 敗北** | 右の道で負ける（50%） | 呪いで石になってしまう |
| 5 | **中立「帰還」** | 「冒険をあきらめて帰る」を選ぶ | 危険を避け、平穏な日常に戻る |
| 6 | **隠し「真の英雄」** | 「周辺を探索」→「左/右の道」→洞窟探索で「y」 | 伝説の財宝を手にし、真の英雄となる |

### 隠しエンディングの詳細な手順

1. メニューで「4. 周辺を探索する」を選び、**錆びた鍵** と **古い地図** を入手する
2. 「1. 左の道を進む」または「2. 右の道を進む」を選ぶ
3. 隠し洞窟の入り口が現れたら `y` と入力する

## 動作要件

- **Python 3.x**（3.6 以上推奨）
- 標準ライブラリのみ使用（追加パッケージ不要）

## 実行方法

```bash
python game.py
```

または実行権限を付与して直接実行：

```bash
chmod +x game.py
./game.py
```

## 配布物の構成

配布パッケージ（`text-adventure-game.zip`）には以下のファイルが含まれています。

| ファイル | 説明 |
|----------|------|
| `game.py` | ゲーム本体（Pythonスクリプト） |
| `README.md` | 本ドキュメント（ゲーム概要・遊び方・インストール手順） |
| `LICENSE` | MITライセンス条文 |
| `ISSUE_TEMPLATE.md` | バグ報告・機能リクエスト用テンプレート |
| `ROADMAP.md` | 今後のアップデート方針 |

## インストール手順

1. 配布用 zip ファイルを任意のディレクトリに解凍します。

   ```bash
   unzip text-adventure-game.zip -d my_adventure_game
   ```

2. 解凍したディレクトリに移動し、ゲームを実行します。

   ```bash
   cd my_adventure_game
   python game.py
   ```

   **Python 3.x**（3.6 以上推奨）が必要です。標準ライブラリのみ使用しているため、追加のパッケージインストールは不要です。

## ダウンロードとプレイ方法

### itch.io からダウンロード

本ゲームは [itch.io](https://itch.io) で公開しています。

- **公開URL**: [https://thefoggymind.itch.io/text-adventure-game](https://thefoggymind.itch.io/text-adventure-game)
- ページ右上の **「Download Now」** または **「Download」** ボタンをクリックすると `text-adventure-game.zip` がダウンロードされます。

### ダウンロード後の実行手順

1. ダウンロードした zip ファイルを任意のフォルダに解凍します。

   ```bash
   unzip text-adventure-game.zip -d text_adventure_game
   ```

   （Windows の場合はエクスプローラーで右クリック → 「すべて展開」でも解凍できます。）

2. 解凍したフォルダに移動し、ゲームを起動します。

   ```bash
   cd text_adventure_game
   python game.py
   ```

3. 画面に表示される選択肢から番号を入力して Enter を押すだけでプレイできます。

### 動作環境

- **OS**: Windows / macOS / Linux いずれでも動作します
- **Python**: 3.6 以上（システムにインストールされている必要があります）
- 追加パッケージは一切不要です（Python標準ライブラリのみ使用）

---

### 公開者向け：itch.io へのアップロード手順

初回アップロードや更新時の参考手順です。配布ZIP（`dist/text-adventure-game.zip`）は既に生成済みです。

#### 方法A：Webブラウザからアップロード（簡単）

1. **ログイン**: [itch.io](https://itch.io) にアクセスし、アカウントを作成またはログインします
2. **新規プロジェクト作成**: ダッシュボード右上の **「Upload new project」** をクリック
3. **プロジェクト情報を入力**:
   - **Title**: `Text Adventure Game`（任意のタイトル）
   - **Project URL**: タイトルから自動生成されるスラッグ（後で変更不可）
   - **Classification**: `Game`
   - **Kind of project**: プロジェクト種別を選択（ダウンロード配信の場合は `HTML` でも可）
4. **ZIPファイルをアップロード**:
   - **Uploads** セクションに `dist/text-adventure-game.zip` をドラッグ＆ドロップ
   - **View this file as**: `A file that will be downloaded by players` を選択
5. **公開設定**:
   - 必要に応じて Description（説明文）に README.md の内容をコピー
   - Screenshots（スクリーンショット）を追加（任意）
   - Tags（タグ）: `text-adventure`, `python`, `interactive-fiction` などを設定（任意）
6. **公開完了**: ページ下部の **「Save & view page」** をクリック
7. **動作確認**: 公開後、`https://thefoggymind.itch.io/text-adventure-game` にアクセスしてZIPがダウンロードできることを確認

#### 方法B：butler CLI でアップロード（上級者向け）

更新が頻繁な場合は公式CLIツール `butler` が便利です。

```bash
# インストール（macOS / Linux）
curl -L -o butler.zip https://broth.itch.ovh/butler/linux-amd64/LATEST.zip
unzip butler.zip -d /usr/local/bin && rm butler.zip
chmod +x /usr/local/bin/butler

# ログイン（APIキーを発行して入力）
butler login

# アップロード（バージョン管理付き）
butler push /workspace/project/dist/text-adventure-game.zip thefoggymind/text-adventure-game:windows-linux-mac
```

> **注意**: `thefoggymind` は実際のitch.ioユーザー名です。ユーザー名が異なる場合は書き換えてください。

---

### 代替配布方法：GitHub Releases

itch.io 以外に GitHub の Releases 機能でも配布可能です。

1. リポジトリの **Releases** ページ（`https://github.com/thefoggymind/text-adventure-game/releases`）を開く
2. **「Create a new release」** をクリック
3. タグ（例: `v1.0.0`）とリリースタイトルを入力
4. `text-adventure-game.zip` をバイナリとしてアップロード
5. **「Publish release」** で公開完了

ダウンロードURL例：
`https://github.com/thefoggymind/text-adventure-game/releases/download/v1.0.0/text-adventure-game.zip`

## サポート

このゲームを気に入っていただけたなら、開発を支援していただけると励みになります。

- **Ko-fi**: [https://ko-fi.com/thefoggymind](https://ko-fi.com/thefoggymind)

皆様のご支援が、さらなる機能追加や新作開発の原動力となります。よろしくお願いいたします。

## 運用中のサポート

公開後も以下の方法でフィードバックを受け付け、ゲームを継続的に改善していきます。

### バグ報告・機能リクエスト

不具合を見つけた場合や、新しい機能のアイデアがある場合は、以下のテンプレートをご利用ください。

- **ISSUE_TEMPLATE.md** — バグ報告・機能リクエストのテンプレート（本ZIPに同梱）
- **GitHub Issues**: [https://github.com/thefoggymind/text-adventure-game/issues](https://github.com/thefoggymind/text-adventure-game/issues)

報告いただいた内容は、今後のアップデートの参考にさせていただきます。

### 今後のアップデート予定

短期的な改善から長期的な拡張まで、以下のようなアップデートを計画しています。

| フェーズ | 内容 | 時期（目安） |
|---------|------|------------|
| 短期 | 既存エンディングのテキスト調整・細かなバグ修正 | 公開後1〜2ヶ月 |
| 中期 | 新規エンディングの追加・選択肢の拡充 | 公開後3〜6ヶ月 |
| 長期 | セーブ機能・分岐マップ表示などの機能拡張 | 公開後6ヶ月〜 |

詳細なロードマップは同梱の **ROADMAP.md** を参照してください。

## 開発者

- **開発者名**: OpenHands AI Agent
- **リポジトリ**: [https://github.com/thefoggymind/text-adventure-game](https://github.com/thefoggymind/text-adventure-game)
- **ライセンス**: MIT License

---

# Community Keeper — Discord Bot

多機能Discord Bot「Community Keeper」は、アンケート（投票）、リマインダー、XP/レベル管理機能を提供します。

## 機能一覧

- **アンケート（投票）機能** — サーバー内で簡単に投票を作成・実施できます
- **リマインダー機能** — 指定した時間後に通知を送信します
- **XP/レベル管理** — メッセージアクティビティに応じてXPを付与し、レベルアップを管理します

## 動作要件

- **Python 3.10 以上**
- 依存パッケージは `requirements.txt` を参照

## セットアップ手順

### 1. リポジトリのクローン

```bash
git clone <repository-url>
cd project
```

### 2. 環境変数の設定

`.env.example` を `.env` にコピーし、必要な値を設定します。

```bash
cp .env.example .env
```

`.env` ファイルをエディタで開き、以下の項目を設定してください。

| 変数名 | 必須 | 説明 |
|--------|------|------|
| `DISCORD_BOT_TOKEN` | ✅ | Discord Developer Portal で発行したBotトークン |
| `DATABASE_PATH` | ❌ | データベース保存先のパス（省略時は `data/`） |

**DISCORD_BOT_TOKEN の取得方法**:
1. [Discord Developer Portal](https://discord.com/developers/applications) にアクセス
2. 「New Application」でアプリケーションを作成
3. 左メニュー「Bot」→「Add Bot」→「Reset Token」でトークンを発行
4. 発行されたトークンを `.env` の `DISCORD_BOT_TOKEN=` に設定

### 3. 依存パッケージのインストール

```bash
pip install -r requirements.txt
```

### 4. Botの起動

```bash
python bot.py
```

起動後、DiscordサーバーでBotがオンラインになっていることを確認してください。

## コマンド一覧

Botが起動したら、Discordのテキストチャンネルで以下のスラッシュコマンドが使用できます。

| コマンド | 説明 |
|----------|------|
| `/poll` | アンケートを作成します |
| `/remind` | リマインダーを設定します |
| `/xp` | 自分のXPとレベルを確認します |
| `/leaderboard` | サーバーのXPランキングを表示します |

## Render（無料プラン）へのデプロイ手順

[Render](https://render.com) の無料プランで Community Keeper を24時間稼働させる手順です。

### 前提条件

- GitHub リポジトリに本プロジェクトがプッシュされていること
- [Discord Developer Portal](https://discord.com/developers/applications) でBotトークン（`DISCORD_BOT_TOKEN`）を発行済みであること

### 1. Render ダッシュボードでの設定

1. [Render Dashboard](https://dashboard.render.com) にログイン
2. **「New +」** → **「Web Service」** をクリック
3. デプロイ元の GitHub リポジトリを選択し、以下を設定:

| 項目 | 設定値 |
|------|--------|
| **Name** | `community-keeper`（任意） |
| **Runtime** | `Python 3` |
| **Region** | 任意（日本に近いリージョンを推奨） |
| **Branch** | `main`（またはデプロイしたいブランチ） |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `python bot.py` |
| **Plan** | **Free** を選択 |

### 2. 環境変数の設定

Render ダッシュボードの **Environment** タブ（または作成ウィザード内の **Environment Variables** セクション）で以下の変数を追加します。

| 変数名 | 値の例 | 必須 | 説明 |
|--------|--------|------|------|
| `DISCORD_BOT_TOKEN` | `MTk4NjIyMjNzZ...` | ✅ | Discord Developer Portal で発行したBotトークン |
| `DATABASE_PATH` | `./data/` | ❌ | データベース保存先ディレクトリ（現状はコード内で `data/` に固定。詳細は下記参照） |

> **注意**: `DISCORD_BOT_TOKEN` は外部に漏れないよう、Renderの環境変数として必ず設定してください。`.env` ファイルはRenderでは使用しません。

### 3. デプロイの実行

1. 設定完了後、**「Create Web Service」** をクリック
2. ビルドログが表示され、自動的にビルド→デプロイが実行されます
3. ログに `✅ Community Keeper 起動完了` と表示されれば成功
4. 初回デプロイには数分かかる場合があります

### 4. 永続化ディスクとDBファイルパスの注意点

**⚠ 無料プランの制限 — データが失われる可能性があります**

Community Keeper は内部で **SQLite** を使用し、データベースファイルをデフォルトで `data/` ディレクトリに保存します。

| プラン | ファイル保存の仕組み | データの永続性 |
|--------|---------------------|---------------|
| **Free（無料）** | エフェメラルディスク（再起動で消去） | ❌ 再起動・再デプロイ時に投票・リマインダー・XPデータが全て消失 |
| **Paid（有料）** | Persistent Disk アドオン（月額$7〜）を追加可能 | ✅ 再起動後もデータ維持 |

**回避策と推奨事項**:

1. **テスト用途（Freeプラン）**: データ消失を前提に運用。定期的なバックアップは期待しないでください。
2. **本番運用（推奨）**: Renderの **Persistent Disk** を月額$7で追加するか、外部データベースサービス（[Railway](https://railway.app) のPostgreSQL無料枠や [TiDB Serverless](https://tidbcloud.com) など）に移行することを検討してください。
3. **DATABASE_PATH 環境変数について**: `.env.example` には `DATABASE_PATH` の記載がありますが、現在のコードでは `data/` ディレクトリがハードコードされています。Persistent Disk を利用する場合は、マウントパスに合わせてコードの `DB_DIR` を修正する必要があります。

### 5. デプロイ後の確認

デプロイが完了したら、Render ダッシュボードの **Logs** タブで起動ログを確認してください。

```text
✅ Community Keeper 起動完了
   Bot名: Community Keeper
   BotID: 123456789012345678
   サーバー数: 1
   ✅ スラッシュコマンド同期完了
```

この出力が確認できれば、Discord サーバーで Bot がオンラインになり、スラッシュコマンドが使用可能です。

### 6. 注意事項

- Render 無料プランは **15分間リクエストがないと自動スリープ** します。外部モニタリングサービス（[UptimeRobot](https://uptimerobot.com) の無料枠など）で15分おきにBotのヘルスチェックエンドポイントへリクエストを送ることでスリープを防止できます。ただし、本BotはHTTPサーバーではないため、ping対策には別途Webサーバーエンドポイントを追加することを検討してください。
- 無料プランは月間 **750時間**（約31日）の稼働が無料で、超過分は課金または停止されます。24時間稼働でも月間約744時間のため、ほぼ上限まで使用することになります。
- データベースはRenderのエフェメラルストレージに保存されるため、**無料プランでは定期的にデータがリセットされます**。本番運用には必ず有料プランまたは外部DBをご検討ください。