# Home Assistant Blueprints by simon42

A collection of Home Assistant automation blueprints.

## Automations

### Intelligente Rollladensteuerung
**File:** `automations/cover_automation.yaml`

Steuert Rollläden basierend auf:
- Morgens öffnen (konfigurierbare Uhrzeit)
- Fenster-Interaktion (offen/gekippt → Rollladen reagiert)
- Nachtmodus (automatisches Schließen)
- Sturmschutz (Wind-Grenzwert mit optionalem Panzer-Modus)
- Benachrichtigungen bei zu lange offenen Fenstern

[![Import Blueprint](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https://github.com/TheRealSimon42/ha-blueprints/blob/main/automations/cover_automation.yaml)

### Synchronisiere Datum+Uhrzeit zu Uhrzeit-Helfer
**File:** `automations/convert_datetime_helper_to_time_helper.yaml`

Synchronisiert die Uhrzeit eines `input_datetime`-Helfers (mit Datum+Uhrzeit) in einen reinen Uhrzeit-Helfer. Nützlich, wenn man nur die Zeitkomponente braucht.

[![Import Blueprint](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https://github.com/TheRealSimon42/ha-blueprints/blob/main/automations/convert_datetime_helper_to_time_helper.yaml)
