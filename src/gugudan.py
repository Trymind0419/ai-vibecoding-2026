"""êµ¬êµ¬???„ë¡œê·¸ë¨ (ìµœì ??ë²„ì „)
- 2??~ 9??ê°€ë¡??Œì´ë¸??¤ë‹¨) ê¹”ë”???„ì²´ ì¶œë ¥
- ?¹ì • ???…ë ¥ ë°?ì¦‰ì‹œ ê³„ì‚° ì¶œë ¥
- ê²¬ê³ ???…ë ¥ ê²€ì¦?ë°??¨ì¶• ì¢…ë£Œ(q) ì§€??"""

import sys


def print_gugudan_all(cols_per_row: int = 4) -> None:
    """2?¨ë???9?¨ê¹Œì§€ ê°€ë¡??¤ë‹¨(ë¸”ë¡) ?•íƒœë¡??•ë ¬?˜ì—¬ ?œëˆˆ??ì¶œë ¥?©ë‹ˆ??"""
    print("\n" + "=" * 68)
    print("                 [ 2??~ 9???„ì²´ êµ¬êµ¬??]")
    print("=" * 68)

    dan_range = list(range(2, 10))

    # cols_per_row ?¨ìœ„ë¡???ë¬¶ìŒ ë¶„í•  (ê¸°ë³¸: 2~5?? 6~9??
    for start_idx in range(0, len(dan_range), cols_per_row):
        group = dan_range[start_idx : start_idx + cols_per_row]

        # ???¤ë” ì¶œë ¥
        headers = [f"  [ {dan}??]    " for dan in group]
        print("\n" + "".join(headers))
        print("-" * (15 * len(group)))

        # 1ë¶€??9ê¹Œì? ê³±ì…ˆ ê²°ê³¼ ê°€ë¡?ì¶œë ¥
        for i in range(1, 10):
            line = [f" {dan} x {i} = {dan * i:>2}   " for dan in group]
            print("".join(line))

    print("\n" + "=" * 68)


def print_gugudan_single(dan: int) -> None:
    """?¬ìš©?ê? ì§€?•í•œ ?¨ì˜ êµ¬êµ¬?¨ì„ ë°•ìŠ¤ ?•íƒœë¡??•ê°ˆ?˜ê²Œ ì¶œë ¥?©ë‹ˆ??"""
    title = f"[ {dan}??]"
    border = "-" * 20
    print(f"\n+{border}+")
    print(f"|{title:^20}|")
    print(f"+{border}+")
    for i in range(1, 10):
        content = f"{dan} x {i} = {dan * i:>3}"
        print(f"| {content:^18} |")
    print(f"+{border}+\n")


def main() -> None:
    """ë©”ì¸ ?¤í–‰ ë£¨í”„"""
    menu = (
        "\n" + "=" * 32 + "\n"
        "        êµ¬êµ¬???„ë¡œê·¸ë¨\n"
        "=" * 32 + "\n"
        " 1. 2??~ 9???„ì²´ ë³´ê¸° (???•ì‹)\n"
        " 2. ?¹ì • ??ê²€??(ì§ì ‘ ?…ë ¥)\n"
        " 3. ì¢…ë£Œ (?ëŠ” 'q' ?…ë ¥)\n"
        + "=" * 32
    )

    while True:
        try:
            print(menu)
            choice = input("> ë©”ë‰´ë¥?? íƒ?˜ì„¸?? ").strip().lower()

            if choice in ("1", "?„ì²´"):
                print_gugudan_all()

            elif choice in ("2", "??):
                raw_input = input("> ì¶œë ¥?????«ì)???…ë ¥?˜ì„¸??(ì·¨ì†Œ: Enter): ").strip()
                if not raw_input:
                    continue

                if raw_input.lower() in ("q", "quit", "exit"):
                    print("?„ë¡œê·¸ë¨??ì¢…ë£Œ?©ë‹ˆ?? ?ˆë…•??ê°€?¸ìš”!")
                    break

                try:
                    dan = int(raw_input)
                    if dan <= 0:
                        print("[?ˆë‚´] 1 ?´ìƒ???ì—°?˜ë? ?…ë ¥?´ì£¼?¸ìš”.")
                        continue
                    print_gugudan_single(dan)
                except ValueError:
                    print("[?¤ë¥˜] ?«ìë§??…ë ¥ ê°€?¥í•©?ˆë‹¤. ?¤ì‹œ ?œë„?´ì£¼?¸ìš”.")

            elif choice in ("3", "q", "quit", "exit", "ì¢…ë£Œ"):
                print("?„ë¡œê·¸ë¨??ì¢…ë£Œ?©ë‹ˆ?? ê°ì‚¬?©ë‹ˆ??")
                break

            else:
                print("[?ˆë‚´] ?¬ë°”ë¥?ë²ˆí˜¸(1, 2, 3) ?ëŠ” 'q'ë¥??…ë ¥?´ì£¼?¸ìš”.")

        except (KeyboardInterrupt, EOFError):
            print("\n\n?„ë¡œê·¸ë¨???ˆì „?˜ê²Œ ì¢…ë£Œ?©ë‹ˆ??")
            sys.exit(0)


if __name__ == "__main__":
    main()

