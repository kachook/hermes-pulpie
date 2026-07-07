"""Pulpie content extraction plugin for Hermes Agent.

Uses the ``pulpie`` Python package (Apache 2.0, model weights CC BY-NC 4.0)
to extract main content from raw HTML. The 210M-parameter encoder labels
every HTML block as content or boilerplate in a single forward pass.

Install::

    pip install git+https://github.com/kachook/hermes-pulpie.git
    hermes config set web.extract_backend pulpie
"""

from __future__ import annotations

from .provider import PulpieWebSearchProvider


def register(ctx) -> None:
    """Entry point — called by Hermes plugin loader."""
    ctx.register_web_search_provider(PulpieWebSearchProvider())
