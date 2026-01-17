POSTGRES_TABLE_FILE_TEMPLATE = """from __future__ import annotations
import datetime
import uuid
from typing import Any

from sqlalchemy import ForeignKey
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
from sqlalchemy.orm import Mapped, mapped_column

from ...base import Base
"""
