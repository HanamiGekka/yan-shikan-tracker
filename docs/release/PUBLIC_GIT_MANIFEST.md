# Public Git Manifest

## Included

- Thin root launcher and `yan_shikan_tracker/` implementation package.
- `tests/` using synthetic fixtures and temporary directories.
- `sample_data/` with fictional workbooks, example configuration, and documentation.
- English, Simplified Chinese, Japanese and Traditional Chinese READMEs; AGENTS, CHANGELOG, ROADMAP and MIT LICENSE.
- Runtime and development requirements, Git text/binary rules, ignore rules, basic CI and the read-only README checker in `scripts/check_readmes.py`.
- Public manual testing instructions and release documentation under `docs/`.

## Excluded

- Runtime data, drafts, backups, generated reports, and charts.
- Local archives, personal notes, prompts, and private audit artifacts.
- Virtual environments, caches, IDE files, build output, and temporary files.

## Review Rules

Only explicitly reviewed public files may be staged. Check the staged diff and ignore rules before publishing. Samples must remain fictional. Inspect both the current tree and reachable commit history for secrets and private data. A public candidate requires passing automated tests, a human CLI smoke test, and no Critical or High privacy findings. Remote CI must pass before tagging a release.
