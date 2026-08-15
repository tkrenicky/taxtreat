import pytest

from taxtreat.consolidation.review_release_state import (
    assess_review_release_state,
)


PACKAGE = {
    "package_sha256": "a" * 64,
}


def human_review():
    return {
        "package_sha256": "a" * 64,
        "reviewer_id": "human-reviewer",
        "reviewed_at": "2026-08-11T14:00:00Z",
        "outcome": "accepted",
    }


def production_approval():
    return {
        "package_sha256": "a" * 64,
        "approver_id": "production-approver",
        "approved_at": "2026-08-11T15:00:00Z",
        "outcome": "approved",
    }


def test_pending_state_is_fail_closed():
    state = assess_review_release_state(PACKAGE)

    assert state.human_review_status == "pending"
    assert state.production_approval_status == "not_approved"
    assert state.human_review_complete is False
    assert state.production_approved is False
    assert state.production_releasable is False
    assert state.verified_scope_count == 0


def test_completed_human_review_does_not_release_or_verify():
    state = assess_review_release_state(
        PACKAGE,
        human_review_event=human_review(),
    )

    assert state.human_review_status == "human_review_complete"
    assert state.human_review_complete is True
    assert state.production_approved is False
    assert state.production_releasable is False
    assert state.verified_scope_count == 0


def test_production_approval_is_separate_from_human_review():
    state = assess_review_release_state(
        PACKAGE,
        human_review_event=human_review(),
        production_approval_event=production_approval(),
    )

    assert state.human_review_complete is True
    assert state.production_approved is True

    # Even approval does not silently open source release.
    assert state.production_releasable is False
    assert state.verified_scope_count == 0


def test_production_approval_without_review_is_rejected():
    with pytest.raises(
        ValueError,
        match="requires completed human review",
    ):
        assess_review_release_state(
            PACKAGE,
            production_approval_event=production_approval(),
        )


def test_review_is_hash_bound():
    event = human_review()
    event["package_sha256"] = "b" * 64

    with pytest.raises(ValueError, match="stale package hash"):
        assess_review_release_state(
            PACKAGE,
            human_review_event=event,
        )


def test_production_approval_is_hash_bound():
    approval = production_approval()
    approval["package_sha256"] = "b" * 64

    with pytest.raises(ValueError, match="stale package hash"):
        assess_review_release_state(
            PACKAGE,
            human_review_event=human_review(),
            production_approval_event=approval,
        )


@pytest.mark.parametrize(
    "event, message",
    [
        (
            {
                "package_sha256": "a" * 64,
                "reviewed_at": "2026-08-11T14:00:00Z",
                "outcome": "accepted",
            },
            "reviewer_id",
        ),
        (
            {
                "package_sha256": "a" * 64,
                "reviewer_id": "human-reviewer",
                "reviewed_at": "bad",
                "outcome": "accepted",
            },
            "invalid reviewed_at",
        ),
        (
            {
                "package_sha256": "a" * 64,
                "reviewer_id": "human-reviewer",
                "reviewed_at": "2026-08-11T14:00:00Z",
                "outcome": "returned_for_correction",
            },
            "outcome='accepted'",
        ),
    ],
)
def test_invalid_human_review_event_fails_closed(event, message):
    with pytest.raises(ValueError, match=message):
        assess_review_release_state(
            PACKAGE,
            human_review_event=event,
        )


def test_missing_review_timestamp_fails_closed():
    event = human_review()
    event["reviewed_at"] = ""
    with pytest.raises(ValueError, match="requires reviewed_at"):
        assess_review_release_state(PACKAGE, human_review_event=event)


def test_invalid_package_hash_fails_closed():
    with pytest.raises(ValueError, match="requires package_sha256"):
        assess_review_release_state({"package_sha256": "too-short"})
