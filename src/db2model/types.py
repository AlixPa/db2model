from enum import Enum


class SqlDialect(str, Enum):
    POSTGRESQL = "POSTGRESQL"


class Language(str, Enum):
    PYTHON = "PYTHON"
