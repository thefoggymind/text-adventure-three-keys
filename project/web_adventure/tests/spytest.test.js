/**
 * @jest-environment jsdom
 */
import { jest, test, expect, beforeAll } from '@jest/globals';
import { ACHIEVEMENT_IDS } from '../game.js';

function setupDOM() {
  document.body.innerHTML = `
    <div id="screen-title" class="screen active">
      <a href="#" class="donate-link">支援</a>
    </div>
    <div id="screen-game" class="screen"></div>
    <div id="screen-ending" class="screen"></div>
    <div id="game-content">
      <div id="story-text"></div>
      <div id="choices"></div>
      <span id="inventory-items">なし</span>
    </div>
    <h2 id="ending-title"></h2>
    <div id="ending-decoration"></div>
    <div id="ending-story"></div>
    <span id="ending-count">0</span>
    <div id="progress-fill"></div>
    <div id="progress-percent">0%</div>
    <button id="btn-new-game"></button>
    <button id="btn-continue" style="display:none"></button>
    <button id="btn-to-title"></button>
    <button id="btn-play-again"></button>
    <button id="btn-save"></button>
    <button id="btn-menu"></button>
    <button id="btn-theme-toggle"></button>
    <button id="show-achievements-btn"></button>
    <div class="ending-share">
      <a href="#" class="btn btn-share">Twitterでシェア</a>
    </div>
    <div id="screen-achievements" class="screen">
      <div id="achievement-list"></div>
    </div>
    <div id="toast" class="toast" style="display:none"></div>
    <div id="achievement-popup" style="display:none"></div>
  `;
}

setupDOM();
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation(q => ({
    matches: false, media: q, onchange: null,
    addListener: jest.fn(), removeListener: jest.fn(),
    addEventListener: jest.fn(), removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
});
const store = {};
jest.spyOn(Storage.prototype, 'getItem').mockImplementation(key => store[key] ?? null);
jest.spyOn(Storage.prototype, 'setItem').mockImplementation((k, v) => { store[k] = String(v); });
jest.spyOn(Storage.prototype, 'removeItem').mockImplementation((key) => { delete store[key]; });
jest.spyOn(Storage.prototype, 'clear').mockImplementation(() => { Object.keys(store).forEach(k => delete store[k]); });

let renderer;
beforeAll(async () => { renderer = await import('../renderer.js'); });

afterEach(() => {
  const popup = document.getElementById('achievement-popup');
  if (popup) {
    popup.style.display = 'none';
    popup.innerHTML = '';
  }
  localStorage.clear();
});

test('checkAndShowAchievements calls showAchievementPopup for newly unlocked achievements', () => {
  renderer.checkAndShowAchievements(['first_step']);
  const popup = document.getElementById('achievement-popup');
  expect(popup.style.display).toBe('flex');
  expect(popup.textContent).toContain('🔰');
  expect(popup.textContent).toContain('はじまりの一歩');
});

test('checkAndShowAchievements does not call showAchievementPopup for already unlocked', () => {
  const data = renderer.getAchievements();
  data.achievements.first_step = true;
  localStorage.setItem('three-keys-achievements-v1', JSON.stringify(data));
  renderer.checkAndShowAchievements(['first_step']);
  const popup = document.getElementById('achievement-popup');
  expect(popup.style.display).toBe('none');
});

test('checkAndShowAchievements calls showAchievementPopup for each when multiple unlocked', () => {
  renderer.checkAndShowAchievements(['first_step', 'left_path', 'victory']);
  const popup = document.getElementById('achievement-popup');
  expect(popup.style.display).toBe('flex');
  expect(popup.textContent).toContain('栄光の勝利');
});

test('checkAndShowAchievements calls showAchievementPopup for hidden achievements', () => {
  renderer.checkAndShowAchievements([ACHIEVEMENT_IDS.TRUE_HERO]);
  const popup = document.getElementById('achievement-popup');
  expect(popup.style.display).toBe('flex');
  expect(popup.textContent).toContain('???');
  expect(popup.textContent).not.toContain('真の英雄');
});