"""API-level checks: the parts of the app that must work without external keys."""
from __future__ import annotations

import requests


def test_api_version(api: requests.Session) -> None:
    response = api.get(f"{api.base_url}/api/version", timeout=5)
    assert response.status_code == 200
    assert "assets" in response.json()


def test_add_and_list_bet(api: requests.Session) -> None:
    payload = {
        "event": "Test United vs Example City",
        "outcome": "Home",
        "stake": 10.0,
        "odds": 2.10,
        "edge_pct": 4.5,
        "sport_group": "soccer",
    }
    created = api.post(f"{api.base_url}/api/bets", json=payload, timeout=5)
    assert created.status_code == 200
    assert created.json()["ok"] is True

    listing = api.get(f"{api.base_url}/api/bets", timeout=5).json()
    matches = [b for b in listing["bets"] if b["event"] == payload["event"]]
    assert len(matches) == 1
    assert matches[0]["status"] == "open"
    assert matches[0]["stake"] == payload["stake"]


def test_settle_bet_and_reject_double_settle(api: requests.Session) -> None:
    payload = {
        "event": "Settle United vs Doubtful Rovers",
        "outcome": "Away",
        "stake": 20.0,
        "odds": 1.50,
        "sport_group": "soccer",
    }
    api.post(f"{api.base_url}/api/bets", json=payload, timeout=5)
    bet = [b for b in api.get(f"{api.base_url}/api/bets", timeout=5).json()["bets"]
           if b["event"] == payload["event"]][0]

    settled = api.post(f"{api.base_url}/api/bets/{bet['id']}/settle?won=true", timeout=5)
    assert settled.status_code == 200
    assert settled.json()["status"] == "won"

    repeat = api.post(f"{api.base_url}/api/bets/{bet['id']}/settle?won=true", timeout=5)
    assert repeat.status_code == 404


def test_value_bets_without_api_keys(api: requests.Session) -> None:
    """No keys configured: the endpoint must answer, not crash."""
    response = api.get(f"{api.base_url}/api/value-bets", timeout=10)
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, (dict, list))


def test_api_bet_appears_in_wallet(api: requests.Session) -> None:
    """Regression: a bet created through /api/bets must be visible in the dashboard wallet.

    The dashboard reads /api/wallet/bets?player=client. Before the fix the quick endpoint
    wrote player='demo', so the bet existed in the database but never showed up in the UI.
    """
    payload = {
        "event": "Wallet United vs Ghost Town",
        "outcome": "Home",
        "stake": 5.0,
        "odds": 1.95,
        "sport_group": "soccer",
    }
    assert api.post(f"{api.base_url}/api/bets", json=payload, timeout=5).status_code == 200

    wallet = api.get(f"{api.base_url}/api/wallet/bets?player=client&settle=0", timeout=5)
    assert wallet.status_code == 200
    events = [bet["event"] for bet in wallet.json()["bets"]]
    assert payload["event"] in events
