[Back to README](../README.md)

# Make Commands

| Command | Description |
|---------|-------------|
| `make help` | Show all available commands |
| `make install` | Install project dependencies from requirements.txt |
| `make run` | Run API server with hot reload at http://127.0.0.1:8000 |
| `make dev` | Alias for `make run` |
| `make migrate` | Apply all database migrations |
| `make migrate-down` | Rollback last migration |
| `make makemigration MSG="description"` | Create new migration with description |
| `make lint` | Run pre-commit code quality checks |
| `make format` | Auto-format code with black and isort |
| `make test` | Run test suite with pytest |
| `make pre-commit` | Install pre-commit git hooks |
| `make clean` | Remove Python cache files |
