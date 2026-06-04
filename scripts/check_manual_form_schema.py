#!/usr/bin/env python3
"""Validate the Tuya BLE manual config flow schema stays frontend-serializable."""

from __future__ import annotations

import ast
from pathlib import Path

CONFIG_FLOW = Path(__file__).resolve().parents[1] / "custom_components" / "tuya_ble" / "config_flow.py"
CUSTOM_VALIDATORS = {"_normalize_address", "_non_empty_string"}
CLOUD_CALLS = {"build_cache", "_try_login", "TuyaOpenAPI", "_login"}


def _find_function(tree: ast.AST, name: str) -> ast.FunctionDef | ast.AsyncFunctionDef:
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            return node
    raise SystemExit(f"Could not find {name} in {CONFIG_FLOW}")


def _manual_schema_values(show_manual: ast.FunctionDef | ast.AsyncFunctionDef) -> list[ast.AST]:
    for call in ast.walk(show_manual):
        if not isinstance(call, ast.Call):
            continue
        func = call.func
        if not (
            isinstance(func, ast.Attribute)
            and func.attr == "Schema"
            and isinstance(func.value, ast.Name)
            and func.value.id == "vol"
        ):
            continue
        if not call.args or not isinstance(call.args[0], ast.Dict):
            raise SystemExit("_show_manual_form vol.Schema must wrap a dict literal")
        return [value for value in call.args[0].values if value is not None]
    raise SystemExit("Could not find vol.Schema dict in _show_manual_form")


def main() -> None:
    tree = ast.parse(CONFIG_FLOW.read_text(encoding="utf-8"), filename=str(CONFIG_FLOW))

    show_manual = _find_function(tree, "_show_manual_form")
    bad_validators = sorted(
        {
            value.id
            for value in _manual_schema_values(show_manual)
            if isinstance(value, ast.Name) and value.id in CUSTOM_VALIDATORS
        }
    )
    if bad_validators:
        raise SystemExit(
            "_show_manual_form data_schema uses frontend-unserializable custom validators: "
            + ", ".join(bad_validators)
        )

    manual_step = _find_function(tree, "async_step_manual")
    cloud_calls = sorted(
        {
            node.attr if isinstance(node, ast.Attribute) else node.id
            for node in ast.walk(manual_step)
            if (
                isinstance(node, ast.Attribute)
                and node.attr in CLOUD_CALLS
            )
            or (isinstance(node, ast.Name) and node.id in CLOUD_CALLS)
        }
    )
    if cloud_calls:
        raise SystemExit(
            "async_step_manual must stay pure-local; found cloud-related calls/names: "
            + ", ".join(cloud_calls)
        )

    print("manual form schema is frontend-serializable and manual step stays pure-local")


if __name__ == "__main__":
    main()
