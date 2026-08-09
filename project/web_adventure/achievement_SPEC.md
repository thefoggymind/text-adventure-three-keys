# SPEC: 実績システム追加 — 「3つの鍵 — Web Edition」

> 作成日: 2026-08-09
> ベース: `/workspace/project/web_adventure/`（game.js + renderer.js + index.html + style.css）
> 選定元: `/workspace/project/PROPOSAL.md`（実績システム追加）
> 既存テスト: 106 passed（game.test.js 49件 + renderer.test.js 57件）

---

## 1. プロジェクト概要

### 1.1 コンセプト
「3つの鍵 — Web Edition」に**実績システム（Achievement System）**を追加する。
現在の `getAchievements()` / `recordEnding()` はエンディング解除のカウントのみ行っているが、
これを拡張し、**個別実績の定義・解除検出・通知表示・一覧画面・SNSシェア**を行う
フル機能の実績システムにアップグレードする。

### 1.2 開発原則
- **既存コード非破壊**: ゲームロジック（game.js）はイベント発火のみ、既存関数は変更しない
- **サーバーサイド不要**: 全データはlocalStorageに保存、API費用ゼロ
- **段階的実装**: コアロジック → UI → SNS連携の3フェーズ
- **全テスト維持**: 既存106テストは全て通過したまま新規追加する

---

## 2. 実績定義（全12個）

### 2.1 実績一覧

| # | ID | 実績名 | カテゴリ | 解除条件 | 非表示 | 難易度 |
|---|-----|--------|---------|---------|--------|--------|
| 1 | `first_step` | 🔰 はじまりの一歩 | プレイ | 初めてゲームを開始する | — | ★ |
| 2 | `left_path` | 🚶 左の道を行く | ルート | 左の道を選択する | — | ★ |
| 3 | `right_path` | 🚶 右の道を行く | ルート | 右の道を選択する | — | ★ |
| 4 | `victory` | 🏆 栄光の勝利 | エンディング | いずれかのエンディングで勝利する（WIN） | — | ★★ |
| 5 | `defeat` | 💀 無念の敗北 | エンディング | いずれかのエンディングで敗北する（LOSE） | — | ★★ |
| 6 | `return_home` | 🏠 帰還 | エンディング | 中立エンディング「帰還」に到達（NEUTRAL） | — | ★ |
| 7 | `true_hero` | 🌟 真の英雄 | エンディング | 隠しエンディング「真の英雄」に到達（HIDDEN） | ○ | ★★★ |
| 8 | `collector` | 💎 収集家 | アイテム | 全アイテム（Shining Jewel, Rusty Key, Old Map）を収集する | — | ★★★ |
| 9 | `explorer` | 🗺️ 探検家 | コンプリート | 全6エンディングをコンプリート | ○ | ★★★★ |
| 10 | `veteran` | 🎮 常連プレイヤー | プレイ | 合計10回プレイする | — | ★★ |
| 11 | `lucky` | 🍀 幸運の女神 | チャレンジ | ランダム勝敗で3回連続勝利する（一度のゲーム内で） | — | ★★★ |
| 12 | `completionist` | 👑 完全制覇 | コンプリート | 全12実績をコンプリート | ○ | ★★★★★ |

### 2.2 非表示実績
- 非表示（`secret: true`）実績は一覧画面で「???」と表示され、解除後に実績名・条件が公開される
- 対象: #7 `true_hero`, #9 `explorer`, #12 `completionist`

### 2.3 カテゴリ分類

| カテゴリ | 実績数 | 説明 |
|---------|--------|------|
| プレイ | 2 (#1, #10) | ゲーム開始・プレイ回数に関する実績 |
| ルート | 2 (#2, #3) | 左右の道の選択に関する実績 |
| エンディング | 4 (#4, #5, #6, #7) | 特定エンディング到達に関する実績 |
| アイテム | 1 (#8) | アイテム収集に関する実績 |
| チャレンジ | 1 (#11) | 特殊条件を満たす実績 |
| コンプリート | 2 (#9, #12) | 全エンディング/全実績コンプリート |

---

## 3. 解除条件の詳細

### 3.1 各実績の解除条件ロジック

#### #1 🔰 はじまりの一歩（`first_step`）
- **発火タイミング**: `EVENT.GAME_START`
- **条件**: `achievements.first_step !== true`
- **備考**: 初回のみ解除。セーブデータ削除後も解除済みは維持

#### #2 🚶 左の道を行く（`left_path`）
- **発火タイミング**: `EVENT.CHOICE_MADE` + `choice === CHOICES.LEFT`
- **条件**: プレイヤーが左の道（`CHOICES.LEFT = '1'`）を選択した
- **備考**: hidden ending経由でも解除

#### #3 🚶 右の道を行く（`right_path`）
- **発火タイミング**: `EVENT.CHOICE_MADE` + `choice === CHOICES.RIGHT`
- **条件**: プレイヤーが右の道（`CHOICES.RIGHT = '2'`）を選択した
- **備考**: hidden ending経由でも解除

#### #4 🏆 栄光の勝利（`victory`）
- **発火タイミング**: `EVENT.ENDING_REACHED`
- **条件**: `outcome === RESULTS.WIN`
- **備考**: left_win / right_win どちらでも解除

#### #5 💀 無念の敗北（`defeat`）
- **発火タイミング**: `EVENT.ENDING_REACHED`
- **条件**: `outcome === RESULTS.LOSE`
- **備考**: left_lose / right_lose どちらでも解除

#### #6 🏠 帰還（`return_home`）
- **発火タイミング**: `EVENT.ENDING_REACHED`
- **条件**: `outcome === RESULTS.NEUTRAL`
- **備考**: GIVE_UP選択時に解除

#### #7 🌟 真の英雄（`true_hero`）
- **発火タイミング**: `EVENT.ENDING_REACHED`
- **条件**: `outcome === RESULTS.HIDDEN`
- **備考**: 非表示実績。hidden ending到達時のみ解除

#### #8 💎 収集家（`collector`）
- **発火タイミング**: `EVENT.ITEM_FOUND`（アイテム入手時）
- **条件**: インベントリに全3種のアイテム（JEWEL, KEY, MAP）が揃った
- **備考**: 複数ゲームまたいでの収集も可（localStorageに累積保存）

#### #9 🗺️ 探検家（`explorer`）
- **発火タイミング**: `EVENT.ENDING_REACHED`
- **条件**: `achievements.endingsUnlocked.length === 6`（全6エンディング解除）
- **備考**: 非表示実績。6種類のoutcomeが全て揃った時点で解除

#### #10 🎮 常連プレイヤー（`veteran`）
- **発火タイミング**: `EVENT.GAME_START`
- **条件**: `achievements.totalPlayCount >= 10`
- **備考**: 10回以上ゲームを開始した時点で解除（過去のプレイもカウント）

#### #11 🍀 幸運の女神（`lucky`）
- **発火タイミング**: `EVENT.ENDING_REACHED`
- **条件**: ランダム勝敗（WIN）が3回連続で発生（**1ゲーム内**）
- **備考**: ゲーム開始時に連続勝利カウンターをリセット。leftPath/rightPathの`randomOutcome`がWINを3回連続で返すと解除

#### #12 👑 完全制覇（`completionist`）
- **発火タイミング**: 任意の実績解除時
- **条件**: `Object.values(achievements.achievements).every(v => v === true)`
- **備考**: 非表示実績。全11実績解除後に自動解除

### 3.2 イベント定義

```javascript
export const EVENTS = {
  GAME_START: 'game_start',       // 新規ゲーム開始時
  CHOICE_MADE: 'choice_made',     // 選択肢選択時（value付き）
  ENDING_REACHED: 'ending_reached', // エンディング到達時（outcome付き）
  ITEM_FOUND: 'item_found',       // アイテム入手時（itemName付き）
};
```

### 3.3 実績ストレージ構造

```javascript
// localStorage キー: 'three-keys-achievements-v1'
// （既存の ACHIEVEMENT_KEY を流用・拡張）
const ACHIEVEMENT_DATA = {
  version: 1,
  endingsUnlocked: ['win', 'lose', 'neutral', 'hidden'], // 既存互換
  totalPlayCount: 12,                                      // 既存互換
  achievements: {                                           // 新規追加
    first_step: true,
    left_path: false,
    right_path: false,
    victory: false,
    defeat: false,
    return_home: false,
    true_hero: false,
    collector: false,
    explorer: false,
    veteran: false,
    lucky: false,
    completionist: false,
  },
  consecutiveWins: 0,         // #11 連続勝利カウンター（1ゲーム内）
  collectedItems: [],         // #8 累積収集アイテム一覧
};
```

---

## 4. 解除検出ロジック

### 4.1 game.js への追加

`game.js` に以下の関数と定数を追加する（既存関数は変更しない）。

```javascript
// 追加する定数
export const ACHIEVEMENT_IDS = {
  FIRST_STEP: 'first_step',
  LEFT_PATH: 'left_path',
  RIGHT_PATH: 'right_path',
  VICTORY: 'victory',
  DEFEAT: 'defeat',
  RETURN_HOME: 'return_home',
  TRUE_HERO: 'true_hero',
  COLLECTOR: 'collector',
  EXPLORER: 'explorer',
  VETERAN: 'veteran',
  LUCKY: 'lucky',
  COMPLETIONIST: 'completionist',
};

// 実績定義リスト（テンプレートとして使用）
export const ACHIEVEMENT_DEFS = [
  { id: ACHIEVEMENT_IDS.FIRST_STEP,   name: '🔰 はじまりの一歩',   secret: false, category: 'play' },
  { id: ACHIEVEMENT_IDS.LEFT_PATH,    name: '🚶 左の道を行く',     secret: false, category: 'route' },
  { id: ACHIEVEMENT_IDS.RIGHT_PATH,   name: '🚶 右の道を行く',     secret: false, category: 'route' },
  { id: ACHIEVEMENT_IDS.VICTORY,      name: '🏆 栄光の勝利',       secret: false, category: 'ending' },
  { id: ACHIEVEMENT_IDS.DEFEAT,       name: '💀 無念の敗北',       secret: false, category: 'ending' },
  { id: ACHIEVEMENT_IDS.RETURN_HOME,  name: '🏠 帰還',             secret: false, category: 'ending' },
  { id: ACHIEVEMENT_IDS.TRUE_HERO,    name: '🌟 真の英雄',         secret: true,  category: 'ending' },
  { id: ACHIEVEMENT_IDS.COLLECTOR,    name: '💎 収集家',           secret: false, category: 'item' },
  { id: ACHIEVEMENT_IDS.EXPLORER,     name: '🗺️ 探検家',           secret: true,  category: 'complete' },
  { id: ACHIEVEMENT_IDS.VETERAN,      name: '🎮 常連プレイヤー',   secret: false, category: 'play' },
  { id: ACHIEVEMENT_IDS.LUCKY,        name: '🍀 幸運の女神',       secret: false, category: 'challenge' },
  { id: ACHIEVEMENT_IDS.COMPLETIONIST, name: '👑 完全制覇',        secret: true,  category: 'complete' },
];
```

#### `checkAchievements(event, data, achievements)` 関数

ゲーム内イベントを受け取り、解除条件をチェックして新たに解除された実績のID配列を返す。

```javascript
/**
 * ゲーム内イベントを監視し、解除条件を満たした実績のID配列を返す。
 * @param {string} event - イベント種別（EVENTS.*）
 * @param {object} data - イベント付随データ（choice, outcome, itemName 等）
 * @param {object} achievements - 現在の実績データ（getAchievements() の戻り値）
 * @returns {string[]} 新たに解除された実績IDの配列（空配列 = 解除なし）
 */
export function checkAchievements(event, data, achievements) {
  const newlyUnlocked = [];
  const a = achievements.achievements || {};
  
  if (event === EVENTS.GAME_START) {
    if (!a.first_step) newlyUnlocked.push(ACHIEVEMENT_IDS.FIRST_STEP);
    if ((achievements.totalPlayCount || 0) + 1 >= 10 && !a.veteran) {
      newlyUnlocked.push(ACHIEVEMENT_IDS.VETERAN);
    }
    // 連続勝利カウンターリセット
    achievements.consecutiveWins = 0;
  }
  
  if (event === EVENTS.CHOICE_MADE) {
    if (data.choice === '1' && !a.left_path) newlyUnlocked.push(ACHIEVEMENT_IDS.LEFT_PATH);
    if (data.choice === '2' && !a.right_path) newlyUnlocked.push(ACHIEVEMENT_IDS.RIGHT_PATH);
  }
  
  if (event === EVENTS.ENDING_REACHED) {
    if (data.outcome === 'win' && !a.victory) newlyUnlocked.push(ACHIEVEMENT_IDS.VICTORY);
    if (data.outcome === 'lose' && !a.defeat) newlyUnlocked.push(ACHIEVEMENT_IDS.DEFEAT);
    if (data.outcome === 'neutral' && !a.return_home) newlyUnlocked.push(ACHIEVEMENT_IDS.RETURN_HOME);
    if (data.outcome === 'hidden' && !a.true_hero) newlyUnlocked.push(ACHIEVEMENT_IDS.TRUE_HERO);
    
    // #11 連続勝利チェック
    if (data.outcome === 'win') {
      achievements.consecutiveWins = (achievements.consecutiveWins || 0) + 1;
    } else if (data.outcome === 'lose') {
      achievements.consecutiveWins = 0;
    }
    if (achievements.consecutiveWins >= 3 && !a.lucky) {
      newlyUnlocked.push(ACHIEVEMENT_IDS.LUCKY);
    }
    
    // #9 全エンディングチェック
    if (achievements.endingsUnlocked.length >= 6 && !a.explorer) {
      newlyUnlocked.push(ACHIEVEMENT_IDS.EXPLORER);
    }
  }
  
  if (event === EVENTS.ITEM_FOUND) {
    // #8 収集家: 累積アイテム収集
    if (!achievements.collectedItems) achievements.collectedItems = [];
    if (!achievements.collectedItems.includes(data.itemName)) {
      achievements.collectedItems.push(data.itemName);
    }
    const allItems = ['Shining Jewel', 'Rusty Key', 'Old Map'];
    const hasAll = allItems.every(item => achievements.collectedItems.includes(item));
    if (hasAll && !a.collector) newlyUnlocked.push(ACHIEVEMENT_IDS.COLLECTOR);
  }
  
  // #12 完全制覇: 全実績解除チェック（解除後に毎回確認）
  if (newlyUnlocked.length > 0 || event !== '') {
    const allIds = ACHIEVEMENT_DEFS.map(def => def.id);
    const allUnlocked = allIds.every(id => {
      if (id === ACHIEVEMENT_IDS.COMPLETIONIST) return false; // 自分自身は除外
      return newlyUnlocked.includes(id) || a[id] === true;
    });
    if (allUnlocked && !a.completionist) {
      newlyUnlocked.push(ACHIEVEMENT_IDS.COMPLETIONIST);
    }
  }
  
  return newlyUnlocked;
}
```

### 4.2 renderer.js の拡張

#### `getAchievements()` の拡張
- 既存の `endingsUnlocked` / `totalPlayCount` を維持
- `achievements` オブジェクト（各実績の解除状態）を新規追加
- 旧フォーマットのデータ（`achievements` フィールドなし）が存在する場合、自動アップグレードする

#### `recordEnding()` の拡張
- 既存のエンディング記録 + playCount増加を維持
- 加えて `checkAchievements(EVENTS.ENDING_REACHED, { outcome }, achievements)` を呼び出し
- 新規解除があった場合、`showAchievementPopup()` を呼び出す

#### 新規関数 `checkAndShowAchievements(event, data)`
- `getAchievements()` で現在の実績データ取得
- `checkAchievements(event, data, achievements)` を呼び出し
- 新規解除があれば achievements を保存し、1つずつ `showAchievementPopup()` を表示

#### 呼び出し箇所（既存関数への追加）

| 既存関数 | 追加する呼び出し |
|---------|----------------|
| `onChoice()` 内 `handleChoice` 後 | `checkAndShowAchievements(EVENTS.CHOICE_MADE, { choice: value })` |
| `recordEnding()` 内 | `checkAndShowAchievements(EVENTS.ENDING_REACHED, { outcome: endingId })` |
| `startNewGame()` 内 | `checkAndShowAchievements(EVENTS.GAME_START, {})` |
| `searchArea()` のアイテム追加後 | `checkAndShowAchievements(EVENTS.ITEM_FOUND, { itemName: item })`（renderer側でフック） |

---

## 5. UI仕様

### 5.1 実績一覧画面

#### 画面構成
タイトル画面からアクセス可能な別画面（`screen-achievements`）として実装する。

```
┌──────────────────────────────────┐
│          🏆 実績一覧              │
│  ═══════════════════════════════  │
│                                  │
│  全12実績中 8/12 達成            │
│  [████████████░░░░░░░░] 67%     │
│                                  │
│  ┌─ 🔰 はじまりの一歩 ────────┐ │
│  │  ✅ 初めてゲームを開始する   │ │
│  └────────────────────────────┘ │
│  ┌─ 🚶 左の道を行く ──────────┐ │
│  │  ✅ 左の道を選択する         │ │
│  └────────────────────────────┘ │
│  ┌─ 🌟 真の英雄 ─────────────┐ │
│  │  ❓ ？？？（非表示実績）    │ │
│  └────────────────────────────┘ │
│  ┌─ 🎮 常連プレイヤー ───────┐ │
│  │  🔒 合計10回プレイする      │ │
│  │     （現在 7/10回）          │ │
│  └────────────────────────────┘ │
│                                  │
│  [ タイトルに戻る ]              │
└──────────────────────────────────┘
```

#### 構成要素

| 要素 | 説明 |
|------|------|
| 画面タイトル | 「🏆 実績一覧」 |
| 全体進捗バー | 全12実績中 n/m + パーセンテージ + プログレスバー |
| 実績カード一覧 | 各実績をカード形式で表示（12個、グリッド or リスト） |
| 「タイトルに戻る」ボタン | タイトル画面へ遷移 |

#### 実績カードの状態別表示

| 状態 | 表示 | 説明 |
|------|------|------|
| ✅ 解除済み | 実績名 + 解除条件 + 解除日時（緑色のチェック） | 通常表示 |
| 🔒 未解除（通常） | 実績名（グレーアウト）+ 解除条件 + 進行度（該当する場合） | 条件が見える |
| ❓ 未解除（非表示） | 「？？？」+ 「非表示実績」 | 解除後に公開 |
| 🆕 新規解除 | 解除時アニメーション + 光るエフェクト | ポップアップ後、一覧でも表示 |

#### 進行度表示

| 実績 | 進行度表示 |
|------|-----------|
| #10 常連プレイヤー | 「現在 7/10回」（`totalPlayCount` を表示） |
| #8 収集家 | 「現在 2/3個」（`collectedItems.length` を表示） |
| #9 探検家 | 「現在 4/6エンディング」（`endingsUnlocked.length` を表示） |
| #11 幸運の女神 | 進行度非表示（ランダム要素のため） |

### 5.2 解除通知

#### ポップアップ仕様
- **表示位置**: 画面中央（既存トーストとは別の専用ポップアップ）
- **表示タイミング**: 実績解除条件を満たした瞬間
- **表示時間**: 3秒（長めに表示）
- **アニメーション**: 上からスライドイン + バウンス + きらめきエフェクト

```
┌──────────────────────────────────┐
│                                  │
│        🏆 実績解除！             │
│                                  │
│     🔰 はじまりの一歩            │
│    「初めてゲームを開始する」     │
│                                  │
│         [ 🐦 シェア ]            │
│                                  │
└──────────────────────────────────┘
```

#### index.html への追加要素
```html
<!-- 実績解除ポップアップ -->
<div id="achievement-popup" class="achievement-popup" style="display:none">
  <div class="achievement-popup-inner">
    <div class="achievement-popup-icon">🏆</div>
    <div class="achievement-popup-label">実績解除！</div>
    <div class="achievement-popup-name" id="popup-achievement-name"></div>
    <div class="achievement-popup-desc" id="popup-achievement-desc"></div>
    <button class="btn btn-share-mini" id="popup-share-btn" style="display:none">🐦 シェア</button>
  </div>
</div>
```

### 5.3 進行度表示（既存エンディング画面の拡張）

現在のエンディング画面の進捗バー（`ending-count` / `progress-fill` / `progress-percent`）は
そのまま維持し、**タイトル画面に実績進捗サマリー**を追加する。

#### タイトル画面への追加
```
  全12実績中 5/12 達成    ← 新規追加
  [████████░░░░░░░░] 42%  ← 新規追加
```

### 5.4 SNSシェアボタン

#### 全実績コンプリート時シェア
- **条件**: #12 `completionist` 解除時
- **シェア内容**: 専用の全実績コンプリート画面を表示
- **Twitterシェアテキスト**: 「🏆 「3つの鍵 — Web Edition」の全12実績を完全制覇しました！ 👑\\n#3つの鍵 #実績コンプリート\\nhttps://...」
- **シェアボタン**: 解除ポップアップ + 実績一覧画面 + 全実績コンプリート専用画面の3箇所

#### 個別実績解除時シェア（任意）
- 各解除ポップアップに「🐦 シェア」ボタン
- シェアテキスト: 「🏆 「3つの鍵」で実績「{実績名}」を解除しました！\\n#3つの鍵\\nhttps://...」

#### 実績一覧画面のシェアボタン
- 全実績コンプリート時のみ、一覧画面下部に「🎉 完全制覇をシェア」ボタン

---

## 6. 技術スタック

### 6.1 アーキテクチャ

```
┌──────────────────────────────────────────────────────┐
│                   renderer.js                         │
│  ┌─────────────┐  ┌──────────────────┐               │
│  │ ゲームUI    │  │ 実績UI           │               │
│  │ (既存)      │  │ showAchievement  │               │
│  │             │  │  Popup()         │               │
│  │             │  │ renderAchieve    │               │
│  │             │  │ mentList()       │               │
│  └──────┬──────┘  └────────┬─────────┘               │
│         │                  │                          │
│         │   イベント発火    │                          │
│         ▼                  ▼                          │
│  ┌──────────────────────────────────────────────────┐│
│  │  checkAndShowAchievements(event, data)           ││
│  │  → checkAchievements() を呼び出し                ││
│  │  → 新規解除があれば保存 → popup表示              ││
│  └──────────────────────┬───────────────────────────┘│
│                         │                             │
└─────────────────────────┼─────────────────────────────┘
                          │
          checkAchievements() 呼び出し
                          │
                          ▼
┌──────────────────────────────────────────────────────┐
│                     game.js                           │
│  ┌─────────────┐  ┌──────────────────┐               │
│  │ ゲームロジック│  │ ACHIEVEMENT_DEFS │               │
│  │ (既存・不変)  │  │ checkAchieve    │               │
│  │             │  │ ments()          │               │
│  └─────────────┘  └──────────────────┘               │
└──────────────────────────────────────────────────────┘
                          │
                    localStorage
                    (three-keys-achievements-v1)
```

### 6.2 変更ファイル一覧

| ファイル | 変更内容 | 追加行数（概算） |
|---------|---------|----------------|
| `game.js` | `ACHIEVEMENT_IDS` 定数, `ACHIEVEMENT_DEFS` 定義, `checkAchievements()` 関数, `EVENTS` 定数を追加 | +120行 |
| `renderer.js` | `getAchievements()` 互換拡張, `checkAndShowAchievements()`追加, `showAchievementPopup()`追加, `renderAchievementList()`追加, イベントフック追加 | +150行 |
| `index.html` | `screen-achievements` 追加, `achievement-popup` 追加, タイトル画面に実績進捗サマリー追加 | +80行 |
| `style.css` | `.screen-achievements`, `.achievement-*`, `.achievement-popup-*` スタイル追加 | +150行 |
| `tests/game.test.js` | `ACHIEVEMENT_IDS` テスト, `checkAchievements()` 全条件テスト | +120行 |
| `tests/renderer.test.js` | `getAchievements()` 拡張テスト, `showAchievementPopup()` テスト, `renderAchievementList()` テスト, 統合テスト | +100行 |

### 6.3 サーバーサイド不要の維持
- 全データは localStorage に保存（`three-keys-achievements-v1` キー）
- SNSシェアは X（Twitter）の `window.open()` URLシェア（Intent URL）
- ホスティング構成変更なし（GitHub Pages / itch.io そのまま）

### 6.4 既存データ互換性
- 旧フォーマット（`{ endingsUnlocked: [...], totalPlayCount: N }`）からの自動アップグレード
- アップグレード時: `achievements` オブジェクトを新規追加、各実績は未解除で初期化
- `endingsUnlocked` の値に基づき該当するエンディング実績（#4〜#7）を自動解除
- 旧フォーマット検出時のアップグレードは1回のみ実行

---

## 7. テスト計画

### 7.1 テスト方針
- **既存テストは一切変更しない**: 既存の106テスト（game.test.js 49件 + renderer.test.js 57件）はそのまま維持
- **新規テストは別テストファイル or 既存ファイル末尾に追加**
- **Jest環境**: jsdom + localStorage mock は既存のものを流用
- **テストパターン**: ユニットテスト（条件ロジック） + DOMテスト（UI表示）

### 7.2 game.test.js 追加テスト（推奨15+件）

| # | テスト名 | 内容 |
|---|---------|------|
| 1 | `ACHIEVEMENT_IDS constant values` | 全12個のIDが正しい値を持っている |
| 2 | `ACHIEVEMENT_DEFS length and fields` | 12個の定義があり、各フィールド（id/name/secret/category）が存在 |
| 3 | `checkAchievements GAME_START first_step` | 初回ゲーム開始で #1 が解除される |
| 4 | `checkAchievements GAME_START veteran at 9` | 9回目のプレイでは #10 解除されない |
| 5 | `checkAchievements GAME_START veteran at 10` | 10回目のプレイで #10 解除される |
| 6 | `checkAchievements CHOICE_MADE left_path` | 左選択で #2 解除 |
| 7 | `checkAchievements CHOICE_MADE right_path` | 右選択で #3 解除 |
| 8 | `checkAchievements ENDING_REACHED win` | WINで #4 解除 |
| 9 | `checkAchievements ENDING_REACHED lose` | LOSEで #5 解除 |
| 10 | `checkAchievements ENDING_REACHED neutral` | NEUTRALで #6 解除 |
| 11 | `checkAchievements ENDING_REACHED hidden` | HIDDENで #7 解除 |
| 12 | `checkAchievements ENDING_REACHED 3 consecutive wins` | 3連続WINで #11 解除 |
| 13 | `checkAchievements ENDING_REACHED 2 consecutive wins` | 2連続では #11 解除されない |
| 14 | `checkAchievements ITEM_FOUND collector` | 3種アイテム収集で #8 解除 |
| 15 | `checkAchievements ENDING_REACHED explorer` | 全6ED解除後 #9 解除 |
| 16 | `checkAchievements completionist` | 全11実績解除後に #12 解除 |
| 17 | `checkAchievements no duplicate` | 既に解除済みの実績は重複解除されない |
| 18 | `checkAchievements no event` | 無関係なイベントでは何も解除されない |

### 7.3 renderer.test.js 追加テスト（推奨12+件）

| # | テスト名 | 内容 |
|---|---------|------|
| 1 | `getAchievements returns default structure` | localStorage空の場合のデフォルト値 |
| 2 | `getAchievements parses stored data` | 保存済みデータのパース |
| 3 | `getAchievements handles corrupted data` | 破損JSON時のfallback |
| 4 | `getAchievements upgrades old format` | 旧フォーマット自動アップグレード |
| 5 | `showAchievementPopup displays correctly` | ポップアップ表示内容の確認 |
| 6 | `showAchievementPopup hides after timeout` | 3秒後に非表示 |
| 7 | `showAchievementPopup for secret achievement` | 非表示実績解除時の表示 |
| 8 | `renderAchievementList renders all 12` | 12個全て表示される |
| 9 | `renderAchievementList locked vs unlocked` | 解除済み/未解除の表示違い |
| 10 | `renderAchievementList secret locked` | 非表示未解除は「???」表示 |
| 11 | `renderAchievementList progress display` | #10 常連プレイヤーの進行度「7/10」表示 |
| 12 | `getAchievements upgrades endingsUnlocked consistency` | アップグレード時に過去解除EDが正しく引き継がれる |

### 7.4 統合テスト（推奨5+件）

| # | テスト名 | 内容 |
|---|---------|------|
| 1 | `full flow: game start → choice → ending` | ゲーム開始→選択→エンディングの一連で実績が適切に解除される |
| 2 | `multiple endings unlock explorer` | 複数ゲームで6ED解除→#9 探検家が解除される |
| 3 | `completionist on all achievements` | 全11実績解除→#12 完全制覇が解除される |
| 4 | `persistent across game restarts` | ゲーム再開後も解除済み実績が保持される |
| 5 | `SNS share button generates correct URL` | シェアボタンが正しいIntent URLを生成する |

### 7.5 テスト実行方法

```bash
# 既存106テスト + 新規テスト をまとめて実行
cd /workspace/project/web_adventure
NODE_OPTIONS=--experimental-vm-modules npx jest

# 特定ファイルのみ実行
NODE_OPTIONS=--experimental-vm-modules npx jest tests/game.test.js
NODE_OPTIONS=--experimental-vm-modules npx jest tests/renderer.test.js
```

**目標**: 全テスト通過（既存106 + 新規35+ = 141+ tests）

---

## 8. 実装計画

### Phase1: コアロジック（推定 4h）

| # | タスク | ファイル | 内容 |
|---|-------|---------|------|
| 1.1 | ACHIEVEMENT_IDS / ACHIEVEMENT_DEFS 定数追加 | `game.js` | 実績ID・定義の定数をエクスポート |
| 1.2 | EVENTS 定数追加 | `game.js` or `constants.js` | ゲーム内イベント定義 |
| 1.3 | checkAchievements() 実装 | `game.js` | 全12実績の解除条件ロジック |
| 1.4 | 単体テスト実装 | `tests/game.test.js` | checkAchievements() 全条件テスト（18件） |

### Phase2: UI実装（推定 5h）

| # | タスク | ファイル | 内容 |
|---|-------|---------|------|
| 2.1 | getAchievements() 拡張 | `renderer.js` | 旧フォーマット互換 + achievements フィールド追加 |
| 2.2 | checkAndShowAchievements() 実装 | `renderer.js` | 検出→保存→表示のパイプライン |
| 2.3 | showAchievementPopup() 実装 | `renderer.js` | ポップアップDOM生成 + アニメーション制御 |
| 2.4 | renderAchievementList() 実装 | `renderer.js` | 実績一覧画面のDOM生成 |
| 2.5 | index.html に画面要素追加 | `index.html` | screen-achievements, popup, 進捗サマリー |
| 2.6 | style.css にスタイル追加 | `style.css` | ポップアップ・一覧画面・アニメーション |
| 2.7 | タイトル画面に実績進捗表示追加 | `renderer.js`, `index.html` | 進捗バー・カウント |

### Phase3: SNS連携・テスト（推定 3h）

| # | タスク | ファイル | 内容 |
|---|-------|---------|------|
| 3.1 | SNSシェアボタン実装 | `renderer.js` | X(Twitter) Intent URL生成 + 個別/全体シェア |
| 3.2 | renderer.test.js 拡張 | `tests/renderer.test.js` | UIテスト追加（12件） |
| 3.3 | 統合テスト追加 | `tests/renderer.test.js` | 結合テスト（5件） |
| 3.4 | 全テスト通過確認 | — | 106 + 35 = 141 tests all green |

**合計工数**: 約12h

---

## 9. 依存関係

- **この実績システムに依存する機能**: なし（独立追加）
- **依存する既存機能**: `getAchievements()`, `recordEnding()`, `showEnding()` の既存シグネチャ
- **外部依存**: なし（X(Twitter) Intent URLは外部リンクのみ）

---

## 10. 改訂履歴

| 日付 | バージョン | 変更内容 | 作成者 |
|------|-----------|---------|-------|
| 2026-08-09 | v1.0 | 初版作成（全10セクション） | OpenHands Agent |