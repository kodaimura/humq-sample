# HUMQ Flow

HUMQ の設計方針を、中規模の業務システムで検証するための B2B 受注・在庫・出荷管理サンプルです。

販売組織と取引先、商品・倉庫、調達、在庫台帳、受注、引当、出荷、返品、請求、入金までを一つの業務フローとして実装しています。データベースは認証を含む 42 テーブル、バックエンドの Python コードは 10,000 行以上で構成しています。

## 主な機能

- 組織、取引先、所属メンバー、住所の管理
- 商品カテゴリ、商品、取引先別単価、倉庫の管理
- 仕入先商品、発注点、補充提案、発注、分納、検品、入荷
- 在庫調整、倉庫別在庫、在庫台帳、倉庫間移動
- 受注登録、在庫引当、部分引当、キャンセル
- 出荷指示、出荷確定、追跡番号、受注・在庫への連動
- 返品可能数、返品承認、部分受入、再入庫・廃棄
- 出荷実績からの請求、請求発行、分割入金、入金配賦、売掛残高
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
    H["発注を承認"] --> I["分納を受入"]
    I --> B
    F --> J["返品を承認・受入"]
    J --> B
    F --> K["請求書を発行"]
    K --> L["入金を配賦"]
```

## HUMQ アーキテクチャ

HUMQ の責務は `Handler`、`Usecase`、`Module`、`Query` の4つです。Handler は必ず Usecase を入口とし、Module は原則として一つのテーブル、Query は複数テーブルを横断する読み取りを担当します。トランザクション境界は Usecase が所有します。

Usecase 責務内の共有部品は、先頭に `_` を付けて内部ファイルであることを示します。DB に依存しない判断・計算は `_policies.py`、Module や Query を使う共有業務処理は所有ドメインの `_operations.py` に置きます。Operation は呼び出し元 Usecase の Session を共有し、自身では commit を行いません。

```mermaid
flowchart LR
    UI["React Operations Console"] --> API["FastAPI Handler"]
    API --> UC["Usecase"]
    UC --> M1["Organization Module"]
    UC --> M2["Order Module"]
    UC --> M3["Inventory Module"]
    UC --> Q["Cross-table Query"]
    UC -.-> P["Usecase-internal Policy"]
    UC -.-> O["Usecase-internal Operation"]
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
- 発注の分納、返品の再入庫・廃棄、複数請求への入金配賦をトランザクション内で処理する
- Usecase 配下の Policy を DB なしで単体テストし、Usecase は判断結果を明示的に業務フローへ組み込む
- 組織ロールの共通認可を Operation として再利用し、トランザクション境界は呼び出し元 Usecase に保つ

## テーブル構成

| 領域 | テーブル | 数 |
| --- | --- | ---: |
| 認証 | `account`, `password_reset_token` | 2 |
| 組織 | `organization`, `organization_member`, `organization_address` | 3 |
| 商品 | `product_category`, `product`, `customer_product_price` | 3 |
| 在庫 | `warehouse`, `inventory_balance`, `inventory_ledger`, `inventory_adjustment`, `inventory_adjustment_item`, `inventory_transfer`, `inventory_transfer_item` | 7 |
| 受注 | `sales_order`, `sales_order_item`, `sales_order_status_history`, `stock_reservation` | 4 |
| 出荷 | `shipment`, `shipment_item`, `shipment_status_history` | 3 |
| 調達 | `supplier_product`, `reorder_policy`, `purchase_order`, `purchase_order_item`, `purchase_order_status_history`, `goods_receipt`, `goods_receipt_item`, `goods_receipt_status_history` | 8 |
| 返品 | `sales_return`, `sales_return_item`, `sales_return_status_history`, `return_receipt`, `return_receipt_item` | 5 |
| 請求 | `invoice`, `invoice_item`, `invoice_status_history`, `payment`, `payment_allocation` | 5 |
| 基盤 | `outbox_event`, `audit_log` | 2 |
| 合計 |  | **42** |

## 実装規模

- Python: 10,000 行以上（`api/app`、Alembic を含む）
- TypeScript / TSX: 約 3,700 行
- PostgreSQL: 42 テーブル
- Python 単体テスト: 54 件
- API E2E: 9 シナリオ

フロントエンドの画面数を増やすことではなく、サーバー側の業務ルール、状態遷移、排他制御、横断トランザクションを厚くする構成です。

## 開発環境

Docker があれば起動できます。

```sh
git clone https://github.com/kodaimura/humq-sample.git
cd humq-sample
make demo
```

`make demo` はイメージのビルド、マイグレーション、デモデータ投入、アプリケーション起動を順番に実行します。デモデータだけを再実行する場合は `make seed` を使用できます。seed は再実行可能で、投入済みの場合はデータを重複作成しません。

- ログインID: `demo@example.com`
- パスワード: `HumqDemo123!`
- 自社組織: `HUMQ Manufacturing`

- Web: http://localhost:3000
- API: http://localhost:8000/api
- OpenAPI: http://localhost:8000/docs
- Health: http://localhost:8000/health
- MailHog: http://localhost:8025

seed には商品・2倉庫の在庫、仕入先、顧客、発注・分納、倉庫移動、受注・引当・出荷、返品、請求・一部入金が含まれます。ログイン後、ヘッダーで `HUMQ Manufacturing` を選択すると、業務状態の異なるデータを各画面で確認できます。

データを完全に作り直す場合は、開発用DBボリュームを削除してから再投入します。

```sh
make down_volumes
make demo
```

## テスト

```sh
make check
make -C api test_e2e
make -C api routes
```

API の E2E テストは、アカウント作成から在庫調整、受注、部分引当、キャンセル、倉庫間移動、出荷確定に加え、補充提案、発注、分納、返品、請求、分割入金、売掛残高までを通して検証します。

## ディレクトリ

- `api/`: FastAPI、SQLAlchemy、Alembic、HUMQ の Module / Query / Usecase
- `web/`: React、TypeScript による業務コンソール

ベースプロジェクトは [webscaf](https://github.com/kodaimura/webscaf) の `fast-react` パターンを利用しています。
