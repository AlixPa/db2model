from sqlalchemy import Column as ALC_Column
from sqlalchemy.dialects.postgresql import CHAR, TIMESTAMP, UUID, VARCHAR

from db2model.models import Column
from db2model.types import SqlDialect

from .utils import _python_type


def _generate_column(col: ALC_Column) -> Column:
    return Column(
        name=col.name,
        nullable=bool(col.nullable),
        init=bool(col.primary_key or col.foreign_keys),
        alchemy_type=col.type,
        is_primary_key=col.primary_key,
        foreign_key_full_name=(
            list(col.foreign_keys)[0].target_fullname if col.foreign_keys else None
        ),
        python_type=_python_type(col),
    )


def _generate_column_code(column: Column, sql_dialect: SqlDialect) -> str:
    typ = column.python_type
    if column.nullable:
        typ = f"{typ} | None"

    args = []

    match sql_dialect:
        case SqlDialect.POSTGRESQL:
            alchemy_type_str = column.alchemy_type.__class__.__name__
            if isinstance(column.alchemy_type, UUID):
                args.append(f"{alchemy_type_str}(as_uuid=True)")
            elif isinstance(column.alchemy_type, TIMESTAMP):
                if column.alchemy_type.timezone:
                    args.append(f"{alchemy_type_str}(timezone=True)")
                else:
                    args.append(f"{alchemy_type_str}(timezone=False)")
            elif isinstance(column.alchemy_type, (VARCHAR, CHAR)):
                if column.alchemy_type.length:
                    args.append(
                        f"{alchemy_type_str}(length={column.alchemy_type.length})"
                    )
                else:
                    args.append(f"{alchemy_type_str}()")
            else:
                args.append(f"{alchemy_type_str}()")
        case _:
            raise ValueError(f"No support yet for the {sql_dialect=}")

    if column.foreign_key_full_name:
        args.append(f'ForeignKey("{column.foreign_key_full_name}")')

    if column.is_primary_key:
        args.append("primary_key=True")

    if column.nullable:
        args.append("nullable=True")
        args.append("default=None")
    else:
        args.append("nullable=False")

    if column.is_primary_key or column.foreign_key_full_name:
        args.append("init=False")

    arg_str = ", ".join(args)
    col_def = f"mapped_column({arg_str})"

    return f"{column.name}: Mapped[{typ}] = {col_def}"
