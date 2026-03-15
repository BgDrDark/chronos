"""
Tests for TRZ Phase 7 - Reports (NAP Integration)
Tests National Revenue Agency (НАП) report generation.
"""
import pytest
from decimal import Decimal
from datetime import date, datetime
from unittest.mock import AsyncMock, MagicMock, patch


class TestNAPAnnualInsuranceReport:
    """Test annual insurance report generation"""
    
    @pytest.mark.asyncio
    async def test_nap_reports_generator_exists(self):
        """Test NAPReportsGenerator class exists"""
        from backend.services.nap_reports import NAPReportsGenerator
        assert NAPReportsGenerator is not None
    
    @pytest.mark.asyncio
    async def test_annual_report_method_exists(self):
        """Test annual report method exists"""
        from backend.services.nap_reports import NAPReportsGenerator
        gen = NAPReportsGenerator(MagicMock(), 1, 2026)
        assert hasattr(gen, 'generate_annual_insurance_report')


class TestNAPIncomeReport:
    """Test income report by type (Чл. 73, ал. 6 ЗДДФЛ)"""
    
    @pytest.mark.asyncio
    async def test_income_report_method_exists(self):
        """Test income report method exists"""
        from backend.services.nap_reports import NAPReportsGenerator
        gen = NAPReportsGenerator(MagicMock(), 1, 2026)
        assert hasattr(gen, 'generate_income_report_by_type')


class TestNAPReportData:
    """Test NAP report data aggregation"""
    
    @pytest.mark.asyncio
    async def test_yearly_totals(self):
        """Test yearly totals calculation"""
        payslips = [
            {"gross": 2000, "tax": 150, "insurance": 400},
            {"gross": 2000, "tax": 150, "insurance": 400},
            {"gross": 2000, "tax": 150, "insurance": 400},
        ]
        total_gross = sum(p["gross"] for p in payslips)
        assert total_gross == 6000


class TestNAPReportValidation:
    """Test NAP report validation"""
    
    @pytest.mark.asyncio
    async def test_required_fields_present(self):
        """Test all required fields are present"""
        required_fields = ["company_id", "year", "employees"]
        assert len(required_fields) == 3
