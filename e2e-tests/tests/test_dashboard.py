"""Browser-level checks: the page a user actually gets."""
from __future__ import annotations

from playwright.sync_api import Page, expect

from pages.dashboard_page import DashboardPage


def test_dashboard_renders_without_console_errors(page: Page, base_url: str) -> None:
    errors: list[str] = []
    page.on("console", lambda msg: errors.append(msg.text) if msg.type == "error" else None)
    page.on("pageerror", lambda exc: errors.append(str(exc)))

    dashboard = DashboardPage(page).open(base_url)
    dashboard.expect_loaded()

    assert errors == [], f"console errors on load: {errors}"


def test_tabs_switch_to_my_bets(page: Page, base_url: str) -> None:
    dashboard = DashboardPage(page).open(base_url)
    dashboard.expect_loaded()
    dashboard.open_my_bets()
    expect(dashboard.bets_tab).to_have_class("tab active")
