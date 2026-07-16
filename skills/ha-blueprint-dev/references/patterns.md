# Blueprint-Patterns aus der Rollladensteuerung V2

Konkrete, erprobte Baupläne. Alle Beispiele nutzen moderne Syntax (2024.10+).

## Inhalt

1. [Ein-Gerät-pro-Instanz-Architektur](#1-ein-gerät-pro-instanz-architektur)
2. [Optionale Inputs & Feature-Toggles](#2-optionale-inputs--feature-toggles)
3. [Status-Helfer für persistenten Zustand](#3-status-helfer-für-persistenten-zustand)
4. [Manual-Override-Erkennung ohne Zusatz-Helfer](#4-manual-override-erkennung-ohne-zusatz-helfer)
5. [Snapshot & Restore mit scene.create](#5-snapshot--restore-mit-scenecreate)
6. [Actionable Notifications mit Instanz-Routing](#6-actionable-notifications-mit-instanz-routing)
7. [Beschattungs-Geometrie](#7-beschattungs-geometrie)
8. ["Erzwingen"-Optionen](#8-erzwingen-optionen)
9. [Bilder & Markdown in Beschreibungen](#9-bilder--markdown-in-beschreibungen)
10. [Live-Verifikation gegen die HA-Instanz](#10-live-verifikation-gegen-die-ha-instanz)

---

## 1. Ein-Gerät-pro-Instanz-Architektur

Ein Blueprint, das mehrere Geräte über **parallele Listen** zuordnet ("Reihenfolge muss
übereinstimmen!"), ist die fehleranfälligste Blueprint-UX überhaupt: Nutzer verwechseln
die Reihenfolge, und jede Index-Rechnung im Code ist eine Bug-Quelle (in V1 hatten zwei
von drei Index-Stellen einen Off-by-One über den 1-basierten `repeat.index`).

Stattdessen: **eine Instanz pro Gerät+Sensor-Paar**. Gemeinsame Einstellungen (Uhrzeit-
Helfer, Modus-Booleans, Wetter-Entität) wählen alle Instanzen identisch aus — das ist
der etablierte Community-Standard und macht Per-Gerät-Konfiguration (z.B. Fenster-
Azimut für Beschattung) überhaupt erst möglich. Der Umstieg von Listen- auf
Einzel-Architektur bricht bestehende Instanzen → immer neue Datei (V2) mit eigener
`source_url`, alte Version als deprecated stehen lassen.

## 2. Optionale Inputs & Feature-Toggles

Ziel: Pflichtfelder nur da, wo ohne Eingabe nichts funktioniert. Alles andere optional.

```yaml
# Feature-Schalter deaktiviert den Trigger komplett (statisch, beim Laden ausgewertet):
triggers:
  - trigger: time
    at: !input morning_time
    id: morning_open
    enabled: !input morning_enabled

# Optionaler Entity-Input, der in einem Trigger steckt:
morning_time:
  default: [] # leere Liste: Trigger ist valide, feuert nie (live verifiziert)
  selector:
    entity:
      domain: input_datetime

# Optionaler Area-Input:
mosquito_area:
  default: "" # NICHT {} — das rendert als "Unbekannter Bereich" in der UI
  selector:
    area: {}
```

In Templates jeden optionalen Input guarden, weil `[]`/`""` sonst Laufzeitfehler oder
leise False-Conditions erzeugen:

```yaml
- "{{ not (night_mode_boolean is string and is_state(night_mode_boolean, 'on')) }}"
```

Fallback-Ketten explizit machen (`is string` = "wurde gesetzt"):

```jinja
{% if shading_temp_sensor is string %}
  {{ states(shading_temp_sensor) | float(-99) }}
{% elif weather_entity is string %}
  {{ state_attr(weather_entity, 'temperature') | float(-99) }}
{% else %}
  -99
{% endif %}
```

Der `-99`-Default ist bewusst gewählt: Er lässt die Start-Bedingung (`>= Schwelle`)
sicher scheitern → Feature ohne Datenquelle ist einfach aus, statt zu spinnen.

## 3. Status-Helfer für persistenten Zustand

Blueprints haben keinen eigenen Speicher. Für Zustand, der Läufe und HA-Neustarts
überleben muss ("Beschattung ist aktiv"), einen `input_boolean` pro Instanz als Input
verlangen (optional mit `default: []`, Feature prüft `is string`).

Regeln aus der Praxis:

- Helfer erst **nach** der zugehörigen Aktion setzen bzw. beim Feature-Start —
  und beim Beenden **zuerst** zurücksetzen, dann fahren.
- Jeder Branch, der das Feature logisch beendet (z.B. Nachtmodus schließt den
  Rollladen), muss den Helfer mit zurücksetzen — sonst feuert das "Feature-Ende"
  zur Unzeit (morgens beim ersten Tick).
- Ohne gesetzten Helfer schlägt das Feature still fehl → in der Beschreibung des
  Enable-Schalters UND des Helfer-Inputs deutlich machen ("zwingend erforderlich").

## 4. Manual-Override-Erkennung ohne Zusatz-Helfer

Problem: Ein periodischer Nachführ-Tick (z.B. alle 5 Min) überschreibt manuelle
Eingriffe → Ping-Pong zwischen Nutzer und Automation.

Kernidee: Zwischen zwei Ticks ändert sich die berechnete Sollposition nur um wenige
Prozent (die Sonne wandert ~1°/4min). Eine große Abweichung Ist↔Soll kann also nur ein
manueller Eingriff sein:

```yaml
# Im Tick, wenn Status-Helfer bereits 'on' (Feature läuft):
- if:
    - "{{ deviation >= shading_min_change and deviation <= shading_override_threshold }}"
  then: [nachführen]
# deviation < min_change: nichts zu tun (Motorschonung)
# deviation > override_threshold: manueller Eingriff → in Ruhe lassen bis Feature-Ende
```

Wichtig: Die **Anfangsbewegung** (Helfer war 'off') ist von der Toleranz ausgenommen —
der erste Sprung ist immer groß. Bekannter Nebeneffekt (dokumentieren!): Fremde große
Bewegungen (z.B. Sturmschutz fährt hoch) sehen ebenfalls wie manuelle Eingriffe aus →
Feature pausiert bis zum regulären Ende. Perfekte Erkennung bräuchte einen
`input_number`-Helfer für die letzte Sollposition — bewusster Trade-off.

## 5. Snapshot & Restore mit scene.create

Für "Position merken → temporär ändern → wiederherstellen":

```yaml
# Snapshot NUR beim Übergang aus "nicht offen" (verhindert, dass gekippt→offen den
# Snapshot mit der bereits veränderten Position überschreibt; unavailable/unknown zählen
# als "nicht offen", damit nach Neustarts trotzdem gesichert wird):
- if:
    - "{{ trigger.from_state is not none and trigger.from_state.state not in ['on', 'open', 'tilted'] }}"
  then:
    - action: scene.create
      data:
        scene_id: "{{ 'reclose_' ~ (cover_entity | slugify) }}"
        snapshot_entities: ["{{ cover_entity }}"]

# Restore — drei Guards:
# 1. Existenz (Szenen aus scene.create überleben keinen HA-Neustart):
- "{{ states(reclose_scene) not in ['unknown', 'unavailable'] }}"
# 2./3. Zustand NACH dem Wait neu bewerten — Nachtmodus/Sturm können während des
# Wartens aktiv geworden sein; dann schließen bzw. gar nichts tun statt restaurieren.
```

Der Restore-ohne-Neubewertung-Bug war der schwerste der V2-Entwicklung: Fenster
tagsüber auf (Snapshot = offen), Nachtmodus kommt, Fenster zu → Restore öffnete den
Rollladen mitten in der Nacht.

## 6. Actionable Notifications mit Instanz-Routing

Mehrere Blueprint-Instanzen empfangen ALLE `mobile_app_notification_action`-Events.
Deshalb: Action-ID pro Instanz eindeutig machen und schon **im Trigger** filtern —
`event_data` unterstützt Limited Templates über `trigger_variables`:

```yaml
trigger_variables:
  window_sensor_tv: !input window_sensor

triggers:
  - trigger: event
    event_type: mobile_app_notification_action
    event_data:
      action: "CLOSE_SHUTTER__{{ window_sensor_tv }}"
    id: close_shutter_action
```

Notify-Services aus Geräte-Auswahl ableiten (mobile_app-Muster), mit None-Guard für
gelöschte Geräte:

```jinja
{% set ns = namespace(names=[]) %}
{% for device_id in notification_device %}
  {% set n = device_attr(device_id, "name") %}
  {% if n %}{% set ns.names = ns.names + ["mobile_app_" + n | slugify] %}{% endif %}
{% endfor %}
{{ ns.names }}
```

Texte: `{%- -%}` gegen Whitespace, `friendly_name or entity_id` gegen None-Anzeige.

## 7. Beschattungs-Geometrie

Eingaben, die ein Endnutzer messen kann: Fenster-Azimut, Fensterhöhe H, Brüstungshöhe
h_sill, maximale Sonneneinfall-Tiefe d (am Boden gemessen).

```jinja
{# Winkeldifferenz Sonne↔Fenster, wrap-sicher in [-180, 180): #}
{% set az_diff = ((sun_azimuth - window_azimuth + 180) % 360) - 180 %}
{# Sonne "im Fenster": #}
{% set sun_in_window = sun_elevation >= min_elevation
   and az_diff >= (0 - fov_left) and az_diff <= fov_right %}
{# Erlaubte Strahlhöhe an der Fensterebene; cos-Korrektur für Schräglicht,
   geklemmt gegen Division durch ~0 am FOV-Rand: #}
{% set ray_height = d * tan(sun_elevation * pi / 180)
   / ([cos(az_diff * pi / 180), 0.087] | max) %}
{# In Cover-Position (100 = offen) umrechnen und klemmen: #}
{% set raw = ((ray_height - h_sill) / H * 100) | round(0) | int %}
{% set p = [[raw, min_position | int, 0] | max, 100] | min %}
```

Sichtfeld-Semantik (häufige Nutzer-Frage): 90° pro Seite ist das geometrische Maximum
(Sonne in der Fassadenebene) — der Default. Verkleinern nur bei realen Hindernissen.
Links/rechts = am Fenster stehend nach draußen geschaut (Südfenster: links = Osten).
Flacher Einfall wird durch die cos-Korrektur automatisch milder behandelt — das
Sichtfeld muss dafür nicht eingeengt werden.

Weitere Zutaten des Beschattungs-Branches: Temperatur-Schwelle mit Hysterese
(Ende erst bei `Schwelle - Hysterese`), Sturm-Check (nicht beschatten bei Starkwind),
Nachtmodus-Check, Fenster-offen-Check, Mindest-Positionsänderung (Motorschonung),
Lüftungsspalt-Klemme bei gekipptem/offenem Fenster (`max(p, tilted_position)`).
Periodik: `time_pattern`-Trigger `/5` Minuten, `enabled: !input shading_enabled`.

## 8. "Erzwingen"-Optionen

Muster für "Automatik soll auch im eigentlich blockierten Fall handeln" (Sturm trotz
offenem Fenster, Beschattung trotz offenem Fenster):

- Boolean-Input, Default `false`, Name "<Aktion> erzwingen".
- Beschreibung nennt den Nutzen UND die Gefahr: `⚠️ Achtung: Aussperr-Gefahr!` bzw.
  "für Balkon-/Terrassentüren nicht empfohlen". Nutzer entscheiden pro Instanz.
- Sicherheitsnetz einbauen, wo möglich (bei erzwungener Beschattung bleibt mindestens
  die Kipp-Position als Lüftungsspalt).
- Wechselwirkungen prüfen: Wenn ein anderer Branch die erzwungene Aktion sofort
  rückgängig machen würde (Fenster-öffnen fährt hoch ↔ Beschattung fährt runter),
  den konkurrierenden Branch für die Dauer des erzwungenen Zustands unterdrücken.

## 9. Bilder & Markdown in Beschreibungen

Blueprint- und Sektions-Beschreibungen rendern Markdown inkl. Bildern — ideal für
Erklärgrafiken bei erklärungsbedürftigen Inputs (z.B. Sichtfeld-Geometrie).

- SVG selbst-eingefärbt bauen: weiße Karte als Hintergrund-Rect, feste Farben —
  die Grafik muss in hellem UND dunklem HA-Theme lesbar sein.
- Ins Repo unter `images/`, einbinden über
  `https://cdn.jsdelivr.net/gh/TheRealSimon42/ha-blueprints@main/images/<name>.svg`.
  **Nicht** `raw.githubusercontent.com` für SVGs — falscher Content-Type, Browser
  zeigen nichts an. (Für die YAML-`source_url` ist raw dagegen richtig.)
- Nach jedem Bild-Update: `curl https://purge.jsdelivr.net/gh/...` und die
  ausgelieferte Version prüfen — jsdelivr cached aggressiv, auch 404s.
- Zeichenreihenfolge in SVGs: Flächen zuerst, Texte zuletzt; Kollisionen zwischen
  Labels, Pfeilen und Flächen aktiv prüfen (der häufigste Grafik-Fehler).

## 10. Live-Verifikation gegen die HA-Instanz

- **Template testen** (`ha_eval_template`): Testfälle als Liste von Dicts, per Loop
  durchrechnen, Ergebniszeilen ausgeben. Immer auch Grenzfälle: leere Inputs (`[]`,
  `""`), `unavailable`, Werte außerhalb des Sichtfelds, negative Elevation.
- **Schema testen** (`ha_config_set_automation` → `ha_config_remove_automation`):
  Wegwerf-Automation mit der fraglichen Trigger-Form anlegen; Erfolg = Schema ok.
  Danach IMMER löschen.
- **Deploy verifizieren** (`ha_get_blueprint` mit `path="TheRealSimon42/<datei>"`):
  Nach `cp` + `automation.reload` prüfen, ob die Antwort die neue Änderung enthält.
  Kommt der alte Stand zurück → Reload vergessen (Blueprint-Cache).
- **Entitäten prüfen** (`ha_get_entity`): device_class, Einheiten, original_name —
  bevor Selector-Filter oder Einheiten-Annahmen ins Blueprint wandern.
