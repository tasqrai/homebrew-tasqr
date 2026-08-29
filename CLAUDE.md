# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A Homebrew tap with exactly one formula. There is no application source here — `Formula/tasqr-mcp.rb` wraps the `tasqr-mcp` **sdist from PyPI** in its own virtualenv. The proxy's behavior lives in `tasqr-mcp-python`; this repo only packages it.

That makes the tap strictly downstream: releasing is publish-to-PyPI first, then rebuild the formula against the new sdist. Nothing in this repo can change what the server does, and a bug in the proxy is never fixed here — it belongs in [`tasqr-mcp-python`](https://github.com/tasqrai/tasqr-mcp-python). A line-for-line Node port of the same server ships separately via `npx` ([`tasqr-mcp-node`](https://github.com/tasqrai/tasqr-mcp-node)); this tap does not package it.

| Path | What it is |
|---|---|
| `Formula/tasqr-mcp.rb` | The formula: pinned sdist URL + sha256, 26 generated `resource` blocks, 5 `depends_on` |
| `.github/workflows/update-formula.yml` | The bump bot — watches PyPI, rebuilds, verifies, pushes to `main` |
| `.github/scripts/bump_formula.py` | Repoints the formula's top-level `url`/`sha256` at a given version |
| `.github/scripts/check_pure_python.py` | The safety gate — fails if any resource ships a compiled extension |

## Commands

There is no test suite, linter, or formatter in this repo. Verification is Homebrew's own, and it needs macOS plus the tap symlinked into Homebrew's tree (Homebrew only reads formulae from inside `$(brew --repository)`, and since 6.0 refuses untrusted third-party taps):

```bash
mkdir -p "$(brew --repository)/Library/Taps/tasqrai"
ln -s "$PWD" "$(brew --repository)/Library/Taps/tasqrai/homebrew-tasqr"
brew trust --tap tasqrai/tasqr
```

The full release loop, which is also what CI runs step for step:

```bash
python3 .github/scripts/bump_formula.py <version>       # url + sha256 only
brew update-python-resources tasqrai/tasqr/tasqr-mcp    # regenerates every resource block
python3 .github/scripts/check_pure_python.py            # MUST run before install (see below)
brew audit --strict --online tasqrai/tasqr/tasqr-mcp
brew install --formula tasqrai/tasqr/tasqr-mcp && brew test tasqrai/tasqr/tasqr-mcp
```

`brew test` only asserts `tasqr-mcp --version` matches the formula version — it does not exercise the proxy. Real coverage lives in the Python repo's pytest suite.

## The pure-Python invariant

The formula's central constraint: **every `resource` must be pure Python**, so installing needs no compiler on the user's machine.

Four dependencies are deliberately *not* resources. Each is a Homebrew formula instead (`depends_on "x" => :no_linkage`) **and** named in `pypi_packages exclude_packages`. The reasons differ:

- `cryptography`, `rpds-py` — ship compiled extensions of their own.
- `pydantic` — pure Python itself, but pulls in `pydantic-core`, which is Rust. Excluding the parent stops `update-python-resources` walking into it.
- `certifi` — pure Python; taken as a formula so the CA bundle tracks `brew` instead of being pinned in this file.

Both halves are required. Drop `cryptography`, `pydantic`, or `rpds-py` from `exclude_packages` and the next `brew update-python-resources` vendors it — or its Rust core — back in as an sdist, and the build starts wanting `rust` + `maturin`.

CI cannot catch this by building, because GitHub's runners already ship Rust and Cargo — a compiled resource goes green there and only fails once it reaches a user with no toolchain. `check_pure_python.py` closes that hole by reading PyPI's wheel tags instead of building: a package publishing only `py3-none-any` wheels is pure, a platform-tagged wheel means compiled code. **It must run before `brew install`**, so a bad tree fails the run before anything is pushed.

A new pure-Python dependency needs nothing. A new *compiled* one needs its own Homebrew formula plus an `exclude_packages` entry — or an explicit build dependency on the toolchain, which pushes the cost onto users and should be a last resort.

## Editing the formula

- `bump_formula.py` rewrites only the **first** `url` / `sha256` in the file (`count=1`, `^  ` anchored at two-space indent). The resource blocks carry the same two keys at four-space indent; a rewrite that loses that anchoring strands the formula on a broken dependency tree. It exits non-zero if it can't find exactly one of each, so don't reindent the top-level pair.
- The version is not stored as a field — everything derives it by regex from the sdist filename in the `url`. The workflow's check job (`sed -n 's|.*/tasqr_mcp-\(.*\)\.tar\.gz".*|\1|p'`) and `check_pure_python.py`'s version parse both depend on the `<name>-<version>.tar.gz` shape.
- `depends_on "python@3.14"` is **not** automated. When Homebrew retires that formula the tap breaks with no warning; it takes a manual bump.
- Resource blocks are generated, never hand-edited — regenerate with `brew update-python-resources`.

## Releases are automated, not unreviewed

`update-formula.yml` commits straight to `main` (weekly Monday cron, `workflow_dispatch`, or a `tasqr-mcp-released` `repository_dispatch` that `tasqr-mcp-python` can fire after publishing). This is intentional: every release it reacts to already passed a human gate in `tasqr-mcp-python`, where publishing requires an explicit Actions run. `check_pure_python.py` stands in for the reviewer.

The cheap version check runs on Linux and gates a macOS job, so a quiet week costs almost nothing. If a run fails partway, `main` is still on the last known-good formula — recover by running the loop above by hand.
