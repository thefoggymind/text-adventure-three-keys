/**
 * Unit tests for game.js — core game logic ported from Python.
 * Covers all constants, state management, branching, random outcomes,
 * items, endings, and game-over/clear conditions.
 */
import {
  CHOICES,
  RESULTS,
  ITEMS,
  DONATION_URL,
  EVENTS,
  ACHIEVEMENT_IDS,
  ACHIEVEMENT_DEFS,
  checkAchievements,
  createInitialState,
  showDonation,
  randomOutcome,
  leftPath,
  rightPath,
  neutralEnding,
  hiddenEnding,
  renderEndingHeader,
  searchArea,
  checkHiddenPath,
  getChoices,
  handleChoice,
} from '../game.js';

// ---------------------------------------------------------------------------
// 定数テスト
// ---------------------------------------------------------------------------
describe('Constants', () => {
  test('CHOICES has all expected values', () => {
    expect(CHOICES.LEFT).toBe('1');
    expect(CHOICES.RIGHT).toBe('2');
    expect(CHOICES.GIVE_UP).toBe('3');
    expect(CHOICES.SEARCH).toBe('4');
  });

  test('RESULTS has all expected values', () => {
    expect(RESULTS.WIN).toBe('win');
    expect(RESULTS.LOSE).toBe('lose');
    expect(RESULTS.NEUTRAL).toBe('neutral');
    expect(RESULTS.HIDDEN).toBe('hidden');
  });

  test('ITEMS has all expected values', () => {
    expect(ITEMS.JEWEL).toBe('Shining Jewel');
    expect(ITEMS.KEY).toBe('Rusty Key');
    expect(ITEMS.MAP).toBe('Old Map');
  });

  test('DONATION_URL is correct', () => {
    expect(DONATION_URL).toBe('https://ko-fi.com/thefoggymind');
  });
});

// ---------------------------------------------------------------------------
// 状態管理テスト
// ---------------------------------------------------------------------------
describe('State management', () => {
  test('createInitialState returns valid initial state', () => {
    const state = createInitialState();
    expect(state.screen).toBe('title');
    expect(state.phase).toBe('intro');
    expect(state.inventory).toEqual([]);
    expect(state.searched).toBe(false);
    expect(state.outcome).toBe('none');
    expect(state.displayText).toEqual([]);
    expect(state.gameOver).toBe(false);
    expect(state.hiddenPlayed).toBe(false);
  });

  test('createInitialState returns a new object each call', () => {
    const s1 = createInitialState();
    const s2 = createInitialState();
    expect(s1).not.toBe(s2);
    s1.inventory.push('test');
    expect(s2.inventory).toEqual([]);
  });
});

// ---------------------------------------------------------------------------
// ユーティリティ関数テスト
// ---------------------------------------------------------------------------
describe('Utility functions', () => {
  describe('showDonation', () => {
    test('adds donation message lines to displayText', () => {
      const dt = [];
      showDonation(dt);
      expect(dt.length).toBe(5);
      expect(dt[0]).toBe('');
      expect(dt[2]).toContain(DONATION_URL);
    });
  });

  describe('renderEndingHeader', () => {
    test('adds header with default decoration', () => {
      const dt = [];
      renderEndingHeader(dt, 'Test Title');
      expect(dt.length).toBe(4);
      expect(dt[1]).toBe('============================================================');
      expect(dt[2]).toContain('---');
      expect(dt[2]).toContain('Test Title');
    });

    test('adds header with custom decoration', () => {
      const dt = [];
      renderEndingHeader(dt, 'Custom', '=== ★');
      expect(dt[2]).toContain('=== ★');
      expect(dt[2]).toContain('Custom');
    });
  });
});

// ---------------------------------------------------------------------------
// randomOutcome テスト
// ---------------------------------------------------------------------------
describe('randomOutcome', () => {
  test('returns RESULT_WIN and adds item when Math.random() < 0.5', () => {
    const mockMath = Object.create(global.Math);
    mockMath.random = () => 0.25;
    global.Math = mockMath;

    const dt = [];
    const inv = [];
    const result = randomOutcome(dt, 'win msg', 'lose msg', inv, ITEMS.JEWEL);
    expect(result).toBe(RESULTS.WIN);
    expect(inv).toContain(ITEMS.JEWEL);
    expect(dt.some(l => l.includes('勝利'))).toBe(true);
    expect(dt.some(l => l.includes('win msg'))).toBe(true);
  });

  test('returns RESULT_LOSE and does not add item when Math.random() >= 0.5', () => {
    const mockMath = Object.create(global.Math);
    mockMath.random = () => 0.75;
    global.Math = mockMath;

    const dt = [];
    const inv = [];
    const result = randomOutcome(dt, 'win msg', 'lose msg', inv, ITEMS.JEWEL);
    expect(result).toBe(RESULTS.LOSE);
    expect(inv).not.toContain(ITEMS.JEWEL);
    expect(dt.some(l => l.includes('敗北'))).toBe(true);
    expect(dt.some(l => l.includes('lose msg'))).toBe(true);
  });

  test('does not add item when itemOnWin is null on win', () => {
    const mockMath = Object.create(global.Math);
    mockMath.random = () => 0.1;
    global.Math = mockMath;

    const dt = [];
    const inv = [];
    const result = randomOutcome(dt, 'win', 'lose', inv, null);
    expect(result).toBe(RESULTS.WIN);
    expect(inv).toEqual([]);
  });
});

// ---------------------------------------------------------------------------
// パス関数テスト
// ---------------------------------------------------------------------------
describe('Path functions', () => {
  beforeEach(() => {
    const mockMath = Object.create(global.Math);
    mockMath.random = () => 0.5; // lose threshold
    global.Math = mockMath;
  });

  describe('leftPath', () => {
    test('returns RESULT_LOSE when random >= 0.5', () => {
      const state = createInitialState();
      const result = leftPath(state);
      expect(result).toBe(RESULTS.LOSE);
      expect(state.outcome).toBe(RESULTS.LOSE);
      expect(state.gameOver).toBe(true);
      expect(state.displayText.length).toBeGreaterThan(0);
    });

    test('adds display text about the river', () => {
      const state = createInitialState();
      leftPath(state);
      const text = state.displayText.join(' ');
      expect(text).toContain('左の道');
      expect(text).toContain('川');
    });

    test('includes donation message', () => {
      const state = createInitialState();
      leftPath(state);
      const text = state.displayText.join(' ');
      expect(text).toContain(DONATION_URL);
    });
  });

  describe('rightPath', () => {
    test('returns RESULT_LOSE when random >= 0.5', () => {
      const state = createInitialState();
      const result = rightPath(state);
      expect(result).toBe(RESULTS.LOSE);
      expect(state.outcome).toBe(RESULTS.LOSE);
      expect(state.gameOver).toBe(true);
    });

    test('adds display text about ruins', () => {
      const state = createInitialState();
      rightPath(state);
      const text = state.displayText.join(' ');
      expect(text).toContain('右の道');
      expect(text).toContain('遺跡');
    });
  });
});

// ---------------------------------------------------------------------------
// エンディングテスト
// ---------------------------------------------------------------------------
describe('Endings', () => {
  describe('neutralEnding', () => {
    test('returns RESULT_NEUTRAL and sets state', () => {
      const state = createInitialState();
      const result = neutralEnding(state);
      expect(result).toBe(RESULTS.NEUTRAL);
      expect(state.outcome).toBe(RESULTS.NEUTRAL);
      expect(state.gameOver).toBe(true);
    });

    test('adds ending header and story text', () => {
      const state = createInitialState();
      neutralEnding(state);
      const text = state.displayText.join(' ');
      expect(text).toContain('中立エンディング');
      expect(text).toContain('帰還');
      expect(text).toContain('村に戻り');
    });
  });

  describe('hiddenEnding', () => {
    test('returns RESULT_HIDDEN and sets state', () => {
      const state = createInitialState();
      const result = hiddenEnding(state);
      expect(result).toBe(RESULTS.HIDDEN);
      expect(state.outcome).toBe(RESULTS.HIDDEN);
      expect(state.gameOver).toBe(true);
    });

    test('adds hidden ending story text', () => {
      const state = createInitialState();
      hiddenEnding(state);
      const text = state.displayText.join(' ');
      expect(text).toContain('真の英雄');
      expect(text).toContain('財宝');
      expect(text).toContain('守護者の魂');
    });
  });
});

// ---------------------------------------------------------------------------
// 探索と隠しパステスト
// ---------------------------------------------------------------------------
describe('Search and hidden path', () => {
  describe('searchArea', () => {
    test('adds key and map to inventory and sets searched flag', () => {
      const state = createInitialState();
      searchArea(state);
      expect(state.inventory).toContain(ITEMS.KEY);
      expect(state.inventory).toContain(ITEMS.MAP);
      expect(state.searched).toBe(true);
    });

    test('adds display text about finding items', () => {
      const state = createInitialState();
      searchArea(state);
      const text = state.displayText.join(' ');
      expect(text).toContain('探索');
      expect(text).toContain('鍵');
      expect(text).toContain('地図');
    });

    test('does not remove existing items', () => {
      const state = createInitialState();
      state.inventory.push(ITEMS.JEWEL);
      searchArea(state);
      expect(state.inventory).toContain(ITEMS.JEWEL);
      expect(state.inventory).toContain(ITEMS.KEY);
      expect(state.inventory).toContain(ITEMS.MAP);
    });
  });

  describe('checkHiddenPath', () => {
    test('returns false when player does not have key and map', () => {
      const state = createInitialState();
      expect(checkHiddenPath(state)).toBe(false);
      expect(state.gameOver).toBe(false);
    });

    test('returns false when player has items but enterCave is false', () => {
      const state = createInitialState();
      state.inventory.push(ITEMS.KEY, ITEMS.MAP);
      const result = checkHiddenPath(state, false);
      expect(result).toBe(false);
      expect(state.displayText.some(l => l.includes('またの機会'))).toBe(true);
    });

    test('returns true and plays hidden ending when conditions met', () => {
      const state = createInitialState();
      state.inventory.push(ITEMS.KEY, ITEMS.MAP);
      const result = checkHiddenPath(state, true);
      expect(result).toBe(true);
      expect(state.hiddenPlayed).toBe(true);
      expect(state.gameOver).toBe(true);
      expect(state.outcome).toBe(RESULTS.HIDDEN);
    });

    test('adds cave discovery text when conditions met', () => {
      const state = createInitialState();
      state.inventory.push(ITEMS.KEY, ITEMS.MAP);
      checkHiddenPath(state, true);
      const text = state.displayText.join(' ');
      expect(text).toContain('洞窟');
    });
  });
});

// ---------------------------------------------------------------------------
// 選択肢テスト
// ---------------------------------------------------------------------------
describe('Choices', () => {
  describe('getChoices', () => {
    test('returns 4 choices when not searched', () => {
      const state = createInitialState();
      const choices = getChoices(state);
      expect(choices).toHaveLength(4);
      expect(choices[3].value).toBe(CHOICES.SEARCH);
      expect(choices[3].label).toContain('探索');
    });

    test('returns 3 choices when already searched', () => {
      const state = createInitialState();
      state.searched = true;
      const choices = getChoices(state);
      expect(choices).toHaveLength(3);
      expect(choices.find(c => c.value === CHOICES.SEARCH)).toBeUndefined();
    });

    test('choices have correct labels', () => {
      const state = createInitialState();
      const choices = getChoices(state);
      expect(choices.find(c => c.value === CHOICES.LEFT).label).toContain('左');
      expect(choices.find(c => c.value === CHOICES.RIGHT).label).toContain('右');
      expect(choices.find(c => c.value === CHOICES.GIVE_UP).label).toContain('帰る');
    });
  });
});

// ---------------------------------------------------------------------------
// handleChoice テスト — ゲームループの中核
// ---------------------------------------------------------------------------
describe('handleChoice — core game loop', () => {
  beforeEach(() => {
    const mockMath = Object.create(global.Math);
    mockMath.random = () => 0.5;
    global.Math = mockMath;
  });

  test('LEFT path without items: calls leftPath', () => {
    const state = createInitialState();
    const result = handleChoice(state, CHOICES.LEFT);
    expect(result).toBe(false);
    expect(state.gameOver).toBe(true);
    expect(state.outcome).toBe(RESULTS.LOSE);
  });

  test('RIGHT path without items: calls rightPath', () => {
    const state = createInitialState();
    const result = handleChoice(state, CHOICES.RIGHT);
    expect(result).toBe(false);
    expect(state.gameOver).toBe(true);
    expect(state.outcome).toBe(RESULTS.LOSE);
  });

  test('GIVE_UP leads to neutral ending', () => {
    const state = createInitialState();
    const result = handleChoice(state, CHOICES.GIVE_UP);
    expect(result).toBe(false);
    expect(state.outcome).toBe(RESULTS.NEUTRAL);
    expect(state.gameOver).toBe(true);
  });

  test('SEARCH before searched: triggers searchArea and continues', () => {
    const state = createInitialState();
    const result = handleChoice(state, CHOICES.SEARCH);
    expect(result).toBe(true);
    expect(state.searched).toBe(true);
    expect(state.inventory).toContain(ITEMS.KEY);
    expect(state.inventory).toContain(ITEMS.MAP);
    expect(state.gameOver).toBe(false);
  });

  test('SEARCH after searched: shows invalid choice message', () => {
    const state = createInitialState();
    state.searched = true;
    const result = handleChoice(state, CHOICES.SEARCH);
    expect(result).toBe(true);
    expect(state.displayText.some(l => l.includes('無効'))).toBe(true);
  });

  test('invalid choice shows error and continues game', () => {
    const state = createInitialState();
    const result = handleChoice(state, '99');
    expect(result).toBe(true);
    expect(state.gameOver).toBe(false);
    expect(state.displayText.some(l => l.includes('無効'))).toBe(true);
  });

  test('LEFT path with hidden items: triggers hidden ending', () => {
    const state = createInitialState();
    state.inventory.push(ITEMS.KEY, ITEMS.MAP);
    const result = handleChoice(state, CHOICES.LEFT, true);
    expect(result).toBe(false);
    expect(state.outcome).toBe(RESULTS.HIDDEN);
    expect(state.hiddenPlayed).toBe(true);
  });

  test('RIGHT path with hidden items: triggers hidden ending', () => {
    const state = createInitialState();
    state.inventory.push(ITEMS.KEY, ITEMS.MAP);
    const result = handleChoice(state, CHOICES.RIGHT, true);
    expect(result).toBe(false);
    expect(state.outcome).toBe(RESULTS.HIDDEN);
  });

  test('LEFT path with hidden items but declined cave: falls through to leftPath', () => {
    const state = createInitialState();
    state.inventory.push(ITEMS.KEY, ITEMS.MAP);
    const result = handleChoice(state, CHOICES.LEFT, false);
    expect(result).toBe(false);
    expect(state.outcome).toBe(RESULTS.LOSE);
    expect(state.hiddenPlayed).toBe(false);
  });

  test('handleChoice returns false when game is already over', () => {
    const state = createInitialState();
    state.gameOver = true;
    const result = handleChoice(state, CHOICES.LEFT);
    expect(result).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// ゲームフローインテグレーションテスト
// ---------------------------------------------------------------------------
describe('Game flow integration', () => {
  beforeEach(() => {
    // Deterministic: first call < 0.5 (win), rest >= 0.5 (lose)
    let callCount = 0;
    const mockMath = Object.create(global.Math);
    mockMath.random = () => {
      callCount++;
      return callCount === 1 ? 0.25 : 0.75;
    };
    global.Math = mockMath;
  });

  test('full flow: LEFT → leftPath with win outcome', () => {
    const state = createInitialState();
    handleChoice(state, CHOICES.LEFT);
    expect(state.gameOver).toBe(true);
    // first randomOutcome call (leftPath) uses callCount=1 -> 0.25 -> WIN
    expect(state.outcome).toBe(RESULTS.WIN);
    expect(state.inventory).toContain(ITEMS.JEWEL);
  });

  test('full flow: RIGHT → rightPath with win outcome', () => {
    // Need Math.random() < 0.5 for rightPath
    const mockMath = Object.create(global.Math);
    mockMath.random = () => 0.25;
    global.Math = mockMath;

    const state = createInitialState();
    handleChoice(state, CHOICES.RIGHT);
    expect(state.gameOver).toBe(true);
    expect(state.outcome).toBe(RESULTS.WIN);
  });

  test('full flow: SEARCH → LEFT (no cave) → leftPath', () => {
    // leftPath will lose (random >= 0.5 with our default)
    const mockMath = Object.create(global.Math);
    mockMath.random = () => 0.75;
    global.Math = mockMath;

    const state = createInitialState();
    handleChoice(state, CHOICES.SEARCH);
    expect(state.searched).toBe(true);
    handleChoice(state, CHOICES.LEFT, false);
    expect(state.gameOver).toBe(true);
    expect(state.outcome).toBe(RESULTS.LOSE);
    expect(state.inventory).toContain(ITEMS.KEY);
    expect(state.inventory).toContain(ITEMS.MAP);
  });

  test('full flow: SEARCH → LEFT → hidden ending', () => {
    const state = createInitialState();
    handleChoice(state, CHOICES.SEARCH);
    handleChoice(state, CHOICES.LEFT, true);
    expect(state.outcome).toBe(RESULTS.HIDDEN);
    expect(state.hiddenPlayed).toBe(true);
  });

  test('GIVE_UP → neutral ending with donation message', () => {
    const state = createInitialState();
    handleChoice(state, CHOICES.GIVE_UP);
    expect(state.outcome).toBe(RESULTS.NEUTRAL);
    expect(state.gameOver).toBe(true);
    const text = state.displayText.join(' ');
    expect(text).toContain(DONATION_URL);
  });
});

// ---------------------------------------------------------------------------
// エッジケーステスト
// ---------------------------------------------------------------------------
describe('Edge cases', () => {
  test('search then search again (already searched) shows invalid', () => {
    const state = createInitialState();
    handleChoice(state, CHOICES.SEARCH);
    handleChoice(state, CHOICES.SEARCH);
    const searchCount = state.displayText.filter(l => l.includes('無効')).length;
    expect(searchCount).toBe(1);
  });

  test('invalid choice for searched state shows correct range', () => {
    const state = createInitialState();
    state.searched = true;
    handleChoice(state, '99');
    expect(state.displayText.some(l => l.includes('1-3'))).toBe(true);
  });

  test('invalid choice for unsearched state shows correct range', () => {
    const state = createInitialState();
    handleChoice(state, '99');
    expect(state.displayText.some(l => l.includes('1-4'))).toBe(true);
  });
});

// ---------------------------------------------------------------------------
// 実績システムテスト
// ---------------------------------------------------------------------------
describe('Achievement System — checkAchievements', () => {
  const makeEmpty = () => ({
    endingsUnlocked: [],
    totalPlayCount: 0,
    achievements: {},
    consecutiveWins: 0,
    collectedItems: [],
    version: 1,
  });

  test('ACHIEVEMENT_IDS constant values', () => {
    expect(ACHIEVEMENT_IDS.FIRST_STEP).toBe('first_step');
    expect(ACHIEVEMENT_IDS.LEFT_PATH).toBe('left_path');
    expect(ACHIEVEMENT_IDS.RIGHT_PATH).toBe('right_path');
    expect(ACHIEVEMENT_IDS.VICTORY).toBe('victory');
    expect(ACHIEVEMENT_IDS.DEFEAT).toBe('defeat');
    expect(ACHIEVEMENT_IDS.RETURN_HOME).toBe('return_home');
    expect(ACHIEVEMENT_IDS.TRUE_HERO).toBe('true_hero');
    expect(ACHIEVEMENT_IDS.COLLECTOR).toBe('collector');
    expect(ACHIEVEMENT_IDS.EXPLORER).toBe('explorer');
    expect(ACHIEVEMENT_IDS.VETERAN).toBe('veteran');
    expect(ACHIEVEMENT_IDS.LUCKY).toBe('lucky');
    expect(ACHIEVEMENT_IDS.COMPLETIONIST).toBe('completionist');
  });

  test('ACHIEVEMENT_DEFS length and fields', () => {
    expect(ACHIEVEMENT_DEFS).toHaveLength(12);
    ACHIEVEMENT_DEFS.forEach(def => {
      expect(def).toHaveProperty('id');
      expect(def).toHaveProperty('name');
      expect(def).toHaveProperty('category');
      expect(def).toHaveProperty('secret');
      expect(def).toHaveProperty('difficulty');
    });
  });

  test('#1 first_step on GAME_START (first time)', () => {
    const data = makeEmpty();
    const result = checkAchievements(EVENTS.GAME_START, {}, data);
    expect(result).toContain(ACHIEVEMENT_IDS.FIRST_STEP);
    expect(data.consecutiveWins).toBe(0);
  });

  test('#1 first_step not re-unlocked when already owned', () => {
    const data = makeEmpty();
    data.achievements.first_step = true;
    const result = checkAchievements(EVENTS.GAME_START, {}, data);
    expect(result).not.toContain(ACHIEVEMENT_IDS.FIRST_STEP);
  });

  test('#10 veteran not unlocked at 9 plays', () => {
    const data = makeEmpty();
    data.totalPlayCount = 8; // +1 in event → 9
    const result = checkAchievements(EVENTS.GAME_START, {}, data);
    expect(result).not.toContain(ACHIEVEMENT_IDS.VETERAN);
  });

  test('#10 veteran unlocked at 10 plays', () => {
    const data = makeEmpty();
    data.totalPlayCount = 9; // +1 in event → 10
    const result = checkAchievements(EVENTS.GAME_START, {}, data);
    expect(result).toContain(ACHIEVEMENT_IDS.VETERAN);
  });

  test('#2 left_path on CHOICE_MADE left', () => {
    const data = makeEmpty();
    const result = checkAchievements(EVENTS.CHOICE_MADE, { choice: '1' }, data);
    expect(result).toContain(ACHIEVEMENT_IDS.LEFT_PATH);
  });

  test('#3 right_path on CHOICE_MADE right', () => {
    const data = makeEmpty();
    const result = checkAchievements(EVENTS.CHOICE_MADE, { choice: '2' }, data);
    expect(result).toContain(ACHIEVEMENT_IDS.RIGHT_PATH);
  });

  test('#4 victory on ENDING_REACHED win', () => {
    const data = makeEmpty();
    const result = checkAchievements(EVENTS.ENDING_REACHED, { outcome: 'win' }, data);
    expect(result).toContain(ACHIEVEMENT_IDS.VICTORY);
  });

  test('#5 defeat on ENDING_REACHED lose', () => {
    const data = makeEmpty();
    const result = checkAchievements(EVENTS.ENDING_REACHED, { outcome: 'lose' }, data);
    expect(result).toContain(ACHIEVEMENT_IDS.DEFEAT);
  });

  test('#6 return_home on ENDING_REACHED neutral', () => {
    const data = makeEmpty();
    const result = checkAchievements(EVENTS.ENDING_REACHED, { outcome: 'neutral' }, data);
    expect(result).toContain(ACHIEVEMENT_IDS.RETURN_HOME);
  });

  test('#7 true_hero on ENDING_REACHED hidden', () => {
    const data = makeEmpty();
    const result = checkAchievements(EVENTS.ENDING_REACHED, { outcome: 'hidden' }, data);
    expect(result).toContain(ACHIEVEMENT_IDS.TRUE_HERO);
  });

  test('#11 lucky unlocked on 3 consecutive wins', () => {
    const data = makeEmpty();
    // win #1
    checkAchievements(EVENTS.ENDING_REACHED, { outcome: 'win' }, data);
    expect(data.consecutiveWins).toBe(1);
    // win #2
    checkAchievements(EVENTS.ENDING_REACHED, { outcome: 'win' }, data);
    expect(data.consecutiveWins).toBe(2);
    // win #3 — should trigger lucky
    const result = checkAchievements(EVENTS.ENDING_REACHED, { outcome: 'win' }, data);
    expect(result).toContain(ACHIEVEMENT_IDS.LUCKY);
    expect(data.consecutiveWins).toBe(3);
  });

  test('#11 lucky not unlocked on 2 consecutive wins', () => {
    const data = makeEmpty();
    checkAchievements(EVENTS.ENDING_REACHED, { outcome: 'win' }, data);
    checkAchievements(EVENTS.ENDING_REACHED, { outcome: 'win' }, data);
    const result = checkAchievements(EVENTS.ENDING_REACHED, { outcome: 'lose' }, data);
    expect(result).not.toContain(ACHIEVEMENT_IDS.LUCKY);
  });

  test('#8 collector on collecting all 3 items', () => {
    const data = makeEmpty();
    checkAchievements(EVENTS.ITEM_FOUND, { itemName: 'Shining Jewel' }, data);
    let result = checkAchievements(EVENTS.ITEM_FOUND, { itemName: 'Rusty Key' }, data);
    expect(result).not.toContain(ACHIEVEMENT_IDS.COLLECTOR);
    result = checkAchievements(EVENTS.ITEM_FOUND, { itemName: 'Old Map' }, data);
    expect(result).toContain(ACHIEVEMENT_IDS.COLLECTOR);
  });

  test('#9 explorer on 6 endings unlocked', () => {
    const data = makeEmpty();
    data.endingsUnlocked = ['win', 'lose', 'neutral', 'hidden', 'extra1', 'extra2'];
    const result = checkAchievements(EVENTS.ENDING_REACHED, { outcome: 'win' }, data);
    expect(result).toContain(ACHIEVEMENT_IDS.EXPLORER);
  });

  test('#12 completionist not triggered when no new unlock', () => {
    const data = makeEmpty();
    data.achievements = {
      first_step: true,
      left_path: true,
      right_path: true,
      victory: true,
      defeat: true,
      return_home: true,
      true_hero: true,
      collector: true,
      explorer: true,
      veteran: true,
      lucky: true,
    };
    // All done except completionist; GAME_START has no new unlock (first_step already true)
    const result = checkAchievements(EVENTS.GAME_START, {}, data);
    expect(result).not.toContain(ACHIEVEMENT_IDS.COMPLETIONIST);
  });

  test('#12 completionist triggers on new unlock when rest are done', () => {
    const data = makeEmpty();
    data.achievements = {
      left_path: true,
      right_path: true,
      victory: true,
      defeat: true,
      return_home: true,
      true_hero: true,
      collector: true,
      explorer: true,
      veteran: true,
      lucky: true,
    };
    // first_step is false → GAME_START will unlock it → check completionist
    const result = checkAchievements(EVENTS.GAME_START, {}, data);
    expect(result).toContain(ACHIEVEMENT_IDS.FIRST_STEP);
    expect(result).toContain(ACHIEVEMENT_IDS.COMPLETIONIST);
  });

  test('no duplicate unlock for already unlocked achievements', () => {
    const data = makeEmpty();
    data.achievements.first_step = true;
    const result = checkAchievements(EVENTS.GAME_START, {}, data);
    expect(result).not.toContain(ACHIEVEMENT_IDS.FIRST_STEP);
  });

  test('no unlock for unrelated event', () => {
    const data = makeEmpty();
    const result = checkAchievements('UNKNOWN_EVENT', {}, data);
    expect(result).toEqual([]);
  });
});