# db2model

Generate typed models from your database for Python, Go, and TypeScript.

## Features

- Database-first: generate from existing DB
- Supported generated language: python
- Supported DBMS: postgresql
- Typed output
- Schema filtering
- Customizable generation rules

## Install

```bash
pip install db2model
```

## Quick start

```bash
db2model generate \
  --db postgresql://user:pass@localhost:5432/mydb \
  --lang python \
  --schema public \
  --out ./models
```

## Example

Input table:
```sql
CREATE TABLE users (
  id UUID PRIMARY KEY,
  email TEXT NOT NULL,
  created_at TIMESTAMP NOT NULL
);
```

Generated (Python):
```py
class User(Base):
    __tablename__ = "users"
    id: Mapped[UUID]
    email: Mapped[str]
    created_at: Mapped[datetime]
```

## Roadmap

- Generate in GO & Typescript.

## License

MIT