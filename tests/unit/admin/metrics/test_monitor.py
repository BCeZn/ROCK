from rock.admin.metrics.monitor import aggregate_metrics


def test_aggregate_metrics():
    sandbox_meta: dict[str, dict[str, str]] = {}
    sandbox_meta["123"] = {"image": "iflow_test"}
    sandbox_meta["456"] = {"image": "iflow_test"}
    sandbox_meta["789"] = {"image": "iflow_test"}
    sandbox_meta["101112"] = {"image": "python:3.11"}
    sandbox_meta["131415"] = {"image": "python:3.11"}
    sandbox_meta["161718"] = {"image": "image_test"}

    aggregated_metrics = aggregate_metrics(sandbox_meta, "image")
    assert aggregated_metrics["iflow_test"] == 3
    assert aggregated_metrics["python:3.11"] == 2
    assert aggregated_metrics["image_test"] == 1
