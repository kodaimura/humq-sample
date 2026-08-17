# HUMQ Flow

HUMQ の設計方針を、中規模の業務システムで検証するための B2B 受注・在庫・出荷管理サンプルです。

販売組織と取引先、商品・倉庫、在庫台帳、受注、引当、出荷までを一つの業務フローとして実装しています。データベースは認証を含む 24 テーブルで構成しています。

## 主な機能

- 組織、取引先、所属メンバー、住所の管理
- 商品カテゴリ、商品、取引先別単価、倉庫の管理
- 在庫調整、倉庫別在庫、在庫台帳、倉庫間移動
- 受注登録、在庫引当、部分引当、キャンセル
- 出荷指示、出荷確定、追跡番号、受注・在庫への連動
- 業務ダッシュボード、監査ログ、Outbox イベント

## 業務フロー

```mermaid
flowchart LR
    A["商品・倉庫を登録"] --> B["初期在庫を登録"]
    B --> C["受注を登録"]
    C --> D["倉庫在庫を引当"]
    D --> E["出荷指示を作成"]
    E --> F["出荷を確定"]
    F --> G["在庫・受注・台帳を更新"]
```

## HUMQ アーキテクチャ

書き込み処理は `Handler -> Usecase -> Module`、複数テーブルを横断する読み取りは `Query` に分離しています。Module は原則として一つのテーブルを担当し、トランザクション境界は Usecase が所有します。

```mermaid
flowchart LR
    UI["React Operations Console"] --> API["FastAPI Handler"]
    API --> UC["Usecase"]
    UC --> M1["Organization Module"]
    UC --> M2["Order Module"]
    UC --> M3["Inventory Module"]
    API --> Q["Cross-table Query"]
    M1 --> DB[(PostgreSQL)]
    M2 --> DB
    M3 --> DB
    Q --> DB
```

代表的な一連の処理で、以下を確認できます。

- 受注確定時に複数倉庫の利用可能在庫を検索し、引当を作成する
- 出荷確定時に引当を消し込み、実在庫と在庫台帳を同一トランザクションで更新する
- 受注・出荷の状態遷移履歴と監査ログを残す
- 外部連携用イベントを Outbox に保存する

## テーブル構成

| 領域 | テーブル | 数 |
| --- | --- | ---: |
| 認証 | `account`, `password_reset_token` | 2 |
| 組織 | `organization`, `organization_member`, `organization_address` | 3 |
| 商品 | `product_category`, `product`, `customer_product_price` | 3 |
| 在庫 | `warehouse`, `inventory_balance`, `inventory_ledger`, `inventory_adjustment`, `inventory_adjustment_item`, `inventory_transfer`, `inventory_transfer_item` | 7 |
| 受注 | `sales_order`, `sales_order_item`, `sales_order_status_history`, `stock_reservation` | 4 |
| 出荷 | `shipment`, `shipment_item`, `shipment_status_history` | 3 |
| 基盤 | `outbox_event`, `audit_log` | 2 |
| 合計 |  | **24** |

## 開発環境

Docker があれば起動できます。

```sh
make build
make up
make migrate
```

- Web: http://localhost:3000
- API: http://localhost:8000/api
- OpenAPI: http://localhost:8000/docs
- Health: http://localhost:8000/health
- MailHog: http://localhost:8025

サインアップ後、最初に `/organizations` で自社組織と取引先を作成してください。ヘッダーで自社組織を選ぶと、商品・在庫・受注・出荷の各画面を操作できます。

## テスト

```sh
make check
make -C api test_e2e
make -C api routes
```

API の E2E テストは、アカウント作成から在庫調整、受注、部分引当、キャンセル、倉庫間移動、出荷確定、ダッシュボード集計までを通して検証します。

## ディレクトリ

- `api/`: FastAPI、SQLAlchemy、Alembic、HUMQ の Module / Query / Usecase
- `web/`: React、TypeScript による業務コンソール

ベースプロジェクトは [webscaf](https://github.com/kodaimura/webscaf) の `fast-react` パターンを利用しています。
