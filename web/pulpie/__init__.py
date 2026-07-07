"""Pulpie content extraction plugin — user-installed web extract provider.

Uses the ``pulpie`` Python package (Apache 2.0 library, CC BY-NC 4.0 model
weights) to extract main content from raw HTML. The 210M-parameter encoder
labels every HTML block as content or boilerplate in a single forward pass.
"""

from __future__ import annotations

from .provider import PulpieWebSearchProvider


def register(ctx) -> None:
    """Register the Pulpie provider with the plugin context."""
    ctx.register_web_search_provider(PulpieWebSearchProvider())
