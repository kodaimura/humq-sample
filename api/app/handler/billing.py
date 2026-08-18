from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.response import ApiResponse
from app.handler._dependency import get_account_id
from app.handler.dto.billing import *
from app.usecase.billing.reads import ListReceivablesUsecase
from app.usecase.billing.invoices import ChangeInvoiceStatusUsecase, GenerateInvoiceInput, GenerateInvoiceUsecase
from app.usecase.billing.payments import CreatePaymentInput, CreatePaymentUsecase, PaymentAllocationInput, PostPaymentUsecase


router = APIRouter(tags=["billing"])


@router.post("/shipments/{shipment_id}/invoices", response_model=InvoiceOperationResponse)
def generate_invoice(shipment_id: int, request: GenerateInvoiceRequest, response: Response, account_id: int = Depends(get_account_id), db: Session = Depends(get_db)):
    entity = GenerateInvoiceUsecase(db).execute(GenerateInvoiceInput(account_id=account_id, shipment_id=shipment_id, issue_date=request.issue_date, due_date=request.due_date))
    return ApiResponse.created(data=InvoiceOperationResponse(invoice=InvoiceResponse.model_validate(entity)), response=response)


@router.post("/invoices/{invoice_id}/issue", response_model=InvoiceOperationResponse)
def issue_invoice(invoice_id: int, request: InvoiceStatusRequest, response: Response, account_id: int = Depends(get_account_id), db: Session = Depends(get_db)):
    entity = ChangeInvoiceStatusUsecase(db).execute(account_id=account_id, invoice_id=invoice_id, action="issue", reason=request.reason)
    return ApiResponse.ok(data=InvoiceOperationResponse(invoice=InvoiceResponse.model_validate(entity)), response=response)


@router.post("/invoices/{invoice_id}/void", response_model=InvoiceOperationResponse)
def void_invoice(invoice_id: int, request: InvoiceStatusRequest, response: Response, account_id: int = Depends(get_account_id), db: Session = Depends(get_db)):
    entity = ChangeInvoiceStatusUsecase(db).execute(account_id=account_id, invoice_id=invoice_id, action="void", reason=request.reason)
    return ApiResponse.ok(data=InvoiceOperationResponse(invoice=InvoiceResponse.model_validate(entity)), response=response)


@router.get("/organizations/{organization_id}/receivables", response_model=ReceivablesResponse)
def receivables(organization_id: int, response: Response, account_id: int = Depends(get_account_id), db: Session = Depends(get_db)):
    rows = ListReceivablesUsecase(db).execute(
        account_id=account_id, organization_id=organization_id
    )
    return ApiResponse.ok(data=ReceivablesResponse(receivables=[ReceivableSummaryResponse.model_validate(row, from_attributes=True) for row in rows]), response=response)


@router.post("/organizations/{organization_id}/payments", response_model=PaymentOperationResponse)
def create_payment(organization_id: int, request: CreatePaymentRequest, response: Response, account_id: int = Depends(get_account_id), db: Session = Depends(get_db)):
    entity = CreatePaymentUsecase(db).execute(CreatePaymentInput(account_id=account_id, payee_organization_id=organization_id, **request.model_dump()))
    return ApiResponse.created(data=PaymentOperationResponse(payment=PaymentResponse.model_validate(entity)), response=response)


@router.post("/payments/{payment_id}/post", response_model=PaymentOperationResponse)
def post_payment(payment_id: int, request: PostPaymentRequest, response: Response, account_id: int = Depends(get_account_id), db: Session = Depends(get_db)):
    entity = PostPaymentUsecase(db).execute(account_id=account_id, payment_id=payment_id, allocations=[PaymentAllocationInput(**item.model_dump()) for item in request.allocations])
    return ApiResponse.ok(data=PaymentOperationResponse(payment=PaymentResponse.model_validate(entity)), response=response)
