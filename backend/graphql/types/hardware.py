
import strawberry
from strawberry.experimental import pydantic as sp

from backend import schemas


@sp.type(schemas.Gateway)
class Gateway:
    id: strawberry.auto
    name: strawberry.auto
    hardware_uuid: strawberry.auto
    alias: strawberry.auto
    ip_address: strawberry.auto
    local_hostname: strawberry.auto
    terminal_port: strawberry.auto
    web_port: strawberry.auto
    is_active: strawberry.auto
    last_heartbeat: strawberry.auto
    registered_at: strawberry.auto
    company_id: strawberry.auto


@sp.type(schemas.Terminal)
class Terminal:
    id: strawberry.auto
    hardware_uuid: strawberry.auto
    device_name: strawberry.auto
    device_type: strawberry.auto
    device_model: strawberry.auto
    os_version: strawberry.auto
    gateway_id: strawberry.auto
    is_active: strawberry.auto
    last_seen: strawberry.auto
    total_scans: strawberry.auto
    alias: strawberry.auto
    mode: strawberry.auto


@sp.type(schemas.Printer)
class Printer:
    id: strawberry.auto
    name: strawberry.auto
    printer_type: strawberry.auto
    ip_address: strawberry.auto
    port: strawberry.auto
    protocol: strawberry.auto
    windows_share_name: strawberry.auto
    manufacturer: strawberry.auto
    model: strawberry.auto
    gateway_id: strawberry.auto
    is_active: strawberry.auto
    is_default: strawberry.auto
    last_test: strawberry.auto
    last_error: strawberry.auto


@strawberry.type
class GatewayStats:
    total_gateways: int
    active_gateways: int
    inactive_gateways: int
    total_terminals: int
    active_terminals: int
    total_printers: int
    active_printers: int
