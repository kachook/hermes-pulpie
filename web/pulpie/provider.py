"""Pulpie content extraction — plugin form.

Subclasses :class:`agent.web_search_provider.WebSearchProvider`. Uses the
``pulpie`` Python package (https://pypi.org/project/pulpie/) which defaults
to the ``pulpie-orange-small`` 210M encoder model.

Config keys this provider responds to::

    web:
      extract_backend: "pulpie"     # explicit per-capability
      backend: "pulpie"             # shared fallback

No API keys required. ``Extractor()`` auto-detects CUDA, Apple MPS, then CPU.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from agent.web_search_provider import WebSearchProvider

logger = logging.getLogger(__name__)

# Browser-like User-Agent to avoid 403 blocks (Wikipedia, etc.)
_USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
)

# ---- lazy import helpers ----


def _import_pulpie():
    import pulpie
    return pulpie


def _import_httpx():
    import httpx
    return httpx


class PulpieWebSearchProvider(WebSearchProvider):
    """Pulpie content extraction: local encoder model for HTML cleaning.

    Extraction-only provider. Does NOT implement search.
    """

    @property
    def name(self) -> str:
        return "pulpie"

    @property
    def display_name(self) -> str:
        return "Pulpie (local model)"

    def is_available(self) -> bool:
        """Return True when the ``pulpie`` package is importable.

        Does NOT pre-load the model — that happens on first ``extract()`` call.
        Must be cheap: called at tool-registration time and on every
        ``hermes tools`` paint.
        """
        try:
            _import_pulpie()
            _import_httpx()
            return True
        except ImportError:
            return False

    def supports_search(self) -> bool:
        return False

    def supports_extract(self) -> bool:
        return True

    def extract(self, urls: List[str], **kwargs: Any) -> List[Dict[str, Any]]:
        """Extract main content from one or more URLs via Pulpie.

        For each URL:
          1. Fetch raw HTML with httpx
          2. Run through ``pulpie.Extractor.extract()``
          3. Return cleaned Markdown (requires ``html2text`` for clean output)

        Returns a list of result dicts shaped for the legacy LLM
        post-processing pipeline. On per-URL failure, carries an ``error``
        field rather than raising.
        """
        try:
            pulpie = _import_pulpie()
            httpx = _import_httpx()
        except ImportError as exc:
            return [
                {
                    "url": u, "title": "", "content": "",
                    "error": f"pulpie package not installed: {exc}",
                }
                for u in urls
            ]

        # Warn if html2text is missing (pulpie silently returns raw HTML)
        try:
            import html2text  # noqa: F401
        except ImportError:
            logger.warning(
                "html2text not installed — pulpie will return raw HTML "
                "instead of clean Markdown. Fix: pip install html2text"
            )

        # Lazy-load the extractor once per call (model cached internally)
        try:
            extractor = pulpie.Extractor(max_tokens=2048, max_batch_tokens=4096)
        except Exception as exc:
            logger.warning("Pulpie Extractor init failed: %s", exc)
            return [
                {
                    "url": u, "title": "", "content": "",
                    "error": f"Pulpie model failed to load: {exc}",
                }
                for u in urls
            ]

        results: List[Dict[str, Any]] = []

        for url in urls:
            try:
                logger.info("Pulpie fetching: %s", url)
                resp = httpx.get(
                    url, timeout=30, follow_redirects=True,
                    headers={"User-Agent": _USER_AGENT},
                )
                resp.raise_for_status()
                html = resp.text

                # Extract title from raw HTML before pulpie strips <title>
                title = _extract_title(html)
                logger.info("Pulpie extracting: %s", url)
                result = extractor.extract(html)

                content = result.markdown or ""

                # Append cleanup savings footer
                raw_len = len(html)
                clean_len = len(content)
                if raw_len:
                    saved = round((1 - clean_len / raw_len) * 100, 1)
                    content += (
                        f"\n\n---\n"
                        f"*Pulpie extraction: {raw_len:,} → {clean_len:,} chars "
                        f"({saved}% saved)*\n"
                    )

                results.append({
                    "url": url,
                    "title": title,
                    "content": content,
                    "metadata": {"sourceURL": url, "title": title},
                })
            except httpx.HTTPError as exc:
                logger.warning("Pulpie HTTP error for %s: %s", url, exc)
                results.append({
                    "url": url, "title": "", "content": "",
                    "error": f"Failed to fetch {url}: {exc}",
                })
            except Exception as exc:  # noqa: BLE001
                logger.warning("Pulpie extract error for %s: %s", url, exc)
                results.append({
                    "url": url, "title": "", "content": "",
                    "error": f"Pulpie extract failed for {url}: {exc}",
                })

        return results

    def get_setup_schema(self) -> Dict[str, Any]:
        return {
            "name": "Pulpie (local model)",
            "badge": "free · local · GPU/CPU",
            "tag": (
                "Extraction via pulpie encoder model — no API key, "
                "auto-detects GPU. Install with `pip install pulpie html2text`."
            ),
            "env_vars": [],
            "post_setup": "pulpie",
        }


def _extract_title(html: str) -> str:
    """Extract the <title> from raw HTML without parsing the full DOM."""
    import re
    m = re.search(
        r"<title[^>]*>\s*(.*?)\s*</title>",
        html,
        re.IGNORECASE | re.DOTALL,
    )
    if m:
        return m.group(1).strip()
    return ""
