# 「3つの鍵 — Web Edition」デプロイ手順

> 本ゲームは静的ファイル（HTML/CSS/JS）のみで構成されています。バックエンドサーバーは不要で、無料ホスティングサービスにそのままデプロイできます。

---

## 1. GitHub Pages（無料）

### 前提条件
- GitHub アカウントを持っている
- リポジトリにコードがプッシュされている

### 手順

1. リポジトリの **Settings** → **Pages** を開く
2. **Source** で **「Deploy from a branch」** を選択
3. **Branch** で `main`（またはデプロイしたいブランチ）を選択
4. **Folder** で `/web_adventure` を選択（リポジトリルートではなく `web_adventure` ディレクトリを指定）
5. **Save** をクリック
6. 数分後、`https://<username>.github.io/<repository>/web_adventure/` で公開完了

### カスタムドメイン（任意）

GitHub Pages の設定画面で **Custom domain** に独自ドメインを入力し、DNS設定を行ってください。

---

## 2. Netlify（無料）

### 前提条件
- GitHub / GitLab / Bitbucket アカウントを持っている
- リポジトリにコードがプッシュされている

### 手順

1. [Netlify](https://app.netlify.com) にログイン（GitHubアカウントでサインアップ可）
2. **「Import from Git」** をクリック
3. ホスティングサービス（GitHub等）を選択し、リポジトリを選ぶ
4. デプロイ設定:
   | 項目 | 設定値 |
   |------|--------|
   | **Branch to deploy** | `main` |
   | **Publish directory** | `web_adventure` |
   | **Build command** | 空欄（ビルド不要） |
5. **「Deploy site」** をクリック
6. デプロイ完了後、`https://<site-name>.netlify.app` で公開
7. （任意）**Site settings** → **Domain management** でカスタムドメインを設定可能

### 自動デプロイ

リポジトリの `main` ブランチにプッシュすると、Netlify が自動でデプロイを実行します。

---

## 3. Cloudflare Pages（無料）

### 手順

1. [Cloudflare Dashboard](https://dash.cloudflare.com) にログイン
2. **Workers & Pages** → **Pages** → **「Connect to Git」**
3. リポジトリを選択
4. デプロイ設定:
   | 項目 | 設定値 |
   |------|--------|
   | **Project name** | 任意（例: `three-keys-web`） |
   | **Production branch** | `main` |
   | **Build command** | 空欄（ビルド不要） |
   | **Build output directory** | `web_adventure` |
5. **「Save and Deploy」** をクリック
6. デプロイ完了後、`https://<project-name>.pages.dev` で公開

---

## 4. Firebase Hosting（無料枠あり）

### 前提条件
- Node.js v18 以上がインストールされている
- Firebase アカウントを持っている

### 手順

1. [Firebase Console](https://console.firebase.google.com) にアクセスし、**「プロジェクトを作成」** をクリック
2. プロジェクト名を入力し、Google アナリティクスは必要に応じて設定
3. Firebase CLI をインストール:
   ```bash
   npm install -g firebase-tools
   ```
4. Firebase にログイン:
   ```bash
   firebase login
   ```
5. `web_adventure/` ディレクトリに移動して初期化:
   ```bash
   cd web_adventure
   firebase init hosting
   ```
6. 質問に回答:
   - **What do you want to use as your public directory?**: `.`（カレントディレクトリ）
   - **Configure as a single-page app?**: `No`
   - **Set up automatic builds with GitHub?**: 任意
7. デプロイ:
   ```bash
   firebase deploy
   ```
8. 完了後、`https://<project-id>.web.app` でアクセス可能

### 注意点
- Firebase Hosting の無料枠（Sparkプラン）は 10GB のストレージ・月間 360MB の転送量が含まれます
- カスタムドメインは Firebase Console の Hosting セクションから設定可能

---

## 5. Vercel（無料）

### 手順

1. [Vercel](https://vercel.com) にログイン
2. **「Add New...」** → **「Project」**
3. GitHub リポジトリをインポート
4. デプロイ設定:
   | 項目 | 設定値 |
   |------|--------|
   | **Framework Preset** | `Other` |
   | **Root Directory** | `web_adventure`（「Edit」で変更） |
   | **Build Command** | 空欄 |
   | **Output Directory** | 空欄（そのまま） |
5. **「Deploy」** をクリック
6. デプロイ完了後、`https://<project-name>.vercel.app` で公開

---

## 5. ローカルでの動作確認

```bash
cd /workspace/project/web_adventure

# 方法1: npx serve（Node.jsが必要）
npx serve -p 3001
# → http://localhost:3001 にアクセス

# 方法2: Python 3（Pythonが必要）
python3 -m http.server 3001
# → http://localhost:3001 にアクセス
```

---

## テスト実行

デプロイ前には必ずテストが通ることを確認してください。

```bash
cd /workspace/project/web_adventure
NODE_OPTIONS=--experimental-vm-modules npx jest
# → 106 tests passed を確認
```

---

## 注意事項

- **Docker 設定は本ドキュメントの対象外です。** 必要な場合は各自で `Dockerfile` を作成してください。
- セーブデータはブラウザの `localStorage` に保存されます。ブラウザのキャッシュクリアやシークレットモードではデータが引き継がれません。
- 各無料プランには帯域幅やビルド時間に制限があります。大量アクセスが見込まれる場合は各サービスの料金プランを確認してください。