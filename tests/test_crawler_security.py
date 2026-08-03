import sys
from pathlib import Path
from types import SimpleNamespace

import pytest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from taxtreat_cz.crawler import Crawler


def test_allowed_host_matching_rejects_suffix_confusion():
    assert Crawler._host_allowed("https://mf.gov.cz/document") is True
    assert Crawler._host_allowed("https://sub.mf.gov.cz/document") is True
    assert Crawler._host_allowed("https://mf.gov.cz.evil.test/document") is False
    assert Crawler._host_allowed("https://evilmf.gov.cz/document") is False


def test_redirect_target_is_revalidated(tmp_path):
    crawler = Crawler(tmp_path)
    response = SimpleNamespace(
        url="https://evil.test/document",
        raise_for_status=lambda: None,
    )
    crawler.session.get = lambda *args, **kwargs: response

    with pytest.raises(ValueError, match="Redirect target"):
        crawler.get("https://mf.gov.cz/document")

    with pytest.raises(ValueError, match="Host is not allowed"):
        crawler.get("https://evil.test/document")
