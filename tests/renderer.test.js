/**
 * Tests for renderer.js — DOM rendering, screen transitions, animations,
 * theme toggling, and notification display.
 *
 * @jest-environment jsdom
 */

import {
  jest, beforeAll, afterAll, beforeEach, afterEach, describe, test, expect,
} from '@jest/globals';

// Re-export game constants for test assertions
import {
  CHOICES, RESULTS, ACHIEVEMENT_IDS, ACHIEVEMENT_DEFS, createInitialState,
} from '../game.js';

/**
 * Set up the full DOM structure before importing renderer.js.
 * renderer.js runs document.getElementById() at module load time,
 * so all required elements must exist in jsdom beforehand.
 */
function setupDOM() {
  document.body.innerHTML = `
    <!-- Title Screen -->
    <div id="screen-title" class="screen active">
      <a href="#" class="donate-link">作者を支援する</a>
    </div>
    <!-- Game Screen -->
    <div id="screen-game" class="screen"></div>
    <!-- Ending Screen -->
    <div id="screen-ending" class="screen"></div>

    <!-- Game Content (inside game screen) -->
    <div id="game-content">
      <div id="story-text"></div>
      <div id="choices"></div>
      <span id="inventory-items">なし</span>
    </div>

    <!-- Ending elements -->
    <h2 id="ending-title"></h2>
    <div id="ending-decoration"></div>
    <div id="ending-story"></div>
    <span id="ending-count">0</span>
    <div id="progress-fill"></div>
    <div id="progress-percent">0%</div>

    <!-- Buttons -->
    <button id="btn-new-game"></button>
    <button id="btn-continue" style="display:none"></button>
    <button id="btn-to-title"></button>
    <button id="btn-play-again"></button>
    <button id="btn-save"></button>
    <button id="btn-menu"></button>
    <button id="btn-theme-toggle"></button>
    <button id="show-achievements-btn"></button>

    <!-- Ending share button -->
    <div class="ending-share">
      <a href="#" class="btn btn-share">Twitterでシェア</a>
    </div>

    <!-- Achievement Screen -->
    <div id="screen-achievements" class="screen">
      <div id="achievement-list"></div>
    </div>

    <!-- Toast -->
    <div id="toast" class="toast" style="display:none"></div>
  `;
}

function clearDOM() {
  document.body.innerHTML = '';
}

let renderer;

beforeAll(async () => {
  setupDOM();
  // Mock window.matchMedia (used by getPreferredTheme)
  Object.defineProperty(window, 'matchMedia', {
    writable: true,
    value: jest.fn().mockImplementation((query) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: jest.fn(),
      removeListener: jest.fn(),
      addEventListener: jest.fn(),
      removeEventListener: jest.fn(),
      dispatchEvent: jest.fn(),
    })),
  });
  // Mock localStorage
  const store = {};
  jest.spyOn(Storage.prototype, 'getItem').mockImplementation((key) => store[key] ?? null);
  jest.spyOn(Storage.prototype, 'setItem').mockImplementation((key, value) => { store[key] = String(value); });
  jest.spyOn(Storage.prototype, 'removeItem').mockImplementation((key) => { delete store[key]; });
  jest.spyOn(Storage.prototype, 'clear').mockImplementation(() => { Object.keys(store).forEach(k => delete store[k]); });

  // Dynamic import so DOM is ready before module evaluation
  renderer = await import('../renderer.js');
});

afterAll(() => {
  clearDOM();
  jest.restoreAllMocks();
});

// ===========================================================================
// Animation Utilities
// ===========================================================================
describe('fadeIn / fadeOut', () => {
  test('fadeIn sets animation to fadeIn on element', () => {
    const el = document.createElement('div');
    renderer.fadeIn(el);
    expect(el.style.animation).toContain('fadeIn');
  });

  test('fadeOut sets animation to fadeOut on element', () => {
    const el = document.createElement('div');
    renderer.fadeOut(el);
    expect(el.style.animation).toContain('fadeOut');
  });
});

// ===========================================================================
// Screen Transition Functions
// ===========================================================================
describe('showTitleScreen', () => {
  beforeEach(() => {
    document.getElementById('btn-continue').style.display = 'none';
    document.getElementById('screen-title').classList.remove('active');
    document.getElementById('screen-game').classList.add('active');
  });

  test('adds active class to title screen', () => {
    renderer.showTitleScreen();
    const titleScreen = document.getElementById('screen-title');
    expect(titleScreen.classList.contains('active')).toBe(true);
  });

  test('removes active class from game screen', () => {
    renderer.showTitleScreen();
    const gameScreen = document.getElementById('screen-game');
    expect(gameScreen.classList.contains('active')).toBe(false);
  });

  test('hides continue button when no save data', () => {
    // localStorage is empty → no save data
    renderer.showTitleScreen();
    const btn = document.getElementById('btn-continue');
    expect(btn.style.display).toBe('none');
  });

  test('shows continue button when save data exists', () => {
    localStorage.setItem('web_adventure_save', JSON.stringify({ version: 1 }));
    renderer.showTitleScreen();
    const btn = document.getElementById('btn-continue');
    expect(btn.style.display).not.toBe('none');
  });
});

describe('showGameScreen', () => {
  beforeEach(() => {
    document.getElementById('screen-game').classList.remove('active');
    document.getElementById('screen-title').classList.add('active');
    document.getElementById('story-text').innerHTML = '';
    document.getElementById('choices').innerHTML = '';
    document.getElementById('inventory-items').textContent = 'なし';
  });

  test('activates game screen', () => {
    renderer.showGameScreen();
    expect(document.getElementById('screen-game').classList.contains('active')).toBe(true);
    expect(document.getElementById('screen-title').classList.contains('active')).toBe(false);
  });

  test('renders initial story text on first call', () => {
    renderer.showGameScreen();
    const storyEl = document.getElementById('story-text');
    expect(storyEl.children.length).toBeGreaterThan(0);
    const text = storyEl.textContent;
    expect(text).toContain('テキストベースアドベンチャー');
    expect(text).toContain('目覚めました');
  });

  test('renders choices buttons', () => {
    renderer.showGameScreen();
    const choicesEl = document.getElementById('choices');
    expect(choicesEl.children.length).toBeGreaterThan(0);
    const firstBtn = choicesEl.querySelector('.btn-choice');
    expect(firstBtn).not.toBeNull();
    expect(firstBtn.textContent).toContain('1.');
  });

  test('renders inventory as "なし" when empty', () => {
    renderer.showGameScreen();
    expect(document.getElementById('inventory-items').textContent).toBe('なし');
  });
});

describe('showEndingScreen', () => {
  beforeEach(() => {
    document.getElementById('screen-ending').classList.remove('active');
    document.getElementById('ending-title').textContent = '';
    document.getElementById('ending-decoration').textContent = '';
    document.getElementById('ending-story').innerHTML = '';
    document.getElementById('ending-count').textContent = '0';
    document.getElementById('progress-fill').style.width = '0%';
    document.getElementById('progress-percent').textContent = '0%';
  });

  test('activates ending screen', () => {
    renderer.showEndingScreen();
    expect(document.getElementById('screen-ending').classList.contains('active')).toBe(true);
  });

  test('displays ending title and decoration', () => {
    renderer.showEndingScreen();
    const titleEl = document.getElementById('ending-title');
    expect(titleEl.textContent.length).toBeGreaterThan(0);
    const decoEl = document.getElementById('ending-decoration');
    expect(decoEl.textContent.length).toBeGreaterThan(0);
  });

  test('shows progress stats', () => {
    renderer.showEndingScreen();
    expect(document.getElementById('progress-fill').style.width).toBeTruthy();
    expect(document.getElementById('progress-percent').textContent).toBeTruthy();
  });

  test('stores data-theme to localStorage on toggle', () => {
    renderer.toggleTheme();
    const theme = localStorage.getItem('three-keys-theme');
    expect(theme).toBe('dark');
  });

  test('renderEndingScene handles null endingData gracefully', () => {
    renderer.renderEndingScene(null);
    expect(document.getElementById('screen-ending').classList.contains('active')).toBe(true);
    expect(document.getElementById('ending-title').textContent).toBe('--- 未達成 ---');
  });

  test('renderEndingScene handles undefined endingData gracefully', () => {
    renderer.renderEndingScene(undefined);
    expect(document.getElementById('screen-ending').classList.contains('active')).toBe(true);
    expect(document.getElementById('ending-title').textContent).toBe('--- 未達成 ---');
  });
});

// ===========================================================================
// Save / Load Integration Tests
// ===========================================================================
describe('Save / Load integration', () => {
  beforeEach(() => {
    // Clear all localStorage before each test
    localStorage.clear();
    // Reset screens to title
    document.getElementById('screen-title').classList.add('active');
    document.getElementById('screen-game').classList.remove('active');
    document.getElementById('screen-ending').classList.remove('active');
  });

  test('title screen hides continue button when no valid save data', () => {
    // No data at all
    renderer.showTitleScreen();
    const btn = document.getElementById('btn-continue');
    expect(btn.style.display).toBe('none');
  });

  test('title screen hides continue button when save data has wrong version', () => {
    localStorage.setItem('web_adventure_save', JSON.stringify({ version: 999 }));
    renderer.showTitleScreen();
    const btn = document.getElementById('btn-continue');
    expect(btn.style.display).toBe('none');
  });

  test('title screen hides continue button when save data is malformed JSON', () => {
    localStorage.setItem('web_adventure_save', '{broken json');
    renderer.showTitleScreen();
    const btn = document.getElementById('btn-continue');
    expect(btn.style.display).toBe('none');
  });

  test('title screen shows continue button when valid save data exists', () => {
    localStorage.setItem('web_adventure_save', JSON.stringify({ version: 1, phase: 'intro', inventory: [], searched: false, outcome: 'none', displayText: ['test'], gameOver: false, hiddenPlayed: false }));
    renderer.showTitleScreen();
    const btn = document.getElementById('btn-continue');
    expect(btn.style.display).not.toBe('none');
  });

  test('save → title → continue restores game state', () => {
    // Start a new game to have a state
    document.getElementById('btn-new-game').click();
    expect(document.getElementById('screen-game').classList.contains('active')).toBe(true);
    // Save the game
    document.getElementById('btn-save').click();
    // Verify toast notification appears
    const toast = document.getElementById('toast');
    expect(toast.textContent).toContain('セーブしました');
    // Go back to title
    document.getElementById('btn-to-title').click();
    expect(document.getElementById('screen-title').classList.contains('active')).toBe(true);
    // Continue button should now be visible
    const btnContinue = document.getElementById('btn-continue');
    expect(btnContinue.style.display).not.toBe('none');
    // Click continue
    btnContinue.click();
    // Should be back on game screen with story intact
    expect(document.getElementById('screen-game').classList.contains('active')).toBe(true);
    const storyEl = document.getElementById('story-text');
    expect(storyEl.children.length).toBeGreaterThan(0);
    expect(storyEl.textContent).toContain('ようこそ');
  });

  test('clicking save button shows save notification', () => {
    document.getElementById('btn-new-game').click();
    document.getElementById('btn-save').click();
    const toast = document.getElementById('toast');
    expect(toast.textContent).toContain('セーブしました');
    expect(toast.style.display).toBe('block');
  });
});

// ===========================================================================
// Content Update Functions
// ===========================================================================
describe('updateStory', () => {
  beforeEach(() => {
    document.getElementById('story-text').innerHTML = '';
  });

  test('renders multiple lines as paragraph elements', () => {
    const lines = ['Line 1', 'Line 2', 'Line 3'];
    renderer.updateStory(lines);
    const storyEl = document.getElementById('story-text');
    expect(storyEl.children.length).toBe(3);
    expect(storyEl.children[0].tagName).toBe('P');
    expect(storyEl.children[0].textContent).toBe('Line 1');
    expect(storyEl.children[1].textContent).toBe('Line 2');
    expect(storyEl.children[2].textContent).toBe('Line 3');
  });

  test('renders empty array with placeholder', () => {
    renderer.updateStory([]);
    const storyEl = document.getElementById('story-text');
    expect(storyEl.children.length).toBe(1);
    expect(storyEl.textContent).toContain('ここにストーリー');
  });

  test('renders empty line as &nbsp;', () => {
    renderer.updateStory(['Hello', '', 'World']);
    const storyEl = document.getElementById('story-text');
    expect(storyEl.children[1].innerHTML).toBe('&nbsp;');
  });

  test('paragraphs have story-paragraph class', () => {
    renderer.updateStory(['Test']);
    const p = document.querySelector('#story-text p');
    expect(p.classList.contains('story-paragraph')).toBe(true);
  });
});

describe('updateChoices', () => {
  beforeEach(() => {
    document.getElementById('choices').innerHTML = '';
  });

  test('renders choice buttons', () => {
    const choices = [
      { value: '1', label: '左の道を行く' },
      { value: '2', label: '右の道を行く' },
    ];
    renderer.updateChoices(choices);
    const container = document.getElementById('choices');
    expect(container.children.length).toBe(2);
    const btns = container.querySelectorAll('.btn-choice');
    expect(btns.length).toBe(2);
  });

  test('button text includes value prefix and label', () => {
    const choices = [{ value: '1', label: 'Test Label' }];
    renderer.updateChoices(choices);
    const btn = document.querySelector('#choices .btn-choice');
    expect(btn.textContent).toContain('1.');
    expect(btn.textContent).toContain('Test Label');
  });

  test('sets data-value and aria-label attributes', () => {
    const choices = [{ value: '2', label: 'Right Path' }];
    renderer.updateChoices(choices);
    const btn = document.querySelector('#choices .btn-choice');
    expect(btn.getAttribute('data-value')).toBe('2');
    expect(btn.getAttribute('aria-label')).toBe('Right Path');
  });

  test('renders empty choices array as empty container', () => {
    renderer.updateChoices([]);
    const container = document.getElementById('choices');
    expect(container.children.length).toBe(0);
  });
});

describe('updateInventory', () => {
  beforeEach(() => {
    document.getElementById('inventory-items').textContent = 'なし';
  });

  test('shows "なし" when items is empty', () => {
    renderer.updateInventory([]);
    expect(document.getElementById('inventory-items').textContent).toBe('なし');
  });

  test('shows "なし" when items is null', () => {
    renderer.updateInventory(null);
    expect(document.getElementById('inventory-items').textContent).toBe('なし');
  });

  test('shows comma-separated items', () => {
    renderer.updateInventory(['鍵', '地図', '宝石']);
    expect(document.getElementById('inventory-items').textContent).toBe('鍵, 地図, 宝石');
  });

  test('shows single item without comma', () => {
    renderer.updateInventory(['鍵']);
    expect(document.getElementById('inventory-items').textContent).toBe('鍵');
  });
});

// ===========================================================================
// Achievement UI Tests
// ===========================================================================
describe('Achievement UI', () => {
  beforeEach(() => {
    localStorage.clear();
    // Remove any leftover popup elements from previous tests
    const oldPopup = document.getElementById('achievement-popup');
    if (oldPopup && oldPopup.parentNode) oldPopup.parentNode.removeChild(oldPopup);
    // Re-create the popup placeholder as in the DOM setup
    const popup = document.createElement('div');
    popup.id = 'achievement-popup';
    popup.className = 'achievement-popup';
    popup.style.display = 'none';
    document.body.appendChild(popup);
  });

  afterEach(() => {
    // Clean up any popup timers
    if (window.achievementPopupTimeout) {
      clearTimeout(window.achievementPopupTimeout);
      window.achievementPopupTimeout = null;
    }
    jest.useRealTimers();
  });

  // ---- checkAndShowAchievements ----

  describe('checkAndShowAchievements', () => {
    test('shows popups for newly unlocked achievements', () => {
      renderer.checkAndShowAchievements(['first_step']);
      const popup = document.getElementById('achievement-popup');
      expect(popup.style.display).toBe('flex');
      expect(popup.textContent).toContain('はじまりの一歩');
    });

    test('shows popup for each achievement with correct icon/title', () => {
      renderer.checkAndShowAchievements(['left_path']);
      const popup = document.getElementById('achievement-popup');
      expect(popup.textContent).toContain('左の道');
    });

    test('does nothing when newlyUnlocked is empty', () => {
      renderer.checkAndShowAchievements([]);
      const popup = document.getElementById('achievement-popup');
      expect(popup.style.display).toBe('none');
    });

    test('does nothing when newlyUnlocked is null/undefined', () => {
      renderer.checkAndShowAchievements(null);
      renderer.checkAndShowAchievements(undefined);
      const popup = document.getElementById('achievement-popup');
      expect(popup.style.display).toBe('none');
    });

    test('(1) calls showAchievementPopup for newly unlocked achievement', () => {
      renderer.checkAndShowAchievements(['first_step']);
      const popup = document.getElementById('achievement-popup');
      expect(popup.style.display).toBe('flex');
      expect(popup.textContent).toContain('🔰');
      expect(popup.textContent).toContain('はじまりの一歩');
    });

    test('(2) does not call showAchievementPopup for already-unlocked achievements', () => {
      const data = renderer.getAchievements();
      data.achievements.first_step = true;
      localStorage.setItem('three-keys-achievements-v1', JSON.stringify(data));
      renderer.checkAndShowAchievements(['first_step']);
      const popup = document.getElementById('achievement-popup');
      expect(popup.style.display).toBe('none');
    });

    test('(3) calls showAchievementPopup for each when multiple achievements unlocked simultaneously', () => {
      renderer.checkAndShowAchievements(['first_step', 'left_path', 'victory']);
      const popup = document.getElementById('achievement-popup');
      expect(popup.style.display).toBe('flex');
      // The last achievement's content should be displayed
      expect(popup.textContent).toContain('🏆');
      expect(popup.textContent).toContain('栄光の勝利');
    });

    test('(4) handles hidden (secret) achievements correctly via checkAndShowAchievements', () => {
      renderer.checkAndShowAchievements([ACHIEVEMENT_IDS.TRUE_HERO]);
      const popup = document.getElementById('achievement-popup');
      expect(popup.style.display).toBe('flex');
      expect(popup.textContent).toContain('???');
      expect(popup.textContent).not.toContain('真の英雄');
    });
  });

  // ---- showAchievementPopup ----

  describe('showAchievementPopup', () => {
    test('displays achievement title and icon', () => {
      renderer.showAchievementPopup({
        id: 'first_step',
        title: '🔰 はじまりの一歩',
        icon: '🔰',
        description: '',
      });
      const popup = document.getElementById('achievement-popup');
      expect(popup.style.display).toBe('flex');
      expect(popup.textContent).toContain('🔰 はじまりの一歩');
      expect(popup.textContent).toContain('実績解除');
    });

    test('shows ??? for hidden (secret) achievements', () => {
      renderer.showAchievementPopup({
        id: 'true_hero',
        title: '🌟 真の英雄',
        icon: '🌟',
        isHidden: true,
        description: '',
      });
      const popup = document.getElementById('achievement-popup');
      expect(popup.textContent).toContain('???');
      expect(popup.textContent).not.toContain('真の英雄');
    });

    test('adds animation class achievement-popup-enter', () => {
      renderer.showAchievementPopup({ id: 'test', title: 'Test', icon: '🏆' });
      const popup = document.getElementById('achievement-popup');
      expect(popup.classList.contains('achievement-popup-enter')).toBe(true);
    });

    test('auto-hides after 2.5 seconds', () => {
      jest.useFakeTimers();
      renderer.showAchievementPopup({ id: 'test', title: 'Test', icon: '🏆' });
      const popup = document.getElementById('achievement-popup');
      expect(popup.style.display).toBe('flex');
      jest.advanceTimersByTime(2500);
      // After 2500ms the leave animation starts; after 2800ms the element is removed
      jest.advanceTimersByTime(300);
      expect(popup.parentNode).toBeNull();
    });

    test('dismisses immediately when OK button is clicked', () => {
      jest.useFakeTimers();
      renderer.showAchievementPopup({ id: 'test', title: 'Test', icon: '🏆' });
      const popup = document.getElementById('achievement-popup');
      expect(popup.style.display).toBe('flex');

      const okBtn = popup.querySelector('.btn-achievement-ok');
      expect(okBtn).not.toBeNull();
      expect(okBtn.textContent).toBe('OK');

      okBtn.click();

      // Popup should be immediately removed (no need to wait 2.5s)
      // After click: fade-out class added + 300ms removal
      expect(popup.classList.contains('fade-out')).toBe(true);
      jest.advanceTimersByTime(300);
      expect(popup.parentNode).toBeNull();
    });
  });

  // ---- renderAchievementList ----

  describe('renderAchievementList', () => {
    test('renders all non-secret achievements when locked', () => {
      const data = renderer.getAchievements();
      localStorage.setItem('three-keys-achievements-v1', JSON.stringify(data));
      renderer.renderAchievementList();
      const items = document.querySelectorAll('.achievement-item');
      // 13 total - 4 secret (hidden when locked) = 9 visible
      expect(items.length).toBe(9);
      // All locked: all show ???
      items.forEach(item => expect(item.textContent).toBe('???'));
    });

    test('shows unlocked vs locked states', () => {
      const data = renderer.getAchievements();
      data.achievements.first_step = true;
      localStorage.setItem('three-keys-achievements-v1', JSON.stringify(data));
      renderer.renderAchievementList();
      const items = document.querySelectorAll('.achievement-item');
      // first_step (index 0): unlocked
      expect(items[0].classList.contains('unlocked')).toBe(true);
      expect(items[0].textContent).toBe('🔰 はじまりの一歩');
      // left_path (index 1): locked
      expect(items[1].classList.contains('unlocked')).toBe(false);
      expect(items[1].textContent).toBe('???');
    });

    test('shows ??? for all locked achievements', () => {
      const data = renderer.getAchievements();
      Object.keys(data.achievements).forEach(k => { data.achievements[k] = false; });
      localStorage.setItem('three-keys-achievements-v1', JSON.stringify(data));
      renderer.renderAchievementList();
      const items = document.querySelectorAll('.achievement-item');
      expect(items.length).toBe(9);
      items.forEach(item => expect(item.textContent).toBe('???'));
    });

    test('renders correctly with empty achievements storage', () => {
      localStorage.removeItem('three-keys-achievements-v1');
      renderer.renderAchievementList();
      const items = document.querySelectorAll('.achievement-item');
      expect(items.length).toBe(9);
      items.forEach(item => expect(item.textContent).toBe('???'));
    });
  });

  // ---- show-achievements-btn ----

  describe('show-achievements-btn', () => {
    beforeEach(() => {
      const list = document.getElementById('achievement-list');
      list.style.display = 'none';
      list.innerHTML = '';
    });

    test('(1) clicking button shows achievement list', () => {
      const btn = document.getElementById('show-achievements-btn');
      btn.click();
      const list = document.getElementById('achievement-list');
      expect(list.style.display).toBe('block');
      const items = list.querySelectorAll('.achievement-item');
      expect(items.length).toBe(9);
    });

    test('(2) displayed content matches getAchievements()', () => {
      const data = renderer.getAchievements();
      data.achievements.first_step = true;
      localStorage.setItem('three-keys-achievements-v1', JSON.stringify(data));
      const btn = document.getElementById('show-achievements-btn');
      btn.click();
      const items = document.querySelectorAll('.achievement-item');
      // first_step (index 0) should be unlocked with name
      expect(items[0].classList.contains('unlocked')).toBe(true);
      expect(items[0].textContent).toBe('🔰 はじまりの一歩');
      // All others locked
      for (let i = 1; i < items.length; i++) {
        expect(items[i].classList.contains('unlocked')).toBe(false);
        expect(items[i].textContent).toBe('???');
      }
    });
  });

  // ---- Integration: Ending → Achievement → UI ----

  describe('Integration: ending unlocks achievements and updates UI', () => {
    test('recordEnding triggers victory popup on win outcome', () => {
      // Set up data so victory is not yet unlocked
      const data = renderer.getAchievements();
      data.achievements.victory = false;
      localStorage.setItem('three-keys-achievements-v1', JSON.stringify(data));
      renderer.recordEnding('win');
      // Should save victory as unlocked and show popup
      const saved = JSON.parse(localStorage.getItem('three-keys-achievements-v1'));
      expect(saved.achievements.victory).toBe(true);
      // Popup should have displayed
      const popup = document.getElementById('achievement-popup');
      expect(popup.textContent).toContain('栄光の勝利');
    });

    test('recordEnding triggers defeat popup on lose outcome', () => {
      const data = renderer.getAchievements();
      data.achievements.defeat = false;
      localStorage.setItem('three-keys-achievements-v1', JSON.stringify(data));
      renderer.recordEnding('lose');
      const saved = JSON.parse(localStorage.getItem('three-keys-achievements-v1'));
      expect(saved.achievements.defeat).toBe(true);
      const popup = document.getElementById('achievement-popup');
      expect(popup.textContent).toContain('無念の敗北');
    });

    test('recordEnding triggers return_home popup on neutral outcome', () => {
      const data = renderer.getAchievements();
      data.achievements.return_home = false;
      localStorage.setItem('three-keys-achievements-v1', JSON.stringify(data));
      renderer.recordEnding('neutral');
      const saved = JSON.parse(localStorage.getItem('three-keys-achievements-v1'));
      expect(saved.achievements.return_home).toBe(true);
      const popup = document.getElementById('achievement-popup');
      expect(popup.textContent).toContain('帰還');
    });

    test('recordEnding triggers true_hero popup on hidden outcome', () => {
      const data = renderer.getAchievements();
      data.achievements.true_hero = false;
      localStorage.setItem('three-keys-achievements-v1', JSON.stringify(data));
      renderer.recordEnding('hidden');
      const saved = JSON.parse(localStorage.getItem('three-keys-achievements-v1'));
      expect(saved.achievements.true_hero).toBe(true);
      const popup = document.getElementById('achievement-popup');
      expect(popup.textContent).toContain('???');
    });

    test('renderAchievementList reflects unlocked ending achievements', () => {
      const data = renderer.getAchievements();
      Object.keys(data.achievements).forEach(k => { data.achievements[k] = false; });
      data.achievements.victory = true;
      data.achievements.defeat = true;
      data.achievements.return_home = true;
      data.achievements.true_hero = true;
      localStorage.setItem('three-keys-achievements-v1', JSON.stringify(data));
      renderer.renderAchievementList();
      const items = document.querySelectorAll('.achievement-item');
      // victory (index 3), defeat (index 4), return_home (index 5), true_hero (index 6): unlocked
      expect(items[3].classList.contains('unlocked')).toBe(true);
      expect(items[3].textContent).toBe('🏆 栄光の勝利');
      expect(items[4].classList.contains('unlocked')).toBe(true);
      expect(items[5].classList.contains('unlocked')).toBe(true);
      expect(items[6].classList.contains('unlocked')).toBe(true);
      // first_step (index 0): locked (false)
      expect(items[0].classList.contains('unlocked')).toBe(false);
      expect(items[0].textContent).toBe('???');
    });

    test('completing all achievements shows share button', () => {
      const data = renderer.getAchievements();
      ACHIEVEMENT_DEFS.forEach(def => { data.achievements[def.id] = true; });
      localStorage.setItem('three-keys-achievements-v1', JSON.stringify(data));
      renderer.renderAchievementList();
      const shareBtn = document.querySelector('.achievement-share-btn');
      expect(shareBtn).not.toBeNull();
      expect(shareBtn.textContent).toContain('完全制覇をシェア');
    });
  });
});

// ===========================================================================
// Notification
// ===========================================================================
describe('showNotification', () => {
  beforeEach(() => {
    jest.useFakeTimers();
    const toast = document.getElementById('toast');
    toast.style.display = 'none';
    toast.textContent = '';
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  test('displays toast message and becomes visible', () => {
    renderer.showNotification('Test Message');
    const toast = document.getElementById('toast');
    expect(toast.textContent).toBe('Test Message');
    expect(toast.style.display).toBe('block');
  });

  test('hides toast after default duration', () => {
    renderer.showNotification('Test');
    jest.advanceTimersByTime(2000);
    const toast = document.getElementById('toast');
    expect(toast.style.display).toBe('none');
  });

  test('hides toast after custom duration', () => {
    renderer.showNotification('Test', 500);
    jest.advanceTimersByTime(500);
    const toast = document.getElementById('toast');
    expect(toast.style.display).toBe('none');
  });

  test('toast is not hidden before duration elapses', () => {
    renderer.showNotification('Test', 1000);
    jest.advanceTimersByTime(500);
    const toast = document.getElementById('toast');
    expect(toast.style.display).toBe('block');
  });
});

// ===========================================================================
// Theme Toggle
// ===========================================================================
describe('Theme functions', () => {
  beforeEach(() => {
    document.documentElement.removeAttribute('data-theme');
    localStorage.removeItem('three-keys-theme');
  });

  describe('initTheme', () => {
    test('does not set data-theme when prefers-color-scheme is light', () => {
      window.matchMedia.mockImplementation(() => ({ matches: false }));
      renderer.initTheme();
      expect(document.documentElement.getAttribute('data-theme')).toBeNull();
    });

    test('sets data-theme=dark when prefers-color-scheme is dark', () => {
      window.matchMedia.mockImplementation(() => ({ matches: true }));
      renderer.initTheme();
      expect(document.documentElement.getAttribute('data-theme')).toBe('dark');
    });

    test('uses localStorage value over prefers-color-scheme', () => {
      localStorage.setItem('three-keys-theme', 'light');
      window.matchMedia.mockImplementation(() => ({ matches: true }));
      renderer.initTheme();
      expect(document.documentElement.getAttribute('data-theme')).toBeNull(); // light = no attribute
    });

    test('uses localStorage dark without OS preference', () => {
      window.matchMedia.mockImplementation(() => ({ matches: false }));
      localStorage.setItem('three-keys-theme', 'dark');
      renderer.initTheme();
      expect(document.documentElement.getAttribute('data-theme')).toBe('dark');
    });
  });

  describe('toggleTheme', () => {
    test('toggles from light to dark', () => {
      document.documentElement.setAttribute('data-theme', 'light');
      renderer.toggleTheme();
      expect(document.documentElement.getAttribute('data-theme')).toBe('dark');
    });

    test('toggles from dark to light', () => {
      document.documentElement.setAttribute('data-theme', 'dark');
      renderer.toggleTheme();
      expect(document.documentElement.getAttribute('data-theme')).toBe('light');
    });

    test('persists choice to localStorage', () => {
      document.documentElement.setAttribute('data-theme', 'dark');
      renderer.toggleTheme();
      expect(localStorage.getItem('three-keys-theme')).toBe('light');
    });

    test('toggles twice returns to original', () => {
      document.documentElement.setAttribute('data-theme', 'light');
      renderer.toggleTheme(); // → dark
      renderer.toggleTheme(); // → light
      expect(document.documentElement.getAttribute('data-theme')).toBe('light');
    });
  });
});

// ===========================================================================
// Game Flow Integration Tests (through DOM interaction)
// ===========================================================================
describe('Game flow integration via DOM', () => {
  test('clicking new game button starts game and shows game screen', () => {
    const btn = document.getElementById('btn-new-game');
    btn.click();
    const gameScreen = document.getElementById('screen-game');
    expect(gameScreen.classList.contains('active')).toBe(true);
    const storyEl = document.getElementById('story-text');
    expect(storyEl.children.length).toBeGreaterThan(0);
    expect(storyEl.textContent).toContain('ようこそ');
  });

  test('game screen has choices after starting new game', () => {
    document.getElementById('btn-new-game').click();
    const choicesEl = document.getElementById('choices');
    expect(choicesEl.children.length).toBeGreaterThan(0);
    const btn = choicesEl.querySelector('.btn-choice');
    expect(btn.textContent).toMatch(/^\d+\./);
  });

  test('clicking title button returns to title screen', () => {
    // First start a game
    document.getElementById('btn-new-game').click();
    // Ending screen has btn-to-title — but we started from new game, so we need
    // to navigate through game → ending or directly trigger showTitleScreen
    document.getElementById('btn-to-title').click();
    const titleScreen = document.getElementById('screen-title');
    expect(titleScreen.classList.contains('active')).toBe(true);
  });

  test('play again button restarts game', () => {
    document.getElementById('btn-new-game').click();
    // Get initial story text
    const storyEl = document.getElementById('story-text');
    const firstText = storyEl.textContent;
    // Play again
    document.getElementById('btn-play-again').click();
    expect(document.getElementById('screen-game').classList.contains('active')).toBe(true);
    // Should have fresh story
    expect(storyEl.textContent).toContain('ようこそ');
  });

  test('starting new game focuses first choice', () => {
    document.getElementById('btn-new-game').click();
    const activeEl = document.activeElement;
    expect(activeEl).not.toBeNull();
    expect(activeEl.classList.contains('btn-choice')).toBe(true);
  });

  // --- Full Screen Transition Integration Tests ---

  function clickChoiceByValue(value) {
    const btn = document.querySelector(`#choices .btn-choice[data-value="${value}"]`);
    if (btn) btn.click();
    return btn;
  }

  test('full flow: title → game → ending screen via GIVE_UP choice', () => {
    // Start from title → game
    document.getElementById('btn-new-game').click();
    expect(document.getElementById('screen-game').classList.contains('active')).toBe(true);
    // Select GIVE_UP (choice 3) → triggers neutral ending
    const btn = clickChoiceByValue('3');
    expect(btn).not.toBeNull();
    expect(document.getElementById('screen-ending').classList.contains('active')).toBe(true);
    // Verify ending content
    const titleEl = document.getElementById('ending-title');
    expect(titleEl.textContent).toContain('帰還');
    const decoEl = document.getElementById('ending-decoration');
    expect(decoEl.textContent.length).toBeGreaterThan(0);
  });

  test('full flow: ending screen → back to title via btn-to-title', () => {
    // Start new game
    document.getElementById('btn-new-game').click();
    // Reach ending via GIVE_UP
    clickChoiceByValue('3');
    expect(document.getElementById('screen-ending').classList.contains('active')).toBe(true);
    // Click "タイトルへ戻る" button
    document.getElementById('btn-to-title').click();
    const titleScreen = document.getElementById('screen-title');
    expect(titleScreen.classList.contains('active')).toBe(true);
    // Verify other screens are not active
    expect(document.getElementById('screen-game').classList.contains('active')).toBe(false);
    expect(document.getElementById('screen-ending').classList.contains('active')).toBe(false);
  });
});

// ===========================================================================
// Edge Cases
// ===========================================================================
describe('Edge cases', () => {
  test('updateStory with very long text', () => {
    const longLine = 'A'.repeat(5000);
    renderer.updateStory([longLine]);
    const storyEl = document.getElementById('story-text');
    expect(storyEl.children.length).toBe(1);
    expect(storyEl.textContent.length).toBe(5000);
  });

  test('updateStory with many lines', () => {
    const lines = Array.from({ length: 100 }, (_, i) => `Line ${i + 1}`);
    renderer.updateStory(lines);
    const storyEl = document.getElementById('story-text');
    expect(storyEl.children.length).toBe(100);
    expect(storyEl.children[99].textContent).toBe('Line 100');
  });

  test('showNotification handles empty message', () => {
    jest.useFakeTimers();
    renderer.showNotification('');
    const toast = document.getElementById('toast');
    expect(toast.textContent).toBe('');
    expect(toast.style.display).toBe('block');
    jest.advanceTimersByTime(2000);
    expect(toast.style.display).toBe('none');
    jest.useRealTimers();
  });

  test('updateInventory with many items', () => {
    const items = Array.from({ length: 10 }, (_, i) => `Item ${i + 1}`);
    renderer.updateInventory(items);
    const text = document.getElementById('inventory-items').textContent;
    expect(text).toContain('Item 1');
    expect(text).toContain('Item 10');
    expect(text.split(', ').length).toBe(10);
  });

  test('updateChoices triggers onclick handler', () => {
    const choices = [{ value: '3', label: 'Give Up' }];
    renderer.updateChoices(choices);
    const btn = document.querySelector('#choices .btn-choice');
    expect(btn.getAttribute('data-value')).toBe('3');
    expect(btn.getAttribute('aria-label')).toBe('Give Up');
    expect(btn.textContent).toContain('3.');
    expect(btn.textContent).toContain('Give Up');
  });

  test('fadeIn and fadeOut are chainable (no errors)', () => {
    const el = document.createElement('div');
    expect(() => {
      renderer.fadeIn(el);
      renderer.fadeOut(el);
      renderer.fadeIn(el);
    }).not.toThrow();
  });
});

// ===========================================================================
// getAchievements — Old-format migration
// ===========================================================================
describe('getAchievements — old-format migration', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  test('migrates old format with endingsUnlocked to achievements object', () => {
    // Simulate old-format data (no "achievements" property)
    const oldData = {
      version: 1,
      endingsUnlocked: ['win', 'lose', 'neutral', 'hidden'],
      totalPlayCount: 3,
    };
    localStorage.setItem('three-keys-achievements-v1', JSON.stringify(oldData));

    const result = renderer.getAchievements();
    expect(result.achievements).toBeDefined();
    // Endings from endingsUnlocked should be set to true
    expect(result.achievements.victory).toBe(true);
    expect(result.achievements.defeat).toBe(true);
    expect(result.achievements.return_home).toBe(true);
    expect(result.achievements.true_hero).toBe(true);
    // Non-ending achievements remain false
    expect(result.achievements.first_step).toBe(false);
    expect(result.achievements.collector).toBe(false);
    // Migration resets these fields
    expect(result.consecutiveWins).toBe(0);
    expect(result.collectedItems).toEqual([]);
    // Other fields preserved
    expect(result.totalPlayCount).toBe(3);
  });

  test('migrates old format without endingsUnlocked — all achievements false', () => {
    // Old data with no achievements and no endingsUnlocked
    const oldData = { version: 1, totalPlayCount: 5 };
    localStorage.setItem('three-keys-achievements-v1', JSON.stringify(oldData));

    const result = renderer.getAchievements();
    expect(result.achievements).toBeDefined();
    // All ending achievements should be false (no endingsUnlocked)
    expect(result.achievements.victory).toBe(false);
    expect(result.achievements.defeat).toBe(false);
    expect(result.achievements.return_home).toBe(false);
    expect(result.achievements.true_hero).toBe(false);
    // All achievements exist and are false
    ACHIEVEMENT_DEFS.forEach(def => {
      expect(result.achievements[def.id]).toBe(false);
    });
    // Migration resets these
    expect(result.consecutiveWins).toBe(0);
    expect(result.collectedItems).toEqual([]);
    // totalPlayCount preserved
    expect(result.totalPlayCount).toBe(5);
  });
});

// ===========================================================================
// showAchievementPopup Tests
// ===========================================================================
describe('showAchievementPopup', () => {
  const testAchievement = {
    id: 'test_achievement_01',
    title: 'テスト実績',
    description: 'これはテスト用の実績です',
    icon: '⭐',
  };

  afterEach(() => {
    // Remove any leftover popup elements and clean up timers
    document.querySelectorAll('.achievement-popup').forEach(el => {
      if (el.parentNode) el.parentNode.removeChild(el);
    });
    jest.useRealTimers();
  });

  test('ポップアップがDOMに追加されること', () => {
    renderer.showAchievementPopup(testAchievement);
    const popup = document.querySelector('.achievement-popup');
    expect(popup).not.toBeNull();
    expect(popup.parentNode).toBe(document.body);
  });

  test('正しいtitleが表示されること', () => {
    renderer.showAchievementPopup(testAchievement);
    const titleEl = document.querySelector('.achievement-popup h3');
    expect(titleEl).not.toBeNull();
    expect(titleEl.textContent).toBe('テスト実績');
  });

  test('正しいdescriptionが表示されること', () => {
    renderer.showAchievementPopup(testAchievement);
    const descEl = document.querySelector('.achievement-popup p');
    expect(descEl).not.toBeNull();
    expect(descEl.textContent).toBe('これはテスト用の実績です');
  });

  test('正しいiconが表示されること', () => {
    renderer.showAchievementPopup(testAchievement);
    const iconEl = document.querySelector('.achievement-popup .achievement-icon');
    expect(iconEl).not.toBeNull();
    expect(iconEl.textContent).toBe('⭐');
  });

  test('2.5秒後にポップアップが削除されること', () => {
    jest.useFakeTimers();
    renderer.showAchievementPopup(testAchievement);
    const popup = document.querySelector('.achievement-popup');
    expect(popup).not.toBeNull();
    // Advance by 2500ms to trigger fade-out
    jest.advanceTimersByTime(2500);
    expect(popup.classList.contains('fade-out')).toBe(true);
    // Advance by another 300ms for the animation end
    jest.advanceTimersByTime(300);
    expect(document.querySelector('.achievement-popup')).toBeNull();
  });

  // --- Branch coverage: popup creation vs reuse (lines 458-465) ---

  test('ポップアップ未存在時は新規要素が生成されること', () => {
    // Ensure no popup element exists beforehand
    document.querySelectorAll('.achievement-popup').forEach(el => el.remove());
    renderer.showAchievementPopup(testAchievement);
    const popup = document.querySelector('.achievement-popup');
    expect(popup).not.toBeNull();
    expect(popup.id).toBe('achievement-popup');
    expect(popup.className).toContain('achievement-popup');
    expect(popup.style.display).toBe('flex');
    // Verify all child elements are created
    expect(popup.querySelector('.achievement-icon')).not.toBeNull();
    expect(popup.querySelector('.achievement-title')).not.toBeNull();
    expect(popup.querySelector('.achievement-description')).not.toBeNull();
    expect(popup.querySelector('.btn-achievement-ok')).not.toBeNull();
    // Verify content
    expect(popup.querySelector('.achievement-icon').textContent).toBe('⭐');
    expect(popup.querySelector('.achievement-title').textContent).toBe('テスト実績');
    expect(popup.querySelector('.achievement-description').textContent).toBe('これはテスト用の実績です');
    expect(popup.querySelector('.btn-achievement-ok').textContent).toBe('OK');
  });

  test('既存ポップアップが存在する場合は要素を再利用し新規作成しないこと', () => {
    // First call: creates popup
    renderer.showAchievementPopup(testAchievement);
    const firstPopupElements = document.querySelectorAll('.achievement-popup');
    expect(firstPopupElements.length).toBe(1);
    const firstPopup = firstPopupElements[0];

    // Second call with different achievement: should reuse same element
    const secondAchievement = {
      id: 'test_achievement_02',
      title: '2つ目の実績',
      description: '2つ目の説明',
      icon: '🏆',
    };
    renderer.showAchievementPopup(secondAchievement);

    // Still only one popup element in the DOM
    const popups = document.querySelectorAll('.achievement-popup');
    expect(popups.length).toBe(1);
    // Same element (still attached to DOM)
    expect(document.body.contains(firstPopup)).toBe(true);
    // Content has been updated to the second achievement
    expect(popups[0].querySelector('.achievement-icon').textContent).toBe('🏆');
    expect(popups[0].querySelector('.achievement-title').textContent).toBe('2つ目の実績');
    expect(popups[0].querySelector('.achievement-description').textContent).toBe('2つ目の説明');
  });
});

// ===========================================================================
// renderAchievementList Tests
// ===========================================================================
describe('renderAchievementList', () => {
  const ACHIEVEMENT_KEY = 'three-keys-achievements-v1';

  beforeEach(() => {
    localStorage.removeItem(ACHIEVEMENT_KEY);
  });

  afterEach(() => {
    // Ensure achievement-list element exists in the DOM for subsequent tests
    if (!document.getElementById('achievement-list')) {
      const el = document.createElement('div');
      el.id = 'achievement-list';
      const screen = document.getElementById('screen-achievements');
      if (screen) {
        screen.appendChild(el);
      } else {
        document.body.appendChild(el);
      }
    }
  });

  test('(1) creates container when not in DOM', () => {
    const el = document.getElementById('achievement-list');
    el.remove();
    expect(document.getElementById('achievement-list')).toBeNull();
    renderer.renderAchievementList();
    const container = document.getElementById('achievement-list');
    expect(container).not.toBeNull();
    expect(container.id).toBe('achievement-list');
    // 13 total - 4 secret (hidden when locked) = 9 visible
    expect(container.children.length).toBe(9);
  });

  test('(2) clears existing content and re-renders', () => {
    const container = document.getElementById('achievement-list');
    container.innerHTML = '<div class="old-content">old</div>';
    expect(container.children.length).toBe(1);
    renderer.renderAchievementList();
    // 13 total - 4 secret (hidden when locked) = 9 visible
    expect(container.children.length).toBe(9);
    expect(container.querySelector('.old-content')).toBeNull();
  });

  test('(3) displays unlocked achievements with their names and class', () => {
    const data = renderer.getAchievements();
    data.achievements.first_step = true;
    data.achievements.left_path = true;
    data.achievements.right_path = true;
    localStorage.setItem(ACHIEVEMENT_KEY, JSON.stringify(data));
    renderer.renderAchievementList();
    const items = document.querySelectorAll('#achievement-list .achievement-item');
    // 3 unlocked (non-secret) + 6 locked (non-secret) = 9 visible; secret remain hidden
    expect(items.length).toBe(9);
    expect(items[0].classList.contains('unlocked')).toBe(true);
    expect(items[0].textContent).toBe('🔰 はじまりの一歩');
    expect(items[1].classList.contains('unlocked')).toBe(true);
    expect(items[1].textContent).toBe('🚶 左の道を行く');
    expect(items[2].classList.contains('unlocked')).toBe(true);
    expect(items[2].textContent).toBe('🚶 右の道を行く');
  });

  test('(4) shows ??? for all locked achievements, hides secret ones', () => {
    const data = renderer.getAchievements();
    Object.keys(data.achievements).forEach(key => { data.achievements[key] = false; });
    localStorage.setItem(ACHIEVEMENT_KEY, JSON.stringify(data));
    renderer.renderAchievementList();
    const items = document.querySelectorAll('#achievement-list .achievement-item');
    // 13 total - 4 secret (hidden) = 9 visible, all locked, all show ???
    expect(items.length).toBe(9);
    items.forEach(item => {
      expect(item.classList.contains('unlocked')).toBe(false);
      expect(item.textContent).toBe('???');
    });
  });

  test('(5) renders mixed unlocked/locked states correctly', () => {
    const data = renderer.getAchievements();
    Object.keys(data.achievements).forEach(key => { data.achievements[key] = false; });
    data.achievements.first_step = true;
    data.achievements.victory = true;
    data.achievements.true_hero = true;
    localStorage.setItem(ACHIEVEMENT_KEY, JSON.stringify(data));
    renderer.renderAchievementList();
    const items = document.querySelectorAll('#achievement-list .achievement-item');
    // 3 unlocked (first_step, victory, true_hero) + 7 locked non-secret - 3 locked secret (explorer, completionist, all_seer) = 10 visible
    expect(items.length).toBe(10);
    // first_step (index 0): unlocked
    expect(items[0].classList.contains('unlocked')).toBe(true);
    expect(items[0].textContent).toBe('🔰 はじまりの一歩');
    // left_path (index 1): locked
    expect(items[1].classList.contains('unlocked')).toBe(false);
    expect(items[1].textContent).toBe('???');
    // victory (index 3): unlocked (after right_path at index 2)
    expect(items[3].classList.contains('unlocked')).toBe(true);
    expect(items[3].textContent).toBe('🏆 栄光の勝利');
    // true_hero (index 6): unlocked (secret, but unlocked so shows name)
    expect(items[6].classList.contains('unlocked')).toBe(true);
    expect(items[6].textContent).toBe('🌟 真の英雄');
    // explorer is secret and locked -> hidden, not in the list
  });

  test('(6) handles fresh state (no saved data) without error', () => {
    localStorage.removeItem(ACHIEVEMENT_KEY);
    expect(() => renderer.renderAchievementList()).not.toThrow();
    const items = document.querySelectorAll('#achievement-list .achievement-item');
    // 13 total - 4 secret (hidden when locked) = 9 visible
    expect(items.length).toBe(9);
    items.forEach(item => {
      expect(item.textContent).toBe('???');
    });
  });
});