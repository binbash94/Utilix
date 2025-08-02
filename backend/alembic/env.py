import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parents[2]))  # adds /app to path

from sqlalchemy import create_engine
from alembic import context
from sqlmodel import SQLModel
from backend.app.models import user, parcel  # import models

config = context.config
target_metadata = SQLModel.metadata

def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata,
                      literal_binds=True, compare_type=True)
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    engine = create_engine(config.get_main_option("sqlalchemy.url"))
    with engine.connect() as connection:
        context.configure(connection=connection,
                          target_metadata=target_metadata,
                          compare_type=True)
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()


#For future model changes:
#alembic revision --autogenerate -m "desc" → alembic upgrade head.
#(Prod) run alembic upgrade head during deploy; don’t auto‑migrate on startup.