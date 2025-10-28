import json
from pathlib import Path
from jinja2 import Template
from typing import Dict, Any
from .utils import ensure_dir

MD_TEMPLATE = """# Pi Forensics Report

**Generated:** {{ generated }}

## Environment
- Toolkit version: {{ version }}
- Root: `{{ root }}`

## Imaging
{% if imaging %}
- Image file: `{{ imaging.image }}`  
- Image SHA256: `{{ imaging.sha256 }}`  
{% else %}
_No imaging artifacts found._
{% endif %}

## Boot partition inventory
{% if boot_files %}
| File | SHA256 |
|---|---|
{% for f, h in boot_files.items() %}
| `{{ f }}` | `{{ h }}` |
{% endfor %}
{% else %}
_No boot files found._
{% endif %}

## Baseline comparison (known-good vs observed)
{% if baseline_compare %}
| File | Status | Observed SHA256 | Expected SHA256 |
|---|---|---|---|
{% for f, rec in baseline_compare.items() %}
| `{{ f }}` | {{ rec.status }} | `{{ rec.observed }}` | `{{ rec.expected if rec.expected else "—" }}` |
{% endfor %}
{% else %}
_No baseline available or no boot files to compare._
{% endif %}

## Interesting indicators
{% if indicators %}
### Domains
{% for d,c in indicators.get('domains', [])[:50] %}
- `{{ d }}` — {{ c }}
{% endfor %}

### URLs
{% for u,c in indicators.get('urls', [])[:50] %}
- `{{ u }}` — {{ c }}
{% endfor %}

### IPs
{% for ip,c in indicators.get('ips', [])[:50] %}
- `{{ ip }}` — {{ c }}
{% endfor %}
{% else %}
_No indicators found._
{% endif %}

## Binwalk / Strings summary
{{ binwalk_summary or "_No binwalk summary present._" }}

## Next steps
- If any **mismatch**: confirm you’re comparing the right firmware version; re-image and re-hash.
- If any **unknown**: add expected hashes to the baseline once verified from the official source.
- Preserve the original image; share this report + `baseline_compare.json` for peer verification.
"""


def render_markdown(root: str, summary: Dict, out_path: str):
    ensure_dir(Path(out_path).parent.as_posix())
    t = Template(MD_TEMPLATE)
    content = t.render(
        generated=summary.get("generated"),
        version=summary.get("version"),
        root=root,
        imaging=summary.get("imaging"),
        boot_files=summary.get("boot_files"),
        baseline_compare=summary.get("baseline_compare"),
        indicators=summary.get("indicators"),
        binwalk_summary=summary.get("binwalk_summary"),
    )
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(content)
    return out_path


def render_html(md_path: str, out_path: str):
    try:
        import markdown

        with open(md_path, "r", encoding="utf-8") as fh:
            html = markdown.markdown(fh.read(), extensions=["tables"])
    except Exception:
        with open(md_path, "r", encoding="utf-8") as fh:
            html = "<pre>" + fh.read() + "</pre>"
    ensure_dir(Path(out_path).parent.as_posix())
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(html)
    return out_path
