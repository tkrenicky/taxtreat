from taxtreat.pipeline.run_pipeline import STEPS


def test_pipeline_contains_required_steps():
    assert [name for name, _ in STEPS] == [
        "Build source manifest",
        "Build canonical legal registry",
        "Build release manifest",
    ]
    assert all(callable(step) for _, step in STEPS)
