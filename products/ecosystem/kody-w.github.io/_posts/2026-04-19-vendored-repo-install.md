---
layout: post
title: "The vendored-repo install pattern"
date: 2026-04-19
tags: [engineering, packaging, distribution, cli-tools]
description: "A surprising number of CLI tools — nvm, pyenv, oh-my-zsh, asdf — install themselves the same way: clone the whole repository into a hidden directory in your home folder, drop a small wrapper on PATH, update by `git pull`. No package manager. No PyPI release. Just a Git clone. Here is why this pattern keeps re-emerging, when to use it, and what it gives up in exchange for simplicity."
---

If you have installed `nvm`, `pyenv`, `rbenv`, `asdf`, or `oh-my-zsh`, you have used a distribution pattern that almost no formal documentation explains and that almost everyone reaches for at some point. The pattern is: clone the entire project repository into a hidden directory in the user's home folder, drop a small wrapper script on the user's PATH, update by `git pull`. There is no PyPI package. There is no Homebrew formula (or if there is, it is a thin wrapper around the same Git clone). There is no "installer." There is `git clone` and a wrapper.

This pattern keeps re-emerging because for a certain kind of project — a CLI tool with multiple files, modest update cadence, and a small enough audience that a real release process feels heavy — it is the right answer. I have used it for several of my own tools, and every time I think *surely there is a more sophisticated way* and every time I come back to it.

This post is the pattern, why it works, what it gives up, and when to use it.

## The shape

Two scripts:

```bash
# install.sh — the thing the user pipes into bash
TOOL_HOME="$HOME/.toolname"
git clone --quiet --depth 1 https://github.com/me/toolname.git "$TOOL_HOME"

# Drop a wrapper on PATH
cat > "$HOME/.local/bin/toolname" <<'EOF'
#!/bin/bash
exec python3 "$HOME/.toolname/bin/toolname.py" "$@"
EOF
chmod +x "$HOME/.local/bin/toolname"
```

The wrapper is the only thing on PATH. It points at the cloned repository's entry point. Everything the tool needs lives in the clone — the entry script, supporting modules, configuration files, asset directories, all of it. The user never has to know the clone exists; they just type `toolname` and it runs.

That is the entire architecture.

## Why clone the whole repository, not just the script?

When users see this pattern for the first time, the immediate question is "why not just download the script?" If the tool's main entry point is one Python file, why pull in the whole project? Three reasons, in increasing order of importance.

**Dependencies travel together.** A tool that consists of a single self-contained script is rare. Most tools have an entry point plus a small library of supporting code, plus configuration files, plus example data, plus templates. Cloning the repository gets you all of those in one operation, in the right relative directory layout. Single-file download would require the user to fetch each supporting file separately, which is a per-version maintenance problem and also a "did you forget to download the template?" problem.

**Updates are a `git pull`.** The wrapper can check for updates by running `git pull` against the clone. There is no version metadata to manage. There is no upgrade endpoint to call. There is no package registry to publish to. You release a new version by pushing a commit. Users get the new version on their next invocation, or the next time they run `toolname update`, or whatever cadence the wrapper enforces. The release process for the maintainer is `git push`. That is dramatically simpler than the alternative.

**The result is hackable.** The user can `cd ~/.toolname && git diff` to see what they are running. They can edit a file to fix a bug locally. They can `git checkout` an older commit to revert a change. They can fork their local copy and add a feature, then send a pull request from their fork. The clone is *their copy of the project*, not a frozen-in-time download.

The third reason is the one I keep coming back to. A user who has the source code can debug their own problems. A user with a binary or a compiled wheel cannot. For a tool that is going to be used in unexpected environments — different operating systems, different shells, different network conditions — letting the user inspect and patch is enormously valuable. The cost is essentially zero.

## Why a hidden directory in `$HOME`?

The dot-prefix convention (`~/.toolname`, `~/.config/toolname`) is the standard Unix signal for "this is configuration or runtime state, not user content." Hidden directories don't show up in default `ls`. They don't clutter the home directory's visible contents. They are discoverable for users who want to find them — the wrapper points to it, `ls -a` shows it — and invisible for users who do not.

The home directory is the right place for this kind of state because it is per-user. The tool's state belongs to the user, not to the system. Putting it under `/usr/local` would require the user to be root for installation; putting it under `/opt` would require permission management. `$HOME` is the user's space, and a dot-prefixed subdirectory inside it is the user's tool.

For a tool that has *both* source code and runtime data — say, a tool that manages multiple environments, where each environment lives in its own subdirectory — the convention I use is to put the source code in a clearly-named subdirectory like `~/.toolname/_repo/`. The leading underscore signals "this is the runtime, not your data." Users browsing their tool's data can ignore `_repo/` cleanly.

## The wrapper

The wrapper script that goes on PATH is short:

```bash
#!/bin/bash
exec python3 "$HOME/.toolname/bin/toolname.py" "$@"
```

That is essentially it. The wrapper's job is:

1. Be on PATH.
2. Find the clone.
3. Pick the right interpreter.
4. Pass through all arguments.

A more sophisticated wrapper might check for updates periodically, check that the clone is still valid (not deleted, not corrupted), or pick between Python versions. None of that is necessary for the basic pattern to work.

The wrapper being so simple is what makes uninstall easy. If the user wants to remove the tool, they delete two things: the clone in `~/.toolname/` and the wrapper in `~/.local/bin/toolname`. Nothing else is left behind. No registry entries. No `~/.bashrc` lines. No daemon files. No package manager state. Clean install, clean uninstall.

## What this pattern is *not*

It is not a PyPI package. PyPI packages are right when:

- The tool is a library that other Python code imports, not a CLI.
- You need version compatibility with other packages (the dependency resolver is doing real work).
- Your audience expects to find tools through `pip install`.
- You have the bandwidth to maintain a release process and respond to packaging-environment bugs.

It is not a Homebrew formula. Homebrew is right when:

- Your tool needs to be installed system-wide, not per-user.
- You need to install on macOS at scale.
- You need binary dependencies (libpng, openssl) that Homebrew already manages.

It is not a single-file download. Single-file download is right when:

- The tool genuinely fits in one file with no external assets.
- The audience is sophisticated enough to manage updates themselves.
- The tool is small and self-contained.

The vendored-repo pattern is right when *none of the above apply*. You have a multi-file project. Your audience is small to medium. You don't want to be a packaging maintainer. You want updates to be `git push`. You want the user to have a hackable copy.

For this niche, vendored-repo is dramatically simpler than the alternatives, and the alternatives' benefits don't matter to your audience.

## What it gives up

To be honest about the trade.

**The user must have Git installed.** If they don't, the install script fails. For developer audiences, this is a non-issue. For non-developer audiences, you would need a different distribution pattern.

**You can't pin versions easily.** A `git pull` always brings the latest commit. If a user wants to be on a specific version, they have to know to `git checkout <tag>` after the install. This is fine for "always latest" tools and bad for "production-stable" ones.

**You can't ship binaries.** The whole tool has to be source code that runs from source. If your tool needs compiled artifacts, you need a different distribution channel for them, or you need to build them on the user's machine at install time.

**You bypass the system's package manager.** Some users will install your tool and then later wonder why it isn't showing up in `apt list` or `brew list`. The answer is "because it didn't come from there," but some users will find this confusing.

**Discoverability is harder.** Users find PyPI packages by searching PyPI. They find Homebrew formulas by searching Homebrew. There is no equivalent registry for vendored-repo tools; users find them through documentation, blog posts, or word of mouth.

For most of these, the cost is real but worth it for the audience this pattern targets. If you need to ship to non-developer users, or you need binary distribution, or you need version pinning to be a first-class concern, this is not the right pattern. For everything else, it is unreasonably effective.

## When this pattern is right

To make the boundary concrete: I use vendored-repo when all of the following are true.

- The tool is a CLI written in an interpreted language (Python, Ruby, Node, shell).
- Users are technical enough to have Git installed.
- The tool has multiple files (source plus templates plus configs).
- The audience is small enough that managing a real release process is overhead I do not want.
- "Update by `git pull`" is acceptable to my users.
- The tool benefits from being hackable.

When even one of those is not true, I use a different pattern. PyPI for libraries. Homebrew for system tools targeting macOS users. A signed binary distribution for tools targeting non-developers. Single-file download for tools that genuinely fit in one file.

The vendored-repo pattern is the right answer for the boring case where the tool is a moderate-sized CLI and you want shipping to be effortless. That case is more common than the package-manager-shaped distribution apparatus would suggest.

## The takeaway

When you ship a CLI tool with multiple files and you do not want to be a package maintainer, vendor the whole repository into a hidden directory in `$HOME`, drop a wrapper script on PATH that points at the right entry point, let updates be `git pull`, let uninstall be `rm`. The user has a complete, hackable copy of your project at all times. You release new versions by pushing a commit.

This is approximately what `nvm`, `pyenv`, `rbenv`, `oh-my-zsh`, and a dozen other "manage versions of $thing" tools do internally. They clone the underlying tool's repository, manage a wrapper that picks the right binary or script, and let the user override anything by editing files in the clone. None of them advertise this as their architecture; they all share it because it is the simple thing that works.

It is not glamorous. It is not what package managers want you to do. It is right for a project that is one `git push` away from a release, where the audience is technical, where the tool benefits from being hackable, and where you would rather spend your time on the tool than on a release engineering apparatus.

For the right kind of project, the vendored-repo pattern is the simplest possible way to ship. That simplicity is the leverage.
