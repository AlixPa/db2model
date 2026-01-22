from pathlib import Path

from db2model.models import TableDef
from db2model.types import SqlDialect

from .utils import _formate_code, _python_table_name


def _code_base_file() -> str:
    return "\n".join(
        [
            "from sqlalchemy.orm import DeclarativeBase, MappedAsDataclass",
            "",
            "class Base(MappedAsDataclass, DeclarativeBase):",
            "    pass",
            "",
        ]
    )


def _write_code_init_file(
    folder_path: Path, lines_import: list[str], lines__all__: list[str]
) -> None:
    lines: list[str] = list()
    lines.extend(lines_import)
    lines.append("__all__ = [")
    lines.extend(lines__all__)
    lines.append("]")
    with open(folder_path / "__init__.py", "w") as f:
        f.write(_formate_code("\n".join(lines)))


def _generate_all_init_files(
    python_rootpath: Path, tables_def: list[TableDef], sql_dialect: SqlDialect
) -> None:
    match sql_dialect:
        case SqlDialect.POSTGRESQL:
            schema_to_tables_map: dict[str, list[str]] = dict()
            for table_def in tables_def:
                schema_name = table_def.schema_name
                table_name = table_def.table_name
                if not schema_name:
                    raise ValueError(
                        f"Postgresql tables should have schema defined, {schema_name=}, {table_name=}."
                    )
                schema_to_tables_map.setdefault(schema_name, list()).append(table_name)

            lines_db_import: list[str] = list()
            lines_db__all__: list[str] = list()
            for schema_name, tables_name in schema_to_tables_map.items():
                if not tables_name:
                    continue

                lines_db_import.append(f"from .{schema_name} import (")

                lines_schema_import: list[str] = list()
                lines_schema__all__: list[str] = list()
                for table_name in tables_name:
                    python_table_name = _python_table_name(table_name)
                    lines_db_import.append(f"{python_table_name},")
                    lines_db__all__.append(f'"{python_table_name}",')
                    lines_schema_import.append(
                        f"from .{table_name} import {python_table_name}"
                    )
                    lines_schema__all__.append(f'"{python_table_name}",')

                lines_db_import.append(f")")

                folder_path = python_rootpath / schema_name
                folder_path.mkdir(parents=True, exist_ok=True)
                _write_code_init_file(
                    folder_path,
                    lines_schema_import,
                    lines_schema__all__,
                )

            if not lines_db_import:
                return

            folder_path = python_rootpath
            folder_path.mkdir(parents=True, exist_ok=True)
            _write_code_init_file(
                folder_path,
                lines_db_import,
                lines_db__all__,
            )

        case _:
            raise ValueError(
                f"No support yet for the {settings.db_settings.sql_dialect=}"
            )
