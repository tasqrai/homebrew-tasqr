#!/usr/bin/env python3
"""Point Formula/tasqr-mcp.rb at a given tasqr-mcp release on PyPI.

Rewrites only the top-level `url` and `sha256`. The `resource` blocks are
regenerated separately by `brew update-python-resources`, which is the only thing
that can resolve the dependency tree.
"""

import json
import pathlib
import re
import sys
import urllib.request

FORMULA = pathlib.Path(__file__).resolve().parents[2] / "Formula" / "tasqr-mcp.rb"
PYPI = "https://pypi.org/pypi/tasqr-mcp/json"


def sdist_for(version: str) -> tuple[str, str]:
    with urllib.request.urlopen(PYPI, timeout=30) as r:
        data = json.load(r)
    releases = data["releases"].get(version)
    if not releases:
        sys.exit(f"tasqr-mcp {version} is not on PyPI")
    for f in releases:
        if f["packagetype"] == "sdist":
            return f["url"], f["digests"]["sha256"]
    # Homebrew builds from the sdist; a wheel-only release cannot be packaged here.
    sys.exit(f"tasqr-mcp {version} has no sdist on PyPI")


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit("usage: bump_formula.py <version>")
    version = sys.argv[1]
    url, sha = sdist_for(version)

    text = FORMULA.read_text()
    # Anchor on the first occurrence only: the resource blocks below carry the same
    # two keys, and clobbering those would strand the formula on a broken tree.
    text, n_url = re.subn(r'^  url ".*"$', f'  url "{url}"', text, count=1, flags=re.M)
    text, n_sha = re.subn(r'^  sha256 ".*"$', f'  sha256 "{sha}"', text, count=1, flags=re.M)
    if n_url != 1 or n_sha != 1:
        sys.exit("could not find the formula's url/sha256 lines - has the file moved?")

    FORMULA.write_text(text)
    print(f"formula now points at tasqr-mcp {version}")


if __name__ == "__main__":
    main()
