import taxtreat.pipeline.run_pipeline as pipeline
from taxtreat.pipeline.run_pipeline import STEPS


def test_pipeline_contains_required_steps():
    assert [name for name, _ in STEPS] == [
        "Build source manifest",
        "Build legal-review queue",
        "Build canonical legal registry",
        "Build release manifest",
    ]
    assert all(callable(step) for _, step in STEPS)


def test_build_review_queue_writes_generated_queue(monkeypatch):
    queue = [{"country": "AT"}]
    written = []
    monkeypatch.setattr(pipeline, "build_legal_review_queue", lambda: queue)
    monkeypatch.setattr(pipeline, "write_legal_review_queue", written.append)

    pipeline.build_review_queue()

    assert written == [queue]
