"""
SEPA Credit Transfer XML Generator
Generates ISO 20022 pain.001.001.03 compliant XML files for batch payments.
"""
from decimal import Decimal
from datetime import datetime
from typing import List, Dict, Any
import xml.etree.ElementTree as ET


class SEPAGenerator:
    """Generates SEPA Credit Transfer XML files"""
    
    # XML Namespaces
    XMLNS_XSI = "http://www.w3.org/2001/XMLSchema-instance"
    XMLNS_PAIN = "urn:iso:std:iso:20022:tech:xsd:pain.001.001.03"
    XMLNS_XSI_SCHEMA_LOCATION = "urn:iso:std:iso:20022:tech:xsd:pain.001.001.03 pain.001.001.03.xsd"
    
    def __init__(
        self,
        sender_name: str,
        sender_iban: str,
        sender_bic: str,
        message_id: str = None
    ):
        self.sender_name = sender_name
        self.sender_iban = sender_iban.replace(" ", "").upper()
        self.sender_bic = sender_bic.replace(" ", "").upper()
        self.message_id = message_id or f"MSG-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    def _clean_iban(self, iban: str) -> str:
        """Remove spaces and convert to uppercase"""
        return iban.replace(" ", "").upper()
    
    def _validate_iban(self, iban: str) -> bool:
        """Basic IBAN validation"""
        iban = self._clean_iban(iban)
        if len(iban) < 15 or len(iban) > 34:
            return False
        # Check that first 2 chars are letters (country code)
        if not iban[:2].isalpha():
            return False
        # Check that next 2 chars are digits
        if not iban[2:4].isdigit():
            return False
        return True
    
    def generate_payment_xml(
        self,
        payments: List[Dict[str, Any]],
        batch_name: str = "Payroll",
        execution_date: str = None
    ) -> str:
        """
        Generate SEPA XML for batch payments.
        
        Args:
            payments: List of dicts with keys:
                - name: Recipient name
                - iban: Recipient IBAN
                - amount: Amount in EUR (Decimal or float)
                - reference: Payment reference
                - description: Payment description (optional)
            batch_name: Name of the payment batch
            execution_date: Date for execution (YYYY-MM-DD), defaults to today
            
        Returns:
            XML string
        """
        if execution_date is None:
            execution_date = datetime.now().strftime("%Y-%m-%d")
        
        # Create root element
        root = ET.Element("Document")
        root.set("xmlns", self.XMLNS_PAIN)
        root.set("xmlns:xsi", self.XMLNS_XSI)
        root.set("xsi:schemaLocation", self.XMLNS_XSI_SCHEMA_LOCATION)
        
        # CstmrCdtTrfInitn
        grp_hdr = ET.SubElement(root, "CstmrCdtTrfInitn")
        
        # GrpHdr
        msg_hdr = ET.SubElement(grp_hdr, "GrpHdr")
        ET.SubElement(msg_hdr, "MsgId").text = self.message_id
        ET.SubElement(msg_hdr, "CreDtTm").text = datetime.now().isoformat()
        ET.SubElement(msg_hdr, "NbOfTxs").text = str(len(payments))
        
        # Calculate total amount
        total_amount = sum(float(p.get("amount", 0)) for p in payments)
        ET.SubElement(msg_hdr, "CtrlSum").text = f"{total_amount:.2f}"
        
        # InitgPty
        initg_pty = ET.SubElement(msg_hdr, "InitgPty")
        ET.SubElement(initg_pty, "Nm").text = self.sender_name
        
        # PmtInf
        pmt_inf = ET.SubElement(grp_hdr, "PmtInf")
        ET.SubElement(pmt_inf, "PmtInfId").text = f"{self.message_id}-BATCH"
        ET.SubElement(pmt_inf, "PmtMtd").text = "TRF"
        ET.SubElement(pmt_inf, "BtchBookg").text = "true"
        ET.SubElement(pmt_inf, "NbOfTxs").text = str(len(payments))
        ET.SubElement(pmt_inf, "CtrlSum").text = f"{total_amount:.2f}"
        
        # PmtTpInf
        pmt_tp_inf = ET.SubElement(pmt_inf, "PmtTpInf")
        svc_lvl = ET.SubElement(pmt_tp_inf, "SvcLvl")
        ET.SubElement(svc_lvl, "Cd").text = "SEPA"
        
        # ReqdExctnDt
        ET.SubElement(pmt_inf, "ReqdExctnDt").text = execution_date
        
        # Dbtr
        dbtr = ET.SubElement(pmt_inf, "Dbtr")
        ET.SubElement(dbtr, "Nm").text = self.sender_name
        
        # DbtrAcct
        dbtr_acct = ET.SubElement(pmt_inf, "DbtrAcct")
        dbtr_acct_id = ET.SubElement(dbtr_acct, "Id")
        ET.SubElement(dbtr_acct_id, "IBAN").text = self.sender_iban
        
        # DbtrAgt
        dbtr_agt = ET.SubElement(pmt_inf, "DbtrAgt")
        dbtr_agt_fin_instn_id = ET.SubElement(dbtr_agt, "FinInstnId")
        ET.SubElement(dbtr_agt_fin_instn_id, "BIC").text = self.sender_bic
        
        # ChrgBr
        ET.SubElement(pmt_inf, "ChrgBr").text = "SLEV"
        
        # Transactions
        for idx, payment in enumerate(payments):
            name = payment.get("name", "")
            iban = self._clean_iban(payment.get("iban", ""))
            amount = Decimal(str(payment.get("amount", 0)))
            reference = payment.get("reference", "")
            description = payment.get("description", batch_name)
            
            if not self._validate_iban(iban):
                continue
            
            # CdtTrfTxInf
            cdt_trf_tx_inf = ET.SubElement(pmt_inf, "CdtTrfTxInf")
            
            # PmtId
            pmt_id = ET.SubElement(cdt_trf_tx_inf, "PmtId")
            ET.SubElement(pmt_id, "EndToEndId").text = f"{self.message_id}-{idx+1:04d}"
            
            # Amt
            amt = ET.SubElement(cdt_trf_tx_inf, "Amt")
            instd_amt = ET.SubElement(amt, "InstdAmt")
            instd_amt.set("Ccy", "EUR")
            instd_amt.text = f"{amount:.2f}"
            
            # CdtrAgt
            cdtr_agt = ET.SubElement(cdt_trf_tx_inf, "CdtrAgt")
            cdtr_agt_fin_instn_id = ET.SubElement(cdtr_agt, "FinInstnId")
            # Use local country if no BIC provided
            cdtr_bic = payment.get("bic", "")
            if cdtr_bic:
                ET.SubElement(cdtr_agt_fin_instn_id, "BIC").text = cdtr_bic.replace(" ", "").upper()
            
            # Cdtr
            cdtr = ET.SubElement(cdt_trf_tx_inf, "Cdtr")
            ET.SubElement(cdtr, "Nm").text = name[:70]  # Max 70 chars
            
            # CdtrAcct
            cdtr_acct = ET.SubElement(cdt_trf_tx_inf, "CdtrAcct")
            cdtr_acct_id = ET.SubElement(cdtr_acct, "Id")
            ET.SubElement(cdtr_acct_id, "IBAN").text = iban
            
            # RmtInf
            rmt_inf = ET.SubElement(cdt_trf_tx_inf, "RmtInf")
            strd = ET.SubElement(rmt_inf, "Strd")
            cdtr_ref_inf = ET.SubElement(strd, "CdtrRefInf")
            ET.SubElement(cdtr_ref_inf, "Ref").text = reference[:35]  # Max 35 chars
        
        # Convert to string
        xml_str = ET.tostring(root, encoding="unicode", method="xml")
        
        # Add XML declaration
        return '<?xml version="1.0" encoding="UTF-8"?>\n' + xml_str
    
    def validate_payments(self, payments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate payment data and return validation results.
        
        Returns:
            Dict with 'valid', 'errors', 'warnings' keys
        """
        errors = []
        warnings = []
        
        if not payments:
            errors.append("No payments provided")
            return {"valid": False, "errors": errors, "warnings": warnings}
        
        total_amount = Decimal("0")
        
        for idx, payment in enumerate(payments):
            # Check required fields
            if not payment.get("name"):
                errors.append(f"Payment {idx+1}: Missing recipient name")
            
            if not payment.get("iban"):
                errors.append(f"Payment {idx+1}: Missing IBAN")
            elif not self._validate_iban(payment["iban"]):
                errors.append(f"Payment {idx+1}: Invalid IBAN format")
            
            amount = payment.get("amount")
            if amount is None:
                errors.append(f"Payment {idx+1}: Missing amount")
            else:
                try:
                    amount = Decimal(str(amount))
                    if amount <= 0:
                        errors.append(f"Payment {idx+1}: Amount must be positive")
                    elif amount > Decimal("999999999.99"):
                        errors.append(f"Payment {idx+1}: Amount exceeds maximum")
                    total_amount += amount
                except Exception:
                    errors.append(f"Payment {idx+1}: Invalid amount format")
            
            if not payment.get("reference"):
                warnings.append(f"Payment {idx+1}: Missing payment reference")
        
        # Check sender IBAN
        if not self._validate_iban(self.sender_iban):
            errors.append("Sender IBAN is invalid")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "total_payments": len(payments),
            "total_amount": float(total_amount)
        }
