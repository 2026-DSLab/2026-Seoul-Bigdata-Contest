"""
main.py  —  CLI 진입점

사용법:
    python main.py                    # 대화형 입력
    python main.py --json input.json  # JSON 파일로 입력
    ##python main.py --json ../data/storyline/inputs/user_input1.json #시나리오 실행

"""

import os
import sys
import json
import argparse
from dotenv import load_dotenv

load_dotenv()

# ── 경로 설정 ────────────────────────────────────────────────────
_CODE_DIR = os.path.dirname(os.path.abspath(__file__))
_ROOT_DIR = os.path.join(_CODE_DIR, "..")
_EXAMPLE_JSON = os.path.join(_ROOT_DIR, "data", "preprocessed", "input_example.json")

USER_FIELDS = [
    ("상호명",          "가게 이름을 입력하세요",               str),
    ("구",              "위치의 구를 입력하세요 (예: 강남구)",   str),
    ("동",              "위치의 동을 입력하세요 (예: 역삼1동)",  str),
    ("업종_카테고리",   "업종 카테고리를 입력하세요\n"
                        "  선택지: 외식/F&B / 식품/식재료 / 생활서비스 / 생활/홈인테리어\n"
                        "          의료/건강 / 교육 / 오락/여가 / 숙박/부동산\n"
                        "          전문서비스 / 전자/디지털 / 자동차/이동수단 / 패션/뷰티",
                                                                 str),
    ("운영_요일",       "운영 요일을 입력하세요 (예: 주5일, 주7일)",  str),
    ("오픈_시간",       "오픈 시간을 입력하세요 (예: 08:00)",  str),
    ("마감_시간",       "마감 시간을 입력하세요 (예: 22:00)",  str),
    ("시그니쳐_상품",   "시그니처 상품을 입력하세요",              str),
    ("분위기",          "가게 분위기를 입력하세요 (예: 감성적인, 모던한, 아늑한)", str),
    ("고민_사항",       "현재 가장 큰 고민이나 개선하고 싶은 점을 입력하세요", str),
    ("주고객_연령층",   "주요 타겟 고객의 연령대를 입력하세요\n"
                        "  선택지: 10대 / 20대 / 30대 / 40대 / 50대 / 60대이상",
                                                                 str),
    ("주고객_성별",     "주요 타겟 고객의 성별을 입력하세요 (남성 / 여성)",  str),
]


# ════════════════════════════════════════════════════════════════
# CLI 인터페이스
# ════════════════════════════════════════════════════════════════

def _print_header():
    print("""
╔══════════════════════════════════════════════════════════════╗
║         🏙️  상권 분석 LLM 멀티에이전트 시스템                ║
║         2026 서울 빅데이터 공모전                             ║
╟──────────────────────────────────────────────────────────────╢
║  점주 정보를 입력하면 AI가 상권을 분석해 솔루션을 제공합니다.  ║
╚══════════════════════════════════════════════════════════════╝
""")


def _collect_user_input() -> dict:
    """대화형 CLI로 사용자 입력 10개 필드 수집."""
    print("📝 가게 정보를 입력해주세요.\n")
    user_data = {}

    for i, (field, prompt, dtype) in enumerate(USER_FIELDS, 1):
        while True:
            try:
                raw = input(f"  [{i:02d}/{len(USER_FIELDS)}] {prompt}: ").strip()
                if not raw:
                    print("       ⚠  빈 값은 입력할 수 없습니다. 다시 입력해주세요.")
                    continue
                user_data[field] = dtype(raw)
                break
            except (ValueError, KeyboardInterrupt):
                print("\n입력이 취소되었습니다.")
                sys.exit(0)

    return user_data


def _load_json_input(path: str) -> dict:
    """JSON 파일에서 사용자 입력 필드를 읽어옵니다."""
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    # input_example.json 전체가 들어온 경우 사용자 입력 10개 필드만 추출
    user_fields = [f for f, _, _ in USER_FIELDS]
    user_data   = {k: raw[k] for k in user_fields if k in raw}

    missing = [k for k in user_fields if k not in user_data]
    if missing:
        print(f"⚠  JSON에서 다음 필드가 없습니다: {missing}")
        print("   대화형으로 누락 필드를 입력합니다.\n")
        for field in missing:
            prompt = next(p for f, p, _ in USER_FIELDS if f == field)
            user_data[field] = input(f"  {field} ({prompt}): ").strip()

    return user_data


def _check_env():
    """환경변수 기본 검증."""
    provider = os.getenv("LLM_PROVIDER", "").lower()
    if not provider:
        print("❌ .env에 LLM_PROVIDER가 설정되지 않았습니다. (.env.example 참고)")
        sys.exit(1)

    if provider == "gemini" and not os.getenv("GEMINI_API_KEY"):
        print("❌ LLM_PROVIDER=gemini 이지만 GEMINI_API_KEY가 없습니다.")
        sys.exit(1)
    elif provider == "openai" and not os.getenv("OPENAI_API_KEY"):
        print("❌ LLM_PROVIDER=openai 이지만 OPENAI_API_KEY가 없습니다.")
        sys.exit(1)

    if not os.getenv("KAKAO_API_KEY"):
        print("⚠  KAKAO_API_KEY가 없습니다. 좌표 조회 없이 진행합니다.\n")


# ════════════════════════════════════════════════════════════════
# 메인
# ════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="상권 분석 LLM 멀티에이전트 시스템"
    )
    parser.add_argument(
        "--json", "-j", metavar="FILE",
        help="사용자 입력 JSON 파일 경로 (input_example.json 형식)"
    )
    parser.add_argument(
        "--example", "-e", action="store_true",
        help="input_example.json 으로 테스트 실행"
    )
    args = parser.parse_args()

    _print_header()
    _check_env()

    # 입력 수집
    if args.example:
        print(f"📄 예시 파일로 실행: {_EXAMPLE_JSON}\n")
        user_input = _load_json_input(_EXAMPLE_JSON)
    elif args.json:
        print(f"📄 JSON 파일로 실행: {args.json}\n")
        user_input = _load_json_input(args.json)
    else:
        user_input = _collect_user_input()

    # 입력 확인
    print("\n📋 입력 확인:")
    for k, v in user_input.items():
        print(f"   {k}: {v}")

    confirm = input("\n위 정보로 분석을 시작할까요? (y/n): ").strip().lower()
    if confirm not in ("y", "yes", "예", "ㅇ"):
        print("취소되었습니다.")
        sys.exit(0)

    # 파이프라인 실행
    from pipeline import run_pipeline
    run_pipeline(user_input)


if __name__ == "__main__":
    main()
