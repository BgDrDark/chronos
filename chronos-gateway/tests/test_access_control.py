import pytest
import sys
import os
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestSR201Relay:
    """Тестове за SR201 Relay клас"""
    
    def test_relay_initialization(self):
        """Тест на инициализация"""
        from gateway.devices.sr201_relay import SR201Relay
        
        relay = SR201Relay(
            device_id="test_relay",
            name="Test Relay",
            ip="192.168.1.100",
            port=6722,
            relay_1_duration=500,
            relay_2_duration=1000
        )
        
        assert relay.device_id == "test_relay"
        assert relay.name == "Test Relay"
        assert relay.ip == "192.168.1.100"
        assert relay.relay_1_duration == 500
        assert relay.relay_2_duration == 1000
    
    def test_relay_duration_bounds(self):
        """Тест на границите за duration"""
        from gateway.devices.sr201_relay import SR201Relay
        
        # Test max
        relay = SR201Relay("test", "test", "192.168.1.1", relay_1_duration=20000)
        assert relay.relay_1_duration == 10000  # Capped to max
        
        # Test min
        relay = SR201Relay("test", "test", "192.168.1.1", relay_1_duration=-100)
        assert relay.relay_1_duration == 0  # Capped to min
    
    def test_get_duration(self):
        """Тест на get_duration метода"""
        from gateway.devices.sr201_relay import SR201Relay
        
        relay = SR201Relay("test", "test", "192.168.1.1", relay_1_duration=500, relay_2_duration=1000)
        
        assert relay.get_duration(1) == 500
        assert relay.get_duration(2) == 1000
        assert relay.get_duration(3) == 500  # Default
    
    def test_to_dict(self):
        """Тест на to_dict метода"""
        from gateway.devices.sr201_relay import SR201Relay
        
        relay = SR201Relay(
            device_id="test_relay",
            name="Test Relay",
            ip="192.168.1.100",
            relay_1_duration=500
        )
        
        data = relay.to_dict()
        
        assert data["device_id"] == "test_relay"
        assert data["name"] == "Test Relay"
        assert data["ip"] == "192.168.1.100"
        assert data["relay_1_duration"] == 500
    
    def test_from_dict(self):
        """Тест на from_dict метода"""
        from gateway.devices.sr201_relay import SR201Relay
        
        data = {
            "device_id": "test_relay",
            "name": "Test Relay",
            "ip": "192.168.1.100",
            "relay_1_duration": 500,
            "relay_2_duration": 1000,
            "relay_1_manual": True,
            "relay_2_manual": False
        }
        
        relay = SR201Relay.from_dict(data)
        
        assert relay.device_id == "test_relay"
        assert relay.relay_1_manual == True
        assert relay.relay_2_manual == False


class TestRelayController:
    """Тестове за RelayController"""
    
    def test_add_device(self):
        """Тест на добавяне на устройство"""
        from gateway.devices.relay_controller import RelayController
        
        controller = RelayController()
        device_id = controller.add_device(
            device_id="sr201_1",
            name="Test Device",
            ip="192.168.1.100",
            device_type="sr201"
        )
        
        assert device_id == "sr201_1"
        assert len(controller.devices) == 1
    
    def test_remove_device(self):
        """Тест на премахване на устройство"""
        from gateway.devices.relay_controller import RelayController
        
        controller = RelayController()
        controller.add_device("sr201_1", "Test", "192.168.1.100")
        
        result = controller.remove_device("sr201_1")
        assert result == True
        assert len(controller.devices) == 0
    
    def test_get_device(self):
        """Тест на връщане на устройство"""
        from gateway.devices.relay_controller import RelayController
        
        controller = RelayController()
        controller.add_device("sr201_1", "Test", "192.168.1.100")
        
        device = controller.get_device("sr201_1")
        assert device is not None
        assert device.ip == "192.168.1.100"
    
    def test_update_device(self):
        """Тест на обновяване на устройство"""
        from gateway.devices.relay_controller import RelayController
        
        controller = RelayController()
        controller.add_device("sr201_1", "Test", "192.168.1.100")
        
        result = controller.update_device("sr201_1", name="Updated Name", relay_1_duration=1000)
        
        assert result == True
        device = controller.get_device("sr201_1")
        assert device.name == "Updated Name"
        assert device.relay_1_duration == 1000


class TestZoneState:
    """Тестове за ZoneState"""
    
    def test_enter_zone(self):
        """Тест на влизане в зона"""
        from gateway.access.zone_state import ZoneState
        
        state = ZoneState()
        state.enter_zone("user1", "zone_1")
        
        assert "zone_1" in state.get_user_zones("user1")
    
    def test_leave_zone(self):
        """Тест на напускане на зона"""
        from gateway.access.zone_state import ZoneState
        
        state = ZoneState()
        state.enter_zone("user1", "zone_1")
        state.leave_zone("user1", "zone_1")
        
        assert "zone_1" not in state.get_user_zones("user1")
    
    def test_check_access_level_1(self):
        """Тест на достъп за level 1 зона"""
        from gateway.access.zone_state import ZoneState, Zone
        
        state = ZoneState()
        zone = Zone(id="zone_1", name="Zone 1", level=1)
        
        allowed, reason = state.check_access("user1", zone)
        
        assert allowed == True
        assert reason == "OK"
    
    def test_check_access_missing_dependency(self):
        """Тест на достъп с липсваща зависимост"""
        from gateway.access.zone_state import ZoneState, Zone
        
        state = ZoneState()
        zone = Zone(id="zone_2", name="Zone 2", level=2, depends_on=["zone_1"])
        
        allowed, reason = state.check_access("user1", zone)
        
        assert allowed == False
        assert "zone_1" in reason
    
    def test_check_access_with_dependency(self):
        """Тест на достъп със удовлетворена зависимост"""
        from gateway.access.zone_state import ZoneState, Zone
        
        state = ZoneState()
        state.enter_zone("user1", "zone_1")
        
        zone = Zone(id="zone_2", name="Zone 2", level=2, depends_on=["zone_1"])
        allowed, reason = state.check_access("user1", zone)
        
        assert allowed == True
    
    def test_reset_user(self):
        """Тест на ресет на потребител"""
        from gateway.access.zone_state import ZoneState
        
        state = ZoneState()
        state.enter_zone("user1", "zone_1")
        state.enter_zone("user1", "zone_2")
        
        state.reset_user("user1")
        
        assert len(state.get_user_zones("user1")) == 0


class TestZone:
    """Тестове за Zone модел"""
    
    def test_zone_initialization(self):
        """Тест на инициализация"""
        from gateway.access.zone_state import Zone
        
        zone = Zone(
            id="zone_1",
            name="Test Zone",
            level=2,
            depends_on=["zone_1"]
        )
        
        assert zone.id == "zone_1"
        assert zone.level == 2
        assert "zone_1" in zone.depends_on
    
    def test_is_within_hours(self):
        """Тест на работно време"""
        from gateway.access.zone_state import Zone
        
        zone = Zone(
            id="zone_1",
            name="Test",
            required_hours_start="00:00",
            required_hours_end="23:59"
        )
        
        allowed, reason = zone.is_within_hours()
        # Should be allowed during typical work hours
        assert allowed == True
    
    def test_zone_to_dict(self):
        """Тест на to_dict"""
        from gateway.access.zone_state import Zone
        
        zone = Zone(id="zone_1", name="Test", level=1)
        data = zone.to_dict()
        
        assert data["id"] == "zone_1"
        assert data["name"] == "Test"
        assert data["level"] == 1
    
    def test_zone_from_dict(self):
        """Тест на from_dict"""
        from gateway.access.zone_state import Zone
        
        data = {
            "id": "zone_1",
            "name": "Test",
            "level": 2,
            "depends_on": ["zone_1"],
            "required_hours": {"start": "08:00", "end": "18:00"},
            "anti_passback": {"enabled": True, "type": "hard"}
        }
        
        zone = Zone.from_dict(data)
        
        assert zone.id == "zone_1"
        assert zone.level == 2
        assert zone.anti_passback_enabled == True


class TestAntiPassback:
    """Тестове за AntiPassbackState"""
    
    def test_check_no_history(self):
        """Тест без история"""
        from gateway.access.anti_passback import AntiPassbackState
        
        state = AntiPassbackState()
        
        allowed, msg = state.check("user1", "zone_1", {"enabled": True, "type": "hard"})
        
        assert allowed == True
    
    def test_check_hard_same_zone(self):
        """Тест hard anti-passback в съща зона"""
        from gateway.access.anti_passback import AntiPassbackState
        
        state = AntiPassbackState()
        state.record("user1", "zone_1", "in")
        
        allowed, msg = state.check("user1", "zone_1", {"enabled": True, "type": "hard"})
        
        assert allowed == False
        assert "Вече" in msg
    
    def test_check_soft_same_zone(self):
        """Тест soft anti-passback в съща зона"""
        from gateway.access.anti_passback import AntiPassbackState
        
        state = AntiPassbackState()
        state.record("user1", "zone_1", "in")
        
        allowed, msg = state.check("user1", "zone_1", {"enabled": True, "type": "soft"})
        
        assert allowed == True  # Soft allows but warns
    
    def test_check_different_zone(self):
        """Тест в различна зона"""
        from gateway.access.anti_passback import AntiPassbackState
        
        state = AntiPassbackState()
        state.record("user1", "zone_1", "in")
        
        allowed, msg = state.check("user1", "zone_2", {"enabled": True, "type": "hard"})
        
        assert allowed == True
    
    def test_check_disabled(self):
        """Тест когато е изключен"""
        from gateway.access.anti_passback import AntiPassbackState
        
        state = AntiPassbackState()
        state.record("user1", "zone_1", "in")
        
        allowed, msg = state.check("user1", "zone_1", {"enabled": False, "type": "hard"})
        
        assert allowed == True
    
    def test_check_exit_not_in_zone(self):
        """Тест на изход когато не е в зоната"""
        from gateway.access.anti_passback import AntiPassbackState
        
        state = AntiPassbackState()
        
        allowed, msg = state.check_exit("user1", "zone_1")
        
        assert allowed == False
    
    def test_check_exit_in_zone(self):
        """Тест на изход когато е в зоната"""
        from gateway.access.anti_passback import AntiPassbackState
        
        state = AntiPassbackState()
        state.record("user1", "zone_1", "in")
        
        allowed, msg = state.check_exit("user1", "zone_1")
        
        assert allowed == True


class TestCodeManager:
    """Тестове за CodeManager"""
    
    def test_generate_code(self):
        """Тест на генериране на код"""
        from gateway.access.code_manager import CodeManager
        
        manager = CodeManager(prefix="G")
        code = manager.generate_code(6)
        
        assert code.startswith("G")
        assert len(code) == 7  # G + 6 digits
    
    def test_create_code(self):
        """Тест на създаване на код"""
        from gateway.access.code_manager import CodeManager
        
        manager = CodeManager()
        code = manager.create_code({
            "code_type": "one_time",
            "zones": ["zone_1"],
            "max_uses": 1
        })
        
        assert code in manager.codes
        assert manager.codes[code].code_type == "one_time"
    
    def test_validate_code_invalid(self):
        """Тест на невалиден код"""
        from gateway.access.code_manager import CodeManager
        
        manager = CodeManager()
        
        valid, msg, _ = manager.validate_code("INVALID", "zone_1")
        
        assert valid == False
    
    def test_validate_code_expired(self):
        """Тест на изтекъл код"""
        from gateway.access.code_manager import CodeManager, AccessCode
        from datetime import datetime, timedelta
        
        manager = CodeManager()
        code = AccessCode(
            code="TEST123",
            code_type="one_time",
            expires_at=datetime.utcnow() - timedelta(hours=1)
        )
        manager.codes["TEST123"] = code
        
        valid, msg, _ = manager.validate_code("TEST123", "zone_1")
        
        assert valid == False
        assert "изтекъл" in msg
    
    def test_use_code(self):
        """Тест на използване на код"""
        from gateway.access.code_manager import CodeManager
        
        manager = CodeManager()
        manager.create_code({
            "code": "TEST123",
            "code_type": "one_time",
            "zones": ["zone_1"],
            "max_uses": 1
        })
        
        success, msg = manager.use_code("TEST123", "user1")
        
        assert success == True
        assert manager.codes["TEST123"].uses_remaining == 0
    
    def test_revoke_code(self):
        """Тест на отнемане на код"""
        from gateway.access.code_manager import CodeManager
        
        manager = CodeManager()
        manager.create_code({
            "code": "TEST123",
            "code_type": "permanent"
        })
        
        result = manager.revoke_code("TEST123")
        
        assert result == True
        assert manager.codes["TEST123"].active == False


class TestZoneManager:
    """Тестове за ZoneManager"""
    
    def test_add_zone(self):
        """Тест на добавяне на зона"""
        from gateway.access.zone_manager import ZoneManager
        
        manager = ZoneManager()
        zone_id = manager.add_zone({
            "id": "zone_1",
            "name": "Test Zone",
            "level": 1
        })
        
        assert zone_id == "zone_1"
        assert "zone_1" in manager.zones
    
    def test_add_door(self):
        """Тест на добавяне на врата"""
        from gateway.access.zone_manager import ZoneManager
        
        manager = ZoneManager()
        manager.add_zone({"id": "zone_1", "name": "Test", "level": 1})
        
        door_id = manager.add_door({
            "id": "door_1",
            "name": "Test Door",
            "zone_id": "zone_1",
            "device_id": "sr201_1",
            "relay_number": 1
        })
        
        assert door_id == "door_1"
        assert "door_1" in manager.doors
    
    def test_validate_zone_dependencies(self):
        """Тест на валидация на зависимости"""
        from gateway.access.zone_manager import ZoneManager
        
        manager = ZoneManager()
        manager.add_zone({"id": "zone_1", "name": "Z1", "level": 1})
        
        # Valid: level 2 with dependency on level 1
        valid, msg = manager.validate_zone_dependencies({
            "id": "zone_2",
            "level": 2,
            "depends_on": ["zone_1"]
        })
        
        assert valid == True
    
    def test_validate_zone_dependencies_invalid(self):
        """Тест на невалидна зависимост"""
        from gateway.access.zone_manager import ZoneManager
        
        manager = ZoneManager()
        manager.add_zone({"id": "zone_1", "name": "Z1", "level": 1})
        
        # Invalid: level 2 without dependency
        valid, msg = manager.validate_zone_dependencies({
            "id": "zone_2",
            "level": 2,
            "depends_on": []
        })
        
        assert valid == False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
