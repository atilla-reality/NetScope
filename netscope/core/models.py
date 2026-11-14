from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class NetworkAddress:
    address: str
    family: str
    prefix_length: Optional[int] = None
    scope: Optional[str] = None

    def to_dict(self):
        return {
            "address": self.address,
            "family": self.family,
            "prefix_length": self.prefix_length,
            "scope": self.scope,
        }


@dataclass
class NetworkInterface:
    name: str
    addresses: List[NetworkAddress] = field(default_factory=list)
    mac_address: Optional[str] = None
    mtu: Optional[int] = None
    is_up: Optional[bool] = None
    status: str = "unknown"
    source: str = "unknown"

    def to_dict(self):
        return {
            "name": self.name,
            "addresses": [
                address.to_dict()
                for address in self.addresses
            ],
            "mac_address": self.mac_address,
            "mtu": self.mtu,
            "is_up": self.is_up,
            "status": self.status,
            "source": self.source,
        }


@dataclass
class NetworkDiagnostics:
    platform: str
    interfaces: List[NetworkInterface] = field(default_factory=list)
    gateway: Optional[str] = None
    route_hint: Optional[dict] = None
    capabilities: dict = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)

    def to_dict(self):
        has_data = bool(
            self.interfaces or self.gateway or self.route_hint
        )

        if self.errors:
            status = "partial" if has_data else "error"
        elif has_data:
            status = "ok"
        else:
            status = "unsupported"

        return {
            "platform": self.platform,
            "status": status,
            "gateway": self.gateway,
            "route_hint": self.route_hint,
            "capabilities": dict(self.capabilities),
            "interfaces": [
                interface.to_dict()
                for interface in self.interfaces
            ],
            "errors": list(self.errors),
        }
