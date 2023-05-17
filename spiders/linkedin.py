import asyncio

from playwright.async_api import async_playwright, Page

from spiders.SpiderBlueprint import AsyncBaseSpider


class LinkedinSpider(AsyncBaseSpider):
    SPIDER_NAME = "linkedin"
    URL = (
        "https://www.linkedin.com/jobs/search/"
        "?currentJobId=3587717169"
        "&f_E=1%2C2%2C3"
        "&geoId=102264497"
        "&keywords=python%20developer"
        "&location=Ukraine"
        "&refresh=true"
    )

    async def parse_vacancies(self, page: Page):
        await page.goto(self.URL)

    async def start(self):
        print("Linkedin start")
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch()
            context = await browser.new_context()
            page = await context.new_page()
            await self.parse_vacancies(page)

            await context.close()
            await browser.close()


if __name__ == '__main__':
    asyncio.run(LinkedinSpider().start())
