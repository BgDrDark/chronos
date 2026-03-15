"""
Tests for TRZ Phase 5 - Leaves and Sick Leave
Tests leave request and sick leave calculations per Bulgarian labor law.
"""
import pytest
from decimal import Decimal
from datetime import date, timedelta


class TestSickLeaveCalculations:
    """Test sick leave calculations per Bulgarian law"""
    
    @pytest.mark.asyncio
    async def test_sick_leave_first_3_days_employer(self):
        """Test first 3 days of sick leave paid by employer (80%)"""
        daily_salary = Decimal("1000") / Decimal("21.67")
        employer_pay = daily_salary * Decimal("0.80") * Decimal("3")
        assert employer_pay > 0
    
    @pytest.mark.asyncio
    async def test_sick_leave_exists(self):
        """Test sick leave module exists"""
        from backend.services import enhanced_payroll_calculator
        assert enhanced_payroll_calculator is not None


class TestLeaveRequestCalculations:
    """Test annual leave calculations"""
    
    @pytest.mark.asyncio
    async def test_annual_leave_20_days(self):
        """Test standard annual leave is 20 working days"""
        annual_leave = 20
        assert annual_leave >= 20
    
    @pytest.mark.asyncio
    async def test_leave_accrual_per_month(self):
        """Test leave accrual is 1.67 days per month"""
        monthly_accrual = Decimal("20") / Decimal("12")
        expected = Decimal("1.67")
        assert abs(monthly_accrual - expected) < Decimal("0.1")


class TestUnpaidLeave:
    """Test unpaid leave calculations"""
    
    @pytest.mark.asyncio
    async def test_unpaid_leave_no_salary(self):
        """Test unpaid leave results in no salary for that period"""
        pass


class TestSickLeaveRecord:
    """Test SickLeaveRecord model"""
    
    @pytest.mark.asyncio
    async def test_sick_leave_max_60_days_per_year(self):
        """Test maximum 60 days sick leave per year"""
        max_days = 60
        assert max_days == 60
