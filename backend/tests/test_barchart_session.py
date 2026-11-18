"""Browser session lifecycle for the Barchart fetcher.

A crashed Chromium used to stay installed on the client: `_ensure_page` only
checked `self._browser is None`, and a failed fetch closed just the context, so
the dead object was reused on every later call. In production that turned one
September crash into a five-week outage in which every fetch failed, a core
span at 100% and six zombie `headless_shell` children accumulated. These tests
pin the recovery behaviour without needing a real browser.
"""
import sys
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.barchart import _BrowserClient, PAGE_MAX_AGE_S  # noqa: E402


class FakeBrowser:
    def __init__(self, connected=True, raises=False):
        self._connected, self._raises = connected, raises
        self.closed = False

    def is_connected(self):
        if self._raises:
            raise RuntimeError("driver connection gone")
        return self._connected

    def close(self):
        self.closed = True


class PageUsabilityTests(unittest.TestCase):
    def setUp(self):
        self.client = _BrowserClient()

    def tearDown(self):
        self.client._executor.shutdown(wait=False)

    def hold(self, browser, age=0.0):
        self.client._page = object()
        self.client._page_opened_at = time.time() - age
        self.client._browser = browser

    def test_a_fresh_client_has_nothing_to_reuse(self):
        self.assertFalse(self.client._page_is_usable())

    def test_a_live_session_is_reused(self):
        self.hold(FakeBrowser())
        self.assertTrue(self.client._page_is_usable())

    def test_a_disconnected_browser_is_not_reused(self):
        # The regression: previously only `is None` was checked, so a crashed
        # browser was reused forever and every fetch failed.
        self.hold(FakeBrowser(connected=False))
        self.assertFalse(self.client._page_is_usable())

    def test_a_broken_driver_connection_is_not_reused(self):
        self.hold(FakeBrowser(raises=True))
        self.assertFalse(self.client._page_is_usable())

    def test_a_stale_page_is_recycled(self):
        self.hold(FakeBrowser(), age=PAGE_MAX_AGE_S + 1)
        self.assertFalse(self.client._page_is_usable())


class IdleReaperTests(unittest.TestCase):
    """The reaper must close an idle session but never a live one.

    Teardown previously happened only on the next request, so one API call
    left Chromium running indefinitely at a third of a core.
    """

    def setUp(self):
        self.client = _BrowserClient()

    def tearDown(self):
        self.client._executor.shutdown(wait=False)

    def test_a_live_session_is_left_alone(self):
        self.client._page = object()
        self.client._page_opened_at = time.time()
        self.client._browser = FakeBrowser()
        self.client._shutdown_if_idle()
        self.assertIsNotNone(self.client._page)

    def test_an_idle_session_is_closed(self):
        self.client._page = object()
        self.client._page_opened_at = time.time() - PAGE_MAX_AGE_S - 1
        browser = FakeBrowser()
        self.client._browser = browser
        self.client._shutdown_if_idle()
        self.assertIsNone(self.client._page)
        self.assertIsNone(self.client._browser)
        self.assertTrue(browser.closed)

    def test_nothing_to_close_is_not_an_error(self):
        self.client._shutdown_if_idle()
        self.assertIsNone(self.client._page)


class FailureTeardownTests(unittest.TestCase):
    def tearDown(self):
        self.client._executor.shutdown(wait=False)

    def test_a_failed_fetch_replaces_the_whole_browser(self):
        """Both attempts must tear the browser down, not just the context.

        Leaving the browser installed is what made the outage permanent, so the
        client must end with no browser for the next call to launch a fresh one.
        """
        self.client = _BrowserClient()
        browser = FakeBrowser()
        self.client._browser = browser
        self.client._pw = None
        attempts = []

        def fail():
            attempts.append(1)
            raise RuntimeError("target closed")

        self.client._ensure_page = fail
        with self.assertRaises(RuntimeError):
            self.client._get_json({"root": "CL"})
        self.assertEqual(len(attempts), 2, "both attempts should run")
        self.assertIsNone(self.client._browser, "browser must not survive a failure")
        self.assertTrue(browser.closed, "the crashed browser should be closed")


if __name__ == "__main__":
    unittest.main()
