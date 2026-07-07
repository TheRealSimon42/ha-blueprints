#!/usr/bin/env python3
"""Lint für Home Assistant Automation-Blueprints.

Prüft die Fallen, die bei der Entwicklung der Rollladensteuerung V2 real
aufgetreten sind. Exit-Code 1 bei Fehlern, 0 bei Erfolg (Warnungen erlaubt).

Aufruf: python3 validate_blueprint.py <blueprint.yaml>
"""
import re
import sys

import yaml


class BlueprintLoader(yaml.SafeLoader):
    pass


BlueprintLoader.add_constructor(
    "!input", lambda loader, node: {"__input__": loader.construct_scalar(node)}
)


def collect_inputs(input_block, defined):
    for key, value in input_block.items():
        if isinstance(value, dict) and "input" in value and "selector" not in value:
            collect_inputs(value["input"], defined)
        else:
            defined[key] = value if isinstance(value, dict) else {}


def collect_used(node, used):
    if isinstance(node, dict):
        if "__input__" in node and len(node) == 1:
            used.add(node["__input__"])
        else:
            for value in node.values():
                collect_used(value, used)
    elif isinstance(node, list):
        for value in node:
            collect_used(value, used)


def main(path):
    errors, warnings = [], []
    with open(path, encoding="utf-8") as f:
        raw = f.read()

    try:
        doc = yaml.load(raw, Loader=BlueprintLoader)
    except yaml.YAMLError as exc:
        print(f"FEHLER: YAML-Parse fehlgeschlagen:\n{exc}")
        return 1

    bp = doc.get("blueprint")
    if not isinstance(bp, dict):
        print("FEHLER: Kein 'blueprint:'-Block gefunden.")
        return 1

    # --- Metadata ---
    if not bp.get("source_url"):
        warnings.append("source_url fehlt — ohne sie kein Re-Import/Update für Nutzer.")
    if not bp.get("homeassistant", {}).get("min_version"):
        warnings.append(
            "homeassistant.min_version fehlt — Input-Sections brauchen 2024.6, "
            "triggers:/actions:-Syntax 2024.10."
        )

    # --- Inputs sammeln und abgleichen ---
    defined = {}
    collect_inputs(bp.get("input", {}), defined)
    used = set()
    collect_used({k: v for k, v in doc.items() if k != "blueprint"}, used)

    missing = used - set(defined)
    unused = set(defined) - used
    if missing:
        errors.append(f"!input ohne Definition: {sorted(missing)}")
    if unused:
        warnings.append(f"Definierte, aber ungenutzte Inputs: {sorted(unused)}")

    required = sorted(k for k, v in defined.items() if "default" not in v)

    # --- Selector-Default-Fallen ---
    for key, value in defined.items():
        selector = value.get("selector", {}) or {}
        default = value.get("default", "__none__")
        if "area" in selector and default == {}:
            errors.append(
                f"Input '{key}': Area-Selector mit default {{}} rendert als "
                "'Unbekannter Bereich' — default: \"\" verwenden."
            )
        if "entity" in selector and default == {}:
            warnings.append(
                f"Input '{key}': Entity-Selector mit default {{}} — default: [] "
                "rendert in der UI sauberer und ist in Triggern valide."
            )

    # --- Template-Fallen im Rohtext ---
    if re.search(r"\{\{[^}]*!input", raw) or re.search(r"\{%[^%]*!input", raw):
        errors.append(
            "!input direkt in einem Template — erst über variables:/trigger_variables: "
            "binden."
        )
    if re.search(r"\binputs\.\w+", raw):
        errors.append(
            "Zugriff auf ein 'inputs.'-Objekt — das existiert in HA-Templates nicht."
        )
    if "wait.completed" in raw and "wait_for_trigger" in raw:
        warnings.append(
            "wait.completed zusammen mit wait_for_trigger — dort heißt die Prüfung "
            "'wait.trigger is not none' (wait.completed gehört zu wait_template)."
        )
    if re.search(r"\[\s*repeat\.index\s*\]", raw):
        warnings.append(
            "repeat.index als Listenindex — repeat.index ist 1-BASIERT, für "
            "0-basierte Listen repeat.index - 1 verwenden (V1-Off-by-One!)."
        )

    # --- Legacy-Syntax ---
    if re.search(r"^\s*-?\s*platform:\s", raw, re.M):
        warnings.append("Legacy 'platform:' in Triggern — modern ist 'trigger: <typ>'.")
    if re.search(r"^\s*-?\s*service:\s", raw, re.M):
        warnings.append("Legacy 'service:' in Aktionen — modern ist 'action:'.")
    if "trigger:" not in raw.split("\n")[0] and doc.get("trigger") is not None:
        warnings.append("Top-Level 'trigger:' (singular) — modern ist 'triggers:'.")
    if doc.get("action") is not None:
        warnings.append("Top-Level 'action:' (singular) — modern ist 'actions:'.")

    # --- Ausgabe ---
    print(f"Blueprint: {bp.get('name', '<ohne Namen>')}")
    print(f"Inputs: {len(defined)} definiert, {len(used)} referenziert")
    print(f"Pflichtfelder (ohne default): {required or 'keine'}")
    print("Sind das wirklich nur die Inputs, ohne die die Automation sinnlos ist?")
    print()
    for w in warnings:
        print(f"WARNUNG: {w}")
    for e in errors:
        print(f"FEHLER:  {e}")
    if not errors and not warnings:
        print("Keine Befunde.")
    print()
    print("FEHLGESCHLAGEN" if errors else "OK")
    return 1 if errors else 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(sys.argv[1]))
