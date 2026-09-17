"""구구단 프로그램 (최적화 버전)
- 2단 ~ 9단 가로 테이블(다단) 깔끔한 전체 출력
- 특정 단 입력 및 즉시 계산 출력
- 견고한 입력 검증 및 단축 종료(q) 지원
"""

import sys


def print_gugudan_all(cols_per_row: int = 4) -> None:
    """2단부터 9단까지 가로 다단(블록) 형태로 정렬하여 한눈에 출력합니다."""
    print("\n" + "=" * 68)
    print("                 [ 2단 ~ 9단 전체 구구단 ]")
    print("=" * 68)

    dan_range = list(range(2, 10))

    # cols_per_row 단위로 행 묶음 분할 (기본: 2~5단, 6~9단)
    for start_idx in range(0, len(dan_range), cols_per_row):
        group = dan_range[start_idx : start_idx + cols_per_row]

        # 단 헤더 출력
        headers = [f"  [ {dan}단 ]    " for dan in group]
        print("\n" + "".join(headers))
        print("-" * (15 * len(group)))

        # 1부터 9까지 곱셈 결과 가로 출력
        for i in range(1, 10):
            line = [f" {dan} x {i} = {dan * i:>2}   " for dan in group]
            print("".join(line))

    print("\n" + "=" * 68)


def print_gugudan_single(dan: int) -> None:
    """사용자가 지정한 단의 구구단을 박스 형태로 정갈하게 출력합니다."""
    title = f"[ {dan}단 ]"
    border = "-" * 20
    print(f"\n+{border}+")
    print(f"|{title:^20}|")
    print(f"+{border}+")
    for i in range(1, 10):
        content = f"{dan} x {i} = {dan * i:>3}"
        print(f"| {content:^18} |")
    print(f"+{border}+\n")


def main() -> None:
    """메인 실행 루프"""
    menu = (
        "\n" + "=" * 32 + "\n"
        "        구구단 프로그램\n"
        "=" * 32 + "\n"
        " 1. 2단 ~ 9단 전체 보기 (표 형식)\n"
        " 2. 특정 단 검색 (직접 입력)\n"
        " 3. 종료 (또는 'q' 입력)\n"
        + "=" * 32
    )

    while True:
        try:
            print(menu)
            choice = input("> 메뉴를 선택하세요: ").strip().lower()

            if choice in ("1", "전체"):
                print_gugudan_all()

            elif choice in ("2", "단"):
                raw_input = input("> 출력할 단(숫자)을 입력하세요 (취소: Enter): ").strip()
                if not raw_input:
                    continue

                if raw_input.lower() in ("q", "quit", "exit"):
                    print("프로그램을 종료합니다. 안녕히 가세요!")
                    break

                try:
                    dan = int(raw_input)
                    if dan <= 0:
                        print("[안내] 1 이상의 자연수를 입력해주세요.")
                        continue
                    print_gugudan_single(dan)
                except ValueError:
                    print("[오류] 숫자만 입력 가능합니다. 다시 시도해주세요.")

            elif choice in ("3", "q", "quit", "exit", "종료"):
                print("프로그램을 종료합니다. 감사합니다!")
                break

            else:
                print("[안내] 올바른 번호(1, 2, 3) 또는 'q'를 입력해주세요.")

        except (KeyboardInterrupt, EOFError):
            print("\n\n프로그램을 안전하게 종료합니다.")
            sys.exit(0)


if __name__ == "__main__":
    main()

