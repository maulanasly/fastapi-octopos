[Back to README](../README.md)

# Make Commands

| Command | Description |
|---------|-------------|
| `make help` | Show all available commands |
| `make install` | Install project dependencies from requirements.txt |
| `make run` | Run the API with uvicorn (host-side, reload) at http://127.0.0.1:8000 |
| `make dev` | Alias for `make run` |
| `make migrate` | Apply all database migrations (`alembic upgrade head`) |
| `make migrate-down` | Roll back the last migration |
| `make makemigration MSG="description"` | Autogenerate a new migration (rename the hex revision per AGENTS.md) |
| `make migration-history` | Show the applied migration history |
| `make migration-current` | Show the current migration revision |
| `make lint` | Run all pre-commit checks on every file |
| `make lint-changes` | Run pre-commit checks on changed files only (PR gate) |
| `make format` | Auto-fix and format with ruff (`ruff check --fix` + `ruff format`) |
| `make test` | Run the test suite with pytest (parallel xdist by default) |
| `make check` | Tests with coverage gate (`--cov-fail-under=75`) + compileall |
| `make check-changes` | Tests + coverage + compile on changed files only (PR gate) |
| `make pre-commit` | Install pre-commit git hooks |
| `make clean` | Remove Python cache files |
| `make client` | Run the Flutter client on Chrome (`--web-port=3001` for CORS) |
| `make client-test` | Run Flutter tests |
| `make client-analyze` | Run Flutter static analysis |
| `make docker-up` | Build & start the production-like stack (postgres + backend) |
| `make docker-down` | Stop the stack |
| `make docker-logs` | Follow backend logs |
| `make docker-ps` | Show running services |
| `make docker-migrate` | Run `alembic upgrade head` inside the backend container |
| `make docker-shell` | Open a shell in the backend container |
| `make docker-dev` | Start the dev stack (source mounted, granian `--reload`) |
| `make docker-dev-down` | Stop the dev stack |
| `make docker-dev-logs` | Follow backend logs (dev) |
| `make screenshots` | Regenerate `docs/images/` admin-panel screenshots (Playwright, seeded demo data; `BASE_URL` overridable) |
