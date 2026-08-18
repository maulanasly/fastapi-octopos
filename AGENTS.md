# Agent Workflow

FastAPI OctoPOS: FastAPI + SQLAlchemy (pgvector) backend, Flutter client (`client/`),
Alembic migrations, PostgreSQL + Redis. Multi-tenant POS with RBAC, order tracking,
and pgvector semantic search.

## Environment

- **Dev stack**: `make docker-dev` runs postgres (`pgvector/pgvector:pg16`,
  host port `5433`, db `octopos`), redis (`6380`), and the backend container
  (`octopos-backend`, uvicorn `--reload`, source mounted). `make docker-dev-down`
  to stop. For production-like stack: `make docker-up` / `make docker-down`.
- **Local Python**: pyenv env `project-1` (Python 3.11). ruff binary:
  `~/.pyenv/versions/3.11.11/envs/project-1/bin/ruff`.
- **Flutter**: `~/.yusufm/development/flutter/bin/flutter` (see `client/`).

## Verification (run before any PR — mirrors CI)

| Step | Command | Notes |
|---|---|---|
| Lint | `pre-commit run --all-files --show-diff-on-failure` | ruff check+format, yaml, eof |
| Lint (fast) | `ruff check .` && `ruff format --check .` | same rules, no pre-commit overhead |
| Auto-fix | `make format` | `ruff check --fix .` then `ruff format .` |
| Backend tests | `make test` | needs local postgres on `:5433` (see below) |
| Coverage gate | `make check` | pytest with `--cov-fail-under=75` + compileall |
| Client | `make client-analyze client-test` | run when `client/` changes |

- Tests rebuild the schema from the real Alembic chain on every run against
  `octopos_test` (default `postgresql+psycopg://postgres:postgres@localhost:5433/octopos_test`,
  override with `TEST_DATABASE_URL`). Start postgres first:
  `docker compose up -d db` (init-test-db.sql creates `octopos_test`).
- CI (`.github/workflows/ci.yml`) runs the same gates on python 3.12 with
  `TEST_DATABASE_URL` pointing at its pgvector service. **Do not change the
  postgres image away from `pgvector/pgvector:pg16`** — migrations `CREATE EXTENSION vector`.

## Ruff rules (pyproject.toml `[tool.ruff]`)

- `select = ["E","F","I","B","UP"]`, `ignore = ["E501"]`, `line-length = 88`,
  `target-version = "py312"`. Do not weaken the rule set.
- FastAPI `Depends`/`Query`/etc. defaults are handled via
  `[tool.ruff.lint.flake8-bugbear] extend-immutable-calls` — add new DI helpers
  there instead of adding `noqa: B008`.
- `__init__.py`, migrations, and venvs are excluded (matches legacy `.flake8`).

## Backend conventions

- **Migrations**: create with `make makemigration MSG="..."`, apply on the dev
  stack with `docker compose exec backend alembic upgrade head`. Each test run
  re-applies the full chain, so new migrations are validated by `make test`.
- **RBAC**: new endpoints need a permission; register in `app/core/rbac.py`
  and gate via `require_permissions` (dependency helper in `app/api/dependencies.py`).
- **i18n**: user-facing messages go through `t()` in `app/core/i18n.py`.
- **Errors**: in `except` blocks always `raise ... from err` / `from None`
  (B904) — deliberate client-error responses use `from None`.
- **Types**: modern syntax only — `X | None`, `list[str]` (PEP 604/585), no
  `Optional`/`Union`/`typing` imports (UP rules).

## Git workflow

1. Branch off `origin/main` (fetch first): `git switch -c <scope>/<change>`.
2. Conventional commits (`feat:`, `fix:`, `chore:`, `docs:`, `test:`), one
   logical change per commit. Never commit secrets.
3. Before pushing: `pre-commit run --all-files`, `make test` (full suite, not
   just new tests), and client checks if `client/` changed.
4. Push and open a PR to `main` (`gh pr create --base main`) with a summary of
   changes + verification results. Wait for CI green; fix CI issues on the same
   branch (new commit), don't amend pushed commits.

## Client conventions

- `client/lib/features/<feature>/` for feature code; models, repos, controllers,
  screens separated. State via `ChangeNotifier`; dependency injection in
  `client/lib/app.dart`.
- Match tests: `client/test/<feature>_test.dart`; assert widget behavior with
  `pumpAndSettle`. Run `flutter analyze` clean + `flutter test` before merging.
