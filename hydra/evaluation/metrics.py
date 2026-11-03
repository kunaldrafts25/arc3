"""Use the installed official scorer instead of an approximate proxy."""
from arc_agi.scorecard import EnvironmentScoreCalculator


def official_game_score(completed, actions, human_baselines):
    if human_baselines is None or any(x is None or x < 0 for x in human_baselines):
        return None
    if not (len(completed) == len(actions) == len(human_baselines)):
        raise ValueError("metrics must have equal lengths")
    calculator = EnvironmentScoreCalculator()
    for index, (done, count, baseline) in enumerate(zip(completed, actions, human_baselines), 1):
        calculator.add_level(index, done, count, baseline)
    return calculator.to_score().score
