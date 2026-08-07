from playwright.sync_api import Page


class ArvalParser:

    def parse_title(self, page: Page) -> str:
        """
        Returns the vehicle title from the offer page.
        Example:
        BYD Atto 2 1.5 PHEV Boost AT
        """

        title = page.locator("h1 span").inner_text().strip()

        return title
    