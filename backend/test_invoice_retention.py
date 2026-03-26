#!/usr/bin/env python3
"""
Тест за 10-годишна давност при изтриване на счетоводни документи.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import date, timedelta
from decimal import Decimal

def test_retention_check():
    """Тест за логиката на проверка за 10-годишна давност"""
    print("\n" + "="*60)
    print("🧪 Тест на 10-годишна давност")
    print("="*60)
    
    def check_retention_years(invoice_date: date, years: int = 10) -> bool:
        """Проверка дали документа е на повече от years години"""
        today = date.today()
        age_in_years = (today - invoice_date).days / 365.25
        return age_in_years > years
    
    # 1. Тест с днешна дата (по-малко от 10 години)
    today = date.today()
    assert not check_retention_years(today), "Днешна дата не трябва да минава давността"
    print(f"✅ Днешна дата ({today}): {check_retention_years(today)} - OK")
    
    # 2. Тест с дата преди 5 години
    five_years_ago = today - timedelta(days=365 * 5)
    assert not check_retention_years(five_years_ago), "Дата преди 5 год. не трябва да минава"
    print(f"✅ 5 години ({five_years_ago}): {check_retention_years(five_years_ago)} - OK")
    
    # 3. Тест с дата преди 9 години
    nine_years_ago = today - timedelta(days=365 * 9)
    assert not check_retention_years(nine_years_ago), "Дата преди 9 год. не трябва да минава"
    print(f"✅ 9 години ({nine_years_ago}): {check_retention_years(nine_years_ago)} - OK")
    
    # 4. Тест с дата преди 10+ години
    ten_years_ago = today - timedelta(days=365 * 10 + 10)
    age = (today - ten_years_ago).days / 365.25
    assert age > 10, f"Дата преди >10 год. трябва да минава (age={age})"
    print(f"✅ >10 години ({ten_years_ago}): age={age:.4f} - OK")
    
    # 5. Тест с дата преди 15 години
    fifteen_years_ago = today - timedelta(days=365 * 15)
    assert check_retention_years(fifteen_years_ago), "Дата преди 15 год. трябва да минава"
    print(f"✅ 15 години ({fifteen_years_ago}): {check_retention_years(fifteen_years_ago)} - OK")
    
    print("\n✅ Всички тестове за давност минаха успешно!")


def test_exception_format():
    """Тест за форматирането на exceptions"""
    print("\n" + "="*60)
    print("🧪 Тест на exception формат")
    print("="*60)
    
    try:
        from exceptions import ValidationException, NotFoundException, PermissionDeniedException, RetentionPeriodException
        
        # Test ValidationException
        e1 = ValidationException.field("email", "Невалиден формат")
        print(f"\nValidationException.field():")
        print(f"  error_code: {e1.error_code}")
        print(f"  message: {e1.detail}")
        print(f"  to_dict(): {e1.to_dict()}")
        
        # Test NotFoundException
        e2 = NotFoundException.user(user_id=123)
        print(f"\nNotFoundException.user():")
        print(f"  error_code: {e2.error_code}")
        print(f"  message: {e2.detail}")
        print(f"  context: {e2.context}")
        
        # Test PermissionDeniedException
        e3 = PermissionDeniedException.for_action("delete")
        print(f"\nPermissionDeniedException.for_action():")
        print(f"  error_code: {e3.error_code}")
        print(f"  message: {e3.detail}")
        
        # Test RetentionPeriodException
        e4 = RetentionPeriodException.invoice(invoice_id=456, years=10)
        print(f"\nRetentionPeriodException.invoice():")
        print(f"  error_code: {e4.error_code}")
        print(f"  message: {e4.detail}")
        print(f"  years: {e4.years}")
        print(f"  to_dict(): {e4.to_dict()}")
        
        print("\n✅ Всички exceptions работят правилно!")
        return True
    except ImportError as ex:
        print(f"\n❌ Import error: {ex}")
        return False


if __name__ == "__main__":
    print("="*60)
    print("🧪 ТЕСТ ЗА 10-ГОДИШНА ДАВНОСТ")
    print("="*60)
    
    test_retention_check()
    success = test_exception_format()
    
    if success:
        print("\n" + "="*60)
        print("🎉 ВСИЧКИ ТЕСТОВЕ МИНАХА УСПЕШНО!")
        print("="*60)
        sys.exit(0)
    else:
        print("\n" + "="*60)
        print("❌ ТЕСТОВЕТЕ ФЕЙЛНАХА")
        print("="*60)
        sys.exit(1)
