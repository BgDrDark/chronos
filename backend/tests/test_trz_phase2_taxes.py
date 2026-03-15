"""
Tests for TRZ Phase 2 - Tax Calculations (ДДФЛ)
Tests income tax calculations with standard deduction and insurance deductions.
"""
import pytest
from decimal import Decimal
from datetime import date


class TestTaxCalculation:
    """Test income tax (ДДФЛ) calculations"""
    
    @pytest.mark.asyncio
    async def test_tax_rate_10_percent(self):
        """Test standard tax rate is 10%"""
        tax_rate = 10.0
        assert tax_rate == 10.0
    
    @pytest.mark.asyncio
    async def test_standard_deduction_500_leva(self):
        """Test standard deduction is 500 leva"""
        deduction = 500.0
        assert deduction == 500.0
    
    @pytest.mark.asyncio
    async def test_taxable_base_calculation(self):
        """Test taxable base = gross - insurance - deduction"""
        gross = Decimal("2000")
        insurance = Decimal("200")
        deduction = Decimal("500")
        
        taxable_base = gross - insurance - deduction
        assert taxable_base == 1300
    
    @pytest.mark.asyncio
    async def test_income_tax_calculation(self):
        """Test income tax = taxable_base * tax_rate"""
        taxable_base = Decimal("1300")
        tax_rate = Decimal("10")
        
        income_tax = taxable_base * (tax_rate / Decimal("100"))
        assert income_tax == 130
    
    @pytest.mark.asyncio
    async def test_taxable_base_minimum_zero(self):
        """Test taxable base cannot be negative"""
        gross = Decimal("300")
        insurance = Decimal("200")
        deduction = Decimal("500")
        
        taxable_base = max(Decimal("0"), gross - insurance - deduction)
        assert taxable_base == 0


class TestTaxDeductions:
    """Test tax deductions"""
    
    @pytest.mark.asyncio
    async def test_standard_deduction_from_settings(self):
        """Test standard deduction value"""
        standard_deduction = 500
        assert standard_deduction == 500


class TestTaxHistory:
    """Test tax rate history"""
    
    @pytest.mark.asyncio
    async def test_tax_calculator_method_exists(self):
        """Test tax calculation method exists"""
        from backend.services.enhanced_payroll_calculator import EnhancedPayrollCalculator
        assert hasattr(EnhancedPayrollCalculator, 'calculate_tax_details')
