"""Page object for the dashboard: selectors live here, tests stay readable."""
from __future__ import annotations

from playwright.sync_api import Page, expect


class DashboardPage:
    def __init__(self, page: Page) -> None:
        self.page = page
        self.tabs = page.locator("#tabs button.tab")
        self.bets_tab = page.locator('button.tab[data-tab="mine"]')

    def open(self, base_url: str) -> "DashboardPage":
        self.page.goto(f"{base_url}/")
        return self

    def expect_loaded(self) -> None:
        expect(self.page).to_have_title("MicrobistBets")
        expect(self.tabs.first).to_be_visible()
        assert self.tabs.count() >= 4

    def open_my_bets(self) -> None:
        self.bets_tab.click()
        expect(self.bets_tab).to_have_class("tab active")
