# HUMQ Flow API

HUMQ Flow の FastAPI バックエンドです。42 テーブルを使った受注・在庫・出荷・調達・返品・請求業務を、HUMQ の4責務である Handler、Usecase、Module、Query に分離しています。

Policy と Operation は独立した層ではなく、Usecase 責務の内部実装です。純粋な共有ルールは `app/usecase/<domain>/_policies.py`、Module や Query を使う共有業務処理は所有ドメインの `_operations.py` に配置します。先頭の `_` は内部ファイルであることを示し、Operation は呼び出し元 Usecase の Session を共有して commit を行いません。

## Create a project

This scaffold supports direct cloning, GitHub's **Use this template**, and
generation through webscaf.

For a direct clone or a repository created from the GitHub template, clone it
using the intended project directory and initialize it once:

```sh
git clone <repository-url> my-app
cd my-app
make init
```

`make init` uses the current directory name. Override it when needed with
`make init PROJECT_NAME=another-name`. webscaf runs the same initialization
automatically. Skip initialization only when developing this scaffold itself.

## Development

This template is intended to run through Docker. Local Python and Node are not
required for normal development.

```sh
make build
make up
make migrate
make seed
```

From a fresh clone, `make demo` builds the images, migrates the database, loads
the demo dataset, and starts the application. The seed is development-only and
idempotent. Sign in with `demo@example.com` / `HumqDemo123!` and select
`HUMQ Manufacturing`.

Useful commands:

```sh
make logs
make exec
make seed
make demo
make check
make test
make test_e2e
make smoke
make routes
make requirements_compile
make down_volumes
```

API E2E tests are organized by domain so new endpoints can add coverage at the
same level. See [`test/e2e/README.md`](test/e2e/README.md).

Host ports are bound to `127.0.0.1` by default. Set `API_BIND_HOST=0.0.0.0`
only when the API must be reachable from outside the host.

Use production compose settings with `ENV=prod`.

```sh
cp .env.example .env
# Edit production secrets and database settings in .env.
make build ENV=prod
make migrate ENV=prod
make up ENV=prod
```

The development database is stored in the Docker named volume
`humq-sample2_postgres_data`.
