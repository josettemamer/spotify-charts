import os
import re
import asyncio
import logging
from pathlib import Path

import nest_asyncio
from dotenv import load_dotenv, set_key
from playwright.async_api import async_playwright

# Allow running from notebooks or CLI
nest_asyncio.apply()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def load_credentials(dotenv_path=".env"):
    """Load Spotify credentials from .env."""
    dotenv_path = Path(dotenv_path)
    load_dotenv(dotenv_path)
    username = os.getenv("SPOTIFY_USERNAME")
    password = os.getenv("SPOTIFY_PASSWORD")
    if not username or not password:
        raise EnvironmentError("SPOTIFY_USERNAME or SPOTIFY_PASSWORD not set in .env")
    return username, password, dotenv_path


async def get_spotify_token(username: str, password: str, dotenv_path: Path) -> str | None:
    """Login to Spotify Charts and capture Bearer token."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=100)
        page = await browser.new_page()
        token = None

        async def intercept_request(request):
            nonlocal token
            if "auth/v1/overview/GLOBAL" in request.url:
                auth_header = request.headers.get("authorization")
                if auth_header and auth_header.startswith("Bearer "):
                    token = auth_header.split("Bearer ")[1]
                    logger.info("Captured Bearer token.")
                    set_key(dotenv_path, "SPOTIFY_BEARER_TOKEN", token)

        page.on("request", intercept_request)

        try:
            logger.info("Opening Spotify Charts homepage...")
            await page.goto("https://charts.spotify.com/home")

            logger.info("Clicking login button...")
            await page.locator('a[data-testid="charts-login"]').click()

            await page.wait_for_url(re.compile(r"https://accounts\.spotify\.com/.*/login.*"), timeout=10000)

            email_field = page.locator('input[data-testid="login-username"]')
            password_field = page.locator('input[data-testid="login-password"]')

            if await email_field.count() > 0 and await password_field.count() > 0:
                logger.info("Login form with email and password detected.")
                await email_field.fill(username)
                await password_field.fill(password)
                await page.locator('button[data-testid="login-button"]').click()

            elif await email_field.count() > 0:
                logger.info("Email-only login flow detected. Entering email...")
                await email_field.fill(username)
                await page.locator('button[data-testid="login-button"]').click()

                logger.info("Waiting for challenge page or fallback...")
                await page.wait_for_timeout(4000)

                current_url = page.url
                if "challenge.spotify.com" in current_url:
                    logger.info("Challenge page detected.")
                    button = page.locator('button:has-text("Log in with a password")')
                    await button.wait_for(state="visible", timeout=5000)
                    await button.click()

                    await page.wait_for_url(re.compile(r"https://accounts\.spotify\.com/.*/login.*"), timeout=10000)
                    password_field = page.locator('input[data-testid="login-password"]')
                    await password_field.wait_for(state="visible", timeout=5000)
                    await password_field.fill(password)
                    await page.locator('button[data-testid="login-button"]').click()
                else:
                    logger.warning("Challenge page not detected. Screenshot saved.")
                    await page.screenshot(path="no_challenge_page.png")

            logger.info("Waiting for Spotify Charts redirect...")
            try:
                await page.wait_for_url("https://charts.spotify.com/charts/overview/global", timeout=15000)
                logger.info("Login successful.")
            except:
                logger.error("Login did not complete successfully.")
                await page.screenshot(path="login_failed.png")
                return None

            await asyncio.sleep(1)
            await browser.close()
            return token

        except Exception as e:
            logger.exception("Error during Spotify login flow.")
            await page.screenshot(path="error_during_login.png")
            await browser.close()
            return None


def main():
    try:
        username, password, dotenv_path = load_credentials()
        token = asyncio.run(get_spotify_token(username, password, dotenv_path))
        if token:
            logger.info("Bearer Token saved to .env.")
        else:
            logger.warning("Bearer Token was not captured.")
    except Exception as e:
        logger.error(f"Fatal error: {e}")


if __name__ == "__main__":
    main()
