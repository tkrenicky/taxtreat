from __future__ import annotations

import subprocess
import tempfile
import urllib.parse
from pathlib import Path

import build_bulk_treaty_en_locale_candidates_v9_20260825 as v9


_ORIGINAL_REQUEST = v9.core._request


def _curl_request(url: str, timeout: int = 25) -> tuple[bytes, str, str]:
    with tempfile.TemporaryDirectory(prefix="taxtreat-en-curl-") as tmp:
        out = Path(tmp) / "body"
        command = [
            "curl",
            "--location",
            "--fail",
            "--silent",
            "--show-error",
            "--compressed",
            "--max-time",
            str(timeout),
            "--retry",
            "1",
            "--retry-delay",
            "1",
            "--user-agent",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/151 Safari/537.36",
            "--header",
            "Accept: application/pdf,text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
            "--header",
            "Accept-Language: en-US,en;q=0.9",
            "--referer",
            url,
            "--output",
            str(out),
            "--write-out",
            "%{url_effective}\n%{content_type}",
            url,
        ]
        completed = subprocess.run(command, check=False, capture_output=True, text=True)
        if completed.returncode != 0:
            raise RuntimeError(f"curl failed ({completed.returncode}): {completed.stderr.strip()[:300]}")
        meta = completed.stdout.splitlines()
        resolved = meta[0].strip() if meta else url
        content_type = meta[1].strip().split(";", 1)[0] if len(meta) > 1 else "application/octet-stream"
        return out.read_bytes(), content_type, resolved


def _resilient_request(url: str, timeout: int = 25) -> tuple[bytes, str, str]:
    original_error: Exception | None = None
    try:
        body, content_type, resolved = _ORIGINAL_REQUEST(url, timeout=timeout)
        # Official download/PDF endpoints returning a tiny HTML/text body are normally
        # an access wrapper, challenge page or incomplete redirect rather than treaty text.
        if len(body) >= 512 or body.startswith(b"%PDF"):
            return body, content_type, resolved
    except Exception as exc:
        original_error = exc

    try:
        body, content_type, resolved = _curl_request(url, timeout=timeout)
        if len(body) < 80 and not body.startswith(b"%PDF"):
            raise RuntimeError(f"curl returned suspiciously short body ({len(body)} bytes)")
        return body, content_type, resolved
    except Exception as curl_error:
        if original_error is not None:
            raise RuntimeError(f"urllib={type(original_error).__name__}: {original_error}; curl={curl_error}") from curl_error
        raise


def main() -> int:
    # Transport-only override. All pair validation, article extraction, Stage-6 rate
    # checks and fail-closed promotion remain exactly those of v9.
    v9.core._request = _resilient_request
    return v9.main()


if __name__ == "__main__":
    raise SystemExit(main())
