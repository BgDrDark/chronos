import datetime
import logging
from decimal import Decimal

import strawberry
from sqlalchemy import func, select

from backend.database import models
from backend.database.transaction_manager import atomic_transaction
from backend.exceptions import (
    AuthenticationException,
    NotFoundException,
    PermissionDeniedException,
    ValidationException,
    internal_server_error,
)
from backend.graphql import inputs, types
from backend.services.accounting_service import AccountingService

logger = logging.getLogger(__name__)
authenticate_msg = "Трябва да се автентикирате"

from backend.config import settings


@strawberry.type
class AccountingMutation:

    @strawberry.mutation
    async def create_invoice(
            self,
            invoice_data: inputs.InvoiceInput,
            info: strawberry.Info,
    ) -> types.Invoice:
        """Create a new invoice with items - atomic operation"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)

        from decimal import Decimal

        async with atomic_transaction(db) as tx:
            # Generate invoice number
            year = invoice_data.date.year
            prefix = "ВХ" if invoice_data.type == "incoming" else "ИЗХ"

            stmt = select(models.Invoice).where(
                models.Invoice.number.like(f"{prefix}-{year}-%"),
            ).order_by(models.Invoice.number.desc())
            res = await tx.execute(stmt)
            last_invoice = res.scalars().first()

            if last_invoice:
                last_num = int(last_invoice.number.split("-")[-1])
                new_num = last_num + 1
            else:
                new_num = 1

            invoice_number = f"{prefix}-{year}-{new_num:04d}"

            # Calculate totals
            subtotal = Decimal(0)
            for item in invoice_data.items:
                item_total = item.quantity * item.unit_price
                item_discount = item_total * (item.discount_percent / 100)
                item_total = item_total - item_discount
                subtotal += item_total

            discount_amount = subtotal * (invoice_data.discount_percent / 100)
            subtotal_after_discount = subtotal - discount_amount
            vat_amount = subtotal_after_discount * (invoice_data.vat_rate / 100)
            total = subtotal_after_discount + vat_amount

            # Create invoice
            invoice = models.Invoice(
                number=invoice_number,
                type=invoice_data.type,
                document_type=invoice_data.document_type,
                griff=invoice_data.griff,
                description=invoice_data.description,
                date=invoice_data.date,
                supplier_id=invoice_data.supplier_id,
                batch_id=invoice_data.batch_id,
                client_name=invoice_data.client_name,
                client_eik=invoice_data.client_eik,
                client_address=invoice_data.client_address,
                subtotal=subtotal,
                discount_percent=invoice_data.discount_percent,
                discount_amount=discount_amount,
                vat_rate=invoice_data.vat_rate,
                vat_amount=vat_amount,
                total=total,
                payment_method=invoice_data.payment_method,
                delivery_method=invoice_data.delivery_method,
                due_date=invoice_data.due_date,
                payment_date=invoice_data.payment_date,
                status=invoice_data.status,
                notes=invoice_data.notes,
                company_id=invoice_data.company_id,
                created_by=current_user.id,
            )

            tx.add(invoice)
            await tx.flush()

            # Create invoice items
            for item in invoice_data.items:
                item_total = item.quantity * item.unit_price
                item_discount = item_total * (item.discount_percent / 100)
                item_total = item_total - item_discount

                invoice_item = models.InvoiceItem(
                    invoice_id=invoice.id,
                    ingredient_id=item.ingredient_id,
                    batch_id=item.batch_id,
                    name=item.name,
                    quantity=item.quantity,
                    unit=item.unit,
                    unit_price=item.unit_price,
                    unit_price_with_vat=item.unit_price_with_vat,
                    discount_percent=item.discount_percent,
                    total=item_total,
                    expiration_date=datetime.datetime.strptime(item.expiration_date, "%Y-%m-%d").date() if item.expiration_date else None,
                    batch_number=item.batch_number,
                )
                tx.add(invoice_item)

                # Обнови цената на партидата от фактурата
                if item.batch_id:
                    batch = await tx.get(models.Batch, item.batch_id)
                    if batch:
                        batch.price_no_vat = float(item.unit_price)
                        batch.price_with_vat = float(item.unit_price_with_vat or item.unit_price * Decimal("1.2"))

            # Log the operation (inside transaction for atomicity)
            log_entry = models.OperationLog(
                operation="create",
                entity_type="invoice",
                entity_id=invoice.id,
                user_id=current_user.id,
                changes={"number": invoice.number, "type": invoice.type, "total": str(total), "status": invoice_data.status},
            )
            tx.add(log_entry)

            # Auto-create cash journal entry if paid in cash (inside transaction)
            if invoice_data.payment_method == "cash" and invoice_data.status == "paid":
                cash_entry = models.CashJournalEntry(
                    date=invoice_data.payment_date or invoice_data.date,
                    operation_type="expense" if invoice_data.type == "incoming" else "income",
                    amount=total,
                    description=f"Фактура {invoice.number}",
                    reference_type="invoice",
                    reference_id=invoice.id,
                    company_id=invoice.company_id,
                    created_by=current_user.id,
                )
                tx.add(cash_entry)

            # Auto-create accounting entries (inside transaction)
            company = await tx.get(models.Company, invoice.company_id)
            if company and invoice_data.status in ["paid", "sent"]:
                from backend.services.accounting_service import AccountingService
                accounting_service = AccountingService(tx)
                entries = await accounting_service.create_invoice_entries(invoice, company, current_user)
                if entries:
                    for entry in entries:
                        tx.add(entry)

        # Transaction committed here - all or nothing
        await db.refresh(invoice)
        return types.Invoice.from_pydantic(invoice)

    @strawberry.mutation
    async def update_invoice(
            self,
            id: int,
            invoice_data: inputs.InvoiceInput,
            info: strawberry.Info,
    ) -> types.Invoice:
        """Update an existing invoice - atomic operation"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)

        from decimal import Decimal

        invoice = await db.get(models.Invoice, id)
        if not invoice:
            raise NotFoundException.record("Invoice")

        if current_user.role.name != "super_admin" and invoice.company_id != current_user.company_id:
            raise PermissionDeniedException.for_action("manage")

        # READONLY check: paid, cancelled, and corrected invoices cannot be edited
        readonly_statuses = ["paid", "cancelled", "corrected"]
        if invoice.status in readonly_statuses:
            raise ValidationException(
                detail=f"Фактура с статус '{invoice.status}' е в READONLY режим и не може да се редактира. Платена/анулирана/коригирана фактура не може да се променя.",
            )

        # Validate status transition
        current_status = invoice.status
        new_status = invoice_data.status

        ALLOWED_TRANSITIONS = {
            "draft": ["sent", "paid", "cancelled"],
            "sent": ["paid", "cancelled"],
            "overdue": ["paid", "cancelled"],
            "corrected": [],  # No transitions from corrected
        }
        # NOTE: 'paid' and 'cancelled' are handled by the READONLY check above

        if new_status != current_status:
            allowed = ALLOWED_TRANSITIONS.get(current_status, [])
            if new_status not in allowed:
                allowed_text = ", ".join([f"'{s}'" for s in allowed]) if allowed else "няма"
                raise ValidationException.field(
                    "status",
                    f"Не може да промените статуса от '{current_status}' на '{new_status}'. Позволени: {allowed_text}",
                )

        async with atomic_transaction(db) as tx:
            # Re-fetch invoice inside transaction for consistency
            invoice = await tx.get(models.Invoice, id)

            # Special protection: accountant, head_accountant, and super_admin can cancel paid invoices
            if current_status == "paid" and new_status == "cancelled":
                if current_user.role.name not in ["super_admin", "head_accountant", "accountant"]:
                    raise PermissionDeniedException(
                        detail="Нямате права да анулирате платена фактура. За това действие са необходими права на счетоводител или по-високи.",
                    )
                # Log the cancellation of paid invoice
                log_entry = models.OperationLog(
                    operation="cancel_paid",
                    entity_type="invoice",
                    entity_id=invoice.id,
                    user_id=current_user.id,
                    company_id=current_user.company_id,
                    changes={
                        "number": invoice.number,
                        "previous_status": "paid",
                        "new_status": "cancelled",
                        "amount": str(invoice.total),
                        "role": current_user.role.name,
                    },
                )
                tx.add(log_entry)

            # Update basic fields
            invoice.type = invoice_data.type
            invoice.document_type = invoice_data.document_type
            invoice.griff = invoice_data.griff
            invoice.description = invoice_data.description
            invoice.date = invoice_data.date
            invoice.supplier_id = invoice_data.supplier_id
            invoice.batch_id = invoice_data.batch_id
            invoice.client_name = invoice_data.client_name
            invoice.client_eik = invoice_data.client_eik
            invoice.client_address = invoice_data.client_address
            invoice.discount_percent = invoice_data.discount_percent
            invoice.vat_rate = invoice_data.vat_rate
            invoice.payment_method = invoice_data.payment_method
            invoice.delivery_method = invoice_data.delivery_method
            invoice.due_date = invoice_data.due_date
            invoice.payment_date = invoice_data.payment_date
            invoice.status = invoice_data.status
            invoice.notes = invoice_data.notes

            # Calculate totals
            subtotal = Decimal(0)
            for item in invoice_data.items:
                item_total = item.quantity * item.unit_price
                item_discount = item_total * (item.discount_percent / 100)
                item_total = item_total - item_discount
                subtotal += item_total

            discount_amount = subtotal * (invoice_data.discount_percent / 100)
            subtotal_after_discount = subtotal - discount_amount
            vat_amount = subtotal_after_discount * (invoice_data.vat_rate / 100)
            total = subtotal_after_discount + vat_amount

            invoice.subtotal = subtotal
            invoice.discount_amount = discount_amount
            invoice.vat_amount = vat_amount
            invoice.total = total

            # Update items: delete old and create new (simpler approach)
            from sqlalchemy import delete
            await tx.execute(delete(models.InvoiceItem).where(models.InvoiceItem.invoice_id == id))

            for item in invoice_data.items:
                item_total = item.quantity * item.unit_price
                item_discount = item_total * (item.discount_percent / 100)
                item_total = item_total - item_discount

                invoice_item = models.InvoiceItem(
                    invoice_id=invoice.id,
                    ingredient_id=item.ingredient_id,
                    batch_id=item.batch_id,
                    name=item.name,
                    quantity=item.quantity,
                    unit=item.unit,
                    unit_price=item.unit_price,
                    unit_price_with_vat=item.unit_price_with_vat,
                    discount_percent=item.discount_percent,
                    total=item_total,
                    expiration_date=datetime.datetime.strptime(item.expiration_date, "%Y-%m-%d").date() if item.expiration_date else None,
                    batch_number=item.batch_number,
                )
                tx.add(invoice_item)

            # Log the operation
            log_entry = models.OperationLog(
                operation="update",
                entity_type="invoice",
                entity_id=invoice.id,
                user_id=current_user.id,
                changes={"number": invoice.number, "total": str(total), "status": invoice_data.status},
            )
            tx.add(log_entry)

            # Handle cash journal entry
            if invoice_data.payment_method == "cash" and invoice_data.status == "paid":
                existing_entry = await tx.execute(
                    select(models.CashJournalEntry).where(
                        models.CashJournalEntry.reference_type == "invoice",
                        models.CashJournalEntry.reference_id == invoice.id,
                    ),
                )
                existing = existing_entry.scalars().first()

                if not existing:
                    cash_entry = models.CashJournalEntry(
                        date=invoice_data.payment_date or invoice_data.date,
                        operation_type="expense" if invoice_data.type == "incoming" else "income",
                        amount=total,
                        description=f"Фактура {invoice.number}",
                        reference_type="invoice",
                        reference_id=invoice.id,
                        company_id=invoice.company_id,
                        created_by=current_user.id,
                    )
                    tx.add(cash_entry)
                else:
                    # Update existing cash entry
                    existing.amount = total
                    existing.date = invoice_data.payment_date or invoice_data.date
                    tx.add(existing)

            # Auto-create accounting entries when status changes to paid/sent
            company = await tx.get(models.Company, invoice.company_id)
            if company and invoice_data.status in ["paid", "sent"]:
                # Check if entries already exist
                existing_accounting = await tx.execute(
                    select(models.AccountingEntry).where(
                        models.AccountingEntry.invoice_id == invoice.id,
                    ),
                )
                existing_acct_entries = existing_accounting.scalars().all()

                if not existing_acct_entries:
                    from backend.services.accounting_service import AccountingService
                    accounting_service = AccountingService(tx)
                    entries = await accounting_service.create_invoice_entries(invoice, company, current_user)
                    if entries:
                        for entry in entries:
                            tx.add(entry)

        # Transaction committed here - all or nothing
        await db.refresh(invoice)
        return types.Invoice.from_pydantic(invoice)

    @strawberry.mutation
    async def create_invoice_from_batch(
            self,
            batch_id: int,
            info: strawberry.Info,
    ) -> types.Invoice:
        """Create an incoming invoice from a received batch"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)

        from decimal import Decimal

        batch = await db.get(models.Batch, batch_id)
        if not batch:
            raise NotFoundException.record("Batch")

        if current_user.role.name != "super_admin" and batch.ingredient.company_id != current_user.company_id:
            raise PermissionDeniedException.for_action("manage")

        # Get ingredient price
        ingredient = await db.get(models.Ingredient, batch.ingredient_id)
        unit_price = ingredient.current_price or Decimal(0)

        # Generate invoice number
        today = datetime.date.today()
        year = today.year
        prefix = "ВХ"

        stmt = select(models.Invoice).where(
            models.Invoice.number.like(f"{prefix}-{year}-%"),
        ).order_by(models.Invoice.number.desc())
        res = await db.execute(stmt)
        last_invoice = res.scalars().first()

        if last_invoice:
            last_num = int(last_invoice.number.split("-")[-1])
            new_num = last_num + 1
        else:
            new_num = 1

        invoice_number = f"{prefix}-{year}-{new_num:04d}"

        # Calculate totals
        subtotal = batch.quantity * unit_price
        vat_rate = Decimal("20.0")
        vat_amount = subtotal * (vat_rate / 100)
        total = subtotal + vat_amount

        # Create invoice
        invoice = models.Invoice(
            number=invoice_number,
            type="incoming",
            date=today,
            supplier_id=batch.supplier_id,
            batch_id=batch.id,
            subtotal=subtotal,
            discount_percent=Decimal(0),
            discount_amount=Decimal(0),
            vat_rate=vat_rate,
            vat_amount=vat_amount,
            total=total,
            status="draft",
            company_id=batch.ingredient.company_id,
            created_by=current_user.id,
        )

        db.add(invoice)
        await db.flush()

        # Create invoice item
        invoice_item = models.InvoiceItem(
            invoice_id=invoice.id,
            ingredient_id=batch.ingredient_id,
            batch_id=batch.id,
            name=ingredient.name,
            quantity=batch.quantity,
            unit=ingredient.unit,
            unit_price=unit_price,
            unit_price_with_vat=batch.price_with_vat,
            discount_percent=Decimal(0),
            total=subtotal,
            expiration_date=batch.expiry_date,
            batch_number=batch.batch_number,
        )
        db.add(invoice_item)

        # Обнови цената на партидата от фактурата
        batch.price_no_vat = float(unit_price)
        batch.price_with_vat = float(batch.price_with_vat or unit_price * Decimal("1.2"))

        await db.commit()
        await db.refresh(invoice)
        return types.Invoice.from_pydantic(invoice)

    @strawberry.mutation
    async def create_cash_journal_entry(
            self,
            input: inputs.CashJournalEntryInput,
            info: strawberry.Info,
    ) -> types.CashJournalEntryType:
        """Create a cash journal entry"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)


        entry = models.CashJournalEntry(
            date=input.date,
            operation_type=input.operation_type,
            amount=input.amount,
            description=input.description,
            reference_type=input.reference_type,
            reference_id=input.reference_id,
            company_id=input.company_id,
            created_by=current_user.id,
        )
        db.add(entry)

        # Log the operation
        log_entry = models.OperationLog(
            operation="create",
            entity_type="cash_journal",
            entity_id=0,  # Will be updated after flush
            user_id=current_user.id,
            changes={"amount": str(input.amount), "operation_type": input.operation_type},
        )
        db.add(log_entry)

        await db.commit()
        await db.refresh(entry)

        # Update log with actual ID
        log_entry.entity_id = entry.id
        await db.commit()

        return types.CashJournalEntryType.from_pydantic(entry)

    @strawberry.mutation
    async def generate_saft_file(
            self,
            info: strawberry.Info,
            company_id: int,
            year: int,
            month: int,
            saft_type: str | None = "monthly",
    ) -> types.SAFTFileResult:
        """Generate SAF-T XML file for Bulgarian NRA.

        Args:
            company_id: Company ID
            year: Year (e.g., 2026)
            month: Month (1-12)
            saft_type: 'monthly', 'annual', or 'on_demand'

        Returns:
            SAFTFileResult with XML content and validation results

        """
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)

        # Import SAF-T generator
        from backend.services.saft_generator import generate_saft_file as saft_generator

        try:
            result = await saft_generator(
                db=db,
                company_id=company_id,
                year=year,
                month=month,
                saft_type=saft_type,
            )

            return types.SAFTFileResult(
                xml_content=result["xml_content"],
                validation_result=types.SAFTValidationResult(
                    status=result["validation_result"]["status"],
                    errors=result["validation_result"].get("errors", []),
                    warnings=result["validation_result"].get("warnings", []),
                    is_valid=result["validation_result"].get("is_valid", False),
                ),
                period_start=result["period_start"],
                period_end=result["period_end"],
                file_size=result["file_size"],
                file_name=result["file_name"],
            )
        except Exception as e:
            raise internal_server_error(f"Error generating SAF-T file: {e!s}")

    @strawberry.mutation
    async def create_invoice_correction(
            self,
            original_invoice_id: int,
            correction_type: str,
            reason: str,
            correction_date: datetime.date,
            info: strawberry.Info,
            create_new_invoice: bool = False,
    ) -> types.InvoiceCorrection:
        """Create a credit or debit note for an invoice"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)

        # Permission check: accountant, head_accountant, super_admin
        allowed_roles = ["super_admin", "head_accountant", "accountant"]
        if current_user.role.name not in allowed_roles:
            raise PermissionDeniedException(
                detail="Нямате права да създавате корекции. За това действие са необходими права на счетоводител или по-високи.",
            )


        original_invoice = await db.get(models.Invoice, original_invoice_id)
        if not original_invoice:
            raise NotFoundException.record("Original Invoice")

        # Validate invoice can be corrected
        if original_invoice.status == "cancelled":
            raise ValidationException(
                detail="Не можете да коригирате тази фактура. Тя е анулирана.",
            )
        if original_invoice.status == "corrected":
            raise ValidationException(
                detail="Не можете да коригирате тази фактура. Тя вече е коригирана.",
            )
        if original_invoice.status == "paid":
            raise ValidationException(
                detail="Платена фактура не може да се коригира.",
            )

        # Validate correction type
        if correction_type not in ["credit", "debit"]:
            raise ValidationException(
                detail="Типът на корекцията трябва да бъде 'credit' или 'debit'.",
            )

        # Generate correction number: КР-{YEAR}-{NNN}
        year = correction_date.year
        last_correction = await db.execute(
            select(models.InvoiceCorrection)
            .where(
                models.InvoiceCorrection.company_id == current_user.company_id,
                func.extract("year", models.InvoiceCorrection.correction_date) == year,
            )
            .order_by(models.InvoiceCorrection.id.desc())
            .limit(1),
        )
        last_num = last_correction.scalar()
        next_num = 1 if not last_num else int(last_num.number.split("-")[-1]) + 1
        correction_number = f"КР-{year}-{next_num:04d}"

        # Calculate amounts based on correction type
        if correction_type == "credit":
            amount_diff = -original_invoice.subtotal
            vat_diff = -original_invoice.vat_amount
        else:  # debit
            amount_diff = original_invoice.subtotal
            vat_diff = original_invoice.vat_amount

        # Create correction
        correction = models.InvoiceCorrection(
            number=correction_number,
            original_invoice_id=original_invoice_id,
            type=correction_type,
            correction_type=correction_type,
            reason=reason,
            amount_diff=amount_diff,
            vat_diff=vat_diff,
            correction_date=correction_date,
            company_id=current_user.company_id,
            created_by=current_user.id,
        )

        db.add(correction)

        # Optionally create new invoice
        if create_new_invoice:
            # Generate invoice number
            prefix = "ИЗХ" if original_invoice.type == "outgoing" else "ВХ"
            year_inv = correction_date.year
            last_invoice = await db.execute(
                select(models.Invoice)
                .where(
                    models.Invoice.company_id == current_user.company_id,
                    models.Invoice.number.like(f"{prefix}-{year_inv}-%"),
                )
                .order_by(models.Invoice.id.desc())
                .limit(1),
            )
            last_inv_num = last_invoice.scalar()
            next_inv_num = 1 if not last_inv_num else int(last_inv_num.number.split("-")[-1]) + 1
            new_invoice_number = f"{prefix}-{year_inv}-{next_inv_num:04d}"

            new_invoice = models.Invoice(
                number=new_invoice_number,
                type=original_invoice.type,
                document_type=original_invoice.document_type,
                date=correction_date,
                client_name=original_invoice.client_name,
                client_eik=original_invoice.client_eik,
                client_address=original_invoice.client_address,
                subtotal=original_invoice.subtotal + amount_diff,
                vat_amount=original_invoice.vat_amount + vat_diff,
                total=(original_invoice.subtotal + amount_diff) + (original_invoice.vat_amount + vat_diff),
                vat_rate=original_invoice.vat_rate,
                status="draft",
                company_id=current_user.company_id,
                created_by=current_user.id,
            )
            db.add(new_invoice)
            correction.new_invoice = new_invoice

        # Mark original as corrected
        original_invoice.status = "corrected"

        # Create reverse accounting entries
        company = await db.get(models.Company, current_user.company_id)
        correction_entries = []
        if company:
            accounting_service = AccountingService(db)
            correction_entries = await accounting_service.create_correction_entries(
                correction=correction,
                invoice=original_invoice,
                company=company,
                created_by=current_user,
            )
            for entry in correction_entries:
                db.add(entry)

        # Log the operation
        log_entry = models.OperationLog(
            operation="create_correction",
            entity_type="correction",
            entity_id=correction.id,
            user_id=current_user.id,
            company_id=current_user.company_id,
            changes={
                "number": correction_number,
                "type": correction_type,
                "original_invoice_id": original_invoice_id,
                "original_invoice_number": original_invoice.number,
                "amount_diff": float(amount_diff),
                "vat_diff": float(vat_diff),
                "reason": reason,
                "create_new_invoice": create_new_invoice,
                "accounting_entries_created": len(correction_entries),
            },
        )
        db.add(log_entry)

        await db.commit()
        await db.refresh(correction, ["original_invoice"])
        return types.InvoiceCorrection.from_pydantic(correction)

    @strawberry.mutation
    async def create_cash_receipt(
            self,
            input: inputs.CashReceiptInput,
            info: strawberry.Info,
    ) -> types.CashReceipt:
        """Create a cash receipt"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)


        receipt = models.CashReceipt(
            receipt_number=input.receipt_number,
            date=input.date,
            payment_type=input.payment_type,
            amount=input.amount,
            vat_amount=input.vat_amount,
            items_json=input.items_json,
            fiscal_printer_id=input.fiscal_printer_id,
            company_id=input.company_id,
            created_by=current_user.id,
        )
        db.add(receipt)
        await db.commit()
        await db.refresh(receipt)
        return types.CashReceipt.from_pydantic(receipt)

    @strawberry.mutation
    async def update_cash_receipt(
            self,
            id: int,
            input: inputs.CashReceiptUpdateInput,
            info: strawberry.Info,
    ) -> types.CashReceipt | None:
        """Update a cash receipt"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)


        receipt = await db.get(models.CashReceipt, id)
        if not receipt:
            raise NotFoundException.record("Cash Receipt")

        if receipt.company_id != current_user.company_id:
            raise PermissionDeniedException.for_action("manage")

        if input.receipt_number is not None:
            receipt.receipt_number = input.receipt_number
        if input.date is not None:
            receipt.date = input.date
        if input.payment_type is not None:
            receipt.payment_type = input.payment_type
        if input.amount is not None:
            receipt.amount = input.amount
        if input.vat_amount is not None:
            receipt.vat_amount = input.vat_amount
        if input.items_json is not None:
            receipt.items_json = input.items_json
        if input.fiscal_printer_id is not None:
            receipt.fiscal_printer_id = input.fiscal_printer_id

        await db.commit()
        await db.refresh(receipt)
        return types.CashReceipt.from_pydantic(receipt)

    @strawberry.mutation
    async def auto_match_bank_transactions(
            self,
            bank_account_id: int,
            info: strawberry.Info,
    ) -> types.AutoMatchResult:
        """Automatically match bank transactions to invoices based on amount and reference"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)

        from sqlalchemy import select

        bank_account = await db.get(models.BankAccount, bank_account_id)
        if not bank_account:
            raise NotFoundException.record("Банкова сметка")

        if bank_account.company_id != current_user.company_id:
            raise PermissionDeniedException()

        unmatched_transactions = await db.execute(
            select(models.BankTransaction).where(
                models.BankTransaction.bank_account_id == bank_account_id,
                not models.BankTransaction.matched,
                models.BankTransaction.invoice_id.is_(None),
            ),
        )
        transactions = unmatched_transactions.scalars().all()

        unpaid_invoices = await db.execute(
            select(models.Invoice).where(
                models.Invoice.company_id == current_user.company_id,
                models.Invoice.status.in_(["sent", "paid"]),
            ),
        )
        invoices = unpaid_invoices.scalars().all()

        matched_count = 0
        for tx in transactions:
            for inv in invoices:
                if (tx.type == "credit" and Decimal(tx.amount) == Decimal(inv.total)) or \
                   (tx.type == "debit" and Decimal(tx.amount) == Decimal(inv.total)):
                    if not inv.bank_transactions:
                        tx.invoice_id = inv.id
                        tx.matched = True
                        matched_count += 1
                        break

        await db.commit()

        unmatched_count = len(transactions) - matched_count
        return types.AutoMatchResult(matched_count=matched_count, unmatched_count=unmatched_count)

    @strawberry.mutation
    async def create_account(
            self,
            input: inputs.AccountInput,
            info: strawberry.Info,
    ) -> types.Account:
        """Create an account in the chart of accounts"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)


        account = models.Account(
            code=input.code,
            name=input.name,
            type=input.type,
            parent_id=input.parent_id,
            company_id=input.company_id,
            opening_balance=input.opening_balance,
            closing_balance=input.opening_balance,
        )
        db.add(account)
        await db.commit()
        await db.refresh(account)
        return types.Account.from_pydantic(account)

    @strawberry.mutation
    async def create_accounting_entry(
            self,
            input: inputs.AccountingEntryInput,
            info: strawberry.Info,
    ) -> types.AccountingEntry:
        """Create an accounting entry"""
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)


        entry = models.AccountingEntry(
            date=input.date,
            entry_number=input.entry_number,
            description=input.description,
            debit_account_id=input.debit_account_id,
            credit_account_id=input.credit_account_id,
            amount=input.amount,
            vat_amount=input.vat_amount,
            invoice_id=input.invoice_id,
            bank_transaction_id=input.bank_transaction_id,
            cash_journal_id=input.cash_journal_id,
            company_id=input.company_id,
            created_by=current_user.id,
        )
        db.add(entry)

        # Log the operation
        log_entry = models.OperationLog(
            operation="create",
            entity_type="accounting_entry",
            entity_id=entry.id,
            user_id=current_user.id,
            company_id=current_user.company_id,
            changes={
                "entry_number": input.entry_number,
                "description": input.description,
                "debit_account_id": input.debit_account_id,
                "credit_account_id": input.credit_account_id,
                "amount": float(input.amount),
                "vat_amount": float(input.vat_amount),
                "invoice_id": input.invoice_id,
            },
        )
        db.add(log_entry)

        await db.commit()
        await db.refresh(entry)
        return types.AccountingEntry.from_pydantic(entry)

    @strawberry.mutation
    async def delete_accounting_entry(
            self,
            id: int,
            info: strawberry.Info,
    ) -> bool:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)


        entry = await db.get(models.AccountingEntry, id)
        if not entry:
            raise NotFoundException.record("Accounting Entry")

        if entry.company_id != current_user.company_id:
            raise PermissionDeniedException.for_action("manage")

        log_entry = models.OperationLog(
            operation="delete",
            entity_type="accounting_entry",
            entity_id=entry.id,
            user_id=current_user.id,
            company_id=current_user.company_id,
            changes={
                "entry_number": entry.entry_number,
                "description": entry.description,
                "amount": float(entry.amount),
            },
        )
        db.add(log_entry)

        await db.delete(entry)
        await db.commit()
        return True

    @strawberry.mutation
    async def generate_vat_register(
            self,
            input: inputs.VATRegisterInput,
            info: strawberry.Info,
    ) -> types.VATRegister:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)


        existing = await db.execute(
            select(models.VATRegister).where(
                models.VATRegister.company_id == input.company_id,
                models.VATRegister.period_month == input.period_month,
                models.VATRegister.period_year == input.period_year,
            ),
        )
        existing_reg = existing.scalars().first()
        if existing_reg:
            await db.delete(existing_reg)
            await db.commit()

        from datetime import date
        start_date = date(input.period_year, input.period_month, 1)
        if input.period_month == 12:
            end_date = date(input.period_year + 1, 1, 1)
        else:
            end_date = date(input.period_year, input.period_month + 1, 1)

        outgoing = await db.execute(
            select(models.Invoice).where(
                models.Invoice.company_id == input.company_id,
                models.Invoice.type == "outgoing",
                models.Invoice.date >= start_date,
                models.Invoice.date < end_date,
                models.Invoice.status == "paid",
            ),
        )
        incoming = await db.execute(
            select(models.Invoice).where(
                models.Invoice.company_id == input.company_id,
                models.Invoice.type == "incoming",
                models.Invoice.date >= start_date,
                models.Invoice.date < end_date,
                models.Invoice.status == "paid",
            ),
        )

        vat_collected_20 = Decimal(0)
        vat_collected_9 = Decimal(0)
        vat_collected_0 = Decimal(0)
        for inv in outgoing.scalars():
            if inv.vat_rate == Decimal(20):
                vat_collected_20 += inv.vat_amount or Decimal(0)
            elif inv.vat_rate == Decimal(9):
                vat_collected_9 += inv.vat_amount or Decimal(0)
            else:
                vat_collected_0 += inv.vat_amount or Decimal(0)

        vat_paid_20 = Decimal(0)
        vat_paid_9 = Decimal(0)
        vat_paid_0 = Decimal(0)
        for inv in incoming.scalars():
            if inv.vat_rate == Decimal(20):
                vat_paid_20 += inv.vat_amount or Decimal(0)
            elif inv.vat_rate == Decimal(9):
                vat_paid_9 += inv.vat_amount or Decimal(0)
            else:
                vat_paid_0 += inv.vat_amount or Decimal(0)

        vat_due = max(Decimal(0), (vat_collected_20 + vat_collected_9) - (vat_paid_20 + vat_paid_9))
        vat_credit = max(Decimal(0), (vat_paid_20 + vat_paid_9) - (vat_collected_20 + vat_collected_9))

        vat_register = models.VATRegister(
            company_id=input.company_id,
            period_month=input.period_month,
            period_year=input.period_year,
            vat_collected_20=vat_collected_20,
            vat_collected_9=vat_collected_9,
            vat_collected_0=vat_collected_0,
            vat_paid_20=vat_paid_20,
            vat_paid_9=vat_paid_9,
            vat_paid_0=vat_paid_0,
            vat_adjustment=Decimal(0),
            vat_due=vat_due,
            vat_credit=vat_credit,
        )
        db.add(vat_register)
        await db.commit()
        await db.refresh(vat_register)
        return types.VATRegister.from_pydantic(vat_register)

    @strawberry.mutation
    async def get_invoice_pdf_url(
        self,
        invoice_id: int,
        info: strawberry.Info,
    ) -> str:
        """Връща URL за изтегляне на PDF на фактура"""
        db = info.context["db"]
        current_user = info.context["current_user"]

        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)

        from backend.database.models import Invoice

        invoice = await db.get(Invoice, invoice_id)
        if not invoice:
            raise NotFoundException.record("Фактура")

        if invoice.company_id != current_user.company_id:
            raise PermissionDeniedException.for_resource("фактура", "access")

        base_url = settings.API_URL
        return f"{base_url}/export/invoice/{invoice_id}/pdf"
