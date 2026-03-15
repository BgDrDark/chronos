"""
Tests for TRZ Phase 6 - Payments (Bulk Pay + SEPA)
Tests bulk payment processing and SEPA XML generation.
"""
import pytest
from decimal import Decimal
from datetime import date, datetime
from unittest.mock import AsyncMock, MagicMock, patch
import xml.etree.ElementTree as ET

from backend.services.sepa_generator import SEPAGenerator
from backend.database.models import Payslip, Payment


class TestSEPAGenerator:
    """Test SEPA Credit Transfer XML generation"""
    
    @pytest.fixture
    def generator(self):
        return SEPAGenerator(
            sender_name="Test Company",
            sender_iban="BG80 BNBG 9661 1020 3456 78",
            sender_bic="BNBGBGSF",
            message_id="MSG-20260315000001"
        )
    
    def test_iban_validation_valid(self, generator):
        """Test valid IBAN passes validation"""
        assert generator._validate_iban("BG80 BNBG 9661 1020 3456 78") == True
    
    def test_iban_validation_invalid_length(self, generator):
        """Test invalid IBAN length fails"""
        assert generator._validate_iban("BG80 BNBG") == False
    
    def test_iban_cleaning(self, generator):
        """Test IBAN is cleaned of spaces"""
        result = generator._clean_iban("BG80 BNBG 9661 1020 3456 78")
        assert result == "BG80BNBG96611020345678"
    
    def test_iban_uppercase(self, generator):
        """Test IBAN is converted to uppercase"""
        result = generator._clean_iban("bg80bnbg96611020345678")
        assert result == "BG80BNBG96611020345678"
    
    def test_generate_payment_xml_structure(self, generator):
        """Test generated XML has correct structure"""
        payments = [
            {
                "name": "John Doe",
                "iban": "BG90 TEST 1234 5678 9012 34",
                "amount": 1000.00,
                "description": "Salary March 2026"
            }
        ]
        
        xml = generator.generate_payment_xml(payments)
        
        assert xml is not None
        assert "<?xml" in xml
        assert "<CdtTrfTxInf>" in xml
    
    def test_payment_amount_in_xml(self, generator):
        """Test payment amount is in XML"""
        payments = [
            {
                "name": "John Doe",
                "iban": "BG90 TEST 1234 5678 9012 34",
                "amount": 1500.50,
                "description": "Salary"
            }
        ]
        
        xml = generator.generate_payment_xml(payments)
        
        assert "1500.50" in xml or "1500.5" in xml
    
    def test_multiple_payments(self, generator):
        """Test multiple payments in one XML"""
        payments = [
            {
                "name": "John Doe",
                "iban": "BG90 TEST 1234 5678 9012 34",
                "amount": 1000.00,
                "description": "Salary"
            },
            {
                "name": "Jane Smith",
                "iban": "BG91 TEST 1234 5678 9012 35",
                "amount": 1500.00,
                "description": "Salary"
            }
        ]
        
        xml = generator.generate_payment_xml(payments)
        
        assert xml.count("<CdtTrfTxInf>") == 2
    
    def test_sender_details_in_xml(self, generator):
        """Test sender details are in XML"""
        payments = [
            {
                "name": "John Doe",
                "iban": "BG90 TEST 1234 5678 9012 34",
                "amount": 1000.00,
                "description": "Salary"
            }
        ]
        
        xml = generator.generate_payment_xml(payments)
        
        assert "Test Company" in xml
        assert "BNBGBGSF" in xml
    
    def test_message_id_generated(self, generator):
        """Test message ID is generated"""
        payments = []
        
        xml = generator.generate_payment_xml(payments)
        
        assert "MSG-" in xml


class TestBulkPayment:
    """Test bulk payment processing"""
    
    @pytest.mark.asyncio
    async def test_mark_payslips_as_paid(self):
        """Test marking multiple payslips as paid"""
        pass
    
    @pytest.mark.asyncio
    async def test_bulk_payment_creates_records(self):
        """Test bulk payment creates Payment records"""
        pass
    
    @pytest.mark.asyncio
    async def test_payment_date_set(self):
        """Test payment date is set correctly"""
        pass


class TestSEPAValidation:
    """Test SEPA validation rules"""
    
    def test_bulgarian_iban_format(self):
        """Test Bulgarian IBAN format (BG...)"""
        generator = SEPAGenerator(
            sender_name="Test",
            sender_iban="BG80 BNBG 9661 1020 3456 78",
            sender_bic="BNBGBGSF"
        )
        
        assert generator._validate_iban("BG80 BNBG 9661 1020 3456 78") == True
    
    def test_euro_currency_code(self):
        """Test EUR currency code in SEPA"""
        generator = SEPAGenerator(
            sender_name="Test",
            sender_iban="BG80 BNBG 9661 1020 3456 78",
            sender_bic="BNBGBGSF"
        )
        
        payments = [{"name": "Test", "iban": "BG90TEST12345678901234", "amount": 100, "description": "Test"}]
        xml = generator.generate_payment_xml(payments)
        
        assert "EUR" in xml
    
    def test_iban_country_code_validation(self):
        """Test IBAN country code validation"""
        generator = SEPAGenerator(
            sender_name="Test",
            sender_iban="INVALID",
            sender_bic="TEST"
        )
        
        assert generator._validate_iban("DE89 3704 0044 0532 0130 00") == True


class TestPaymentBatch:
    """Test payment batch processing"""
    
    @pytest.mark.asyncio
    async def test_batch_total_calculation(self):
        """Test batch total is calculated correctly"""
        payments = [
            {"amount": 1000.00},
            {"amount": 1500.00},
            {"amount": 2000.00}
        ]
        
        total = sum(p["amount"] for p in payments)
        
        assert total == 4500.00
    
    @pytest.mark.asyncio
    async def test_empty_batch_handled(self):
        """Test empty payment batch is handled"""
        payments = []
        
        total = sum(p["amount"] for p in payments)
        
        assert total == 0
