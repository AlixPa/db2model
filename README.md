# db2model

Generate typed models from your database for Python, Go, and TypeScript.

## Features

- Database-first: generate from existing DB
- Typed output
- Customizable generation rules

## Generation supported

- python
  - postgresql

## Install

```bash
pip install db2model
```

## Quick start

It is strongly recommended to use the library within python script as it offers way more control than cli.

### Within a script

```python
import logging
from pathlib import Path

from db2model.config import Db2ModelSettings, DbSettings, PathSettings
from db2model.generator.python import generate_python_models
from db2model.types import SqlDialect

logging.basicConfig(level=logging.DEBUG)

logger = logging.getLogger()

db2model_settings = Db2ModelSettings(
    path_settings=PathSettings(
        output_python_models_path=Path(OUT_PY).resolve(),
        output_raw_path=Path(OUT_RAW).resolve(),
    ),
    db_settings=DbSettings(
        user="user",
        password="password",
        host="localhost",
        port=5432,
        db="my_db",
        default_schema="public",
        sql_dialect=SqlDialect.POSTGRESQL,
    ),
    globally_ignored_tables=[
        "_yoyo_log",
        "_yoyo_migration",
        "_yoyo_version",
        "yoyo_lock",
        "spatial_ref_sys",
    ],

    ## Specific to Postgresql
    schemas=["auth", "public", "schema1"],
    schema_to_ignored_tables_map={
        "auth": ["specific_table_of_auth"],
        "public": ["specific_table_of_public"],
        "schema1": [
            "specific_table_of_schema1",
            "other_specific_table_of_schema1",
        ],
    },

    ## Specific to python typing
    # These fields will not be arguments of the __init__ class function
    init_false_column_names=["created_at", "updated_at", "deleted_at"],
)

if __name__ == "__main__":
    generate_python_models(db2model_settings, logger)
```

Will generate

```text
OUT_RAW/
├── <...>.py
└── ...

OUT_PY/
├── __init__.py
├── auth/
│   ├── __init__.py
│   ├── table1.py
│   ├── ...
│   └── tableN.py
├── public/
│   └── ...
└── schema1/
    └── ...
```

### Using cli

Limited usage.

```bash
db2model generate \
  --db-url postgresql://user:pass@localhost:5432/mydb \
  --lang python \
  --output-path ./models
  ## To ignore tables
  --ignored-tables table_to_ignore1
  --ignored-tables table_to_ignore2
  --ignored-tables table_to_ignore3
  ## If dialect is postgresql you must provide the schemas targetted
  --schemas public
  --schemas my_schema1
```

## Example

Input table:
```sql
CREATE TABLE sessions (
    id UUID DEFAULT uuidv7(),
    user_id UUID NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at TIMESTAMPTZ NOT NULL,
    last_used_at TIMESTAMPTZ,
    revoked_at TIMESTAMPTZ,
    ip_address INET,
    user_agent TEXT,

    CONSTRAINT pk_sessions_id PRIMARY KEY (id),

    CONSTRAINT fk_sessions_users FOREIGN KEY (user_id)
        REFERENCES users (id)
        ON DELETE CASCADE
);

CREATE INDEX idx_sessions_expiresat
    ON sessions (expires_at);

CREATE INDEX idx_sessions_revokedat
    ON sessions (revoked_at);

CREATE INDEX idx_sessions_userid
    ON sessions (user_id);
```

Generated (Python):
```py
class Sessions(Base):
    __tablename__ = "sessions"
    __table_args__ = (
        ForeignKeyConstraint(
            ["user_id"], ["auth.users.id"], ondelete="CASCADE", name="fk_sessions_users"
        ),
        PrimaryKeyConstraint("id", name="pk_sessions_id"),
        Index("idx_sessions_expiresat", "expires_at"),
        Index("idx_sessions_revokedat", "revoked_at"),
        Index("idx_sessions_userid", "user_id"),
        {"schema": "auth"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, server_default=text("uuidv7()"), init=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, init=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(True), nullable=False, server_default=text("now()"), init=False
    )
    expires_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(True), nullable=False
    )
    user: Mapped["Users"] = relationship("Users", back_populates="sessions")
    last_used_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(True), default=None
    )
    revoked_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(True), default=None
    )
    ip_address: Mapped[Optional[Any]] = mapped_column(INET, default=None)
    user_agent: Mapped[Optional[str]] = mapped_column(Text, default=None)

```

## Roadmap

- Generate in GO & Typescript.
- Support other sql dialects.

## Limitations

- Two tables within the same database cannot have the same name.
- In python models, `init=False` is only applied to child tables if the column holding the foreign key starts with the name of the parent table;
  - If the parent table is `users` and the column is `user_id`, behaves as expected.
  - If the parent table is `users` and the column is `agent_id`, then `init=False` will not be applied.
- Does not support cross-db foreign constraint (neither SqlAlchemy though).

## License

MIT