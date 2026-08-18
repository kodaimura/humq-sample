# HUMQ Flow API

HUMQ Flow の FastAPI バックエンドです。42 テーブルを使った受注・在庫・出荷・調達・返品・請求業務を、HUMQ の4責務である Handler、Usecase、Module、Query に分離しています。

純粋な業務ルールは独立した第5層ではなく、Usecase の内部実装として管理します。領域共通のルールは `app/usecase/<domain>/policies.py`、全領域共通のルールは `app/usecase/policies.py` に配置し、単一Usecaseでしか使わない処理はそのファイル内に残します。DB を使う複数 Module 共通処理は Usecase 配下の Operation とし、呼び出し元の Session を共有して commit は行いません。

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
```

Useful commands:

```sh
make logs
make exec
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
