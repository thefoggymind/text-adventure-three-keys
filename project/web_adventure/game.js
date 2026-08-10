/**
 * Text-based adventure game "3つの鍵 — Web Edition" core logic.
 * Ported from /workspace/project/game.py (Python) to JavaScript.
 *
 * === Ending List ===
 * 1. Left path - Win     : 清らかな川で回復、宝石を入手
 * 2. Left path - Lose    : 毒の川で倒れる
 * 3. Right path - Win    : 古代の宝具で富と名声
 * 4. Right path - Lose   : 呪いで石になる
 * 5. Neutral ending      : 冒険をあきらめて帰還
 * 6. Hidden ending       : 鍵と地図で真の英雄（条件付き）
 */

// --- 定数 ---
export const CHOICES = {
  LEFT: '1',
  RIGHT: '2',
  GIVE_UP: '3',
  SEARCH: '4',
};

export const RESULTS = {
  WIN: 'win',
  LOSE: 'lose',
  NEUTRAL: 'neutral',
  HIDDEN: 'hidden',
};

export const ITEMS = {
  JEWEL: 'Shining Jewel',
  KEY: 'Rusty Key',
  MAP: 'Old Map',
};

export const DONATION_URL = 'https://ko-fi.com/thefoggymind';

// --- 実績システム定数 ---

export const EVENTS = {
  GAME_START: 'game_start',
  CHOICE_MADE: 'choice_made',
  ENDING_REACHED: 'ending_reached',
  ITEM_FOUND: 'item_found',
};

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
  ALL_SEER: 'all_seer',
};

export const ACHIEVEMENT_DEFS = [
  { id: ACHIEVEMENT_IDS.FIRST_STEP, name: '🔰 はじまりの一歩', category: 'play', secret: false, difficulty: '★' },
  { id: ACHIEVEMENT_IDS.LEFT_PATH, name: '🚶 左の道を行く', category: 'route', secret: false, difficulty: '★' },
  { id: ACHIEVEMENT_IDS.RIGHT_PATH, name: '🚶 右の道を行く', category: 'route', secret: false, difficulty: '★' },
  { id: ACHIEVEMENT_IDS.VICTORY, name: '🏆 栄光の勝利', category: 'ending', secret: false, difficulty: '★★' },
  { id: ACHIEVEMENT_IDS.DEFEAT, name: '💀 無念の敗北', category: 'ending', secret: false, difficulty: '★★' },
  { id: ACHIEVEMENT_IDS.RETURN_HOME, name: '🏠 帰還', category: 'ending', secret: false, difficulty: '★' },
  { id: ACHIEVEMENT_IDS.TRUE_HERO, name: '🌟 真の英雄', category: 'ending', secret: true, difficulty: '★★★' },
  { id: ACHIEVEMENT_IDS.COLLECTOR, name: '💎 収集家', category: 'item', secret: false, difficulty: '★★★' },
  { id: ACHIEVEMENT_IDS.EXPLORER, name: '🗺️ 探検家', category: 'complete', secret: true, difficulty: '★★★★' },
  { id: ACHIEVEMENT_IDS.VETERAN, name: '🎮 常連プレイヤー', category: 'play', secret: false, difficulty: '★★' },
  { id: ACHIEVEMENT_IDS.LUCKY, name: '🍀 幸運の女神', category: 'challenge', secret: false, difficulty: '★★★' },
  { id: ACHIEVEMENT_IDS.COMPLETIONIST, name: '👑 完全制覇', category: 'complete', secret: true, difficulty: '★★★★★' },
  { id: ACHIEVEMENT_IDS.ALL_SEER, name: '👁️ すべてを見通す者', category: 'complete', secret: true, difficulty: '★★★★' },
];

/**
 * ゲーム内イベントを監視し、解除条件を満たした実績のID配列を返す。
 * @param {string} event - イベント種別（EVENTS.*）
 * @param {object} data - イベント付随データ
 * @param {object} achievements - 現在の実績データ
 * @returns {string[]} 新たに解除された実績IDの配列
 */
export function checkAchievements(event, data, achievements) {
  const newlyUnlocked = [];
  const a = achievements.achievements || {};

  if (event === EVENTS.GAME_START) {
    if (!a.first_step) newlyUnlocked.push(ACHIEVEMENT_IDS.FIRST_STEP);
    if ((achievements.totalPlayCount || 0) + 1 >= 10 && !a.veteran) {
      newlyUnlocked.push(ACHIEVEMENT_IDS.VETERAN);
    }
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

    if (data.outcome === 'win') {
      achievements.consecutiveWins = (achievements.consecutiveWins || 0) + 1;
    } else if (data.outcome === 'lose') {
      achievements.consecutiveWins = 0;
    }
    if (achievements.consecutiveWins >= 3 && !a.lucky) {
      newlyUnlocked.push(ACHIEVEMENT_IDS.LUCKY);
    }

    if ((achievements.endingsUnlocked?.length || 0) >= 6 && !a.explorer) {
      newlyUnlocked.push(ACHIEVEMENT_IDS.EXPLORER);
    }

    // #13 すべてを見通す者: 全5エンディングを閲覧済みか確認
    if (!a.all_seer) {
      try {
        const allSeen = [1, 2, 3, 4, 5].every(i => localStorage.getItem(`ending_seen_${i}`) === 'true');
        if (allSeen) {
          newlyUnlocked.push(ACHIEVEMENT_IDS.ALL_SEER);
        }
      } catch (_) { /* localStorage unavailable */ }
    }
  }

  if (event === EVENTS.ITEM_FOUND) {
    if (!achievements.collectedItems) achievements.collectedItems = [];
    if (!achievements.collectedItems.includes(data.itemName)) {
      achievements.collectedItems.push(data.itemName);
    }
    const allItems = ['Shining Jewel', 'Rusty Key', 'Old Map'];
    const hasAll = allItems.every(item => achievements.collectedItems.includes(item));
    if (hasAll && !a.collector) newlyUnlocked.push(ACHIEVEMENT_IDS.COLLECTOR);
  }

  // #12 完全制覇: 新規解除があった場合のみチェック
  if (newlyUnlocked.length > 0) {
    const allIds = ACHIEVEMENT_DEFS.map(def => def.id);
    const allUnlocked = allIds.every(id => {
      if (id === ACHIEVEMENT_IDS.COMPLETIONIST) return true;
      return newlyUnlocked.includes(id) || a[id] === true;
    });
    if (allUnlocked && !a.completionist) {
      newlyUnlocked.push(ACHIEVEMENT_IDS.COMPLETIONIST);
    }
  }

  return newlyUnlocked;
}

// --- 状態管理 ---

/**
 * ゲームの初期状態を作成する。
 * @returns {import('./game.js').GameState}
 */
export function createInitialState() {
  return {
    screen: 'title',
    phase: 'intro',
    inventory: [],
    searched: false,
    outcome: 'none',
    displayText: [],
    gameOver: false,
    hiddenPlayed: false,
  };
}

/**
 * 現在のゲーム状態をシリアライズ可能なプレーンオブジェクトとして取得する。
 * @param {import('./game.js').GameState} state - 現在のゲーム状態
 * @returns {object} シリアライズ可能な状態オブジェクト
 */
export function getState(state) {
  return {
    version: 1,
    phase: state.phase,
    inventory: [...state.inventory],
    searched: state.searched,
    outcome: state.outcome,
    displayText: [...state.displayText],
    gameOver: state.gameOver,
    hiddenPlayed: state.hiddenPlayed,
  };
}

/**
 * シリアライズされたデータからゲーム状態を復元する。
 * @param {object} data - 復元元のデータオブジェクト
 * @returns {import('./game.js').GameState} 復元されたゲーム状態
 */
export function restoreState(data) {
  const state = createInitialState();
  state.phase = data.phase || 'intro';
  state.inventory = data.inventory ? [...data.inventory] : [];
  state.searched = data.searched || false;
  state.outcome = data.outcome || 'none';
  state.displayText = data.displayText ? [...data.displayText] : [];
  state.gameOver = data.gameOver || false;
  state.hiddenPlayed = data.hiddenPlayed || false;
  return state;
}

// --- ユーティリティ関数 ---

/**
 * 寄付のお願いメッセージを表示テキストに追加する。
 * @param {string[]} displayText - 表示テキスト配列
 * @returns {void}
 */
export function showDonation(displayText) {
  displayText.push('');
  displayText.push('============================================================');
  displayText.push(`  このゲームを気に入ったら寄付で支援してください：${DONATION_URL}`);
  displayText.push('============================================================');
  displayText.push('');
}

// --- 道中の分岐処理 ---

/**
 * 50%確率で勝敗を決め、結果に応じたメッセージを表示テキストに追加する。
 *
 * @param {string[]} displayText - 表示テキスト配列
 * @param {string} msgWin - 勝利時のメッセージ
 * @param {string} msgLose - 敗北時のメッセージ
 * @param {string[]} inventory - プレイヤーのインベントリ
 * @param {string|null} [itemOnWin=null] - 勝利時にインベントリへ追加するアイテム名
 * @returns {string} RESULT_WIN または RESULT_LOSE
 */
export function randomOutcome(displayText, msgWin, msgLose, inventory, itemOnWin = null) {
  if (Math.random() < 0.5) {
    displayText.push('');
    displayText.push('--- 勝利！ ---');
    displayText.push(msgWin);
    if (itemOnWin) {
      inventory.push(itemOnWin);
    }
    return RESULTS.WIN;
  } else {
    displayText.push('');
    displayText.push('--- 敗北 ---');
    displayText.push(msgLose);
    return RESULTS.LOSE;
  }
}

/**
 * 左の道：川で休息、勝敗でアイテム獲得または毒で敗北。
 * @param {import('./game.js').GameState} state - ゲーム状態
 * @returns {string} 結果定数
 */
export function leftPath(state) {
  const dt = state.displayText;
  dt.push('あなたは左の道を進み、きらめく川を見つけました。');
  dt.push('川のほとりで休憩し、水を飲むことにしました。');

  const result = randomOutcome(
    dt,
    '川の水は清らかで、エネルギーを完全に回復しました。\n'
      + 'あなたは無事に森を抜け出すことができました。\n'
      + 'さらに、川岸で輝く宝石を手に入れました！',
    '川の水は毒されており、あなたは体調を崩してしまいました。\n'
      + '森の中で倒れてしまいました…。',
    state.inventory,
    ITEMS.JEWEL,
  );
  state.outcome = result;
  state.gameOver = true;
  showDonation(dt);
  return result;
}

/**
 * 右の道：遺跡で発見、勝敗で宝具獲得または呪いで敗北。
 * @param {import('./game.js').GameState} state - ゲーム状態
 * @returns {string} 結果定数
 */
export function rightPath(state) {
  const dt = state.displayText;
  dt.push('あなたは右の道を進み、古い遺跡を発見しました。');
  dt.push('遺跡の中から不思議な遺物を見つけました。');

  const result = randomOutcome(
    dt,
    'その遺物は古代の宝具であり、あなたは富と名声を得ました。',
    '遺物には呪いがかかっており、あなたは石になってしまいました。',
    state.inventory,
  );
  state.outcome = result;
  state.gameOver = true;
  showDonation(dt);
  return result;
}

// --- エンディング ---

/**
 * エンディングタイトルを表示テキストに追加する。
 * @param {string[]} displayText - 表示テキスト配列
 * @param {string} title - エンディングタイトル
 * @param {string} [decoration='---'] - 装飾文字
 * @returns {void}
 */
export function renderEndingHeader(displayText, title, decoration = '---') {
  displayText.push('');
  displayText.push('============================================================');
  displayText.push(`  ${decoration} ${title} ${decoration}`);
  displayText.push('============================================================');
}

/**
 * 中立エンディング「帰還」：冒険をあきらめて日常に戻る。
 * @param {import('./game.js').GameState} state - ゲーム状態
 * @returns {string} RESULT_NEUTRAL
 */
export function neutralEnding(state) {
  const dt = state.displayText;
  renderEndingHeader(dt, '中立エンディング：帰還');
  dt.push('');
  dt.push('「やっぱり危険すぎる…」');
  dt.push('あなたは来た道を引き返すことにしました。');
  dt.push('森の入り口で出会った村人が言いました。「賢明な選択だ。」');
  dt.push('村に戻り、あなたは静かで平和な日常に戻りました。');
  dt.push('冒険の記憶は、いつか誰かに語る小さな思い出話になるでしょう。');
  dt.push('');
  dt.push('（危険を避けるのも勇気の一つ…平穏な日常を手に入れました。）');

  state.outcome = RESULTS.NEUTRAL;
  state.gameOver = true;
  showDonation(dt);
  return RESULTS.NEUTRAL;
}

/**
 * 隠しエンディング「真の英雄」：鍵と地図を持ち、隠し洞窟で財宝を獲得。
 * @param {import('./game.js').GameState} state - ゲーム状態
 * @returns {string} RESULT_HIDDEN
 */
export function hiddenEnding(state) {
  const dt = state.displayText;
  renderEndingHeader(dt, '★ 真の英雄', '--- ★');
  dt.push('');
  dt.push('あなたは錆びた鍵と古い地図を手に、隠された洞窟の入り口を発見した。');
  dt.push('洞窟の奥には、古代の王が眠る宝物庫があった。');
  dt.push('そこに立つ守護者の魂が語りかける…');
  dt.push('「よく来たな、勇者よ。その鍵と地図は、真に価する者にのみ与えられる。」');
  dt.push('「お前は運命を切り開く力を示した。この先にある全てを授けよう。」');
  dt.push('');
  dt.push('あなたは伝説の財宝を手に入れ、王国中から称賛される英雄となった。');
  dt.push('その名は永遠に語り継がれるだろう。');
  dt.push('');
  dt.push('（全ての謎を解き明かした者だけが到達できる、真のエンディング！）');

  state.outcome = RESULTS.HIDDEN;
  state.gameOver = true;
  showDonation(dt);
  return RESULTS.HIDDEN;
}

// --- 探索と隠しパス ---

/**
 * 周辺を探索し、隠しエンディングに必要なアイテムを入手する。
 * @param {import('./game.js').GameState} state - ゲーム状態
 * @returns {void}
 */
export function searchArea(state) {
  const dt = state.displayText;
  dt.push('あなたは周辺を注意深く探索し始めた。');
  dt.push('茂みの陰で何かが光っている…。');
  dt.push('それは「錆びた鍵」と「古い地図」でした！');
  state.inventory.push(ITEMS.KEY);
  state.inventory.push(ITEMS.MAP);
  dt.push('（アイテムを手に入れた：錆びた鍵、古い地図）');
  state.searched = true;
}

/**
 * 隠しパス条件確認：アイテム所持時に入力確認し、隠しEDへ遷移。
 *
 * @param {import('./game.js').GameState} state - ゲーム状態
 * @param {boolean} [enterCave=true] - 洞窟に入るかどうか（テスト用に外部から指定可能）
 * @returns {boolean} 隠しエンディングをプレイした場合は true
 */
export function checkHiddenPath(state, enterCave = true) {
  const hasKey = state.inventory.includes(ITEMS.KEY);
  const hasMap = state.inventory.includes(ITEMS.MAP);
  if (hasKey && hasMap) {
    const dt = state.displayText;
    dt.push('');
    dt.push('★ 錆びた鍵と古い地図を持っている…隠された洞窟の入り口を見つけました！');
    if (enterCave) {
      hiddenEnding(state);
      state.hiddenPlayed = true;
      return true;
    }
    dt.push('（またの機会にすることにした…）');
  }
  return false;
}

// --- メインゲームループ ---

/**
 * メインメニューの選択肢を決定する（DOMレンダリング用データ）。
 * @param {import('./game.js').GameState} state - ゲーム状態
 * @returns {Array<{value: string, label: string}>} 選択肢の配列
 */
export function getChoices(state) {
  const choices = [
    { value: CHOICES.LEFT, label: '左の道を進む' },
    { value: CHOICES.RIGHT, label: '右の道を進む' },
    { value: CHOICES.GIVE_UP, label: '冒険をあきらめて帰る' },
  ];
  if (!state.searched) {
    choices.push({ value: CHOICES.SEARCH, label: '周辺を探索する' });
  }
  return choices;
}

/**
 * プレイヤーの選択肢を処理し、ゲーム状態を更新する。
 * @param {import('./game.js').GameState} state - ゲーム状態
 * @param {string} choice - プレイヤーの選択
 * @param {boolean} [enterCave=true] - 洞窟探索時の応答（テスト用）
 * @returns {boolean} ゲーム続行の場合は true
 */
export function handleChoice(state, choice, enterCave = true) {
  if (state.gameOver) return false;

  if (choice === CHOICES.LEFT) {
    if (!checkHiddenPath(state, enterCave)) {
      leftPath(state);
    }
    return false;
  }

  if (choice === CHOICES.RIGHT) {
    if (!checkHiddenPath(state, enterCave)) {
      rightPath(state);
    }
    return false;
  }

  if (choice === CHOICES.GIVE_UP) {
    neutralEnding(state);
    return false;
  }

  if (choice === CHOICES.SEARCH && !state.searched) {
    searchArea(state);
    return true;
  }

  // 無効な選択肢
  const validRange = state.searched ? '1-3' : '1-4';
  state.displayText.push(`\n無効な選択肢です。${validRange}の範囲で入力してください。`);
  return true;
}