import math
from itertools import combinations


def implied_probability(decimal_odds):
    if decimal_odds <= 1:
        return 0.0
    return 1.0 / decimal_odds


def remove_margin(probs):
    total = sum(probs)
    if total <= 0:
        return probs
    return [p / total for p in probs]


def fair_odds(prob):
    if prob <= 0:
        return 0.0
    return 1.0 / prob


def poisson_pmf(k, lam):
    if lam <= 0:
        return 1.0 if k == 0 else 0.0
    return (lam ** k) * math.exp(-lam) / math.factorial(k)


def poisson_1x2(home_goals, away_goals, max_goals=8):
    home_w = draw = away_w = 0.0
    for i in range(max_goals + 1):
        for j in range(max_goals + 1):
            p = poisson_pmf(i, home_goals) * poisson_pmf(j, away_goals)
            if i > j:
                home_w += p
            elif i == j:
                draw += p
            else:
                away_w += p
    return home_w, draw, away_w