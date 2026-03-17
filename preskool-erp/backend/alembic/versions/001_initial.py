from alembic import op
import sqlalchemy as sa

from app.core.database import Base
from app.models import *  # noqa: F401,F403

revision = "001_initial"
down_revision = None
branch_labels = None
depends_on = None


def _rls_sql(table_name: str) -> None:
    op.execute(f"ALTER TABLE {table_name} ENABLE ROW LEVEL SECURITY;")
    op.execute(
        f"""
        CREATE POLICY tenant_isolation_{table_name}
        ON {table_name}
        USING (tenant_id = current_setting('app.current_tenant_id')::text);
        """
    )
    op.execute(
        f"""
        CREATE POLICY superadmin_all_{table_name}
        ON {table_name}
        USING (current_setting('app.is_superadmin', true)::boolean = true);
        """
    )


def upgrade() -> None:
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)
    if bind.dialect.name == "postgresql":
        for table_name in Base.metadata.tables:
            if table_name != "tenants":
                _rls_sql(table_name)


def downgrade() -> None:
    Base.metadata.drop_all(bind=op.get_bind())
