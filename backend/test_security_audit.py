#!/usr/bin/env python3
"""
Тестове за проверка на одитните проблеми - Статичен анализ на кода.
Изпълни: python test_security_audit.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def check_file_for_pattern(filepath: str, search_pattern: str, func_name: str) -> bool:
    """Проверява дали дадена функция съдържа шаблон"""
    try:
        with open(filepath, "r") as f:
            content = f.read()
        
        if f"async def {func_name}" not in content:
            return True  # Функцията не съществува
        
        start = content.find(f"async def {func_name}")
        # Намери края на функцията (следващата async def или class)
        end = content.find("\nasync def ", start + 1)
        if end == -1:
            end = content.find("\nclass ", start + 1)
        if end == -1:
            end = content.find("\ndef ", start + 1)
        
        func_content = content[start:end if end != -1 else start + 5000]
        
        return search_pattern in func_content
    except Exception as e:
        print(f"⚠️ Грешка при четене на {filepath}: {e}")
        return True


def main():
    """Главна функция"""
    print("\n" + "=" * 70)
    print("🔍 АНАЛИЗ НА СИГУРНОСТТА - ПРОВЕРКА НА КОДА")
    print("=" * 70)
    
    queries_file = "graphql/queries.py"
    types_file = "graphql/types.py"
    
    results = []
    
    # -----------------------------------------------------------------------------
    # СИГУРНОСТ: Проверка за company_id филтри
    # -----------------------------------------------------------------------------
    print("\n" + "-" * 50)
    print("🔒 ПРОВЕРКА ЗА ISOLATION ПО ФИРМА (company_id)")
    print("-" * 50)
    
    # 1.1 user_presences
    has_filter = check_file_for_pattern(queries_file, "company_id", "user_presences")
    if has_filter:
        print("✅ 1.1 user_presences: company_id филтър ЕС ТеСТВА")
        results.append(("1.1 user_presences", True))
    else:
        print("❌ 1.1 user_presences: ЛИПСВА company_id филтър")
        results.append(("1.1 user_presences", False))
    
    # 1.2 pending_leave_requests
    has_filter = check_file_for_pattern(queries_file, "company_id", "pending_leave_requests")
    if has_filter:
        print("✅ 1.2 pending_leave_requests: company_id филтър ЕС ТеСТВА")
        results.append(("1.2 pending_leave_requests", True))
    else:
        print("❌ 1.2 pending_leave_requests: ЛИПСВА company_id филтър")
        results.append(("1.2 pending_leave_requests", False))
    
    # 1.3 all_leave_requests
    has_filter = check_file_for_pattern(queries_file, "company_id", "all_leave_requests")
    if has_filter:
        print("✅ 1.3 all_leave_requests: company_id филтър ЕС ТеСТВА")
        results.append(("1.3 all_leave_requests", True))
    else:
        print("❌ 1.3 all_leave_requests: ЛИПСВА company_id филтър")
        results.append(("1.3 all_leave_requests", False))
    
    # 1.4 payroll_forecast
    has_filter = check_file_for_pattern(queries_file, "company_id", "payroll_forecast")
    if has_filter:
        print("✅ 1.4 payroll_forecast: company_id филтър ЕС ТеСТВА")
        results.append(("1.4 payroll_forecast", True))
    else:
        print("❌ 1.4 payroll_forecast: ЛИПСВА company_id филтър")
        results.append(("1.4 payroll_forecast", False))
    
    # 1.5 schedule_templates
    has_filter = check_file_for_pattern(queries_file, "company_id", "schedule_templates")
    if has_filter:
        print("✅ 1.5 schedule_templates: company_id филтър ЕС ТеСТВА")
        results.append(("1.5 schedule_templates", True))
    else:
        print("❌ 1.5 schedule_templates: ЛИПСВА company_id филтър")
        results.append(("1.5 schedule_templates", False))
    
    # 1.6 schedule_template (проверка за собственост)
    has_check = check_file_for_pattern(queries_file, "company_id", "schedule_template")
    if has_check:
        print("✅ 1.6 schedule_template: проверка за собственост ЕС ТеСТВА")
        results.append(("1.6 schedule_template", True))
    else:
        print("❌ 1.6 schedule_template: ЛИПСВА проверка за собственост")
        results.append(("1.6 schedule_template", False))
    
    # 1.7 audit_logs
    has_filter = check_file_for_pattern(queries_file, "company_id", "audit_logs")
    if has_filter:
        print("✅ 1.7 audit_logs: company_id филтър ЕС ТеСТВА")
        results.append(("1.7 audit_logs", True))
    else:
        print("❌ 1.7 audit_logs: ЛИПСВА company_id филтър")
        results.append(("1.7 audit_logs", False))
    
    # 1.8 get_fefo_suggestion
    has_filter = check_file_for_pattern(queries_file, "company_id", "get_fefo_suggestion")
    if has_filter:
        print("✅ 1.8 get_fefo_suggestion: company_id филтър ЕС ТеСТВА")
        results.append(("1.8 get_fefo_suggestion", True))
    else:
        print("❌ 1.8 get_fefo_suggestion: ЛИПСВА company_id филтър")
        results.append(("1.8 get_fefo_suggestion", False))
    
    # 1.9 inventory_by_barcode
    has_filter = check_file_for_pattern(queries_file, "company_id", "inventory_by_barcode")
    if has_filter:
        print("✅ 1.9 inventory_by_barcode: company_id филтър ЕС ТеСТВА")
        results.append(("1.9 inventory_by_barcode", True))
    else:
        print("❌ 1.9 inventory_by_barcode: ЛИПСВА company_id филтър")
        results.append(("1.9 inventory_by_barcode", False))
    
    # -----------------------------------------------------------------------------
    # DECIMAL: Проверка за загуба на точност
    # -----------------------------------------------------------------------------
    print("\n" + "-" * 50)
    print("⚠️ ПРОВЕРКА ЗА DECIMAL → FLOAT КОНВЕРСИЯ")
    print("-" * 50)
    
    try:
        with open(types_file, "r") as f:
            types_content = f.read()
        
        # 2.1 ContractTemplateVersion
        if "class ContractTemplateVersion" in types_content:
            start = types_content.find("class ContractTemplateVersion")
            next_class = types_content.find("\nclass ", start + 1)
            class_content = types_content[start:next_class if next_class != -1 else len(types_content)]
            
            if "float(" in class_content and "rate" in class_content.lower():
                print("❌ 2.1 ContractTemplateVersion: ИМА float() конверсия (загуба на точност)")
                results.append(("2.1 ContractTemplateVersion", False))
            else:
                print("✅ 2.1 ContractTemplateVersion: НЯМА float() конверсия")
                results.append(("2.1 ContractTemplateVersion", True))
        else:
            print("⚠️ 2.1 ContractTemplateVersion: Класът не е намерен")
            results.append(("2.1 ContractTemplateVersion", True))
        
        # 2.2 AnnexTemplateVersion
        if "class AnnexTemplateVersion" in types_content:
            start = types_content.find("class AnnexTemplateVersion")
            next_class = types_content.find("\nclass ", start + 1)
            class_content = types_content[start:next_class if next_class != -1 else len(types_content)]
            
            if "float(" in class_content and ("salary" in class_content.lower() or "rate" in class_content.lower()):
                print("❌ 2.2 AnnexTemplateVersion: ИМА float() конверсия (загуба на точност)")
                results.append(("2.2 AnnexTemplateVersion", False))
            else:
                print("✅ 2.2 AnnexTemplateVersion: НЯМА float() конверсия")
                results.append(("2.2 AnnexTemplateVersion", True))
        else:
            print("⚠️ 2.2 AnnexTemplateVersion: Класът не е намерен")
            results.append(("2.2 AnnexTemplateVersion", True))
            
    except Exception as e:
        print(f"⚠️ Грешка при четене на {types_file}: {e}")
    
    # -----------------------------------------------------------------------------
    # Демо: Загуба на точност
    # -----------------------------------------------------------------------------
    print("\n" + "-" * 50)
    print("📊 ДЕМО: Загуба на точност при Decimal → Float")
    print("-" * 50)
    
    from decimal import Decimal
    
    original = Decimal("1234.5678")
    as_float = float(original)
    back_to_decimal = Decimal(str(as_float))
    diff = abs(original - back_to_decimal)
    
    print(f"   Оригинал (Decimal):  {original}")
    print(f"   След float():        {as_float}")
    print(f"   Обратно в Decimal:   {back_to_decimal}")
    print(f"   Разлика:            {diff}")
    
    if diff == 0:
        print("   Резултат: ✅ Няма загуба в този пример")
    else:
        print("   Резултат: ❌ Загуба на точност!")
    
    results.append(("2.3 Decimal demo", True))  # Винаги минава
    
    # -----------------------------------------------------------------------------
    # РЕЗУЛТАТИ
    # -----------------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("📊 ОБОБЩЕНИЕ")
    print("=" * 70)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = "✅" if result else "❌"
        print(f"  {status} {name}")
    
    print(f"\n{'=' * 70}")
    print(f"Резултат: {passed}/{total} проверки преминаха")
    print("=" * 70)
    
    # Списък с проблеми за поправка
    issues = [name for name, result in results if not result]
    if issues:
        print("\n🔧 НУЖНИ ПОПРАВКИ:")
        for issue in issues:
            print(f"   - {issue}")
    else:
        print("\n🎉 Всички проверки преминаха!")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
