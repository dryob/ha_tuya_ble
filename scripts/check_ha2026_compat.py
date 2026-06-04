#!/usr/bin/env python3
"""Lightweight static checks for Home Assistant 2026 compatibility."""

from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INTEGRATION = ROOT / "custom_components" / "tuya_ble"

# Legacy aliases removed from homeassistant.const by HA 2026. Use the StrEnum
# classes instead (for example UnitOfTime.MINUTES, UnitOfVolume.MILLILITERS).
REMOVED_HA_CONST_IMPORTS = {
    "TEMP_CELSIUS": "UnitOfTemperature.CELSIUS",
    "TIME_MINUTES": "UnitOfTime.MINUTES",
    "TIME_SECONDS": "UnitOfTime.SECONDS",
    "VOLUME_MILLILITERS": "UnitOfVolume.MILLILITERS",
}

FORBIDDEN_IMPORTS = {"pycountry"}


def _module_name(path: Path) -> str:
    return ".".join(path.relative_to(ROOT).with_suffix("").parts)


def main() -> None:
    failures: list[str] = []

    for path in sorted(INTEGRATION.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        module = _module_name(path)

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root_name = alias.name.split(".", 1)[0]
                    if root_name in FORBIDDEN_IMPORTS:
                        failures.append(f"{module}: forbidden import {alias.name}")

            if isinstance(node, ast.ImportFrom):
                if node.module:
                    root_name = node.module.split(".", 1)[0]
                    if root_name in FORBIDDEN_IMPORTS:
                        failures.append(f"{module}: forbidden import from {node.module}")

                if node.module == "homeassistant.const":
                    for alias in node.names:
                        replacement = REMOVED_HA_CONST_IMPORTS.get(alias.name)
                        if replacement:
                            failures.append(
                                f"{module}: homeassistant.const.{alias.name} was removed; "
                                f"use {replacement}"
                            )

    if failures:
        raise SystemExit("\n".join(failures))

    print("HA 2026 const imports and pycountry scan are clean")


if __name__ == "__main__":
    main()
