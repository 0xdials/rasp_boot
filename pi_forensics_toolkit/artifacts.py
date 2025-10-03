import json
import os
from pathlib import Path
from typing import Dict, List, Optional
from .utils import sha256_of_file, ensure_dir, run_command

EXPECTED_BOOT_FILES = ["start.elf", "bootcode.bin", "fixup.dat", "fixup_cd.dat", "config.txt"]

class ArtifactNotFound(Exception):
    pass

def find_image(root: str) -> Optional[str]:
    """
    Look for an image under root/images/ named *.img
    """
    images_dir = Path(root) / "images"
    if not images_dir.exists():
        return None
    for p in images_dir.glob("*.img"):
        return str(p)
    return None

def collect_boot_files(root: str, boot_mount: str) -> List[str]:
    """
    Return list of files (full paths) for files of interest in boot mount.
    """
    found = []
    for name in EXPECTED_BOOT_FILES:
        p = Path(boot_mount) / name
        if p.exists():
            found.append(str(p))
    # Also include any start*.elf or boot*.bin
    for p in Path(boot_mount).glob("start*.elf"):
        found.append(str(p))
    for p in Path(boot_mount).glob("boot*.bin"):
        found.append(str(p))
    return sorted(found)

def compute_hashes_for_files(file_paths: List[str], out_path: str) -> Dict[str, str]:
    ensure_dir(os.path.dirname(out_path))
    results = {}
    with open(out_path, "w") as fh:
        for p in file_paths:
            try:
                h = sha256_of_file(p)
            except FileNotFoundError:
                continue
            results[p] = h
            fh.write(f"{h}  {p}\n")
    return results

def load_binwalk_summary(root: str) -> Dict[str, dict]:
    """
    Load any binwalk JSON outputs under analysis/binwalk/.
    """
    out = {}
    bw_dir = Path(root) / "analysis" / "binwalk"
    if not bw_dir.exists():
        return out
    for p in bw_dir.glob("*.json"):
        try:
            with open(p, "r", encoding="utf-8") as fh:
                import json
                out[str(p)] = json.load(fh)
        except Exception:
            out[str(p)] = {"error": "failed to load"}
    return out

