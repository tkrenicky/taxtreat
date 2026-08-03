from __future__ import annotations

from taxtreat.pipeline.release import build_release_manifest


def render() -> str:
    manifest = build_release_manifest()
    parser = manifest["parser"]
    sources = manifest["sources"]
    legal = manifest["legal"]
    lines = [
        "TaxTreat release dashboard",
        f"Parser datasets: {parser['datasets']}",
        f"Relevant articles: {parser['relevant_articles']}",
        f"Source auditability: {sources['auditability']} "
        f"({sources['artifacts_with_hash']}/{sources['total']})",
        f"Structured legal scopes: {legal['scopes']}/300",
        f"Verified legal scopes: {legal['verified_scopes']}/300",
        f"Golden cases: {manifest['golden_cases']}",
        f"Production ready: {manifest['production_ready']}",
    ]
    return "\n".join(lines)


def main() -> None:
    print(render())


if __name__ == "__main__":  # pragma: no cover
    main()
