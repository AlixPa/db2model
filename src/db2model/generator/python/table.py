import re

from db2model.models import TableDef, TableImport
from db2model.types import SqlDialect

from .utils import _python_table_name


def _fix_cross_schema_foreign_key_postgres(raw_str: str, default_schema: str) -> str:
    lines: list[str] = list()
    fk_line_re = re.compile(r"ForeignKeyConstraint\(\[[^\]]*\],\s*\[([^\]]*)\]")
    target_re = re.compile(r"'([^']+)'")
    no_schema_re = re.compile(r"^[^.]+\.[^.]+$")

    for line in raw_str.split("\n"):
        foreign_match = fk_line_re.search(line)
        if not foreign_match:
            lines.append(line)
            continue

        targets_block = foreign_match.group(1)
        targets = target_re.findall(targets_block)

        fixed_targets = []
        for t in targets:
            if no_schema_re.match(t):
                fixed_targets.append(f"{default_schema}.{t}")
            else:
                fixed_targets.append(t)

        new_block = ", ".join(f'"{t}"' for t in fixed_targets)
        lines.append(
            line[: foreign_match.start(1)] + new_block + line[foreign_match.end(1) :]
        )

    return "\n".join(lines)


def _get_table_code(
    imports_raw_text: str,
    table_def: TableDef,
    sql_dialect: SqlDialect,
    default_schema: str | None = None,
) -> str:
    match sql_dialect:
        case SqlDialect.POSTGRESQL:
            if not default_schema:
                raise ValueError("Need to provide a default schema for postgresql.")
            return (
                imports_raw_text
                + "\n"
                + _get_table_imports_code(table_def)
                + "\n"
                + _fix_cross_schema_foreign_key_postgres(
                    table_def.raw_str, default_schema
                )
            )
        case _:
            raise ValueError(
                f"No support yet for the {settings.db_settings.sql_dialect=}"
            )


def _group_table_per_name(tables_def: list[TableDef]) -> dict[str, list[TableDef]]:
    name_to_tables_def_map: dict[str, list[TableDef]] = dict()

    for table_def in tables_def:
        name_to_tables_def_map.setdefault(table_def.table_name, list()).append(
            table_def
        )

    return name_to_tables_def_map


def _fusion_tables(table_name: str, tables_def: list[TableDef]) -> TableDef:
    if not tables_def:
        raise ValueError(f"No table_def given for {table_name}.")

    table_name = tables_def[0].table_name
    schema_name = tables_def[0].schema_name

    relation_ships: set[str] = set()

    for table_def in tables_def:
        if table_def.table_name != table_name:
            raise ValueError(
                f"Table def table name is different from the others {table_name=}, {table_def.table_name}."
            )
        if table_def.schema_name != schema_name:
            raise ValueError(
                f"Table def schema name is different from the others {table_name=} {schema_name=}, {table_def.schema_name}."
            )
        splits = table_def.raw_str.split("\n")
        for line in splits:
            if "] = relationship(" in line:
                relation_ships.add(line)

    raw_str = tables_def[0].raw_str
    for relation_ship in relation_ships:
        if relation_ship not in raw_str:
            raw_str = raw_str + "\n" + relation_ship

    return TableDef(
        raw_str=raw_str,
        table_name=table_name,
        schema_name=schema_name,
    )


def _get_python_name_to_table_def_map(
    tables_def: list[TableDef],
) -> dict[str, TableDef]:
    python_name_to_table_def_map: dict[str, TableDef] = dict()
    for table_def in tables_def:
        python_name_to_table_def_map[_python_table_name(table_def.table_name)] = (
            table_def
        )
    return python_name_to_table_def_map


def _fill_table_imports(
    table_def: TableDef, python_name_to_table_def_map: dict[str, TableDef]
) -> None:
    tables_to_import_python_names: set[str] = set()
    splits = table_def.raw_str.split("\n")

    for split in splits:
        if "] = relationship(" in split:
            relationship_match = re.search(r"relationship\(\s*'([^']+)'", split)
            if not relationship_match:
                raise ValueError(
                    f"Problem during python file generation, could not find relationship table name. {split=}"
                )
            tables_to_import_python_names.add(relationship_match.group(1))

    for python_table_name in tables_to_import_python_names:
        if not python_table_name in python_name_to_table_def_map:
            raise ValueError(f"Could not find table def. {python_table_name=}")
        table_def_to_import = python_name_to_table_def_map[python_table_name]
        table_def.imports.append(
            TableImport(
                schema_name=table_def_to_import.schema_name,
                table_name=table_def_to_import.table_name,
            )
        )


def _set_table_default_none(table_def: TableDef) -> None:
    lines: list[str] = list()
    nullable_lines: list[str] = list()
    not_nullable_lines: list[str] = list()
    for line in table_def.raw_str.split("\n"):
        column_match = re.search(r"^ {4}([a-z_]+):", line)
        if column_match:
            if "Mapped[Optional" in line and ", server_default=" not in line:
                nullable_lines.append("    " + line.strip()[:-1] + ",default=None)")
            else:
                not_nullable_lines.append(line)
        else:
            lines.append(line)
    table_def.raw_str = "\n".join(lines + not_nullable_lines + nullable_lines)


def _set_table_inits_false(
    table_def: TableDef, init_false_column_names: list[str]
) -> None:
    init_false_columns: set[str] = {cn for cn in init_false_column_names}
    for line in table_def.raw_str.split("\n"):
        if "PrimaryKeyConstraint(" in line:
            primary_match = re.search(r"PrimaryKeyConstraint\(\s*'([^']+)'", line)
            if not primary_match:
                raise ValueError(
                    f"Problem during python file generation, could not find primary key column name. {line=}"
                )
            init_false_columns.add(primary_match.group(1))
        if "ForeignKeyConstraint(" in line:
            foreign_match = re.search(r"ForeignKeyConstraint\(\s*\['([^',]+)'\]", line)
            if not foreign_match:
                continue  # Can happen due to multiple columns in foreign key
            init_false_columns.add(foreign_match.group(1))

    lines_to_init_false: set[str] = set()
    for line in table_def.raw_str.split("\n"):
        column_match = re.search(r"^ {4}([a-z_]+):", line)
        if not column_match:
            continue
        column_name = column_match.group(1)
        # Nullable column without default value
        if column_name in init_false_columns:
            lines_to_init_false.add(line)
            continue
        # Foreign parents to prevent typing issues
        if (
            "] = relationship(" in line
            and f"ForeignKeyConstraint(['{column_name}" not in table_def.raw_str
        ):
            lines_to_init_false.add(line)
            continue

    lines: list[str] = list()
    for line in table_def.raw_str.split("\n"):
        if line in lines_to_init_false:
            lines.append("    " + line.strip()[:-1] + ",init=False)")
        else:
            lines.append(line)
    table_def.raw_str = "\n".join(lines)


def _get_table_imports_code(table_def: TableDef) -> str:
    lines: list[str] = list()
    for table_import in table_def.imports:
        if table_import.schema_name:
            lines.append(
                f"from ..{table_import.schema_name} import {_python_table_name(table_import.table_name)}"
            )
        else:
            lines.append(
                f"from .{table_import.table_name} import {_python_table_name(table_import.table_name)}"
            )
    if lines:
        return "\n    ".join(["if TYPE_CHECKING:"] + lines)
    else:
        return ""
