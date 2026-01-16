from typing import Any

from sqlalchemy.dialects.postgresql import (
    BIGINT,
    BOOLEAN,
    CHAR,
    DATE,
    FLOAT,
    INET,
    INTEGER,
    JSONB,
    SMALLINT,
    TEXT,
    TIMESTAMP,
    UUID,
    VARCHAR,
)

from db2model.types import SqlDialect

TYPE_MAP: dict[SqlDialect, list[tuple[Any, str]]] = {
    SqlDialect.POSTGRESQL: [
        (BIGINT, "int"),
        (BOOLEAN, "bool"),
        (CHAR, "int"),
        (DATE, "datetime.datetime"),
        (FLOAT, "float"),
        (INET, "str"),
        (INTEGER, "int"),
        (JSONB, "dict"),
        (SMALLINT, "int"),
        (TEXT, "str"),
        (TIMESTAMP, "datetime.datetime"),
        (UUID, "uuid.UUID"),
        (VARCHAR, "str"),
    ]
}
