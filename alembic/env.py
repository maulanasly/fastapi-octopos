from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

import app.models.customer  # noqa: F401 E402
import app.models.drawer  # noqa: F401 E402
import app.models.order  # noqa: F401 E402
import app.models.payment  # noqa: F401 E402
import app.models.product  # noqa: F401 E402
import app.models.promotion  # noqa: F401 E402
import app.models.purchase  # noqa: F401 E402
import app.models.refresh_token  # noqa: F401 E402
import app.models.refund  # noqa: F401 E402
import app.models.shift_reconciliation  # noqa: F401 E402
import app.models.stock_movement  # noqa: F401 E402
import app.models.user  # noqa: F401 E402

# Import app settings and all models so autogenerate can detect them
from app.core.config import settings  # noqa: F401 E402
from app.core.database import Base  # noqa: F401 E402

target_metadata = Base.metadata

# Override sqlalchemy.url from app settings so we don't duplicate config
config.set_main_option("sqlalchemy.url", settings.SQLALCHEMY_DATABASE_URI)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
