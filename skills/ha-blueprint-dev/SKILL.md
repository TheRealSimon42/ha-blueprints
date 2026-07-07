---
name: ha-blueprint-dev
description: >
  Entwickelt, erweitert und reviewt Home Assistant Automation-Blueprints in Simons Repo
  TheRealSimon42/ha-blueprints (z.B. die Rollladensteuerung cover_automation_v2) auf
  Senior-Niveau — Architektur-Entscheidungen, Input-/Selector-Design, Jinja-Fallen,
  Validierung, Deploy auf die HA-Instanz und GitHub-Push. IMMER verwenden, wenn es um
  Blueprints, cover_automation, Rollladen-/Cover-/Beschattungslogik, !input, Selektoren,
  Blueprint-YAML oder das ha-blueprints-Repo geht — auch bei scheinbar kleinen Änderungen,
  denn die typischen Fallen (1-basierter repeat.index, Blueprint-Cache, Selector-Defaults,
  Race Conditions bei mode parallel) treffen gerade die einfachen Edits.
---

# Home Assistant Blueprint-Entwicklung (ha-blueprints)

Dieser Skill destilliert die Arbeitsweise, mit der die Rollladensteuerung V2 entwickelt
wurde. Das Ziel ist nicht nur korrektes YAML, sondern ein Prozess, der Fehler findet,
bevor der Nutzer sie findet: verifizieren statt vermuten, unabhängig reviewen lassen,
live gegen die echte HA-Instanz testen.

## Umgebung

| Was | Wo |
|-----|-----|
| GitHub-Repo | `TheRealSimon42/ha-blueprints` (gh CLI ist authentifiziert, Push auf `main` ist Simons üblicher Workflow — trotzdem vor dem ersten Push der Session einmal fragen bzw. auf explizite Freigabe achten) |
| Haupt-Blueprint | `automations/cover_automation_v2.yaml` (V1 daneben ist deprecated, nicht anfassen ohne Auftrag) |
| HA-Config-Share | `/Volumes/config/` (SMB-Mount der HA-Instanz; Blueprints unter `blueprints/automation/TheRealSimon42/`) — falls nicht gemountet, Simon bitten |
| HA-Zugriff | HA-MCP-Tools (`ha_eval_template`, `ha_get_blueprint`, `ha_call_service`, `ha_config_set_automation`, `ha_get_entity`, …) — ggf. per ToolSearch laden |
| Bilder in Beschreibungen | `images/` im Repo, eingebunden über `https://cdn.jsdelivr.net/gh/TheRealSimon42/ha-blueprints@main/...` |

## Arbeitsweise — das Wichtigste zuerst

1. **Erst vollständig lesen.** Vor jeder Änderung das ganze Blueprint lesen, nicht nur
   die Stelle, um die es geht. Die Branches interagieren (mode: parallel!) — die meisten
   echten Bugs entstehen an den Wechselwirkungen, nicht in der geänderten Zeile.

2. **Best-Practices-Skill dazuladen.** Wenn der Skill `home-assistant-best-practices`
   verfügbar ist, dessen `references/blueprint-guide.md` und bei Trigger-/Condition-Fragen
   `references/automation-patterns.md` lesen. Dieser Skill hier ersetzt das nicht — er
   ergänzt es um Repo-Workflow und projektspezifische Learnings.

3. **Verifizieren statt vermuten.** Bei Unsicherheit über HA-Verhalten nicht raten:
   - Jinja-Templates mit konkreten Testwerten über `ha_eval_template` gegen die echte
     Instanz laufen lassen (Namespace-Loop mit mehreren Testfällen, siehe Referenz).
   - Schema-Fragen ("akzeptiert ein state-Trigger `entity_id: []`?") mit einer
     Wegwerf-Automation über `ha_config_set_automation` testen und sie sofort wieder
     löschen. Der Config-API-Erfolg IST die Schema-Validierung.
   - Behauptungen über Entitäten (device_class, Einheiten) mit `ha_get_entity` prüfen.

4. **Unabhängige Review nach größeren Änderungen.** Einen frischen Subagenten (ohne
   Autoren-Kontext) das geänderte Blueprint adversarial reviewen lassen: Jinja-Fehler,
   Race Conditions zwischen parallelen Branches, Trigger-Edge-Cases, Verhalten bei
   leeren/optionalen Inputs, unnötige Pflichtfelder. Findings nicht blind übernehmen —
   jedes einzeln verifizieren (Agenten liefern auch plausible Fehlalarme) und bewusst
   entscheiden, was gefixt und was nur dokumentiert wird.

5. **Input-Keys sind öffentliche API.** Nutzer haben Instanzen mit gespeicherten Werten.
   Keys nie umbenennen oder entfernen; neue Inputs bekommen immer einen `default:`,
   damit bestehende Instanzen nach Re-Import weiterlaufen. Semantik-Änderungen an
   bestehenden Keys = neue Blueprint-Datei (V2, V3, …) mit eigener `source_url`.

6. **Zustand muss Neustarts überleben.** Alles, was sich das Blueprint über Läufe hinweg
   merken muss (z.B. "Beschattung aktiv"), gehört in einen Helfer (`input_boolean`),
   nicht in Variablen oder dynamische Szenen. Dynamische `scene.create`-Szenen sind
   nach einem HA-Neustart weg — nur für Kurzfristiges (Snapshot/Restore) verwenden
   und vor `scene.turn_on` die Existenz prüfen.

7. **Nach jedem `wait_for_trigger` die Welt neu bewerten.** Während des Wartens können
   Minuten bis Stunden vergehen — Nachtmodus, Sturm oder Beschattung können inzwischen
   aktiv sein. Bedingungen, die vor dem Wait geprüft wurden, gelten danach nicht mehr.
   Das war der schwerste Bug der V2-Entwicklung (Restore öffnete Rollladen nachts).

## Kern-Regeln (hart erarbeitete Fallen)

Diese Fehler sind alle real passiert — beim Schreiben und Reviewen gezielt danach suchen:

- `repeat.index` ist **1-basiert**. Als Listenindex immer `repeat.index - 1` — oder
  besser: die Architektur so wählen, dass es keine parallelen Listen gibt
  (ein Gerät + ein Sensor pro Blueprint-Instanz statt Listen-Zuordnung über Reihenfolge).
- `!input` funktioniert **nie** in Templates. Erst im `variables:`-Block binden, in
  Trigger-Templates über `trigger_variables:`. Ein `inputs.`-Objekt existiert nicht.
- Bei `wait_for_trigger` heißt die Erfolgsprüfung `wait.trigger is not none` —
  `wait.completed` gehört zu `wait_template`.
- Optionale Entity-Inputs: `default: []` — auch wenn der Input in einem Trigger steckt
  (Trigger mit leerer Entity-Liste sind valide und feuern nie; live verifiziert).
  Area-Selector: `default: ""` (ein `{}` rendert als "Unbekannter Bereich" in der UI).
  Vor jedem `states()`/`is_state()` auf optionalen Inputs mit `x is string` guarden —
  sonst stirbt die Condition leise und der Branch tut nie etwas.
- **Pflichtfelder nur für echte Pflicht** (typisch: nur die Entities, ohne die die
  Automation sinnlos ist). Features per `enabled: !input <boolean>` am Trigger
  abschaltbar machen statt Nutzer zu Dummy-Eingaben zu zwingen.
- Numerik absichern: `| int(-1)` / `| float(0)` mit bewusstem Default, und für Cover
  ohne `current_position`-Attribut einen Fallback vorsehen (`is none` → `open_cover`
  statt Positionsfahrt, oder Branch überspringen).
- Einheiten prüfen statt annehmen: `wind_speed` u.ä. kommen je nach Integration in
  km/h, m/s oder mph — Trigger vergleichen roh. Im Zweifel Einheit der konkreten
  Entität nachsehen und die Falle in der Input-Beschreibung dokumentieren.
- Event-Trigger (z.B. `mobile_app_notification_action`) schon **im Trigger** filtern
  (`event_data` + `trigger_variables`), nicht erst in der Condition — sonst startet
  jede Instanz bei jedem Event einen Lauf.
- Notification-Texte: Jinja-Blöcke mit `{%- -%}` trimmen, `friendly_name` kann `None`
  sein (`or entity_id` als Fallback), `device_attr(id, "name")` kann `None` liefern.
- Metadata: `source_url` (Update-Anker!), `author`, `homeassistant.min_version` passend
  zu den genutzten Features (Input-Sections ≥ 2024.6, `triggers:`/`actions:`-Syntax
  ≥ 2024.10). Moderne Syntax verwenden: `triggers:`/`conditions:`/`actions:`,
  `trigger:`/`action:`-Keys — kein `platform:`/`service:`.

Für die ausgearbeiteten Muster (Status-Helfer, Manual-Override-Erkennung,
Snapshot/Restore, Beschattungs-Geometrie, Notification-Actions, Force-Optionen mit
Aussperr-Warnung) → **`references/patterns.md`** lesen, bevor eines dieser Themen
angefasst wird.

## Workflow für jede Änderung

1. Blueprint vollständig lesen; bei Architektur-/Pattern-Fragen `references/patterns.md`.
2. Änderung umsetzen. Beschreibungen der Inputs sind Teil des Produkts: Sie erklären
   dem Endnutzer das *Warum* (inkl. ⚠️-Warnungen bei Aussperr-Gefahr o.ä.) und
   dürfen Markdown inkl. Bildern enthalten.
3. **Lokal validieren:** `python3 scripts/validate_blueprint.py <datei>` (im Skill-Ordner).
   Das Script prüft YAML, !input-Referenzen, Pflichtfelder, Legacy-Syntax und die
   bekannten Template-Fallen. Fehler beheben, bevor irgendetwas deployt wird.
4. Kritische Templates mit `ha_eval_template` gegen die Live-Instanz testen
   (mehrere Testfälle, auch die Leerwert-/Grenzfälle).
5. **Deploy aufs Testsystem:** Datei nach
   `/Volumes/config/blueprints/automation/TheRealSimon42/` kopieren, dann
   `automation.reload` aufrufen — **HA cached Blueprints im Speicher**, ohne Reload
   wird die alte Version ausgeliefert. Danach mit `ha_get_blueprint` verifizieren,
   dass HA die neue Version parst (die Antwort zeigt die Inputs — stichprobenartig
   prüfen, ob die Änderung drin ist).
6. Bei größeren Änderungen: unabhängige Subagenten-Review (siehe Arbeitsweise Punkt 4).
7. **Push:** Frischen Clone in den Scratchpad (`git clone --depth 1`), Datei(en)
   hineinkopieren, committen (prägnante englische Commit-Message: was + warum),
   auf `main` pushen. Bei geänderten Bildern anschließend
   `curl https://purge.jsdelivr.net/gh/TheRealSimon42/ha-blueprints@main/<pfad>`
   und die ausgelieferte Version verifizieren — jsdelivr cached auch 404s.
8. Dem Nutzer berichten, was sich verhaltensmäßig ändert (nicht nur was am Code) —
   inklusive bekannter Nebeneffekte und bewusst NICHT gefixter Punkte.

## Grundsätze fürs Antworten

- Erst das Ergebnis, dann die Details. Bugs klar als Bugs benennen, mit konkretem
  Fehlszenario ("Fenster tagsüber auf, Nachtmodus an, Fenster zu → Rollladen öffnet
  nachts"), nicht als vage Möglichkeit.
- Trade-offs ehrlich machen: Was wurde bewusst nicht gebaut und warum (z.B. Sturm-
  Entwarnung, zweiter Helfer für perfektes Override-Tracking). Solche offenen Punkte
  am Ende explizit auflisten, damit der Nutzer entscheiden kann.
- Wenn der Nutzer eine Idee beschreibt (z.B. "Beschattung erzwingen"), das Muster
  bestehender Optionen wiederverwenden (analoge Benennung, analoge Warnungen) —
  Konsistenz im Formular ist ein Feature.
