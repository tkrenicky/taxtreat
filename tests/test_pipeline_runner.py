from taxtreat.pipeline.run_pipeline import STEPS


def test_pipeline_contains_required_steps():
    assert len(STEPS) >= 7
    assert STEPS[-1][0] == "Build database"
