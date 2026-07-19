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
hermes chat -q "Extract https://example.com and summarize"
```

Look for the `*Pulpie extraction: N → M chars (X% saved)*` footer on extracted content.

## How it works

When the agent calls `web_extract`, Hermes routes the URL through pulpie's pipeline:

1. **Fetch** — `httpx` GET with browser User-Agent
2. **Classify** — Pulpie encoder labels each HTML block as content or boilerplate in one forward pass
3. **Reconstruct** — keep only content-labeled blocks, drop nav/ads/footers
4. **Convert** — `html2text` renders clean Markdown for the LLM

For JS-heavy pages (SPAs, news sites), use the bundled `pulpie-browser` script — Playwright renders the page in headless Chromium first, then the same pipeline runs on the full DOM.

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

## Uninstall

Two install modes are possible (pip, or `hermes plugins install` / manual copy). Run the steps that match how you installed.

### 1. Reset the config (always)

```bash
hermes config set web.extract_backend ""
```

This stops Hermes from routing `web_extract` through Pulpie; new sessions fall back to the default backend.

### 2. Remove the plugin

If installed via `hermes plugins install`:

```bash
hermes plugins remove pulpie
```

If installed via pip:

```bash
~/.hermes/hermes-agent/venv/bin/pip uninstall -y hermes-pulpie
```

If installed manually (or left behind by the steps above), delete the directory directly:

```bash
rm -rf ~/.hermes/plugins/web/pulpie
```

### 3. Remove the browser script

`pulpie-browser` is standalone and is **not** removed by pip or `hermes plugins remove`:

```bash
rm -f ~/.hermes/scripts/pulpie-browser
```

### 4. Uninstall Python packages

Only `pulpie` and `html2text` are Pulpie-specific. **Do not uninstall `httpx`** — it is a core Hermes dependency used by many other tools (`hermes-agent`, `openai`, `ddgs`, etc.).

```bash
~/.hermes/hermes-agent/venv/bin/pip uninstall -y pulpie html2text
```

### 5. (Optional) Free the model weights

The ~421MB encoder cache is safe to delete:

```bash
rm -rf ~/.cache/huggingface/hub/models--feyninc--pulpie-orange-small
```

### 6. (Optional) Remove the project source

`~/hermes/projects/hermes-pulpie` is a git submodule of the main hermes repo. To remove the source checkout entirely:

```bash
cd ~/hermes && \
  git submodule deinit -f projects/hermes-pulpie && \
  git rm -f projects/hermes-pulpie && \
  rm -rf .git/modules/projects/hermes-pulpie
```

Skip this step if you only want to disable the plugin but keep the code.

### Verify

```bash
hermes config show | grep extract_backend   # should print nothing (empty)
hermes plugins list                          # pulpie should not appear
ls ~/.hermes/plugins/web/pulpie 2>&1         # "No such file or directory"
```

## License

Plugin code: MIT.  
Pulpie library: Apache 2.0.  
Pulpie model weights: CC BY-NC 4.0.
