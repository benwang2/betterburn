import importlib

import pytest


def test_importing_steamboard_has_no_network_side_effects(monkeypatch):
    """Importing the module shouldn't make HTTP calls.

    This guards against accidental import-time side effects like creating a
    SteamLeaderboard and calling update() at module import.
    """

    def _boom(*args, **kwargs):  # pragma: no cover
        raise AssertionError("requests.get was called during import")

    # In case other tests imported it already.
    importlib.invalidate_caches()

    # Patch before import.
    monkeypatch.setattr("requests.get", _boom, raising=True)

    # Import must succeed without triggering requests.get.
    importlib.import_module("src.steamboard")


@pytest.mark.parametrize(
    "attr",
    ["SteamLeaderboard", "get_default_leaderboard"],
)
def test_steamboard_exports(attr):
    mod = importlib.import_module("src.steamboard")
    assert hasattr(mod, attr)
