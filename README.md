# Hermes Pulpie — Local Web Content Extraction

[Pulpie](https://huggingface.co/blog/feyninc/pulpie) backend for Hermes Agent's `web_extract` tool. Strips nav, ads, sidebars, and footers from HTML using a local 210M encoder model — **no API key needed**.

- Matches Dripper quality at 1/3 the size (0.862 vs 0.864 ROUGE-5 F1)
- Auto-detects GPU (CUDA/MPS) with CPU fallback
- ~80% token savings on typical pages

## Install

### Recommended: pip (handles dependencies)

```bash
pip install git+https://github.com/kachook/hermes-pulpie.git
hermes config set web.extract_backend pulpie
```

That's it. The plugin registers itself via pip entry point and `pyproject.toml` pulls in `pulpie`, `html2text`, and `httpx` automatically.

### Alternative: hermes plugins install

```bash
hermes plugins install kachook/hermes-pulpie --enable

# Install dependencies manually into the Hermes venv:
~/.hermes/hermes-agent/venv/bin/pip install pulpie html2text

# Configure:
hermes config set web.extract_backend pulpie
```

## Verify

```bash
hermes chat -q "Extract https://example.com and summarize" --yolo
```

Look for the `*Pulpie extraction: N → M chars (X% saved)*` footer on extracted content.

## Browser script

For JS-heavy pages (SPAs, news sites), render first via Playwright then clean:

```bash
~/.hermes/hermes-agent/venv/bin/python pulpie-browser https://www.msn.com/...
```

Requires `playwright` and Chromium: `pip install playwright && playwright install chromium`.

## Requirements

| Package | Why |
|---|---|
| `pulpie>=0.0.2` | The extraction model |
| `html2text` | Converts cleaned HTML → Markdown (without it, raw HTML is returned) |
| `httpx` | HTTP client for fetching URLs |

## License

Plugin code: MIT.  
Pulpie library: Apache 2.0.  
Pulpie model weights: CC BY-NC 4.0.
