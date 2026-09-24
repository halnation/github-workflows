# github-workflows

Reusable workflows called by a five-line file in each delivering repository. Budget: 300 lines YAML, 80 lines Python. Security rules: see the master plan.

## Files

| File | What |
|---|---|
| `.github/workflows/foundry-ci.yml` | `workflow_call`: `forge fmt --check`, build, tests with fork RPC (`aave-dao/action-rpc-env`), gas, coverage and size diffs (`aave-dao` actions pinned to a commit), reports written to `/tmp/content/*.txt` (the contract the report actions already use) and uploaded as one artifact with the PR number and head SHA. On push to the default branch it uploads the baseline coverage and size artifacts the diffs compare against. Job permissions: `contents: read` |
| `.github/workflows/report-comment.yml` | `workflow_call` for the caller's `workflow_run`: check the run's workflow, repository, conclusion, PR number and head SHA against the PR; download the artifact as data only; post or update one PR comment from a file. Never checks out code. Job permissions: `pull-requests: write`, `actions: read` |
| `.github/workflows/pr-board.yml` | `workflow_call`, input `command` (`pr-issue-check` on PR opened/synchronize/reopened/edited, `pr-sync` on review requested/removed, review submitted/dismissed, PR closed): fork-gated, mints an App token (owner, repositories: caller, `General-Task`, `board-app`, `github-workflows`; `pr-issue-check` scoped read-only with `permission-*` inputs, `pr-sync` unscoped -- org-issue-fields has no `permission-*` input) → checks out `board-app` at a pinned ref → runs `board.py "$command"` |
| `.github/workflows/ai-comment.yml` | `workflow_call`, input `kind` (`review` for a PR, `scope` for an issue). **Three jobs**: `collect` (`contents: read`, `pull-requests: read`) writes the PR diff or issue body to an artifact; `generate` (`permissions: {}`, no checkout of the PR, only the Anthropic secret) runs `ai.py` from this repository at a pinned ref and uploads `out.md`; `post` (`issues: write` or `pull-requests: write`, no Anthropic secret) posts `out.md` as one comment with a hidden marker, updated in place. The prompt tells the model the input is untrusted data; the post step caps the length and posts plain text only |
| `ai.py` | Read prompt template for `kind` + input file, one call to the Anthropic Messages API (urllib), write text to `out.md`. `DRY_RUN` writes a placeholder `out.md` and prints `{"would": "ai-call", ...}`. Model from env, default `claude-sonnet-5` |
| `prompts/review.md`, `prompts/scope.md` | The two prompts, plain text |
| `callers/delivering-repo/` | Complete callers for a delivering repository: `ci.yml` (pull_request, push to default branch), `report.yml` (workflow_run on ci, default branch), `board.yml` (pull_request review and close events), `ai.yml`; each with its permissions and forwarded secrets |
| `callers/general-task-ai.yml` | Example caller: AI scope questions on issue opened |
| `test_ai.py` | unittest: prompt assembly, dry mode, output file |

## Rules

- Every workflow sets `permissions:` explicitly; default is none.
- Third-party actions pinned to a full commit SHA.
- No secrets on pull requests from forks (`if: github.event.pull_request.head.repo.full_name == github.repository`).
- AI: one comment per PR per day (skip if a comment from the bot exists in the last 24 hours); private repositories only (`if: github.event.repository.private`).
- Board writes only through `board.py`; this repository never calls the project API itself.

## Tests

`test_ai.py` for `ai.py`. Workflows: `actionlint` if available, else YAML parse. Live: a test repository in `halnation` with the callers, run once in dry mode.
