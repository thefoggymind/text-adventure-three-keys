# SPEC: 「3つの鍵 — Web Edition」

> 作成日: 2026-08-09
> ベース: `/workspace/project/game.py`（Python製テキストアドベンチャー、6エンディング）
> 選定元: `/workspace/project/PROPOSAL.md` プロジェクト案A

---

## 1. プロジェクト概要

### 1.1 コンセプト
既存のPython製テキストアドベンチャー「3つの鍵」（6エンディング）を、ブラウザで動作するWebアプリケーションとしてフル移植する。
サーバーサイド不要の完全静的サイトとして構築し、GitHub Pages / itch.io でゼロコスト公開する。

### 1.2 移植元
| 項目 | 内容 |
|------|------|
| ソース | `/workspace/project/game.py`（2,236 bytes / 236行） |
| エンディング数 | 6（左勝利 / 左敗北 / 右勝利 / 右敗北 / 中立 / 隠し） |
| 状態管理 | インベントリ（文字列リスト）+ searched フラグ + ランダム勝敗 |
| 収益化 | Ko-fi 寄付リンク（`https://ko-fi.com/thefoggymind`） |
| テスト | `/workspace/project/test_all_endings.py`（19テスト、全6ED到達確認） |

### 1.3 開発原則
- **フレームワーク不使用**: vanilla JS (ES2020+) + HTML5 + CSS3（最小依存）
- **完全静的**: サーバーサイド不要、GitHub Pages / itch.io にホスティング可能
- **モバイルファースト**: スマートフォンでのプレイを最優先
- **段階的拡張**: Phase1（コア移植）→ Phase4（公開）の4フェーズ

---

## 2. 画面構成

### 2.1 画面一覧

| # | 画面ID | 画面名 | 表示タイミング | 備考 |
|---|--------|--------|---------------|------|
| 1 | `title` | タイトル画面 | アプリ起動時 | ブラウザ開いて最初に表示 |
| 2 | `game` | ゲーム画面 | 「はじめる」選択後 | テキスト表示＋選択肢 |
| 3 | `ending` | エンディング画面 | 各エンディング到達時 | 結果表示＋寄付リンク |

### 2.2 タイトル画面 (`title`)

```
┌──────────────────────────────────┐
│                                  │
│    ⚔  ⚔  ⚔                      │
│   3つの鍵 — Web Edition          │
│    ⚔  ⚔  ⚔                      │
│                                  │
│       [ はじめる ]               │
│       [ つづきから ] ← セーブあれば表示 │
│                                  │
│     ver 1.0.0                    │
│     © thefoggymind               │
│                                  │
│  支援: [Ko-fi]                   │
└──────────────────────────────────┘
```

**構成要素**:
- ゲームタイトルロゴ（CSS装飾）
- 「はじめる」ボタン（新規ゲーム開始）
- 「つづきから」ボタン（セーブデータ存在時のみ表示、グレーアウト不可）
- バージョン表記 + コピーライト
- Ko-fi 寄付リンク（フッターアイコン）

### 2.3 ゲーム画面 (`game`)

```
┌──────────────────────────────────┐
│  📖 3つの鍵                      │
├──────────────────────────────────┤
│                                  │
│  あなたは森の中で目覚めました。    │
│  前には二つの道があります。        │
│                                  │
│  何をしますか？                   │
│                                  │
│  ┌──────────────────────────┐   │
│  │ [1] 左の道を進む          │   │
│  │ [2] 右の道を進む          │   │
│  │ [3] 冒険をあきらめて帰る  │   │
│  │ [4] 周辺を探索する        │   │  ← 未探索時のみ表示
│  └──────────────────────────┘   │
│                                  │
│  🎒 アイテム: 錆びた鍵, 古い地図  │
│                                  │
├──────────────────────────────────┤
│  ☰ メニュー    💾 セーブ         │
└──────────────────────────────────┘
```

**構成要素**:
| 領域 | 要素 | 説明 |
|------|------|------|
| ヘッダー | ゲームタイトル + ハンバーガーメニュー | 常時固定表示 |
| メイン | ストーリーテキスト表示エリア | スクロール可能、最新テキストが下 |
| 選択肢 | ボタンリスト | 条件により動的に表示数変更（1-3 or 1-4） |
| ステータス | インベントリ表示 | 所持アイテムをカンマ区切りで表示 |
| フッター | メニュー / セーブボタン | ゲーム進行中は常時表示 |

**画面遷移**:
- 選択肢押下 → 次テキストへ遷移（同一画面内でテキスト更新）
- 左/右の道選択後、勝敗分岐 → `ending` 画面へ
- 「あきらめて帰る」選択 → `ending` 画面（中立ED）へ
- 探索（4番）→ アイテム獲得後、再び選択肢表示

### 2.4 エンディング画面 (`ending`)

```
┌──────────────────────────────────┐
│                                  │
│  ═══════════════════════════════  │
│    --- ★ 真の英雄 ★ ---         │
│  ═══════════════════════════════  │
│                                  │
│  あなたは錆びた鍵と古い地図を手に │
│  隠された洞窟の入り口を発見した… │
│   （ストーリーテキスト）          │
│                                  │
│  ────────────────────────────    │
│  全6エンディング中 1/6 コンプリート│
│  [█████░░░░░░░░░░░░░░░] 17%     │
│  ────────────────────────────    │
│                                  │
│      [ タイトルに戻る ]           │
│      [ もう一度遊ぶ ]             │
│                                  │
│  ☕ このゲームを気に入ったら       │
│  寄付で支援してください           │
│  [☕ Ko-fiで支援する]             │
│                                  │
└──────────────────────────────────┘
```

**構成要素**:
| 要素 | 説明 |
|------|------|
| エンディングタイトル | 装飾付き（--- ★ 真の英雄 ★ --- 等） |
| エンディングストーリー | エンディングごとの個別テキスト |
| コンプリート進捗バー | LocalStorageに保存された実績から計算 |
| 「タイトルに戻る」ボタン | `title` 画面へ遷移 |
| 「もう一度遊ぶ」ボタン | `game` 画面へ新規開始 |
| Ko-fi寄付リンク | Python版の `show_donation_message()` に相当 |

**エンディング種別と表示装飾**:

| # | ED名 | タイトル装飾 | 条件 |
|---|------|------------|------|
| 1 | left_win | 「--- 勝利：清らかな川 ---」 | 左の道で勝ち |
| 2 | left_lose | 「--- 敗北：毒の川 ---」 | 左の道で負け |
| 3 | right_win | 「--- 勝利：古代の宝具 ---」 | 右の道で勝ち |
| 4 | right_lose | 「--- 敗北：呪いの遺物 ---」 | 右の道で負け |
| 5 | neutral | 「--- 中立：帰還 ---」 | 「あきらめて帰る」選択 |
| 6 | hidden | 「--- ★ 真の英雄 ★ ---」 | 鍵＋地図所持＋洞窟探索(y) |

---

## 3. ゲームロジック

### 3.1 状態管理

JavaScript のゲーム状態は単一の状態オブジェクトで管理する。

```typescript
interface GameState {
  // 画面状態
  screen: 'title' | 'game' | 'ending';
  
  // ゲーム進行状態
  phase: 'intro' | 'menu' | 'left_path' | 'right_path' | 'ending';
  
  // プレイヤー状態
  inventory: string[];          // 所持アイテム名の配列
  itemKey: boolean;            // Rusty Key 所持フラグ（簡易参照用）
  itemMap: boolean;            // Old Map 所持フラグ（簡易参照用）
  itemJewel: boolean;          // Shining Jewel 所持フラグ（簡易参照用）
  
  // 探索状態
  searched: boolean;           // 周辺探索実施済みか
  
  // 分岐結果
  outcome: 'none' | 'win' | 'lose';
  
  // 表示用
  displayText: string[];       // 画面表示テキストの行配列
  choices: Choice[];           // 現在の選択肢リスト
  
  // 実績
  endingsUnlocked: string[];   // 解除済みエンディングID一覧
  
  // メタ
  createdAt: string;           // ゲーム開始日時（ISO8601）
  updatedAt: string;           // 最終更新日時
}
```

### 3.2 定数定義

Python版の定数をJSに移植:

```javascript
// game.py からの移植 (lines 22-38)
const CHOICES = {
  LEFT: '1',
  RIGHT: '2',
  GIVE_UP: '3',
  SEARCH: '4',
};

const RESULTS = {
  WIN: 'win',
  LOSE: 'lose',
  NEUTRAL: 'neutral',
  HIDDEN: 'hidden',
};

const ITEMS = {
  JEWEL: 'Shining Jewel',
  KEY: 'Rusty Key',
  MAP: 'Old Map',
};

const DONATION_URL = 'https://ko-fi.com/thefoggymind';
const GAME_TITLE = '3つの鍵 — Web Edition';
const MAX_ENDINGS = 6;
```

### 3.3 分岐ロジック（Python→JS 移植対応表）

| Python関数 (game.py) | 行 | JS移植先 | 移植方式 |
|----------------------|-----|---------|---------|
| `_random_outcome()` | 59-85 | `randomOutcome()` | 同ロジック: `Math.random() < 0.5` |
| `left_path()` | 88-103 | `leftPath()` | テキスト表示 + 勝敗分岐 |
| `right_path()` | 106-117 | `rightPath()` | テキスト表示 + 勝敗分岐 |
| `neutral_ending()` | 122-133 | `neutralEnding()` | テキスト表示 |
| `hidden_ending()` | 136-153 | `hiddenEnding()` | テキスト表示 |
| `search_area()` | 158-165 | `searchArea()` | アイテム追加 |
| `check_hidden_path()` | 168-181 | `checkHiddenPath()` | 条件判定 + confirm |
| `show_menu()` | 186-200 | `renderChoices()` | DOM生成に変更 |
| `show_donation_message()` | 43-47 | `showDonation()` | Ko-fiリンク表示 |
| `show_ending_header()` | 50-54 | `renderEndingHeader()` | DOM生成に変更 |
| `main()` | 205-236 | `gameLoop(choice)` | イベント駆動に変更 |

### 3.4 フロー図

```
[起動] → title画面
           │
           ├─ 「はじめる」 → 状態初期化 → game画面 (intro)
           │                                   │
           │                             メニュー表示
           │                                   │
           │      ┌── 1: 左の道 ──┐      ┌── 2: 右の道 ──┐
           │      │               │      │               │
           │  隠し条件確認 ─┐    ┌── 隠し条件確認 ─┐    │
           │   │          │    │   │          │    │
           │  条件満たす     満たさない   満たさない    条件満たす
           │   │          │    │   │          │    │
           │  洞窟探索?    左の道   右の道    洞窟探索?
           │  y│  n│    │    │   │  n│  y│
           │   │  │  左勝利 左敗北 右勝利 右敗北  │   │
           │   │  │    │    │    │    │   │   │
           │ ★隠しED  │    │    │    │    │  ★隠しED
           │   │      │    │    │    │    │    │
           │   └──────┴────┴────┴────┴────┘    │
           │               │                    │
           │          ending画面                │
           │               │                    │
           │          ┌────┴────┐               │
           │    タイトルに戻る  もう一度         │
           └─────────────────────────────────────┘
           
           3: 帰る → neutralED → ending画面
           4: 探索 → アイテム獲得 → メニュー再表示
```

### 3.5 ランダム勝敗ロジック（`randomOutcome()`）

```javascript
/**
 * 50% 確率で勝敗を決める。Python版 _random_outcome() の移植。
 * @param {string} msgWin - 勝利時のメッセージ
 * @param {string} msgLose - 敗北時のメッセージ
 * @param {string|null} itemOnWin - 勝利時に追加するアイテム名（任意）
 * @returns {string} 'win' | 'lose'
 */
function randomOutcome(msgWin, msgLose, itemOnWin = null) {
  if (Math.random() < 0.5) {
    addDisplayText('--- 勝利！ ---');
    addDisplayText(msgWin);
    if (itemOnWin) {
      state.inventory.push(itemOnWin);
      updateItemFlags();
    }
    return RESULTS.WIN;
  } else {
    addDisplayText('--- 敗北 ---');
    addDisplayText(msgLose);
    return RESULTS.LOSE;
  }
}
```

### 3.6 テキスト管理

ゲーム内テキストはすべて日本語固定（Phase2移行でi18n対応検討）。
テキストデータはJSの定数オブジェクトとして一元管理する。

```javascript
const STORY = {
  intro: [
    'テキストベースアドベンチャーゲームへようこそ！',
    'あなたは森の中で目覚めました。前には二つの道があります。',
  ],
  menu: {
    prompt_searched: '選択肢を入力してください (1-3):',
    prompt_unsearched: '選択肢を入力してください (1-4):',
    choice_left: '左の道を進む',
    choice_right: '右の道を進む',
    choice_giveup: '冒険をあきらめて帰る',
    choice_search: '周辺を探索する',
  },
  left_path: {
    desc: 'あなたは左の道を進み、きらめく川を見つけました。',
    desc2: '川のほとりで休憩し、水を飲むことにしました。',
    win: '川の水は清らかで、エネルギーを完全に回復しました。\nあなたは無事に森を抜け出すことができました。\nさらに、川岸で輝く宝石を手に入れました！',
    lose: '川の水は毒されており、あなたは体調を崩してしまいました。\n森の中で倒れてしまいました…。',
  },
  right_path: { /* ... */ },
  // ... 以下全テキスト
};
```

---

## 4. セーブ機能（LocalStorage）

### 4.1 保存データ構造

```javascript
interface SaveData {
  version: 1;                        // セーブデータフォーマットバージョン
  timestamp: string;                 // 保存日時（ISO8601）
  gameState: {
    phase: string;                   // 現在のフェーズ
    inventory: string[];             // インベントリ
    searched: boolean;               // 探索済みフラグ
    displayText: string[];           // 表示テキスト履歴（最後の10行まで）
  };
  achievements: {
    endingsUnlocked: string[];       // 解除済みエンディングID一覧
    totalPlayCount: number;          // 総プレイ回数
  };
}
```

### 4.2 キー設計

| LocalStorage Key | 内容 | 保存タイミング |
|-----------------|------|--------------|
| `three-keys-save-v1` | ゲーム進行状態 | プレイヤーが「セーブ」押下時 / 自動セーブ（オプション） |
| `three-keys-achievements-v1` | 実績データ | エンディング到達時（毎回） |
| `three-keys-settings-v1` | ユーザー設定（BGM音量等） | Phase2以降 |

### 4.3 API設計（`storage.js`）

```javascript
class SaveManager {
  static SAVE_KEY = 'three-keys-save-v1';
  static ACHIEVEMENT_KEY = 'three-keys-achievements-v1';
  static SETTINGS_KEY = 'three-keys-settings-v1';

  /**
   * ゲーム進行状態を保存。
   * @param {GameState} state
   */
  static save(state) { /* ... */ }

  /**
   * ゲーム進行状態を復元。存在しない場合は null を返す。
   * @returns {SaveData|null}
   */
  static load() { /* ... */ }

  /**
   * セーブデータの存在確認。
   * @returns {boolean}
   */
  static hasSave() { /* ... */ }

  /**
   * セーブデータを削除。
   */
  static deleteSave() { /* ... */ }

  /**
   * 実績（解除済みエンディング）を記録。
   * @param {string} endingId
   */
  static recordEnding(endingId) { /* ... */ }

  /**
   * 全実績データを取得。
   * @returns {{ endingsUnlocked: string[], totalPlayCount: number }}
   */
  static getAchievements() { /* ... */ }

  /**
   * すべての保存データを消去。
   */
  static clearAll() { /* ... */ }
}
```

### 4.4 セーブ・ロードフロー

```
【セーブ】
プレイヤーが「💾 セーブ」押下
  → SaveManager.save(state)
  → localStorage.setItem(SAVE_KEY, JSON.stringify(data))
  → 「セーブしました」トースト通知

【ロード（タイトル画面）】
アプリ起動
  → SaveManager.hasSave() ? true
  → 「つづきから」ボタンを表示
  → プレイヤーが「つづきから」押下
  → SaveManager.load()
  → GameState に展開
  → 該当 phase からゲーム再開

【ロード（エラーハンドリング）】
JSON.parse 失敗
  → セーブデータ破損と判断
  → セーブデータ削除
  → 「セーブデータが破損していたため初期化しました」表示
  → 新規ゲーム開始
```

### 4.5 制約事項

| 項目 | 制約 |
|------|------|
| 保存容量 | LocalStorage 上限 ~5MB（テキストのみなので問題なし） |
| 保存数 | 1スロットのみ（Phase2で複数スロット検討） |
| 自動セーブ | Phase1では手動セーブのみ（Phase3で10分ごと自動セーブ追加） |
| オフライン | LocalStorage はオフラインでも動作 |
| データ消失 | ユーザーがブラウザデータ消去時は消失 |

---

## 5. UI/UX仕様

### 5.1 デザイン原則
- **ミニマル**: 装飾より可読性重視。背景は淡色、テキストは高コントラスト
- **ノスタルジック**: 古のテキストアドベンチャー風の雰囲気（オプションでダークテーマ）
- **タップ操作最適化**: スマートフォンでのタップを想定し、ボタンサイズは 44px 以上

### 5.2 レスポンシブデザイン

| ブレークポイント | 対象 | レイアウト |
|----------------|------|-----------|
| ~ 480px | スマートフォン | 1カラム、ボタン全面 |
| 481px ~ 768px | タブレット | 1カラム、最大幅 600px 中央寄せ |
| 769px ~ | デスクトップ | 1カラム、最大幅 720px 中央寄せ + 装飾枠 |

### 5.3 カラースキーム

| ロール | 色（ライト） | 色（ダーク） | 用途 |
|--------|------------|------------|------|
| 背景 | `#f5f0e8` (生成り) | `#1a1a2e` | 画面全体 |
| メインテキスト | `#2c2c2c` | `#e8e8e8` | ストーリーテキスト |
| 選択肢ボタン | `#4a6741` (深緑) | `#6b8f5e` | 通常選択肢 |
| ボタンテキスト | `#ffffff` | `#ffffff` | 選択肢ラベル |
| アクセント | `#c9a96e` (金色) | `#d4af37` | エンディング装飾・アイコン |
| 危険 | `#8b3a3a` | `#b04a4a` | 敗北ED・警告 |
| リンク | `#4a7c9b` | `#7ab8d4` | Ko-fi等 |

### 5.4 タイポグラフィ

| 要素 | フォント | サイズ | ウェイト |
|------|---------|--------|---------|
| タイトル | `'Georgia', serif` | 2.0rem | 700 |
| ストーリーテキスト | `'Noto Sans JP', sans-serif` | 1.0rem (16px) | 400 |
| 選択肢 | `'Noto Sans JP', sans-serif` | 1.0rem | 500 |
| インベントリ | `'Noto Sans JP', sans-serif` | 0.875rem | 400 |
| フッターリンク | `'Noto Sans JP', sans-serif` | 0.75rem | 400 |

### 5.5 画面遷移・アニメーション

| 要素 | アニメーション | 時間 | 備考 |
|------|--------------|------|------|
| 画面切り替え | `fadeIn` / `fadeOut` | 300ms | opacity 0→1 |
| テキスト表示 | 一行ずつ `typewriter` | 30ms/字 | Phase2で実装（実装任意） |
| ボタンホバー | `scale(1.02)` + `box-shadow` | 200ms | タップ時も同様 |
| トースト通知 | `slideIn` (上から) | 250ms | セーブ完了等 |

### 5.6 キーボードショートカット（デスクトップ用）

| キー | 動作 |
|------|------|
| `1` / `2` / `3` / `4` | 選択肢を選択 |
| `Enter` | 選択確定（フォーカス中のボタンをクリック） |
| `s` / `S` | セーブ |
| `Esc` | 確認ダイアログ：「ゲームを終了しますか？」 |

### 5.7 アクセシビリティ

| 要件 | 対応 |
|------|------|
| ARIAラベル | 全ボタン・アイコンに `aria-label` 設定 |
| フォーカス管理 | 画面遷移時に適切な要素にフォーカス移動 |
| 色覚多様性 | 色＋記号（⚠ ★）で情報を伝達 |
| フォントサイズ | ブラウザの文字サイズ変更に対応（相対単位使用） |
| スクリーンリーダー | テキスト更新時に `aria-live="polite"` で通知 |

---

## 6. ファイル構成

```
/workspace/project/web_adventure/
├── index.html              # メインページ（全画面をSPAで実装）
├── css/
│   └── style.css           # 全スタイル（リセット + レイアウト + テーマ）
├── js/
│   ├── game.js             # ゲームエンジン（状態管理 + 分岐ロジック）
│   ├── renderer.js         # DOMレンダリング（全画面の描画）
│   ├── storage.js          # LocalStorage セーブ/ロード
│   └── constants.js        # 定数・テキストデータ
├── assets/
│   ├── favicon.ico         # ファビコン
│   └── ogp.png             # OGP画像（SNSシェア用）
├── SPEC.md                 # ← 本ファイル
├── README.md               # セットアップ・開発方法
└── dist/
    └── three-keys-web.zip  # 配布用ZIP（Phase4で作成）
```

### 6.1 ファイル責務

| ファイル | 責務 | サイズ目安 |
|---------|------|-----------|
| `index.html` | HTML骨格、SPAコンテナ、OGPタグ、アセット読み込み | ~2KB |
| `style.css` | 全スタイル定義、レスポンシブ、アニメーション、ダークテーマ変数 | ~8KB |
| `game.js` | ゲームFMS、状態管理、分岐ロジック、イベントハンドラ | ~15KB |
| `renderer.js` | DOM構築、画面切り替え、テキスト表示、選択肢レンダリング | ~10KB |
| `storage.js` | LocalStorage読み書き、保存データ管理、実績管理 | ~4KB |
| `constants.js` | ゲーム内定数、全テキストデータ、設定値 | ~8KB |

---

## 7. Pythonコードからの移植ポイント

### 7.1 ロジック直接移植（変更不要）

| Python | JavaScript | 備考 |
|--------|-----------|------|
| `random.random() < 0.5` | `Math.random() < 0.5` | 同一ロジック |
| `inventory.append(item)` | `state.inventory.push(item)` | 配列操作のみ |
| `item in inventory` | `state.inventory.includes(item)` | 存在確認 |
| `input().strip()` | `const choice = e.target.dataset.value` | イベント駆動に変更 |
| `print(...)` | `addDisplayText(...)` + DOM更新 | 表示系はrendererに委譲 |
| `if/elif/else` 分岐 | 同様の if/else if/else | 構造はそのまま |
| 文字列連結（f-stringなし） | テンプレートリテラル | `\n` は `<br>` に変換 |

### 7.2 アーキテクチャ変更が必要な箇所

| Python (CLI) | Web (JS) | 理由 |
|-------------|----------|------|
| `input()` ブロッキング待機 | イベント駆動 + コールバック | Webは非同期イベントループ |
| `main()` 関数内ループ | 状態機械 + レンダリング関数 | DOM更新には状態が必要 |
| `print()` 逐次出力 | テキストバッファ → 一括レンダリング | スクロール制御のため |
| グローバル関数 | ES Module / 名前空間オブジェクト | スコープ管理のため |
| 単一ファイル (236行) | 5ファイルに分割 | 責務分離のため |

### 7.3 追加実装が必要な箇所（Python版に存在しない機能）

| 機能 | 該当ファイル | 理由 |
|------|------------|------|
| SPA画面ルーター | `game.js` | タイトル→ゲーム→エンディング画面遷移 |
| DOMレンダリング | `renderer.js` | CLIには不要なWeb特有の処理 |
| スタイル定義 | `style.css` | 同上 |
| LocalStorage入出力 | `storage.js` | 同上 |
| レスポンシブ対応 | `style.css` | 同上 |
| タッチイベント対応 | `game.js` + `renderer.js` | モバイル対応のため |
| OGP / ファビコン | `index.html` (`<head>`) | SNSシェア用 |
| 実績管理（進捗バー） | `storage.js` + `renderer.js` | エンディング画面のリプレイ性向上 |

### 7.4 既存テストの活用

`/workspace/project/test_all_endings.py`（19テスト）はJS移植後に以下の形で活用:

| Pythonテスト | JSでの検証方法 |
|-------------|---------------|
| 各ED到達確認（6テスト） | `game.js` の分岐ロジックをJest/Vitestで単体テスト |
| 無効入力→再入力（4テスト） | 選択肢ボタン制限 + イベントハンドラテスト |
| アイテム条件（3テスト） | `checkHiddenPath()` 条件分岐テスト |
| セーブ/ロード（新規） | `storage.js` の単体テスト（localStorageモック使用） |
| E2Eテスト（新規） | Playwright で全ED到達のブラウザテスト |

---

## 8. フェーズ分割

### Phase1: コアロジック移植（目標: 1週目）

**目標**: Python版と機能的に同等のWebアプリ（MVP）を完成させる。

| # | タスク | ファイル | 見積もり |
|---|-------|---------|---------|
| 1.1 | プロジェクトディレクトリ作成・ファイル構成準備 | 全体 | 0.5h |
| 1.2 | `constants.js` 作成：全定数・テキストデータのJS移植 | `js/constants.js` | 2h |
| 1.3 | `game.js` 作成：状態管理 + 全分岐ロジックのJS移植 | `js/game.js` | 4h |
| 1.4 | `renderer.js` 作成：タイトル画面・ゲーム画面・ED画面レンダリング | `js/renderer.js` | 4h |
| 1.5 | `index.html` 作成：SPA骨格 + アセット読み込み | `index.html` | 1h |
| 1.6 | `style.css` 作成：基本レイアウト + レスポンシブ | `css/style.css` | 3h |
| 1.7 | 全6エンディング到達の動作確認（手動） | 全体 | 1h |
| 1.8 | バグ修正・エッジケース対応 | 全体 | 2h |

**成果物**: ブラウザで遊べるMVP（Python版と完全互換の6ED + インベントリ）
**合計工数**: 約17.5h

### Phase2: UI/UX実装（目標: 2週目）

**目標**: リッチなユーザー体験を提供するUIを実装する。

| # | タスク | ファイル | 見積もり |
|---|-------|---------|---------|
| 2.1 | ダークテーマ / ライトテーマ切替機能 | `style.css`, `renderer.js` | 2h |
| 2.2 | タイプライターアニメーション実装 | `renderer.js`, `style.css` | 2h |
| 2.3 | 画面遷移フェードアニメーション | `style.css` | 1h |
| 2.4 | キーボードショートカット対応 (1-4, s, Esc) | `game.js` | 1h |
| 2.5 | アクセシビリティ対応（ARIAラベル, フォーカス管理） | `renderer.js`, `index.html` | 2h |
| 2.6 | スマホ表示最適化・タッチイベント調整 | `style.css`, `game.js` | 2h |
| 2.7 | OGP設定・ファビコン・SNSシェア対応 | `index.html` | 0.5h |

**成果物**: アニメーション・テーマ切り替え・キーボード操作に対応したリッチUI
**合計工数**: 約10.5h

### Phase3: セーブ機能（目標: 3週目）

**目標**: ゲーム進行の保存・復元と実績管理を実装する。

| # | タスク | ファイル | 見積もり |
|---|-------|---------|---------|
| 3.1 | `storage.js` 作成：SaveManager クラス実装（save/load/hasSave/deleteSave） | `js/storage.js` | 3h |
| 3.2 | タイトル画面の「つづきから」ボタン連携 | `renderer.js`, `game.js` | 1h |
| 3.3 | ゲーム画面内「💾 セーブ」ボタン実装 + トースト通知 | `renderer.js`, `game.js` | 1h |
| 3.4 | エンディング到達時の自動実績保存 | `game.js`, `storage.js` | 1h |
| 3.5 | エンディング画面のコンプリート進捗バー表示 | `renderer.js`, `storage.js` | 1.5h |
| 3.6 | セーブデータ破損検出 + フォールバック処理 | `storage.js` | 1h |
| 3.7 | 複数スロット対応の設計・実装（拡張） | `storage.js`, `renderer.js` | 2h |
| 3.8 | セーブデータの単体テスト（localStorageモック） | `tests/storage.test.js` | 2h |

**成果物**: セーブ/ロードが可能な本格的なWebゲーム体験
**合計工数**: 約12.5h

### Phase4: 公開・収益化（目標: 4週目）

**目標**: GitHub Pages と itch.io で公開し、収益化を開始する。

| # | タスク | ファイル | 見積もり |
|---|-------|---------|---------|
| 4.1 | GitHub Pages 用設定（`docs/` or `gh-pages` ブランチ） | GitHub設定 | 0.5h |
| 4.2 | 配布用ZIP生成スクリプト `create_dist.sh` | `dist/` | 1h |
| 4.3 | `README.md` 作成（セットアップ・遊び方・構成） | `README.md` | 1.5h |
| 4.4 | `PUBLISH_GUIDE.md` 作成（itch.io公開手順） | `PUBLISH_GUIDE.md` | 1h |
| 4.5 | GitHub Pages でプレビュー公開・動作確認 | — | 0.5h |
| 4.6 | itch.io プロジェクト作成・ZIPアップロード（人間作業） | — | — |
| 4.7 | Ko-fi リンク・寄付導線確認 | `renderer.js`, `constants.js` | 0.5h |
| 4.8 | 全フェーズの結合テスト・最終確認 | 全体 | 2h |

**成果物**: itch.io で販売開始、収益発生開始
**合計工数**: 約7h（人間作業除く）

---

## 9. 既存コードからの移植対応表（完全網羅）

### 9.1 Python関数 → JS関数 対応

| Python (game.py) | 行 | JS (game.js) | 移植方式 | 変更点 |
|------------------|-----|-------------|---------|--------|
| `_random_outcome()` | 59-85 | `randomOutcome()` | コピー＋微修正 | `print()` → `addDisplayText()` |
| `left_path()` | 88-103 | `leftPath()` | コピー＋微修正 | 同上 |
| `right_path()` | 106-117 | `rightPath()` | コピー＋微修正 | 同上 |
| `neutral_ending()` | 122-133 | `neutralEnding()` | コピー＋微修正 | 同上 |
| `hidden_ending()` | 136-153 | `hiddenEnding()` | コピー＋微修正 | 同上 |
| `search_area()` | 158-165 | `searchArea()` | コピー＋微修正 | `inventory.append` → `push` |
| `check_hidden_path()` | 168-181 | `checkHiddenPath()` | コピー＋微修正 | `input()` → ボタンイベント |
| `show_menu()` | 186-200 | `renderChoices()` | 構造変更 | CLI → DOMレンダリング |
| `show_donation_message()` | 43-47 | `showDonation()` | 構造変更 | CLI → Ko-fiボタン埋め込み |
| `show_ending_header()` | 50-54 | `renderEndingHeader()` | 構造変更 | CLI → DOMレンダリング |
| `main()` | 205-236 | `gameLoop()` / `initGame()` | 構造変更 | CLIループ → イベント駆動 |

### 9.2 Python定数 → JS定数 対応

| Python (game.py) | 値 | JS (constants.js) |
|------------------|-----|------------------|
| `CHOICE_LEFT = "1"` | `"1"` | `CHOICES.LEFT` |
| `CHOICE_RIGHT = "2"` | `"2"` | `CHOICES.RIGHT` |
| `CHOICE_GIVE_UP = "3"` | `"3"` | `CHOICES.GIVE_UP` |
| `CHOICE_SEARCH = "4"` | `"4"` | `CHOICES.SEARCH` |
| `RESULT_WIN = "win"` | `"win"` | `RESULTS.WIN` |
| `RESULT_LOSE = "lose"` | `"lose"` | `RESULTS.LOSE` |
| `RESULT_NEUTRAL = "neutral"` | `"neutral"` | `RESULTS.NEUTRAL` |
| `RESULT_HIDDEN = "hidden"` | `"hidden"` | `RESULTS.HIDDEN` |
| `ITEM_JEWEL = "Shining Jewel"` | `"Shining Jewel"` | `ITEMS.JEWEL` |
| `ITEM_KEY = "Rusty Key"` | `"Rusty Key"` | `ITEMS.KEY` |
| `ITEM_MAP = "Old Map"` | `"Old Map"` | `ITEMS.MAP` |
| `DONATION_URL` | `"https://ko-fi.com/thefoggymind"` | `DONATION_URL` |

### 9.3 Python型ヒント → JSDoc 対応

| Python | JSDoc |
|--------|-------|
| `inventory: List[str]` | `@param {string[]} inventory` |
| `item_on_win: str \| None = None` | `@param {string|null} [itemOnWin=null]` |
| `-> str` | `@returns {string}` |
| `-> bool` | `@returns {boolean}` |
| `-> None` | `@returns {void}` |

### 9.4 テスト移植計画

| Pythonテストファイル | JSテストファイル | テストフレームワーク |
|---------------------|-----------------|-------------------|
| `test_all_endings.py` (19 tests) | `tests/game.test.js` | Vitest |
| — (新規) | `tests/storage.test.js` | Vitest + localStorage mock |
| — (新規) | `tests/renderer.test.js` | Vitest + jsdom |
| — (新規) | `tests/e2e/endings.spec.js` | Playwright |

---

## 10. 非機能要件

### 10.1 パフォーマンス目標

| 指標 | 目標値 | 測定方法 |
|------|-------|---------|
| 初回読み込み完了 | < 2秒 (3G) | Lighthouse |
| インタラクティブ準備完了 | < 3秒 (3G) | Lighthouse |
| バンドルサイズ | < 200KB total | ファイルサイズ合計 |
| FPS（選択肢表示時） | 60fps | Chrome DevTools |
| LocalStorage読み込み | < 10ms | `performance.now()` |

### 10.2 ブラウザ対応

| ブラウザ | 対応 |
|---------|------|
| Google Chrome (最新2メジャーバージョン) | ✅ プライマリ対応 |
| Firefox (最新2メジャーバージョン) | ✅ セカンダリ対応 |
| Safari (最新2メジャーバージョン) | ✅ セカンダリ対応 |
| Edge (Chromium) | ✅ セカンダリ対応 |
| iOS Safari (最新2バージョン) | ✅ モバイルプライマリ |
| Android Chrome (最新2バージョン) | ✅ モバイルプライマリ |

### 10.3 セキュリティ

| 項目 | 対応 |
|------|------|
| スクリプト | サードパーティスクリプト不使用（CDNフォントのみ） |
| LocalStorage | 機密情報は保存しない（ゲームデータのみ） |
| XSS | `innerHTML` 不使用、`textContent` でテキスト挿入 |
| CSP | `<meta http-equiv="Content-Security-Policy">` 設定 |

### 10.4 オフライン対応

| Phase | 対応内容 |
|-------|---------|
| Phase1-2 | オンライン必須（CDNフォント読み込みのため） |
| Phase3 | Service Worker によるオフラインキャッシュ（PWA化） |
| Phase4 | 完全オフライン動作対応（フォントをセルフホスト） |

---

## 11. 運用設計

### 11.1 ホスティング

```
[開発] localhost:5500 (Live Server)
   ↓ git push
[ステージング] GitHub Pages (https://thefoggymind.github.io/three-keys-web/)
   ↓ ZIPアップロード
[本番] itch.io (https://thefoggymind.itch.io/three-keys-web)
```

### 11.2 バージョン管理

| 種別 | 形式 | 例 |
|------|------|-----|
| タグ | `v1.0.0` | リリースポイント |
| ブランチ | `main` / `develop` / `feature/*` | Git Flow準拠 |
| セーブ互換性 | メジャーバージョンのみ破棄可能 | `version` フィールドで管理 |

### 11.3 収支試算

| 期間 | 費用 | 収入（保守的） | 累計収支 |
|------|------|---------------|---------|
| Phase1-3 (開発期間) | 0円 | 0円 | 0円 |
| 公開初月 | 0円 | 3,000円 | +3,000円 |
| 3ヶ月目 | 0円 | 1,500円/月 | +6,000円 |
| 6ヶ月目 | 0円 | 1,000円/月 | +9,000円 |
| 12ヶ月目 | 0円 | 800円/月 | +13,800円 |

---

## 12. 付録

### 12.1 Python版 game.py 全文対応マップ

```python
# game.py の行番号と内容、移植先ファイルの対応
#    1-14:  ドックストリング → constants.js (STORY 定数として)
#   16-18:  インポート → （JSでは不要）
#   20-38:  定数定義 → constants.js
#   41-47:  show_donation_message() → renderer.js
#   50-54:  show_ending_header() → renderer.js
#   57-85:  _random_outcome() → game.js
#   88-103: left_path() → game.js
#  106-117: right_path() → game.js
#  120-133: neutral_ending() → game.js
#  136-153: hidden_ending() → game.js
#  156-165: search_area() → game.js
#  168-181: check_hidden_path() → game.js
#  184-200: show_menu() → renderer.js (renderChoices)
#  203-236: main() → game.js (イベント駆動に再構成)
```

### 12.2 開発環境セットアップ

```bash
# 開発サーバー起動（VS Code Live Server 推奨）
cd /workspace/project/web_adventure
npx live-server --port=5500

# テスト実行（Phase1以降）
npx vitest run

# E2Eテスト（Phase1以降）
npx playwright test

# ビルド・配布用ZIP作成（Phase4）
bash create_dist.sh
```

### 12.3 参考資料

| 資料 | 場所 | 用途 |
|------|------|------|
| Python版ソース | `/workspace/project/game.py` | 移植元コード全文 |
| Python版テスト | `/workspace/project/test_all_endings.py` | テストケース設計の参考 |
| プロジェクト提案書 | `/workspace/project/PROPOSAL.md` | 事業計画・収益化戦略 |
| Python版公開ガイド | `/workspace/project/PUBLISH_GUIDE.md` | itch.io公開手順の参考 |
| Python版README | `/workspace/project/README.md` | ゲーム説明文の参考 |

---

## 13. 改訂履歴

| 日付 | バージョン | 変更内容 | 作成者 |
|------|-----------|---------|-------|
| 2026-08-09 | v1.0 | 初版作成（全12セクション） | OpenHands Agent |