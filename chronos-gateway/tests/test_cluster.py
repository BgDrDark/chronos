import pytest
import hmac
import hashlib
import sqlite3
import os
from pathlib import Path
from gateway.cluster.scorer import calculate_hardware_score
from gateway.access.controller import AccessController
from gateway.config import config

def test_hardware_scorer():
    """Проверка дали скорът се изчислява и е положително число"""
    score = calculate_hardware_score()
    assert isinstance(score, int)
    assert score > 0

def test_log_signature_integrity():
    """Тест на HMAC подписите за логовете"""
    controller = AccessController()
    log_entry = {
        "id": "test_log_1",
        "timestamp": "2026-03-04T10:00:00",
        "user_id": "1",
        "result": "granted"
    }
    
    # Генерираме подпис
    secret = config.get("cluster.shared_secret", "chronos_cluster_secret")
    msg = f"{log_entry['id']}|{log_entry['timestamp']}|{log_entry['user_id']}|{log_entry['result']}"
    signature = hmac.new(secret.encode(), msg.encode(), hashlib.sha256).hexdigest()
    log_entry["signature"] = signature
    
    # Проверка чрез контролера
    assert controller.verify_log_signature(log_entry) is True
    
    # Опит за подмяна на данните (tampering)
    log_entry["result"] = "denied"
    assert controller.verify_log_signature(log_entry) is False

def test_sqlite_persistence(tmp_path):
    """Тест за запис и четене от SQLite базата"""
    # Пренасочваме базата към временна папка
    config.set("logging.file", str(tmp_path / "test.log"))
    controller = AccessController()
    
    # Създаваме тестов лог
    controller._create_log(
        user_id="user_999",
        user_name="Test User",
        zone_id="zone_1",
        result="granted",
        action="enter"
    )
    
    # Проверяваме дали е в базата
    unsynced = controller.get_unsynced_logs()
    assert len(unsynced) == 1
    assert unsynced[0]["user_id"] == "user_999"
    assert unsynced[0]["synced"] == 0
    
    # Тест на маркиране като синхронизиран
    controller.mark_as_synced([unsynced[0]["id"]])
    assert len(controller.get_unsynced_logs()) == 0
