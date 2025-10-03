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
- Manual review of suspicious domains/IPs
- Compare start.elf / bootcode.bin hashes to known-good references (if available)
- Preserve original image in cold-storage
"""

def render_markdown(root: str, summary: Dict[str, Any], out_path: str):
    ensure_dir(Path(out_path).parent.as_posix())
    t = Template(MD_TEMPLATE)
    content = t.render(
        generated=summary.get("generated"),
        version=summary.get("version"),
        root=root,
        imaging=summary.get("imaging"),
        boot_files=summary.get("boot_files"),
        indicators=summary.get("indicators"),
        binwalk_summary=summary.get("binwalk_summary")
    )
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(content)
    return out_path

def render_html(md_path: str, out_path: str):
    # Minimal conversion using markdown (avoid adding dependency). Use simple conversion.
    try:
        import markdown
        with open(md_path, "r", encoding="utf-8") as fh:
            html = markdown.markdown(fh.read(), extensions=['tables'])
    except Exception:
        # fallback: wrap in <pre>
        with open(md_path, "r", encoding="utf-8") as fh:
            html = "<pre>" + fh.read() + "</pre>"
    ensure_dir(Path(out_path).parent.as_posix())
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(html)
    return out_path

