from pathlib import Path

from taxtreat.services.rule_engine import build_dividend_rule

DB_PATH = Path(__file__).resolve().parent / "taxtreat.db"


def main() -> None:
    rule = build_dividend_rule(10, DB_PATH)
    print(rule)


if __name__ == "__main__":
    main()
