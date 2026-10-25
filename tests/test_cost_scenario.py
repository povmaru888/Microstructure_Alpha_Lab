from microalpha.evaluate import cost_scenarios


def test_cost_scenarios_are_sensitivity_only() -> None:
    report = cost_scenarios()
    assert len(report["scenarios"]) == 18
    assert "not_a_net_profit_claim" in report["limitations"]
    assert "no_queue_position_model" in report["limitations"]
    assert "profit" not in report
