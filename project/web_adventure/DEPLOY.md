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

## 4. Vercel（無料）

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