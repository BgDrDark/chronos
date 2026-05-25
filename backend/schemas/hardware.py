from datetime import datetime

from backend.schemas.base import CustomBaseModel


class GatewayBase(CustomBaseModel):
    name: str
    hardware_uuid: str
    alias: str | None = None
    ip_address: str | None = None
    local_hostname: str | None = None
    terminal_port: int = 8080
    web_port: int = 8888
    is_active: bool
    last_heartbeat: datetime | None = None
    registered_at: datetime
    company_id: int | None = None


class Gateway(GatewayBase):
    id: int


class TerminalBase(CustomBaseModel):
    hardware_uuid: str
    device_name: str | None = None
    device_type: str | None = None
    device_model: str | None = None
    os_version: str | None = None
    gateway_id: int | None = None
    is_active: bool
    last_seen: datetime | None = None
    total_scans: int = 0
    alias: str | None = None
    mode: str = "both"


class Terminal(TerminalBase):
    id: int


class PrinterBase(CustomBaseModel):
    name: str
    printer_type: str | None = None
    ip_address: str | None = None
    port: int = 9100
    protocol: str | None = None
    windows_share_name: str | None = None
    manufacturer: str | None = None
    model: str | None = None
    gateway_id: int
    is_active: bool
    is_default: bool
    last_test: datetime | None = None
    last_error: str | None = None


class Printer(PrinterBase):
    id: int
