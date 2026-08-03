"""Compatibility entry point for the canonical release builder.

The former implementation exported a flat CSV whose fields did not exist in
the parsed treaty schema.  All generated release data now comes from
``taxtreat.pipeline.release``.
"""

from taxtreat.pipeline.release import (
    MANIFEST_DIR as OUTPUT_DIR,
    build_legal_registry,
    build_release_manifest,
    build_source_manifest,
)


def main() -> None:
    build_source_manifest()
    build_legal_registry()
    build_release_manifest()
    print("Canonical manifests exported.")


if __name__ == "__main__":  # pragma: no cover
    main()
