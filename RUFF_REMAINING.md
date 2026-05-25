# Останали 549 ръчни грешки (ruff check —unsafe-fixes)

След `--fix --unsafe-fixes` (4350+ автоматично поправени).

## Статистика по правило

| Брой | Код | Правило | Нужен преглед? |
|------|-----|---------|----------------|
| 150 | E701 | multiple-statements-on-one-line-colon | ⚠️ основно в миграции |
| 132 | B008 | function-call-in-default-argument | ❌ да — `def f(x={})` |
| 120 | F401 | unused-import | ✅ може да се махнат |
|  26 | B904 | raise-without-from-inside-except | ❌ да |
|  20 | E741 | ambiguous-variable-name (l, O, I) | ✅ безопасно |
|  17 | F821 | undefined-name | ❌ да — потенциални бъгове |
|  17 | SIM102 | collapsible-if | ✅ безопасно |
|  13 | E722 | bare-except | ❌ да |
|  12 | F811 | redefined-while-unused | ❌ да |
|   8 | N806 | non-lowercase-variable-in-function | ✅ безопасно |
|   6 | | invalid-syntax | ❌ да |
|   6 | SIM117 | multiple-with-statements | ✅ безопасно |
|   5 | E702 | multiple-statements-on-one-line-semicolon | ✅ безопасно |
|   5 | UP035 | deprecated-import | ✅ безопасно |
|   3 | B017 | assert-raises-exception | ❌ да |
|   3 | N802 | invalid-function-name | ⚠️ |
|   2 | N818 | error-suffix-on-exception-name | ⚠️ |
|   2 | SIM105 | suppressible-exception | ✅ безопасно |
|   1 | B007 | unused-loop-control-variable | ⚠️ |
|   1 | UP007 | non-pep604-annotation-union | ✅ безопасно |

## Препоръка

Безопасни за автоматично оправяне: **F401** (unused import), **E741** (l/O/I vars), **SIM102** (collapsible if), **N806** (variable case), **SIM117** (with merge), **E702** (semicolons), **UP035** (deprecated imports), **SIM105** (suppress), **UP007** (union syntax).
Това са ~197 допълнителни грешки.

Останалото (B008, B904, E722, F821, F811, B017) изисква code review.

## Пълен списък с файлове

(виж `RUFF_REMAINING_FULL.txt`)
