#!/usr/bin/env python3
"""Regression test for manual Tuya BLE config flow option persistence."""

from __future__ import annotations

import asyncio
import importlib.util
import sys
import types
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONFIG_FLOW = ROOT / "custom_components" / "tuya_ble" / "config_flow.py"
PACKAGE_PATH = ROOT / "custom_components" / "tuya_ble"


def _setattr(module: types.ModuleType, name: str, value: Any) -> None:
    """Set a dynamic module attribute without static-type noise."""
    setattr(module, name, value)


def _install_stubs() -> None:
    """Install enough Home Assistant/Tuya stubs to import config_flow standalone."""
    voluptuous = types.ModuleType("voluptuous")

    class Invalid(Exception):
        pass

    class Schema:
        def __init__(self, schema: Any) -> None:
            self.schema = schema

    class _Marker:
        def __init__(self, key: str, default: Any = None) -> None:
            self.key = key
            self.default = default

        def __hash__(self) -> int:
            return hash((self.key, self.default))

        def __eq__(self, other: object) -> bool:
            return (
                isinstance(other, _Marker)
                and self.key == other.key
                and self.default == other.default
            )

    def _required(key: str, default: Any = None) -> _Marker:
        return _Marker(key, default)

    def _optional(key: str, default: Any = None) -> _Marker:
        return _Marker(key, default)

    def _in(options: Any) -> Any:
        return options

    _setattr(voluptuous, "Invalid", Invalid)
    _setattr(voluptuous, "Schema", Schema)
    _setattr(voluptuous, "Required", _required)
    _setattr(voluptuous, "Optional", _optional)
    _setattr(voluptuous, "In", _in)
    sys.modules["voluptuous"] = voluptuous

    tuya_iot = types.ModuleType("tuya_iot")

    class AuthType:
        CUSTOM = "custom"
        SMART_HOME = "smart_home"

    class TuyaCloudOpenAPIEndpoint:
        AMERICA = "https://openapi.tuyaus.com"
        CHINA = "https://openapi.tuyacn.com"
        EUROPE = "https://openapi.tuyaeu.com"
        INDIA = "https://openapi.tuyain.com"

    _setattr(tuya_iot, "AuthType", AuthType)
    _setattr(tuya_iot, "TuyaCloudOpenAPIEndpoint", TuyaCloudOpenAPIEndpoint)
    sys.modules["tuya_iot"] = tuya_iot

    ha = types.ModuleType("homeassistant")
    ha.__path__ = []
    sys.modules["homeassistant"] = ha

    config_entries = types.ModuleType("homeassistant.config_entries")

    class ConfigEntry:
        pass

    class FlowHandler:
        pass

    class ConfigFlow:
        VERSION = 1
        MINOR_VERSION = 1
        source = "user"
        flow_id = "fake-flow"
        handler = "tuya_ble"

        def __init_subclass__(cls, **kwargs: Any) -> None:
            super().__init_subclass__()

        def __init__(self) -> None:
            self.context: dict[str, Any] = {}
            self.hass = types.SimpleNamespace(config=types.SimpleNamespace(country="Japan"))
            self.unique_id: str | None = None

        async def async_set_unique_id(
            self, unique_id: str, raise_on_progress: bool = True
        ) -> None:
            self.unique_id = unique_id

        def _abort_if_unique_id_configured(self) -> None:
            return None

        def async_show_menu(
            self, *, step_id: str, menu_options: list[str]
        ) -> dict[str, Any]:
            return {"type": "menu", "step_id": step_id, "menu_options": menu_options}

        def async_show_form(
            self, *, step_id: str, data_schema: Any, errors: dict[str, str], **kwargs: Any
        ) -> dict[str, Any]:
            result = {"type": "form", "step_id": step_id, "data_schema": data_schema, "errors": errors}
            result.update(kwargs)
            return result

        def async_create_entry(
            self, *, title: str, data: dict[str, Any], options: dict[str, Any] | None = None
        ) -> dict[str, Any]:
            # Match Home Assistant's important behavior here: the result keeps the
            # mapping object handed by the integration. If the integration passes
            # self._data directly, later self._data mutation mutates result options.
            return {
                "type": "create_entry",
                "title": title,
                "data": data,
                "options": options or {},
            }

    class OptionsFlowWithConfigEntry:
        def __init__(self, config_entry: ConfigEntry) -> None:
            self.config_entry = config_entry

    _setattr(config_entries, "ConfigEntry", ConfigEntry)
    _setattr(config_entries, "ConfigFlow", ConfigFlow)
    _setattr(config_entries, "OptionsFlowWithConfigEntry", OptionsFlowWithConfigEntry)
    _setattr(config_entries, "ConfigFlowResult", dict)
    sys.modules["homeassistant.config_entries"] = config_entries

    bluetooth = types.ModuleType("homeassistant.components.bluetooth")
    _setattr(bluetooth, "BluetoothServiceInfoBleak", type("BluetoothServiceInfoBleak", (), {}))
    _setattr(bluetooth, "async_discovered_service_info", lambda hass: [])
    sys.modules["homeassistant.components"] = types.ModuleType("homeassistant.components")
    sys.modules["homeassistant.components.bluetooth"] = bluetooth

    const = types.ModuleType("homeassistant.const")
    _setattr(const, "CONF_ADDRESS", "address")
    _setattr(const, "CONF_DEVICE_ID", "device_id")
    sys.modules["homeassistant.const"] = const

    core = types.ModuleType("homeassistant.core")
    _setattr(core, "callback", lambda func: func)
    sys.modules["homeassistant.core"] = core

    data_entry_flow = types.ModuleType("homeassistant.data_entry_flow")
    _setattr(data_entry_flow, "FlowHandler", FlowHandler)
    sys.modules["homeassistant.data_entry_flow"] = data_entry_flow

    custom_components = types.ModuleType("custom_components")
    custom_components.__path__ = [str(ROOT / "custom_components")]
    sys.modules["custom_components"] = custom_components

    package = types.ModuleType("custom_components.tuya_ble")
    package.__path__ = [str(PACKAGE_PATH)]
    sys.modules["custom_components.tuya_ble"] = package

    tuya_ble_module = types.ModuleType("custom_components.tuya_ble.tuya_ble")
    _setattr(tuya_ble_module, "SERVICE_UUID", "0000tuya-0000-1000-8000-00805f9b34fb")
    _setattr(tuya_ble_module, "TuyaBLEDeviceCredentials", type("TuyaBLEDeviceCredentials", (), {}))
    sys.modules["custom_components.tuya_ble.tuya_ble"] = tuya_ble_module

    devices = types.ModuleType("custom_components.tuya_ble.devices")
    _setattr(devices, "TuyaBLEData", type("TuyaBLEData", (), {}))
    _setattr(devices, "get_short_address", lambda address: address.replace(":", "")[-4:])

    async def get_device_readable_name(*args: Any, **kwargs: Any) -> str:
        return "Fake Tuya BLE"

    _setattr(devices, "get_device_readable_name", get_device_readable_name)
    sys.modules["custom_components.tuya_ble.devices"] = devices

    cloud = types.ModuleType("custom_components.tuya_ble.cloud")

    class HASSTuyaBLEDeviceManager:
        def __init__(self, hass: Any, data: dict[str, Any]) -> None:
            self.data = data

    _setattr(cloud, "HASSTuyaBLEDeviceManager", HASSTuyaBLEDeviceManager)
    sys.modules["custom_components.tuya_ble.cloud"] = cloud


def _load_config_flow() -> Any:
    _install_stubs()
    spec = importlib.util.spec_from_file_location(
        "custom_components.tuya_ble.config_flow", CONFIG_FLOW
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


async def _run() -> None:
    config_flow = _load_config_flow()
    flow = config_flow.TuyaBLEConfigFlow()

    menu = await flow.async_step_user()
    assert menu["type"] == "menu"
    assert menu["menu_options"] == ["manual", "login"]

    user_input = {
        "address": "aa-bb-cc-dd-ee-ff",
        "uuid": "fake-uuid",
        "local_key": "fake-local-key",
        "device_id": "fake-device-id",
        "category": "wkcz",
        "product_id": "fake-product-id",
        "device_name": "Fake CADO MAT",
        "product_name": "Fake Product",
        "product_model": "Fake Model",
    }
    result = await flow.async_step_manual(user_input)

    assert result["type"] == "create_entry"
    assert result["title"] == "Fake CADO MAT"
    assert result["data"] == {"address": "AA:BB:CC:DD:EE:FF"}
    assert result["options"]["uuid"] == "fake-uuid"
    assert result["options"]["local_key"] == "fake-local-key"
    assert result["options"]["device_id"] == "fake-device-id"
    assert result["options"]["category"] == "wkcz"
    assert result["options"]["product_id"] == "fake-product-id"
    assert result["options"]["device_name"] == "Fake CADO MAT"
    assert result["options"]["product_name"] == "Fake Product"
    assert result["options"]["product_model"] == "Fake Model"

    flow._data.clear()
    flow._data.update(
        {"access_id": "", "access_secret": "", "username": "", "password": ""}
    )

    assert result["options"] is not flow._data
    assert result["options"] == {
        "address": "AA:BB:CC:DD:EE:FF",
        "uuid": "fake-uuid",
        "local_key": "fake-local-key",
        "device_id": "fake-device-id",
        "category": "wkcz",
        "product_id": "fake-product-id",
        "device_name": "Fake CADO MAT",
        "product_name": "Fake Product",
        "product_model": "Fake Model",
    }


def main() -> None:
    asyncio.run(_run())
    print("manual flow persists device credentials in independent entry options")


if __name__ == "__main__":
    main()
