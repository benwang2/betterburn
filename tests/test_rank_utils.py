from src.constants import Rank
from src.db.cache.utils import get_rank_from_values


def test_get_rank_from_values_defaults_to_stone():
    assert get_rank_from_values(499, 999) == Rank.Stone


def test_get_rank_from_values_returns_aetherean_for_top_players():
    assert get_rank_from_values(1800, 100) == Rank.Aetherean


def test_get_rank_from_values_returns_grandmaster_when_not_top_100():
    assert get_rank_from_values(1800, 101) == Rank.Grandmaster
