from __future__ import annotations

import json

from taxtreat.tools import build_sk_pre_review_readiness as readiness_module
from taxtreat.tools import build_sk_prerelease_runtime_manifest as manifest_module
from taxtreat.tools import validate_sk_prerelease_decision_matrix as matrix_module


def _write(path, payload) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def run() -> dict:
    manifest = manifest_module.build_manifest()
    manifest_summary = manifest_module.build_summary(manifest)
    _write(manifest_module.OUTPUT_PATH, manifest)
    _write(manifest_module.SUMMARY_PATH, manifest_summary)

    matrix_summary = matrix_module.validate_matrix(manifest)
    _write(matrix_module.SUMMARY_PATH, matrix_summary)

    readiness = readiness_module.build_readiness()
    _write(readiness_module.OUTPUT_PATH, readiness)

    return {
        "schema_version": 1,
        "source_country": "SK",
        "offline": True,
        "network_fetches_performed": False,
        "runtime_manifest": manifest_summary,
        "decision_matrix": matrix_summary,
        "readiness": {
            "all_machine_evidence_ready": readiness["all_machine_evidence_ready"],
            "blockers": readiness["blockers"],
            "human_review": readiness["human_review"],
            "runtime": readiness["runtime"],
        },
        "fail_closed": True,
    }


def main() -> None:
    print(json.dumps(run(), ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
