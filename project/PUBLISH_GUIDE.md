# 公開手順ガイド (Publishing Guide)

本ガイドは、`text-adventure-game` を **itch.io** で一般公開するための手順をまとめたものです。

---

## クイックスタート：手動で itch.io にアップロードする手順

以下の5ステップで公開できます。配布ZIP（`dist/text-adventure-game.zip`）は既に生成済みです。

### Step 1: itch.io にログイン
1. ブラウザで [https://itch.io](https://itch.io) を開く
2. 右上の **「Log in」** をクリック
3. ユーザー名（`thefoggymind`）とパスワードを入力してログイン

### Step 2: 新規プロジェクトを作成
1. ダッシュボード右上の **「Upload new project」** ボタンをクリック
2. 以下の項目を入力：
   - **Title**: `Text Adventure Game`
   - **Classification**: `Game`
   - **Kind of project**: ダウンロード形式で配信する場合はプロジェクト種別を選択（`HTML`でも可）
3. **Uploads** セクションまでスクロール

### Step 3: ZIPファイルをアップロード
1. `dist/text-adventure-game.zip` をドラッグ＆ドロップ
2. **「View this file as」** で **「A file that will be downloaded by players」** を選択

### Step 4: 公開設定
1. 必要に応じて Description（説明文）に README.md の内容をコピー
2. ページ下部の **「Save & view page」** をクリック

### Step 5: 完了確認
1. 公開URL（`https://thefoggymind.itch.io/text-adventure-game`）にアクセス
2. ゲームが正しく表示され、ZIPがダウンロードできることを確認

> **補足**: 詳細な手順と代替方法（butler CLI）については、以下のセクションを参照してください。

---

## 1. itch.io アカウント作成

1. **https://itch.io** にアクセスします。
2. 右上の **「Register」** または **「Sign Up」** をクリックします。
3. ユーザー名（公開プロフィールに表示される名前）、メールアドレス、パスワードを入力します。
4. 登録メールアドレス宛に届く確認メール内のリンクをクリックしてアカウントを有効化します。
5. アカウントが作成されたらログインします。

> **注意**: ユーザー名は後で公開URLの一部になります。
> 例: `https://<ユーザー名>.itch.io/<プロジェクト名>`

---

## 2. プロジェクト（ゲームページ）作成

1. ダッシュボード右上の **「Upload new project」** ボタンをクリックします。
2. 以下の項目を入力・設定します。

   | 項目 | 推奨値 | 説明 |
   |------|--------|------|
   | **Title** | `Text Adventure Game` | ゲームのタイトル（後で変更可能） |
   | **Project URL** | 自動生成 | タイトルから自動生成される一意のスラッグ（後で変更不可） |
   | **Classification** | `Game` | プロジェクトの種別 |
   | **Kind of project** | `HTML` | ダウンロードZIPとして配信する場合は HTML を選択 |
   | **Uploads** | `text-adventure-game.zip` | 次の手順でアップロード |
   | **View this file as** | `A file that will be downloaded by players` | ZIPをダウンロード形式で配信 |

3. 必要に応じて以下の項目も設定します。
   - **Description**: ゲームの説明文（README.md の内容をコピー推奨）
   - **Screenshots**: ゲームプレイ画面のスクリーンショット（あれば）
   - **Tags**: `text-adventure`, `python`, `interactive-fiction` など

4. **「Save & view page」** をクリックして公開します。

---

## 3. ZIPファイルのアップロード

### 方法A：Webブラウザからアップロード（簡単）

1. プロジェクト編集画面を開きます（ダッシュボード → 該当プロジェクト → 「Edit project」）。
2. **「Uploads」** セクションまでスクロールします。
3. `/workspace/project/dist/text-adventure-game.zip` をドラッグ＆ドロップするか、ファイル選択ダイアログからアップロードします。
4. **「View this file as」** で **「A file that will be downloaded by players」** を選択します。
5. ページ下部の **「Save & view page」** をクリックして反映します。

### 方法B：butler CLI でアップロード（上級者向け）

更新が頻繁な場合は公式 CLI ツール `butler` を使用すると効率的です。

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

> **補足**: `butler push` の構文は `butler push <ZIPファイル> <ユーザー名>/<プロジェクトスラッグ>:<チャンネル>` です。
> チャンネル名は任意（例: `windows-linux-mac`, `html`, `download` 等）ですが、一貫性を持たせてください。

---

## 4. README.md の URL 確認

`README.md` 内のURLはすべて実際のユーザー名 `thefoggymind` に置換済みです。以下のURLが正しく設定されていることを確認してください。

| # | 確認するURL | 行番号（目安） |
|---|-----------|--------------|
| 1 | `https://thefoggymind.itch.io/text-adventure-game` | 86行目 |
| 2 | `thefoggymind/text-adventure-game:windows-linux-mac` | 153行目 |
| 3 | `https://github.com/thefoggymind/text-adventure-game/releases` | 164行目 |
| 4 | `https://github.com/thefoggymind/text-adventure-game/releases/download/v1.0.0/text-adventure-game.zip` | 171行目 |
| 5 | `https://ko-fi.com/thefoggymind` | 177行目 |
| 6 | `https://github.com/thefoggymind/text-adventure-game` | 184行目 |

---

## 5. 補足情報

### 配布パッケージの再生成

ゲームファイルを更新したら、以下のコマンドで配布用ZIPを再生成してください。

```bash
cd /workspace/project
bash create_dist.sh
```

生成先: `/workspace/project/dist/text-adventure-game.zip`

### テストの実行

公開前に全エンディングが正しく動作することを確認してください。

```bash
cd /workspace/project
python -m pytest test_all_endings.py -v
```

または直接実行：

```bash
cd /workspace/project
python test_all_endings.py
```

### 更新時の流れ

1. `game.py` を修正
2. `python test_all_endings.py` でテスト
3. `bash create_dist.sh` でZIP再生成
4. （Webブラウザ方式）ZIPを itch.io プロジェクトに再アップロード
5. （butler方式）`butler push` で更新

---

## 6. 公開前最終チェックリスト

公開直前に以下の項目をすべて確認し、チェックを入れてください。

- [x] **プレースホルダー置換**: `README.md` 内の `my-game-dev` → `thefoggymind` に置換済み
- [x] **プレースホルダー置換**: `README.md` 内の `your-ko-fi-id` → `thefoggymind` に置換済み
- [x] **プレースホルダー置換**: `game.py` 内の `DONATION_URL` → `https://ko-fi.com/thefoggymind` に置換済み
- [ ] **テスト実行**: `python test_all_endings.py` を実行し、全6エンディングが正常に動作することを確認した
- [ ] **ZIP再生成**: `bash create_dist.sh` を実行し、`dist/text-adventure-game.zip` を最新版に更新した
- [ ] **ZIP内容確認**: ZIP 内に `game.py`, `README.md`, `LICENSE` の3ファイルが正格納されていることを確認した
- [ ] **itch.io アップロード**: `dist/text-adventure-game.zip` を itch.io のプロジェクトページにアップロードした
- [ ] **公開URL確認**: アップロード後に公開URL（`https://thefoggymind.itch.io/text-adventure-game`）にアクセスし、正しくダウンロードできることを確認した

---

## 7. 公開後の最終作業

itch.io へのアップロードと公開が完了したら、以下の作業を行ってください。

### 7.0 自動化スクリプトで一括処理（推奨）

`post_publish.sh` を使用すると、注意書き削除とZIP再生成を一度に実行できます。

```bash
cd /workspace/project
bash post_publish.sh
```

このスクリプトは以下の処理を自動で行います。
1. `README.md` の公開前注意書きを削除
2. 配布ZIPを再生成（`bash create_dist.sh`）

注意書き削除後の状態や各処理を手動で確認したい場合は、以下の個別手順（7.1〜7.4）を参照してください。

### 7.1 README.md の注意書きを削除

`README.md` 86行目に以下の注意書きが残っています：

```
（⚠ 公開前のURLです。itch.ioへのアップロード完了後に有効になります。アップロード後は本カッコ書きを削除し、ZIPを再生成してください）
```

公開が完了したら、このカッコ書き全体を削除してください（`post_publish.sh` を実行した場合は自動で削除されます）。削除後の行は以下のようになります。

```markdown
- **公開URL**: [https://thefoggymind.itch.io/text-adventure-game](https://thefoggymind.itch.io/text-adventure-game)
```

### 7.2 ZIP を再生成

README.md を修正したら、配布ZIPを再生成します（`post_publish.sh` を実行した場合は自動で再生成されます）。

```bash
cd /workspace/project
bash create_dist.sh
```

### 7.3 再生成したZIPを itch.io に再アップロード

1. ダッシュボードから該当プロジェクトの **「Edit project」** を開く
2. **Uploads** セクションで新しい `text-adventure-game.zip` をドラッグ＆ドロップ（上書き）
3. **「Save & view page」** をクリック

### 7.4 完了確認

- 公開URL（`https://thefoggymind.itch.io/text-adventure-game`）にアクセスし、ZIPがダウンロードできることを確認
- ダウンロードしたZIPを解凍し、`python game.py` でゲームが起動することを確認

---

*作成日: 2026年8月9日*