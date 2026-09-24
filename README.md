# github-workflows

Reusable CI/PR/AI workflows for TokenLogic delivering repositories, called by short
caller files (see `callers/delivering-repo/`). This repository never talks to the
project board's API directly -- `board.py` in `board-app` is the only code that
reads or writes issues and the board. See `PLAN.md` for the design.

## Adding the callers to a delivering repository

Copy the four files from `callers/delivering-repo/` into the repository's own
`.github/workflows/`, replacing the placeholder `@000...0` refs with the commit SHA
of the reviewed `github-workflows` revision:

| Caller | Reusable workflow | Trigger |
|---|---|---|
| `ci.yml` | `foundry-ci.yml` | `pull_request`, push to `main` |
| `report.yml` | `report-comment.yml` | `workflow_run` on the `ci` workflow |
| `board.yml` | `pr-board.yml` (called twice, `command: pr-issue-check` / `command: pr-sync`) | PR opened/sync/reopened/edited (check), review requested/removed/submitted/dismissed and PR closed (sync) |
| `ai.yml` | `ai-comment.yml` | PR opened/synchronize (`kind: review`), issue opened (`kind: scope`) |

`General-Task` (the issues repository) instead takes only `callers/general-task-ai.yml`
for AI scope notes on newly opened issues; its board sync already lives in
`board-app/callers/general-task/issue-events.yml`.

Every caller passes `dry_run: true` in these examples; flip to `false` only for an
approved live window (Principle 4: dry mode is the default everywhere).

## GitHub App installation

The board App must be installed on **the caller repository, `General-Task`, and
`board-app`** -- `pr-board.yml` mints one token scoped to those three
(`repositories: <caller>,General-Task,board-app`) because it checks out
`board-app` with that same token. Installing on only the caller and
`General-Task` makes the `board-app` checkout fail authentication.
`github-workflows` is deliberately left off this list: `pr-board.yml` never
checks it out, and `create-github-app-token` fails outright if the App is not
installed on every repository named in `repositories:`, so listing a repo the
token never uses is a pure liability, not a safety margin.

`github-workflows` itself must still be a **public** repository: `ai-comment.yml`'s
`generate` job checks it out with the default job token (`permissions: {}`,
no App token -- kept isolated from the Anthropic secret on purpose) to fetch
`ai.py` at a pinned commit. That checkout only works on a public repo; a
private `github-workflows` would need a separate App-token-based checkout
path here, which this round does not add (it holds no secrets, only pinned
commit references, so public is the correct shape regardless).

## Secrets and variables the callers need

| Name | Kind | Used by |
|---|---|---|
| `ALCHEMY_API_KEY`, `QUICKNODE_TOKEN`, `QUICKNODE_ENDPOINT_NAME` | secrets (optional) | `ci.yml`, forwarded to the fork-RPC action |
| `BOARD_APP_ID` | repository/org variable | `board.yml`, minting the board App token |
| `BOARD_APP_PRIVATE_KEY` | repository/org secret | `board.yml`, minting the board App token |
| `ANTHROPIC_API_KEY` | secret, `backend: anthropic` only, private repos only | `ai.yml`, `generate` only |
| `TS_OAUTH_CLIENT_ID`, `TS_OAUTH_SECRET` | secrets, `backend: local` only | `ai.yml`, `generate` only, to join the tailnet |
| `LOCAL_LLM_URL` | secret, `backend: local` only | `ai.yml`, `generate` only, the llama.cpp endpoint |
| `LOCAL_LLM_MODEL` | repository/org variable, `backend: local` only | `ai.yml`, `generate` only |

Before use, replace the `ref: 0000...0` placeholders in `pr-board.yml` (board-app),
`ai-comment.yml` (this repo's own commit, for the `generate` job's pinned checkout),
and every caller's `@000...0` with the reviewed commit SHA of the relevant repository.

## Token scoping (`permission-*`)

`pr-board.yml` mints two different tokens depending on `command`:
- `pr-issue-check` (read-only): `permission-pull-requests: read`,
  `permission-issues: read`, `permission-contents: read`. It only reads
  `closingIssuesReferences` off the PR.
- `pr-sync`: **unscoped** (no `permission-*` inputs). board-app's own
  `issue-events.yml` documents why: the org-issue-fields permission it needs for
  `setIssueFieldValue` has no matching `permission-*` input on
  `actions/create-github-app-token@v3.2.0`, and specifying *some* `permission-*`
  inputs without all of them narrows the token to only the ones named -- so a
  partial scoping would silently break `pr-sync`. The installation itself is
  already the ceiling (`app-manifest.json` grants exactly five permissions).

`pr-issue-check` only runs (both in the `check` caller job and in `pr-board.yml`'s
`run` job) when the PR's base branch is the repository default branch; `pr-sync`
runs for every PR base regardless.

## Fork behaviour

- `foundry-ci.yml` runs on `pull_request`, which GitHub already denies secrets to for
  fork PRs; no extra gating needed.
- `pr-board.yml`'s job explicitly skips (`if:`) when the PR head repository is not
  this one, for both `pr-issue-check` and `pr-sync`.
- `ai-comment.yml`'s `collect` job skips the same way for `kind: review`, and the whole
  workflow only runs on private repositories (`github.event.repository.private`).
  Fork PRs to `pr-issue-check` are also excluded from the required-check bypass this
  implies -- a fork PR that never gets checked and a fork PR the App can't reach look
  identical from the branch-protection side. Accepted for this round.
- `report-comment.yml` is triggered by `workflow_run`, never `pull_request_target`, and
  never checks out or executes anything from the PR or the artifact. It binds the
  report to **trusted event fields only** (`workflow_run.head_sha`,
  `.head_repository.full_name`, `.event`, `.pull_requests[0].number`, falling back to
  a `repos/{repo}/commits/{sha}/pulls` lookup for forks where `pull_requests` is
  empty), looks up that PR's live `.head.sha`/`.head.repo.full_name` and requires both
  to match. The artifact's own `pr_number.txt`/`head_sha.txt` are read only to
  cross-check against those trusted values and reject on mismatch -- never to choose
  the comment's target. HTML comments are stripped from the report body so it cannot
  forge the `<!-- github-workflows-report -->` marker.

## AI comments

`ai-comment.yml` runs three jobs at different privilege levels: `collect` (reads the
diff or issue body, no Anthropic secret), `generate` (only the Anthropic secret, no
checkout of PR code, no GitHub token), `post` (the write token, no Anthropic secret).
`ai.py` treats its input as untrusted data wrapped inside the prompt, never as
instructions, and caps the model's output length; an empty model response fails the
run instead of posting a bare marker. The posted comment is a fixed header
("AI note (advisory, not a review)") followed by the model's text inside a fenced
`text` block, with `@` mentions zero-width-split and `<!--`/`-->`/backticks
neutralised so prompt-injected content can't forge markers, escape the fence, or
mention people.

Dedup/recency: `collect`'s gate and `post`'s dedup lookup both paginate
(`gh api --paginate | jq -rs`) and match only comments containing the hidden
`<!-- github-workflows-ai -->` marker, keyed off `updated_at` (the comment is
edited in place, not recreated) rather than `created_at`. A `concurrency` group per
PR/issue number serialises overlapping runs so two quick pushes can't both post.

### Backends

`ai-comment.yml` takes an input `backend`, `anthropic` (default) or `local`:

- `anthropic`: `generate` calls the Anthropic Messages API with `ANTHROPIC_API_KEY`.
  Unchanged from before.
- `local`: `generate` first joins the team tailnet (`tailscale/github-action`,
  pinned to a commit SHA) using an OAuth client (`TS_OAUTH_CLIENT_ID`/
  `TS_OAUTH_SECRET` secrets, tag `tag:ci`), then calls an OpenAI-compatible
  endpoint -- the team's llama.cpp server on a desktop machine, reached over
  Tailscale at `LOCAL_LLM_URL` (secret) with model `LOCAL_LLM_MODEL` (var) and
  `AI_MAX_TOKENS=4096` (the 27B reasoning model needs headroom for `<think>`
  output, which `ai.py` strips before posting). The Tailscale secrets and the
  local-LLM values are visible only to `generate`; `collect` and `post` never
  see them, and `generate` still runs with `permissions: {}` and no GitHub
  token -- joining the tailnet doesn't change that.

Tailnet ACL note: `tag:ci` is expected to be scoped in the tailnet's ACL to
reach only the desktop's port 8080, not the rest of the tailnet -- verify this
in the ACL before relying on it, this repository doesn't control it.

The `Join tailnet` step is deliberately the last step before `Run ai.py` in
`generate`, and no step in `generate` ever checks out or reads PR/issue
content (only the pinned `github-workflows` repo and the already-downloaded
`ai-input` artifact) -- `tailscaled` therefore only ever inherits that step's
own environment, never PR-controlled data or the Anthropic/local-LLM secrets,
which are scoped to the following `Run ai.py` step.

**Desktop off = the AI comment job fails; nothing else is affected.** The
local backend has no fallback to Anthropic -- if the desktop or its llama.cpp
server is unreachable, `generate` fails and no AI comment is posted, but
`ci`/`report`/`board` are independent workflows and keep working normally.

Run `ai.py` locally in dry mode (the default unless `DRY_RUN=0`):

```bash
DRY_RUN=1 python3 ai.py review path/to/diff.txt out.md
```

## Tests

```bash
python3 -B -m unittest test_ai -v
```

Workflow YAML is validated with `python3 -c "import yaml; yaml.safe_load(open(f))"`
over every file, plus a script asserting no `${{ }}` expression appears inside any
`run:` block. `actionlint` was not run (not installable in this environment -- no
`go`, and no outbound network access to fetch a release binary).

## Budget

`ai.py` is within its 80-line budget. The combined YAML (`.github/workflows/` +
`callers/`) is over the 340-line budget after this fix round -- see the fix-round
report for the exact count and why (the mandated B1/B3/B5/S3/S4/S5 fixes add real,
non-optional lines: trusted-event PR binding, per-command token scoping, paginated
dedup, output sanitisation). No security fix was cut to hit the line count.
