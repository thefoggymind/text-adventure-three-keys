#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Text-based adventure game with 6 endings.

=== Ending List ===
1. Left path - Win     : 清らかな川で回復、宝石を入手
2. Left path - Lose    : 毒の川で倒れる
3. Right path - Win    : 古代の宝具で富と名声
4. Right path - Lose   : 呪いで石になる
5. Neutral ending      : 冒険をあきらめて帰還
6. Hidden ending       : 鍵と地図で真の英雄（条件付き）
"""

import random
from typing import List


# --- 定数 ---
# 選択肢
CHOICE_LEFT = "1"
CHOICE_RIGHT = "2"
CHOICE_GIVE_UP = "3"
CHOICE_SEARCH = "4"

# 結果
RESULT_WIN = "win"
RESULT_LOSE = "lose"
RESULT_NEUTRAL = "neutral"
RESULT_HIDDEN = "hidden"

# アイテム
ITEM_JEWEL = "Shining Jewel"
ITEM_KEY = "Rusty Key"
ITEM_MAP = "Old Map"

DONATION_URL = "https://ko-fi.com/thefoggymind"


# --- ユーティリティ関数 ---

def show_donation_message() -> None:
    """寄付のお願いメッセージを表示する。"""
    print("\n" + "=" * 60)
    print(f"  このゲームを気に入ったら寄付で支援してください：{DONATION_URL}")
    print("=" * 60 + "\n")


def show_ending_header(title: str, decoration: str = "---") -> None:
    """エンディングタイトルを装飾付きで表示する。"""
    print("\n" + "=" * 60)
    print(f"  {decoration} {title} {decoration}")
    print("=" * 60)


# --- 道中の分岐処理 ---

def _random_outcome(
    msg_win: str,
    msg_lose: str,
    inventory: List[str],
    item_on_win: str | None = None,
) -> str:
    """50%確率で勝敗を決め、結果に応じたメッセージを表示する。

    Args:
        msg_win: 勝利時のメッセージ。
        msg_lose: 敗北時のメッセージ。
        inventory: プレイヤーのインベントリ（勝利時アイテム追加に使用）。
        item_on_win: 勝利時にインベントリへ追加するアイテム名（任意）。

    Returns:
        RESULT_WIN または RESULT_LOSE。
    """
    if random.random() < 0.5:
        print("\n--- 勝利！ ---")
        print(msg_win)
        if item_on_win:
            inventory.append(item_on_win)
        return RESULT_WIN
    else:
        print("\n--- 敗北 ---")
        print(msg_lose)
        return RESULT_LOSE


def left_path(inventory: List[str]) -> str:
    """左の道：川で休息、勝敗でアイテム獲得または毒で敗北。"""
    print("\nあなたは左の道を進み、きらめく川を見つけました。")
    print("川のほとりで休憩し、水を飲むことにしました。")

    result = _random_outcome(
        "川の水は清らかで、エネルギーを完全に回復しました。\n"
        "あなたは無事に森を抜け出すことができました。\n"
        "さらに、川岸で輝く宝石を手に入れました！",
        "川の水は毒されており、あなたは体調を崩してしまいました。\n"
        "森の中で倒れてしまいました…。",
        inventory,
        item_on_win=ITEM_JEWEL,
    )
    show_donation_message()
    return result


def right_path(inventory: List[str]) -> str:
    """右の道：遺跡で発見、勝敗で宝具獲得または呪いで敗北。"""
    print("\nあなたは右の道を進み、古い遺跡を発見しました。")
    print("遺跡の中から不思議な遺物を見つけました。")

    result = _random_outcome(
        "その遺物は古代の宝具であり、あなたは富と名声を得ました。",
        "遺物には呪いがかかっており、あなたは石になってしまいました。",
        inventory,
    )
    show_donation_message()
    return result


# --- エンディング ---

def neutral_ending() -> str:
    """中立エンディング「帰還」：冒険をあきらめて日常に戻る。"""
    show_ending_header("中立エンディング：帰還")
    print("\n「やっぱり危険すぎる…」")
    print("あなたは来た道を引き返すことにしました。")
    print("森の入り口で出会った村人が言いました。「賢明な選択だ。」")
    print("村に戻り、あなたは静かで平和な日常に戻りました。")
    print("冒険の記憶は、いつか誰かに語る小さな思い出話になるでしょう。")
    print("\n（危険を避けるのも勇気の一つ…平穏な日常を手に入れました。）")

    show_donation_message()
    return RESULT_NEUTRAL


def hidden_ending() -> str:
    """隠しエンディング「真の英雄」：鍵と地図を持ち、隠し洞窟で財宝を獲得。

    条件: Rusty Key と Old Map の両方がインベントリにある状態で
    左／右の道を選び、洞窟探索に「y」で応える。
    """
    show_ending_header("★ 隠しエンディング：真の英雄", decoration="--- ★")
    print("\nあなたは錆びた鍵と古い地図を手に、隠された洞窟の入り口を発見した。")
    print("洞窟の奥には、古代の王が眠る宝物庫があった。")
    print("そこに立つ守護者の魂が語りかける…")
    print("「よく来たな、勇者よ。その鍵と地図は、真に価する者にのみ与えられる。」")
    print("「お前は運命を切り開く力を示した。この先にある全てを授けよう。」")
    print("\nあなたは伝説の財宝を手に入れ、王国中から称賛される英雄となった。")
    print("その名は永遠に語り継がれるだろう。")
    print("\n（全ての謎を解き明かした者だけが到達できる、真のエンディング！）")

    show_donation_message()
    return RESULT_HIDDEN


# --- 探索と隠しパス ---

def search_area(inventory: List[str]) -> None:
    """周辺を探索し、隠しエンディングに必要なアイテムを入手する。"""
    print("\nあなたは周辺を注意深く探索し始めた。")
    print("茂みの陰で何かが光っている…。")
    print("それは「錆びた鍵」と「古い地図」でした！")
    inventory.append(ITEM_KEY)
    inventory.append(ITEM_MAP)
    print("（アイテムを手に入れた：錆びた鍵、古い地図）")


def check_hidden_path(inventory: List[str]) -> bool:
    """隠しパス条件確認：アイテム所持時に入力確認し、隠しEDへ遷移。

    Returns:
        隠しエンディングをプレイした場合は True、それ以外は False。
    """
    if ITEM_KEY in inventory and ITEM_MAP in inventory:
        print("\n★ 錆びた鍵と古い地図を持っている…隠された洞窟の入り口を見つけました！")
        ans = input("洞窟の中を探索しますか？ (y/n): ").strip().lower()
        if ans == "y":
            hidden_ending()
            return True
        print("（またの機会にすることにした…）")
    return False


# --- メニュー ---

def show_menu(searched: bool) -> str:
    """メインメニューを表示し、プレイヤーの選択を受け付ける。"""
    print("\n何をしますか？")
    print("1. 左の道を進む")
    print("2. 右の道を進む")
    print("3. 冒険をあきらめて帰る")
    if not searched:
        print("4. 周辺を探索する")

    prompt = (
        "選択肢を入力してください (1-3): "
        if searched
        else "選択肢を入力してください (1-4): "
    )
    return input(prompt).strip()


# --- メインエントリーポイント ---

def main() -> None:
    """ゲームのメインループ。"""
    print("テキストベースアドベンチャーゲームへようこそ！")
    print("あなたは森の中で目覚めました。前には二つの道があります。")

    inventory: List[str] = []
    searched = False

    while True:
        choice = show_menu(searched)

        if choice == CHOICE_LEFT:
            if not check_hidden_path(inventory):
                left_path(inventory)
            break
        elif choice == CHOICE_RIGHT:
            if not check_hidden_path(inventory):
                right_path(inventory)
            break
        elif choice == CHOICE_GIVE_UP:
            neutral_ending()
            break
        elif choice == CHOICE_SEARCH and not searched:
            search_area(inventory)
            searched = True
        else:
            valid_range = "1-3" if searched else "1-4"
            print(f"\n無効な選択肢です。{valid_range}の範囲で入力してください。")


if __name__ == "__main__":
    main()
