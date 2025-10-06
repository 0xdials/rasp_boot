import hashlib
import os
import subprocess
import datetime
from pathlib import Path
from typing import List, Tuple

def now_timestamp() -> str:
    return datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")

def sha256_of_file(path: str, block_size: int = 65536) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(block_size), b""):
            h.update(block)
    return h.hexdigest()

def ensure_dir(path: str):
    Path(path).mkdir(parents=True, exist_ok=True)

def run_command(cmd: List[str], capture_output: bool = False, check: bool = True):
    """
    Safe subprocess wrapper. Returns (returncode, stdout).
    Does not use shell unless caller explicitly wraps.
    """
    proc = subprocess.run(cmd, stdout=subprocess.PIPE if capture_output else None,
                          stderr=subprocess.STDOUT, check=False)
    out = proc.stdout.decode("utf-8", errors="replace") if proc.stdout else ""
    if check and proc.returncode != 0:
        raise RuntimeError(f"Command {cmd} failed (rc={proc.returncode}):\n{out}")
    return proc.returncode, out

def list_files_recursive(root: str):
    p = Path(root)
    for fp in p.rglob("*"):
        yield str(fp)

