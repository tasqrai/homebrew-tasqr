# homebrew-tasqr

[![brew install tasqrai/tasqr/tasqr-mcp](https://img.shields.io/badge/brew%20install-tasqrai%2Ftasqr%2Ftasqr--mcp-informational?logo=homebrew&logoColor=white)](#install)
[![update formula](https://github.com/tasqrai/homebrew-tasqr/actions/workflows/update-formula.yml/badge.svg)](https://github.com/tasqrai/homebrew-tasqr/actions/workflows/update-formula.yml)
[![PyPI](https://img.shields.io/pypi/v/tasqr-mcp?label=tasqr-mcp)](https://pypi.org/project/tasqr-mcp/)

Homebrew tap for [Tasqr](https://tasqr.ai) — task state management for AI agents.

## Install

```bash
brew tap tasqrai/tasqr
brew trust --tap tasqrai/tasqr
brew install tasqr-mcp
```

That puts the `tasqr-mcp` MCP server on your PATH. It runs as a local stdio process
that reads your API key from `~/.config/tasqr/credentials` and proxies tool calls to
Tasqr, so your MCP client config holds no secrets.

Homebrew is one of three ways to get the same server. If you'd rather not add a tap,
`uvx tasqr-mcp` ([Python](https://github.com/tasqrai/tasqr-mcp-python)) and
`npx tasqr-mcp` ([Node](https://github.com/tasqrai/tasqr-mcp-node)) need no install
step at all.

## First run

Run it once in a terminal before wiring it into a client:

```bash
tasqr-mcp
```

With no API key on disk it starts GitHub device-flow signup: it opens your browser,
copies the device code to your clipboard to paste in, and asks which workspace to use
if your account has more than one. It then writes the credentials file and starts
serving; press Ctrl-C to exit.

Signup is interactive, so it only runs when stdin is a terminal. An MCP client
launching the server headlessly with no key on disk will exit and tell you to do this
first. Its message names `uvx tasqr-mcp`; with the Homebrew install, plain
`tasqr-mcp` is the equivalent.

## Credentials file

Device-flow signup writes this for you, so you only need it if you'd rather set the key
up by hand, or you're adding a second profile:

```
~/.config/tasqr/credentials
```

```ini
[default]
api_key = tasqr_abc123...
```

It's written `0600` (owner read/write only), inside a directory tightened to `0700` so
the filenames aren't exposed either. Grab a key from [tasqr.ai](https://tasqr.ai) if
you'd rather not go through device flow.

The same file carries the optional settings — extra `[profile]` sections, `log_path`,
and `kms_key_id` for client-side encryption (BYOK). Those are documented in full in the
[client README](https://github.com/tasqrai/tasqr-mcp-python#credentials), which the
Homebrew build behaves identically to.

## MCP client config

```json
{
  "mcpServers": {
    "tasqr": {
      "command": "tasqr-mcp"
    }
  }
}
```

## Upgrading

```bash
brew update && brew upgrade tasqr-mcp
```

## Uninstalling

```bash
brew uninstall tasqr-mcp
brew untap tasqrai/tasqr
```

Your credentials are left in place. Delete `~/.config/tasqr/credentials` to remove
them too.

## Configuration

The formula wraps the [`tasqr-mcp` sdist from PyPI](https://pypi.org/project/tasqr-mcp/)
in its own virtualenv, so it shares nothing with any Python you have installed and
behaves identically to the `uvx` and `npx` builds. Profiles, alternate servers,
logging, and client-side encryption (BYOK) are documented in the
[client README](https://github.com/tasqrai/tasqr-mcp-python#environment-variables).

## Troubleshooting

**`Refusing to load formula ... from untrusted tap`**

Homebrew 6 will not load a formula from a third-party tap until you trust it. This is
the `brew trust` line in [Install](#install); run it and retry:

```bash
brew trust --tap tasqrai/tasqr
```

## Security

Please don't open a public issue for a security problem. Use GitHub's private
vulnerability reporting instead: **Security** tab → **Report a vulnerability**.
