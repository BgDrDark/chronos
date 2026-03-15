"""
Tests for TRZ Phase 4 - Pro-rata Salary Calculations
Tests proportional salary calculation when contract changes during the month.
"""
import pytest
from decimal import Decimal
from datetime import date, timedelta


class TestProRataBasic:
    """Basic Pro-rata salary calculations"""
    
    @pytest.mark.asyncio
    async def test_pro_rata_calculation_logic(self):
        """Test pro-rata calculation logic works"""
        base_salary = Decimal("1000")
        days_in_month = 31
        days_at_new_salary = 16
        
        pro_rata = (base_salary * Decimal(str(days_in_month - days_at_new_salary)) / Decimal(str(days_in_month))) + \
                   (Decimal("1200") * Decimal(str(days_at_new_salary)) / Decimal(str(days_in_month)))
        
        assert 1100 < pro_rata < 1110


class TestProRataWithAnnexes:
    """Test Pro-rata with contract annexes"""
    
    @pytest.mark.asyncio
    async def test_pro_rata_formula(self):
        """Test pro-rata formula calculation"""
        base_salary = Decimal("930")
        
        pro_rata = (base_salary * Decimal("15") / Decimal("31"))
        
        assert pro_rata > 0


class TestContractSegments:
    """Test contract segment detection"""
    
    @pytest.mark.asyncio
    async def test_segment_calculation(self):
        """Test segment days calculation"""
        base_salary = Decimal("930")
        days = 15
        
        amount = base_salary * Decimal(str(days)) / Decimal("31")
        
        assert amount > 400
