"""Compatibility entry point for the canonical release builder.

The former implementation exported a flat CSV whose fields did not exist in
the parsed treaty schema.  All generated release data now comes from
``taxtreat.pipeline.release``.
"""

from taxtreat.consolidation.legal_review_queue import (
    build_legal_review_queue,
    write_legal_review_queue,
)
from taxtreat.pipeline.release import (
    MANIFEST_DIR as OUTPUT_DIR,
    build_legal_registry,
    build_release_manifest,
    build_source_manifest,
)


def main() -> None:
    build_source_manifest()
    write_legal_review_queue(build_legal_review_queue())
    build_legal_registry()
    build_release_manifest()
    print("Canonical manifests exported.")


if __name__ == "__main__":  # pragma: no cover
    main()
