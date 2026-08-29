#!/usr/bin/env python3
"""Fail if any pinned resource ships a compiled extension.

Homebrew builds every `resource` from its sdist. A resource with a C or Rust
extension therefore needs a compiler *on the user's machine* unless the formula
declares `depends_on "rust" => :build` and friends. CI never catches this on its
own, because GitHub's runners already have those toolchains installed: the build
goes green here and fails for the user.

PyPI's wheel tags settle it without building anything. A project that publishes
only `py3-none-any` wheels is pure Python; a platform-tagged wheel
(`cp314-cp314-macosx_11_0_arm64`) means compiled code.

The formula's four excluded dependencies are deliberately not resources at all -
they are Homebrew formulae named in `pypi_packages exclude_packages` - so a clean
run here means every resource really is pure Python. (Only cryptography and rpds-py
are compiled themselves; pydantic is excluded because it pulls in Rust pydantic-core,
and certifi so the CA bundle tracks brew. See the formula's notes.)
"""

import json
import pathlib
import re
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor

FORMULA = pathlib.Path(__file__).resolve().parents[2] / "Formula" / "tasqr-mcp.rb"
RESOURCE = re.compile(r'^  resource "([^"]+)" do\n    url "([^"]+)"', re.M)
PURE = ("-py3-none-any.whl", "-py2.py3-none-any.whl")


def pinned() -> list[tuple[str, str]]:
    """(name, version) for every resource, version taken from the sdist filename."""
    out = []
    for name, url in RESOURCE.findall(FORMULA.read_text()):
        filename = url.rsplit("/", 1)[-1]
        stem = re.sub(r"\.(tar\.gz|zip)$", "", filename)
        out.append((name, stem.rsplit("-", 1)[-1]))
    return out


def verdict(item: tuple[str, str]) -> tuple[str, str, str]:
    name, version = item
    url = f"https://pypi.org/pypi/{name}/{version}/json"
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            files = json.load(r)["urls"]
    except (urllib.error.HTTPError, urllib.error.URLError) as exc:
        return name, version, f"could not reach PyPI ({exc})"

    wheels = [f["filename"] for f in files if f["packagetype"] == "bdist_wheel"]
    if not wheels:
        # No wheel at all means no tag to read, so this cannot be cleared here.
        return name, version, "publishes no wheel, so its build cannot be verified"
    platform_specific = [w for w in wheels if not w.endswith(PURE)]
    if platform_specific:
        return name, version, f"ships a platform wheel ({platform_specific[0]})"
    return name, version, ""


def main() -> None:
    resources = pinned()
    if not resources:
        sys.exit("no resource blocks found - has Formula/tasqr-mcp.rb moved?")

    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(verdict, resources))

    problems = [(n, v, why) for n, v, why in results if why]
    for name, version, why in problems:
        print(f"::error::{name} {version} {why}")

    if problems:
        print(
            "\nEach of these needs either its own Homebrew formula "
            '(depends_on "<pkg>" => :no_linkage plus an entry in pypi_packages '
            "exclude_packages) or an explicit build dependency on the toolchain it "
            "needs. Leaving it as a plain resource means every user compiles it."
        )
        sys.exit(1)

    print(f"All {len(resources)} resources are pure Python.")


if __name__ == "__main__":
    main()
