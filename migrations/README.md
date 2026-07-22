# Database migrations

Run `alembic upgrade head` before starting the API or worker. The baseline
revision adopts databases created by the pre-migration MVP using SQLAlchemy's
idempotent `create_all`; every schema change after the baseline must use
explicit Alembic operations.
