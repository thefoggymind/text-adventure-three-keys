# デプロイチェックリスト

> 詳細な手順は [DEPLOY.md](./DEPLOY.md) を参照。
> 本ゲームは静的ファイル（HTML/CSS/JS）のみで構成され、ビルド不要。

---

## □ デプロイ先の選択

各サービスの特性を考慮して1つ選ぶ。

| 項目 | GitHub Pages | Netlify | Cloudflare Pages | Vercel |
|------|-------------|---------|-----------------|--------|
| 公開ディレクトリ指定 | `web_adventure` | `web_adventure` | `web_adventure` | Root Directory: `web_adventure` |
| カスタムドメイン | 設定画面で入力 + DNS | Domain management | Cloudflare DNS連携 | Domains設定 |
| 自動デプロイ | mainブランチプッシュ | mainブランチプッシュ | mainブランチプッシュ | mainブランチプッシュ |
| 主な制限 | リポジトリ公開必須（無料プラン） | 帯域幅制限あり | リクエスト数制限あり | 商用利用にはPro推奨 |

**選択したデプロイ先:** □ GitHub Pages  □ Netlify  □ Cloudflare Pages  □ Vercel

□ [DEPLOY.md](./DEPLOY.md) の該当セクションに従いデプロイ設定を行う

---

## □ デプロイ前に人間が設定すべき項目

### 1. 寄付リンク先URL

- `index.html` 38行目: `<a href="#" class="donate-link">` → `#` を実際の寄付URLに変更
- `index.html` 98行目: `<a href="#" class="btn btn-donate">` → 同上
- 例: `https://www.buymeacoffee.com/yourname` / `https://ko-fi.com/yourname`

□ 寄付リンクを実際のURLに変更した

### 2. Twitterシェアボタン

- `index.html` 105行目: `<a href="#" class="btn btn-share">` → `#` を実際のシェアURLに変更
- 例: `https://twitter.com/intent/tweet?text=3つの鍵を遊んでみた！&url=https://<デプロイURL>`

□ TwitterシェアURLを設定した

### 3. OGP画像（SNSシェア用）

- ファイル: `assets/ogp.svg` — デフォルトのSVGが配置済み
- 必要に応じて `assets/ogp.png`（1200×630px推奨）に差し替え、`index.html` の `og:image` を更新

□ OGP画像を確認・差し替えた（任意）

### 4. ファビコン

- ファイル: `assets/favicon.svg` — SVGファビコンが配置済み
- 必要に応じて差し替え

□ ファビコンを確認・差し替えた（任意）

### 5. カスタムドメイン（任意）

各サービスの設定画面でDNSレコードを追加し、カスタムドメインを割り当てる。

□ カスタムドメインを設定する（設定する場合）
□ DNSのAレコード / CNAMEレコードを追加した

### 6. コピーライト表記

- `index.html` 35行目: `© thefoggymind` — 必要に応じて変更

□ コピーライト表記を確認・修正した

---

## □ テスト通過確認

```bash
cd /workspace/project/web_adventure
NODE_OPTIONS=--experimental-vm-modules npx jest
```

□ 全テストが通過した（106 passed）ことを確認した

---

## □ 最終確認

□ デプロイ先のURLにアクセスし、トップ画面が表示されることを確認
□ ゲームがプレイできることを確認（新規ゲーム開始 → 選択 → 進行）
□ セーブ/ロードが正常に動作することを確認
□ テーマ切替（ライト/ダーク）が動作することを確認
□ スマートフォン表示でレイアウトが崩れないことを確認