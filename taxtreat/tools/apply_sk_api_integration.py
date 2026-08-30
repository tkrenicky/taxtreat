from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MAIN_PATH = ROOT / "app" / "main.py"

_IMPORT_ANCHOR = """from taxtreat.services.reporting import (\n    build_professional_report,\n    render_report_html,\n)\n"""
_IMPORT_REPLACEMENT = _IMPORT_ANCHOR + """from taxtreat.services.source_country_release_gate import (\n    SourceCountryNotReleasedError,\n    UnsupportedSourceCountryError,\n    require_source_country_analysis_release,\n)\nfrom app.sk_prerelease import router as sk_prerelease_router\n"""

_MOUNT_ANCHOR = """app.mount(\n    \"/ui-assets\",\n    StaticFiles(directory=WEB_ROOT),\n    name=\"ui-assets\",\n)\n"""
_MOUNT_REPLACEMENT = _MOUNT_ANCHOR + "app.include_router(sk_prerelease_router)\n"

_RELEASE_ANCHOR = """    if source != \"CZ\":\n        return None\n\n    treaty_pair_id = f\"{source}-{recipient}\"\n"""
_RELEASE_REPLACEMENT = """    if source != \"CZ\":\n        try:\n            require_source_country_analysis_release(source)\n        except UnsupportedSourceCountryError as exc:\n            raise HTTPException(\n                status_code=422,\n                detail={\n                    \"code\": \"UNSUPPORTED_SOURCE_COUNTRY\",\n                    \"source_country\": source,\n                },\n            ) from exc\n        except SourceCountryNotReleasedError as exc:\n            decision = exc.decision\n            raise HTTPException(\n                status_code=409,\n                detail={\n                    \"code\": decision.code,\n                    \"source_country\": source,\n                    \"release_status\": decision.release_status,\n                    \"release_blockers\": list(decision.blockers),\n                },\n            ) from exc\n        raise HTTPException(\n            status_code=409,\n            detail={\n                \"code\": \"SOURCE_COUNTRY_RELEASE_GATE_MISSING\",\n                \"source_country\": source,\n            },\n        )\n\n    treaty_pair_id = f\"{source}-{recipient}\"\n"""


def _replace_once(text: str, anchor: str, replacement: str, label: str) -> str:
    count = text.count(anchor)
    if count != 1:
        raise RuntimeError(
            f"Expected exactly one {label} anchor, found {count}; refusing to patch."
        )
    return text.replace(anchor, replacement, 1)


def build_integrated_main(text: str) -> str:
    if "from app.sk_prerelease import router as sk_prerelease_router" not in text:
        text = _replace_once(text, _IMPORT_ANCHOR, _IMPORT_REPLACEMENT, "import")
    if "app.include_router(sk_prerelease_router)" not in text:
        text = _replace_once(text, _MOUNT_ANCHOR, _MOUNT_REPLACEMENT, "router mount")

    if _RELEASE_REPLACEMENT not in text:
        text = _replace_once(text, _RELEASE_ANCHOR, _RELEASE_REPLACEMENT, "release gate")

    return text


def main() -> None:
    original = MAIN_PATH.read_text(encoding="utf-8")
    integrated = build_integrated_main(original)
    if integrated == original:
        print("SK API integration already applied; no changes.")
        return
    MAIN_PATH.write_text(integrated, encoding="utf-8")
    print("Applied SK API integration to app/main.py")


if __name__ == "__main__":
    main()
