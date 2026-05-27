# Git History Rewriting — `git-filter-repo`

Replaced `git filter-branch` as the standard tool for scrubbing secrets from git history.

## Why `git-filter-repo` over `git filter-branch`

| | `git filter-branch` | `git-filter-repo` |
|---|---|---|
| Speed (9600 commits) | 300s+ (times out) | < 1s |
| Safety check | Blocks on unstaged changes — including phantom changes from session restoration | Clean-tree check is reliable |
| Recursive delete | Requires `-r` flag, easy to forget | Default behavior |
| Backup refs | Creates `refs/original/` that must be manually cleaned | No stale refs |
| Reliability | Repeated "unstaged changes" errors even on clean trees | Deterministic |

## Installation

```bash
python3 -m pip install git-filter-repo --user
export PATH="$HOME/Library/Python/3.9/bin:$PATH"
```

## Usage

```bash
cd /path/to/repo
git status  # must be clean

# Remove specific files from all history
python3 -m git_filter_repo --path keys.txt --path pastes/ --invert-paths -f

# Remove a directory recursively
python3 -m git_filter_repo --path secrets/ --invert-paths -f

# Remove by glob
python3 -m git_filter_repo --path-glob '*.env' --invert-paths -f
```

## Verify

```bash
git log --all --full-history -- keys.txt   # nothing
git log --all --full-history -- pastes/    # nothing
```

## Force-push after scrubbing

```bash
git push fork --force --all
git push fork --force --tags
```

## Pitfall: Phantom unstaged changes

`git filter-branch` fails with "Cannot rewrite branches: You have unstaged changes" even on clean trees when background terminal sessions restore phantom state. Fix:

```bash
git stash drop
rm -rf .git-rewrite
git for-each-ref --format="delete %(refname)" refs/original/ | git update-ref --stdin
git status  # verify clean
```