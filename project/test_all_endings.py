#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test script for game.py — validates all 6 endings.
Run: python -m project.test_all_endings
"""

import sys
import os
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from project.game import (
    left_path,
    right_path,
    neutral_ending,
    hidden_ending,
    search_area,
    check_hidden_path,
    show_menu,
    RESULT_WIN,
    RESULT_LOSE,
    RESULT_NEUTRAL,
    RESULT_HIDDEN,
    ITEM_KEY,
    ITEM_MAP,
)


def test_left_path_win():
    """左の道・勝利"""
    inv = []
    with patch("project.game.random.random", return_value=0.3):
        result = left_path(inv)
    assert result == RESULT_WIN, f"Expected {RESULT_WIN}, got {result}"
    assert "Shining Jewel" in inv, "Jewel should be in inventory on win"
    print("[PASS] left_path_win")


def test_left_path_lose():
    """左の道・敗北"""
    inv = []
    with patch("project.game.random.random", return_value=0.7):
        result = left_path(inv)
    assert result == RESULT_LOSE, f"Expected {RESULT_LOSE}, got {result}"
    assert "Shining Jewel" not in inv, "Jewel should NOT be in inventory on lose"
    print("[PASS] left_path_lose")


def test_right_path_win():
    """右の道・勝利"""
    inv = []
    with patch("project.game.random.random", return_value=0.3):
        result = right_path(inv)
    assert result == RESULT_WIN, f"Expected {RESULT_WIN}, got {result}"
    print("[PASS] right_path_win")


def test_right_path_lose():
    """右の道・敗北"""
    inv = []
    with patch("project.game.random.random", return_value=0.7):
        result = right_path(inv)
    assert result == RESULT_LOSE, f"Expected {RESULT_LOSE}, got {result}"
    print("[PASS] right_path_lose")


def test_neutral_ending():
    """中立エンディング"""
    result = neutral_ending()
    assert result == RESULT_NEUTRAL, f"Expected {RESULT_NEUTRAL}, got {result}"
    print("[PASS] neutral_ending")


def test_hidden_ending():
    """隠しエンディング"""
    result = hidden_ending()
    assert result == RESULT_HIDDEN, f"Expected {RESULT_HIDDEN}, got {result}"
    print("[PASS] hidden_ending")


def test_search_area():
    """探索でアイテム入手"""
    inv = []
    search_area(inv)
    assert ITEM_KEY in inv, "Key should be added"
    assert ITEM_MAP in inv, "Map should be added"
    print("[PASS] search_area")


def test_check_hidden_path_yes():
    """隠しパス：アイテムあり、y を選ぶ → hidden_ending 遷移"""
    inv = [ITEM_KEY, ITEM_MAP]
    with patch("builtins.input", return_value="y"):
        result = check_hidden_path(inv)
    assert result is True, "Should return True when entering hidden ending"
    print("[PASS] check_hidden_path_yes")


def test_check_hidden_path_no():
    """隠しパス：アイテムあり、n を選ぶ → False"""
    inv = [ITEM_KEY, ITEM_MAP]
    with patch("builtins.input", return_value="n"):
        result = check_hidden_path(inv)
    assert result is False, "Should return False when declining"
    print("[PASS] check_hidden_path_no")


def test_check_hidden_path_no_items():
    """隠しパス：アイテムなし → 何も起こらない"""
    inv = []
    result = check_hidden_path(inv)
    assert result is False, "Should return False when no items"
    print("[PASS] check_hidden_path_no_items")


def test_show_menu():
    """メニュー表示と選択肢受付"""
    with patch("builtins.input", return_value="1"):
        choice = show_menu(searched=False)
    assert choice == "1", "Menu should return user choice"
    print("[PASS] show_menu")


# --- 統合テスト: メインフロー（全6 endingを人力シミュレーション） ---

def test_main_neutral():
    """メインルーチン：中立（選択肢3）"""
    from project.game import main
    with patch("builtins.input", side_effect=["3"]):
        try:
            main()
        except SystemExit:
            pass
    print("[PASS] main_neutral")


def test_main_left_win():
    """メインルーチン：左win"""
    from project.game import main
    with (
        patch("builtins.input", side_effect=["1"]),
        patch("project.game.random.random", return_value=0.3),
    ):
        try:
            main()
        except SystemExit:
            pass
    print("[PASS] main_left_win")


def test_main_left_lose():
    """メインルーチン：左lose"""
    from project.game import main
    with (
        patch("builtins.input", side_effect=["1"]),
        patch("project.game.random.random", return_value=0.7),
    ):
        try:
            main()
        except SystemExit:
            pass
    print("[PASS] main_left_lose")


def test_main_right_win():
    """メインルーチン：右win"""
    from project.game import main
    with (
        patch("builtins.input", side_effect=["2"]),
        patch("project.game.random.random", return_value=0.3),
    ):
        try:
            main()
        except SystemExit:
            pass
    print("[PASS] main_right_win")


def test_main_right_lose():
    """メインルーチン：右lose"""
    from project.game import main
    with (
        patch("builtins.input", side_effect=["2"]),
        patch("project.game.random.random", return_value=0.7),
    ):
        try:
            main()
        except SystemExit:
            pass
    print("[PASS] main_right_lose")


def test_main_hidden():
    """メインルーチン：探索→左→隠し"""
    from project.game import main
    with (
        patch("builtins.input", side_effect=["4", "1", "y"]),
        patch("project.game.random.random", return_value=0.3),
    ):
        try:
            main()
        except SystemExit:
            pass
    print("[PASS] main_hidden")


def test_main_hidden_right():
    """メインルーチン：探索→右→隠し"""
    from project.game import main
    with (
        patch("builtins.input", side_effect=["4", "2", "y"]),
        patch("project.game.random.random", return_value=0.3),
    ):
        try:
            main()
        except SystemExit:
            pass
    print("[PASS] main_hidden_right")


def test_main_invalid_then_valid():
    """無効な選択肢 → 再入力で正しい選択肢"""
    from project.game import main
    with (
        patch("builtins.input", side_effect=["5", "3"]),
    ):
        try:
            main()
        except SystemExit:
            pass
    print("[PASS] main_invalid_then_valid")


if __name__ == "__main__":
    tests = [
        ("left_path_win", test_left_path_win),
        ("left_path_lose", test_left_path_lose),
        ("right_path_win", test_right_path_win),
        ("right_path_lose", test_right_path_lose),
        ("neutral_ending", test_neutral_ending),
        ("hidden_ending", test_hidden_ending),
        ("search_area", test_search_area),
        ("check_hidden_path_yes", test_check_hidden_path_yes),
        ("check_hidden_path_no", test_check_hidden_path_no),
        ("check_hidden_path_no_items", test_check_hidden_path_no_items),
        ("show_menu", test_show_menu),
        ("main_neutral", test_main_neutral),
        ("main_left_win", test_main_left_win),
        ("main_left_lose", test_main_left_lose),
        ("main_right_win", test_main_right_win),
        ("main_right_lose", test_main_right_lose),
        ("main_hidden", test_main_hidden),
        ("main_hidden_right", test_main_hidden_right),
        ("main_invalid_then_valid", test_main_invalid_then_valid),
    ]

    failed = 0
    for name, fn in tests:
        try:
            fn()
        except Exception as e:
            print(f"[FAIL] {name}: {e}")
            failed += 1

    print(f"\n{'=' * 40}")
    print(f"Results: {len(tests) - failed}/{len(tests)} passed")
    if failed:
        print(f"Failures: {failed}")
        sys.exit(1)
    else:
        print("All tests passed!")