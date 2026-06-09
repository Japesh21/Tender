"""
Browser session manager using Playwright.
Logs into the TGTS portal with credentials from .env,
saves cookies to a file, and loads them into a requests session.
"""

import json
import logging
import os
import time
from typing import Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

BASE_URL = "https://tender.telangana.gov.in"
LOGIN_URL = f"{BASE_URL}/login.html"
COOKIES_FILE = os.path.join(os.path.dirname(__file__), ".portal_cookies.json")

# How long (seconds) before we consider saved cookies stale and re-login
COOKIE_TTL = 3600  # 1 hour


def _save_cookies(cookies: list):
    """Persist cookies to disk with a timestamp."""
    data = {"saved_at": time.time(), "cookies": cookies}
    with open(COOKIES_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f)
    logger.info(f"Cookies saved to {COOKIES_FILE}")


def _load_cookies() -> Optional[list]:
    """Load cookies from disk if they exist and are not stale."""
    if not os.path.exists(COOKIES_FILE):
        return None
    try:
        with open(COOKIES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        age = time.time() - data.get("saved_at", 0)
        if age > COOKIE_TTL:
            logger.info(f"Saved cookies are {int(age)}s old (TTL={COOKIE_TTL}s) — will re-login")
            return None
        logger.info(f"Loaded saved cookies (age {int(age)}s)")
        return data["cookies"]
    except Exception as e:
        logger.warning(f"Could not load cookies: {e}")
        return None


def _playwright_login(username: str, password: str) -> list:
    """
    Open a Playwright browser, log in, return the session cookies.
    Headless=False so you can see what's happening.
    """
    from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

    logger.info("Launching browser for portal login...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=100)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = context.new_page()

        page.goto(LOGIN_URL, wait_until="networkidle", timeout=30000)
        logger.info("Login page loaded")

        # Fill credentials
        page.fill("#userName", username)
        page.fill("#password", password)
        logger.info("Credentials filled")

        # Click login button
        page.click("#btnLogin")

        # Wait for navigation away from login page (up to 30s)
        try:
            page.wait_for_url(lambda url: "login.html" not in url, timeout=30000)
            logger.info(f"Login successful — landed on {page.url}")
        except PWTimeout:
            # Check if still on login page (wrong credentials)
            if "login.html" in page.url:
                browser.close()
                raise RuntimeError(
                    "Login failed — still on login page after 30s. "
                    "Check PORTAL_USERNAME and PORTAL_PASSWORD in .env"
                )
            logger.info("Login appeared to succeed (timeout but URL changed)")

        # Grab all cookies from the browser context
        cookies = context.cookies()
        logger.info(f"Captured {len(cookies)} cookies")

        browser.close()
        return cookies


def get_authenticated_session(username: str, password: str) -> requests.Session:
    """
    Return a requests.Session pre-loaded with valid portal cookies.
    Uses cached cookies if fresh, otherwise re-logs in via Playwright.
    """
    cookies = _load_cookies()

    if not cookies:
        cookies = _playwright_login(username, password)
        _save_cookies(cookies)

    session = requests.Session()

    # Configure retry
    retry = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "POST"]
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": BASE_URL,
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "en-US,en;q=0.9",
        "X-Requested-With": "XMLHttpRequest",
    })

    # Load cookies into the requests session
    for cookie in cookies:
        session.cookies.set(
            cookie["name"],
            cookie["value"],
            domain=cookie.get("domain", "").lstrip("."),
        )

    logger.info(f"Requests session ready with {len(cookies)} cookies")
    return session


def invalidate_cookies():
    """Delete saved cookies file to force re-login on next run."""
    if os.path.exists(COOKIES_FILE):
        os.remove(COOKIES_FILE)
        logger.info("Cookies invalidated")
