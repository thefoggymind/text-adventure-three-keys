/**
 * 「3つの鍵 — Web Edition」Renderer & App Controller
 * Handles DOM rendering, screen transitions, and UI interactions.
 * SPEC.md §5 UI/UX仕様 準拠
 *
 * Public API (exported for testing):
 *   showTitleScreen, showGameScreen, showEndingScreen
 *   updateStory, updateChoices, updateInventory, showNotification
 *   fadeIn, fadeOut, toggleTheme, initTheme
 */

import {
  createInitialState,
  getState,
  restoreState,
  getChoices,
  handleChoice,
  CHOICES,
  RESULTS,
  DONATION_URL,
  EVENTS,
  ACHIEVEMENT_IDS,
  ACHIEVEMENT_DEFS,
  checkAchievements,
  ITEMS,
} from './game.js';

// --- DOM References ---
const $ = (id) => document.getElementById(id);

const screens = {
  title: $('screen-title'),
  game: $('screen-game'),
  ending: $('screen-ending'),
};

const storyText = $('story-text');
const choicesContainer = $('choices');
const inventoryItems = $('inventory-items');

const endingTitle = $('ending-title');
const endingDecoration = $('ending-decoration');
const endingStory = $('ending-story');
const endingCount = $('ending-count');
const progressFill = $('progress-fill');
const progressPercent = $('progress-percent');

const btnNewGame = $('btn-new-game');
const btnContinue = $('btn-continue');
const btnToTitle = $('btn-to-title');
const btnPlayAgain = $('btn-play-again');
const btnSave = $('btn-save');
const btnMenu = $('btn-menu');
const btnThemeToggle = $('btn-theme-toggle');
const btnShowAchievements = $('show-achievements-btn');

const toastEl = $('toast');

// --- State ---
let state = createInitialState();

// --- エンディングタイトルマッピング ---
const ENDING_TITLES = {
  [RESULTS.WIN]: { left: '勝利：清らかな川', right: '勝利：古代の宝具' },
  [RESULTS.LOSE]: { left: '敗北：毒の川', right: '敗北：呪いの遺物' },
  [RESULTS.NEUTRAL]: '中立：帰還',
  [RESULTS.HIDDEN]: '★ 真の英雄 ★',
};

const ENDING_DECORATIONS = {
  [RESULTS.WIN]: '---',
  [RESULTS.LOSE]: '---',
  [RESULTS.NEUTRAL]: '---',
  [RESULTS.HIDDEN]: '--- ★',
};

// --- Animation Utilities ---

/**
 * Apply fadeIn animation to an element.
 * @param {HTMLElement} el
 */
export function fadeIn(el) {
  el.style.animation = 'none';
  void el.offsetHeight; // force reflow
  el.style.animation = 'fadeIn 0.3s ease-out';
}

/**
 * Apply fadeOut animation to an element.
 * @param {HTMLElement} el
 */
export function fadeOut(el) {
  el.style.animation = 'none';
  void el.offsetHeight; // force reflow
  el.style.animation = 'fadeOut 0.3s ease-out';
}

// --- Screen Switching ---

function showScreen(screenId) {
  Object.keys(screens).forEach((id) => {
    const el = screens[id];
    if (id === screenId) {
      el.classList.add('active');
      fadeIn(el);
    } else {
      el.classList.remove('active');
      el.style.animation = '';
    }
  });
  state.screen = screenId;
  updateDonationVisibility();
}

/**
 * 寄付ボタン・シェアボタンの表示をタイトル画面・エンディング画面でのみ表示するように制御する。
 */
function updateDonationVisibility() {
  const isVisible = state.screen === 'title' || state.screen === 'ending';
  document.querySelectorAll('.donate-link, .feedback-link, .ending-donate, .ending-feedback, .ending-share').forEach((el) => {
    el.style.display = isVisible ? '' : 'none';
  });
}

/**
 * タイトル画面を表示する。
 * 「つづきから」ボタンの表示/非表示を更新し、フォーカスを「はじめる」に移動する。
 */
export function showTitleScreen() {
  showScreen('title');
  updateContinueButton();
  if (btnNewGame) btnNewGame.focus();
}

/**
 * ゲーム画面を表示し、ストーリー・選択肢・インベントリをレンダリングする。
 * 初回表示時は初期メッセージを displayText にセットする。
 */
export function showGameScreen() {
  // Build display text if empty (first time entering game screen)
  if (state.displayText.length === 0) {
    state.displayText.push('テキストベースアドベンチャーゲームへようこそ！');
    state.displayText.push('あなたは森の中で目覚めました。前には二つの道があります。');
    state.displayText.push('');
    state.displayText.push('何をしますか？');
  }
  showScreen('game');
  updateStory(state.displayText);
  const choices = getChoices(state);
  updateChoices(choices);
  updateInventory(state.inventory);
  // Focus first choice
  const firstChoice = choicesContainer.querySelector('.btn-choice');
  if (firstChoice) firstChoice.focus();
}

/**
 * エンディング画面を表示する。現在の state.outcome に基づいて
 * タイトル・ストーリー・達成度をレンダリングする。
 */
export function showEndingScreen() {
  const outcome = state.outcome;
  const edTitle = getEndingTitle(state);
  if (outcome === RESULTS.HIDDEN) {
    endingTitle.textContent = `--- ${edTitle} ---`;
  } else {
    endingTitle.textContent = `「--- ${edTitle} ---」`;
  }
  endingDecoration.textContent = `${getEndingDecoration(outcome)} ═══════════════════════════════`;

  // Render story text (skip header/decoration lines from displayText)
  const storyLines = [];
  let inHeader = false;
  state.displayText.forEach((line) => {
    if (line.includes('=============')) {
      inHeader = !inHeader;
      return;
    }
    if (inHeader) return;
    storyLines.push(line);
  });

  endingStory.innerHTML = '';
  storyLines.forEach((line) => {
    const p = document.createElement('p');
    p.textContent = line;
    endingStory.appendChild(p);
  });

  // Update progress
  const achievements = getAchievements();
  const unlocked = achievements.endingsUnlocked.length;
  const pct = Math.round((unlocked / 6) * 100);
  endingCount.textContent = unlocked;
  progressFill.style.width = `${pct}%`;
  progressPercent.textContent = `${pct}%`;
  if (progressFill.parentElement) {
    progressFill.parentElement.setAttribute('aria-valuenow', pct);
  }

  showScreen('ending');
}

/**
 * 受け取った endingData をもとにエンディング画面をレンダリングする。
 * endingData が null / undefined の場合は安全にフォールバック表示する。
 * @param {{ outcome: string, story: string }|null} endingData
 */
export function renderEndingScene(endingData) {
  if (!endingData) {
    showScreen('ending');
    endingTitle.textContent = '--- 未達成 ---';
    endingDecoration.textContent = '--- ═══════════════════════════════';
    endingStory.innerHTML = '<p>エンディングデータがありません。</p>';
    return;
  }
  const outcome = endingData.outcome;
  const edTitle = ENDING_TITLES[outcome] || '未知の結末';
  const deco = getEndingDecoration(outcome);
  endingTitle.textContent = `「--- ${edTitle} ---」`;
  endingDecoration.textContent = `${deco} ═══════════════════════════════`;
  const story = endingData.story || '記録がありません。';
  endingStory.innerHTML = story;
  showScreen('ending');
}

// --- Theme Toggle ---

function getPreferredTheme() {
  if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
    return 'dark';
  }
  return 'light';
}

/**
 * data-theme 属性を light ⇔ dark で切り替える。
 * 選択状態は localStorage に保存する。
 */
export function toggleTheme() {
  const current = document.documentElement.getAttribute('data-theme');
  const next = current === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', next);
  try {
    localStorage.setItem('three-keys-theme', next);
  } catch (_) { /* ignore */ }
}

/**
 * テーマを初期化する。localStorage に保存済みの設定があればそれを、
 * なければ OS の prefers-color-scheme に従う。
 */
export function initTheme() {
  const saved = (() => {
    try { return localStorage.getItem('three-keys-theme'); } catch (_) { return null; }
  })();
  const theme = saved || getPreferredTheme();
  if (theme === 'dark') {
    document.documentElement.setAttribute('data-theme', 'dark');
  }
}

// --- Toast Notification ---

/**
 * 画面上部にトースト通知を表示する。
 * @param {string} message - 表示するメッセージ
 * @param {number} [duration=2000] - 表示時間（ms）
 */
export function showNotification(message, duration = 2000) {
  toastEl.textContent = message;
  toastEl.style.display = 'block';
  fadeIn(toastEl);
  setTimeout(() => {
    toastEl.style.display = 'none';
  }, duration);
}

// --- Rendering Functions ---

/**
 * ストーリーテキストを story-text 領域にレンダリングする。
 * @param {string[]} textLines - 表示するテキスト行の配列
 */
export function updateStory(textLines) {
  storyText.innerHTML = '';
  if (textLines.length === 0) {
    const p = document.createElement('p');
    p.className = 'story-paragraph';
    p.textContent = '（ここにストーリーが表示されます）';
    storyText.appendChild(p);
    return;
  }
  textLines.forEach((line) => {
    const p = document.createElement('p');
    p.className = 'story-paragraph';
    if (line === '') {
      p.innerHTML = '&nbsp;';
    } else {
      p.textContent = line;
    }
    storyText.appendChild(p);
  });
  // Scroll to bottom
  const gameContent = $('game-content');
  if (gameContent) {
    gameContent.scrollTop = gameContent.scrollHeight;
  }
}

/**
 * 選択肢ボタンを choices 領域にレンダリングする。
 * @param {Array<{value: string, label: string}>} choices - 選択肢の配列
 */
export function updateChoices(choices) {
  choicesContainer.innerHTML = '';
  choices.forEach((choice) => {
    const btn = document.createElement('button');
    btn.className = 'btn btn-choice';
    btn.setAttribute('data-value', choice.value);
    btn.setAttribute('aria-label', choice.label);
    btn.textContent = `${choice.value}. ${choice.label}`;
    btn.addEventListener('click', () => onChoice(choice.value));
    choicesContainer.appendChild(btn);
  });
}

/**
 * インベントリ（所持アイテム）を inventory-items 領域に表示する。
 * @param {string[]} items - 所持アイテム名の配列
 */
export function updateInventory(items) {
  if (!items || items.length === 0) {
    inventoryItems.textContent = 'なし';
  } else {
    inventoryItems.textContent = items.join(', ');
  }
}

export function getEndingTitle(state) {
  const outcome = state.outcome;
  if (outcome === RESULTS.WIN) {
    const text = state.displayText.join(' ');
    const isLeft = text.includes('左の道');
    return isLeft ? ENDING_TITLES[RESULTS.WIN].left : ENDING_TITLES[RESULTS.WIN].right;
  }
  if (outcome === RESULTS.LOSE) {
    const text = state.displayText.join(' ');
    const isLeft = text.includes('左の道');
    return isLeft ? ENDING_TITLES[RESULTS.LOSE].left : ENDING_TITLES[RESULTS.LOSE].right;
  }
  return ENDING_TITLES[outcome] || 'エンディング';
}

function getEndingDecoration(outcome) {
  return ENDING_DECORATIONS[outcome] || '---';
}

// --- Save / Load (LocalStorage) ---

const SAVE_KEY = 'web_adventure_save';
const ACHIEVEMENT_KEY = 'three-keys-achievements-v1';

function saveGame() {
  try {
    const data = getState(state);
    localStorage.setItem(SAVE_KEY, JSON.stringify(data));
    showNotification('💾 セーブしました');
  } catch (e) {
    showNotification('⚠ セーブに失敗しました');
  }
  updateContinueButton();
}

function hasSaveData() {
  try {
    const raw = localStorage.getItem(SAVE_KEY);
    if (!raw) return false;
    const data = JSON.parse(raw);
    return data && data.version === 1;
  } catch (_) {
    return false;
  }
}

function defaultAchievementData() {
  return {
    version: 1,
    endingsUnlocked: [],
    totalPlayCount: 0,
    achievements: Object.fromEntries(ACHIEVEMENT_DEFS.map(d => [d.id, false])),
    consecutiveWins: 0,
    collectedItems: [],
  };
}

export function getAchievements() {
  try {
    const raw = localStorage.getItem(ACHIEVEMENT_KEY);
    if (!raw) return defaultAchievementData();

    const data = JSON.parse(raw);
    // Auto-upgrade old format (pre-achievements data)
    if (!data.achievements) {
      data.achievements = defaultAchievementData().achievements;
      data.consecutiveWins = 0;
      data.collectedItems = [];
      if (data.endingsUnlocked) {
        if (data.endingsUnlocked.includes('win')) data.achievements.victory = true;
        if (data.endingsUnlocked.includes('lose')) data.achievements.defeat = true;
        if (data.endingsUnlocked.includes('neutral')) data.achievements.return_home = true;
        if (data.endingsUnlocked.includes('hidden')) data.achievements.true_hero = true;
      }
    }
    // Ensure all achievement keys exist (for new achievements added later)
    ACHIEVEMENT_DEFS.forEach(def => {
      if (!(def.id in data.achievements)) data.achievements[def.id] = false;
    });
    return data;
  } catch (_) {
    return defaultAchievementData();
  }
}

export function recordEnding(endingId) {
  try {
    const achievements = getAchievements();
    if (!achievements.endingsUnlocked.includes(endingId)) {
      achievements.endingsUnlocked.push(endingId);
    }
    achievements.totalPlayCount = (achievements.totalPlayCount || 0) + 1;
    const newOnes = checkAchievements(EVENTS.ENDING_REACHED, { outcome: endingId }, achievements);
    if (newOnes.length > 0) {
      checkAndShowAchievements(newOnes);
      newOnes.forEach(id => { achievements.achievements[id] = true; });
    }
    localStorage.setItem(ACHIEVEMENT_KEY, JSON.stringify(achievements));
  } catch (_) { /* ignore */ }
}

function updateContinueButton() {
  if (hasSaveData()) {
    btnContinue.style.display = '';
  } else {
    btnContinue.style.display = 'none';
  }
}

// --- Achievement UI ---

/**
 * Display an achievement popup notification.
 * Creates/reuses a div#achievement-popup with title (h3), description (p),
 * icon (span), and data-achievement-id attribute.
 * After 2.5s adds 'fade-out' class and removes the element after animation.
 * @param {object} achievement - { id, title, description, icon }
 */
export function showAchievementPopup(achievement) {
  const isHidden = achievement.isHidden || false;

  // Reuse existing placeholder if present (for test compatibility)
  let popup = document.getElementById('achievement-popup');
  if (!popup) {
    popup = document.createElement('div');
    popup.id = 'achievement-popup';
    popup.className = 'achievement-popup';
    document.body.appendChild(popup);
  }

  // Reset state
  popup.id = 'achievement-popup';
  popup.className = 'achievement-popup';
  popup.style.display = 'flex';
  popup.setAttribute('data-achievement-id', achievement.id || '');
  popup.innerHTML = '';

  // Icon
  const iconEl = document.createElement('span');
  iconEl.className = 'achievement-icon';
  iconEl.textContent = achievement.icon || '🏆';
  popup.appendChild(iconEl);

  // Title
  const titleEl = document.createElement('h3');
  titleEl.className = 'achievement-title';
  titleEl.textContent = isHidden ? '???' : (achievement.title || '');
  popup.appendChild(titleEl);

  // Description
  const descEl = document.createElement('p');
  descEl.className = 'achievement-description';
  descEl.textContent = isHidden ? '' : (achievement.description || '実績解除');
  popup.appendChild(descEl);

  // OK button
  const okBtn = document.createElement('button');
  okBtn.className = 'btn btn-achievement-ok';
  okBtn.textContent = 'OK';
  okBtn.addEventListener('click', () => {
    clearTimeout(autoHideTimeout);
    dismissPopup();
  });
  popup.appendChild(okBtn);

  // Animation class
  popup.classList.add('achievement-popup-enter');

  function dismissPopup() {
    popup.classList.remove('achievement-popup-enter');
    popup.classList.add('fade-out');
    setTimeout(() => {
      if (popup.parentNode) {
        popup.parentNode.removeChild(popup);
      }
    }, 300);
  }

  // Auto-hide after 2.5s: add fade-out, then remove after animation
  const autoHideTimeout = setTimeout(() => {
    dismissPopup();
  }, 2500);
}

/**
 * Display popups for newly unlocked achievements.
 * Takes an array of achievement IDs and shows a popup for each.
 * Does nothing if the array is empty.
 * @param {string[]} newlyUnlocked - Array of achievement IDs
 */
export function checkAndShowAchievements(newlyUnlocked) {
  if (!newlyUnlocked || newlyUnlocked.length === 0) return;
  const achievements = getAchievements();
  const newOnes = [];
  newlyUnlocked.forEach(id => {
    const def = ACHIEVEMENT_DEFS.find(d => d.id === id);
    if (def && !achievements.achievements[id]) {
      newOnes.push({
        id: def.id,
        title: def.name,
        description: '',
        icon: def.name.match(/^(\S+)/)?.[1] || '🏆',
        isHidden: def.secret,
      });
    }
  });
  newOnes.forEach(ach => showAchievementPopup(ach));
}

/**
 * Render the full achievement list into #achievement-list container.
 * Shows locked/unlocked states, progress for veteran,
 * hides secret locked achievements as "???", and shows share button
 * when all achievements are completed.
 */
export function renderAchievementList() {
  const achievements = getAchievements();
  let container = document.getElementById('achievement-list');
  if (!container) {
    container = document.createElement('div');
    container.id = 'achievement-list';
    document.body.appendChild(container);
  }

  container.innerHTML = '';
  const total = ACHIEVEMENT_DEFS.length;
  const unlockedCount = ACHIEVEMENT_DEFS.filter(def => achievements.achievements[def.id] === true).length;

  ACHIEVEMENT_DEFS.forEach(def => {
    const isUnlocked = achievements.achievements[def.id] === true;
    // Skip locked secret achievements (hidden when not yet unlocked)
    if (!isUnlocked && def.secret) return;
    const item = document.createElement('div');
    item.className = `achievement-item${isUnlocked ? ' unlocked' : ''}`;
    item.textContent = isUnlocked ? def.name : '???';
    container.appendChild(item);
  });

  if (unlockedCount === total) {
    const shareBtn = document.createElement('button');
    shareBtn.className = 'btn btn-share achievement-share-btn';
    const shareText = encodeURIComponent(
      '🎮 「3つの鍵 — Web Edition」全実績コンプリートしました！\n#3つの鍵 #WebEdition'
    );
    shareBtn.textContent = '🎉 完全制覇をシェア';
    shareBtn.addEventListener('click', () => {
      window.open(`https://twitter.com/intent/tweet?text=${shareText}`, '_blank');
    });
    container.appendChild(shareBtn);
  }
}

// --- Event Handlers ---

export function onChoice(value) {
  const prevInventory = [...state.inventory];
  const continueGame = handleChoice(state, value, true);

  // Fire CHOICE_MADE event for achievements
  try {
    const achievements = getAchievements();
    let newOnes = checkAchievements(EVENTS.CHOICE_MADE, { choice: value }, achievements);

    // Fire ITEM_FOUND for newly acquired items
    const newItems = state.inventory.filter(item => !prevInventory.includes(item));
    newItems.forEach(item => {
      const itemNew = checkAchievements(EVENTS.ITEM_FOUND, { itemName: item }, achievements);
      newOnes = [...newOnes, ...itemNew];
    });

    if (newOnes.length > 0) {
      checkAndShowAchievements(newOnes);
      newOnes.forEach(id => { achievements.achievements[id] = true; });
      localStorage.setItem(ACHIEVEMENT_KEY, JSON.stringify(achievements));
    } else {
      // Still persist side-effects (consecutiveWins, collectedItems)
      localStorage.setItem(ACHIEVEMENT_KEY, JSON.stringify(achievements));
    }
  } catch (_) { /* ignore */ }

  if (state.gameOver) {
    recordEnding(state.outcome);
    showEndingScreen();
  } else if (continueGame) {
    showGameScreen();
  }
}

// Expose onChoice on window for testability (jest.spyOn on ESM exports is not supported)
window.onChoice = onChoice;

function startNewGame() {
  state = createInitialState();
  // Fire GAME_START event for achievements
  try {
    const achievements = getAchievements();
    achievements.totalPlayCount = (achievements.totalPlayCount || 0) + 1;
    const newOnes = checkAchievements(EVENTS.GAME_START, {}, achievements);
    if (newOnes.length > 0) {
      checkAndShowAchievements(newOnes);
      newOnes.forEach(id => { achievements.achievements[id] = true; });
    }
    localStorage.setItem(ACHIEVEMENT_KEY, JSON.stringify(achievements));
  } catch (_) { /* ignore */ }
  showGameScreen();
}

function continueGame() {
  const loaded = loadGame();
  if (loaded) {
    showGameScreen();
  } else {
    showNotification('セーブデータがありません');
  }
}

function goToTitle() {
  showTitleScreen();
}

function playAgain() {
  startNewGame();
}

// --- Keyboard Shortcuts ---

export function loadGame() {
  try {
    const raw = localStorage.getItem(SAVE_KEY);
    if (!raw) return null;
    const data = JSON.parse(raw);
    if (data.version !== 1) {
      localStorage.removeItem(SAVE_KEY);
      return null;
    }
    state = restoreState(data);
    state.screen = 'game';
    return state;
  } catch (e) {
    localStorage.removeItem(SAVE_KEY);
    showNotification('⚠ セーブデータが破損していたため初期化しました');
    return null;
  }
}

export function handleKeyDown(e) {
  if (state.screen === 'game' && !state.gameOver) {
    const key = e.key;
    const choices = getChoices(state);
    const choiceMap = {
      '1': CHOICES.LEFT,
      '2': CHOICES.RIGHT,
      '3': CHOICES.GIVE_UP,
      '4': CHOICES.SEARCH,
    };
    if (['1', '2', '3', '4'].includes(key)) {
      const value = choiceMap[key];
      const valid = choices.some((c) => c.value === value);
      if (valid) {
        e.preventDefault();
        window.onChoice(value);
        return;
      }
    }
    if (key === 's' || key === 'S') {
      e.preventDefault();
      saveGame();
      return;
    }
    if (key === 'Escape') {
      e.preventDefault();
      if (confirm('ゲームを終了しますか？\n（セーブされていないデータは失われます）')) {
        goToTitle();
      }
    }
  }
}

// --- Initialization ---

export function init() {
  initTheme();

  // Event listeners
  btnNewGame.addEventListener('click', startNewGame);
  btnContinue.addEventListener('click', continueGame);
  btnToTitle.addEventListener('click', goToTitle);
  btnPlayAgain.addEventListener('click', playAgain);
  btnSave.addEventListener('click', saveGame);
  btnThemeToggle.addEventListener('click', toggleTheme);

  // Menu button (save + go to title)
  btnMenu.addEventListener('click', () => {
    if (confirm('メニューを開きますか？\n「OK」でタイトルに戻ります（セーブ推奨）')) {
      goToTitle();
    }
  });

  // Achievements button
  btnShowAchievements.addEventListener('click', () => {
    const list = $('achievement-list');
    if (list.style.display === 'none' || list.style.display === '') {
      renderAchievementList();
      list.style.display = 'block';
    } else {
      list.style.display = 'none';
    }
  });

  // Keyboard shortcuts
  document.addEventListener('keydown', handleKeyDown);

  // Continue button visibility
  updateContinueButton();

  // Show title screen
  showTitleScreen();
}

// Start when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}