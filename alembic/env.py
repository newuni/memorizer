from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

from app.db.base import Base
from app.models.memory import Memory  # noqa: F401
from app.models.api_key import ApiKey  # noqa: F401
from app.models.connector import Connector  # noqa: F401
from app.models.document import Document, DocumentChunk  # noqa: F401
from app.models.ingestion_job import IngestionJob  # noqa: F401
from app.models.audit_log import AuditLog  # noqa: F401
from app.models.admin_token import AdminToken  # noqa: F401
from app.models.event_log import EventLog  # noqa: F401
from app.models.governance_task import GovernanceTask  # noqa: F401
from app.models.tenant import Tenant  # noqa: F401
from app.models.tenant_namespace import TenantNamespace  # noqa: F401
from app.core.config import settings

config = context.config
config.set_main_option("sqlalchemy.url", settings.database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
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
