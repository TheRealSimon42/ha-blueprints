# Intelligente Rollladensteuerung — Dokumentation

**Blueprint:** `automations/cover_automation_v2.yaml` · Mindestversion: Home Assistant 2024.10

[![Import Blueprint](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https://github.com/TheRealSimon42/ha-blueprints/blob/main/automations/cover_automation_v2.yaml)

## Konzept

**Eine Automation pro Fenster/Rollladen-Paar.** Du legst für jedes Fenster eine eigene
Instanz aus diesem Blueprint an und wählst dort genau einen Rollladen und — wenn
vorhanden — genau einen Fensterkontakt aus. Als Fensterkontakt funktionieren klassische
binäre Sensoren (offen/geschlossen) genauso wie Drei-Zustands-Sensoren
(offen/gekippt/geschlossen, auch mit großgeschriebenen Zuständen wie `Tilted`).
Gemeinsame Einstellungen — die Uhrzeit fürs morgendliche Öffnen, der Nachtmodus-Helfer,
die Wetter-Entität — sind Helfer, die du einfach in allen Instanzen identisch auswählst.

Warum so? Weil jedes Fenster eigene Eigenschaften hat (Ausrichtung, Größe, Balkontür
oder nicht) und weil damit jede Instanz für sich verständlich, testbar und abschaltbar
bleibt. Nur **ein** Feld ist Pflicht: der Rollladen. Der Fenstersensor ist optional —
festverglaste Fenster ohne Kontakt bekommen trotzdem Morgens-Öffnen, Nachtmodus,
Sturmschutz, Beschattung, Sonnenheizen und Frostschutz; nur die fensterbezogenen
Funktionen (Fenster-Interaktion, Benachrichtigungen, Moskito-Modus) entfallen dann.
Jedes Feature darüber hinaus ist per Schalter zuschaltbar.

## Einrichtung

1. **Blueprint importieren** (Button oben) und unter _Einstellungen → Automatisierungen
   & Szenen → Blueprints_ eine Instanz pro Fenster anlegen.
   Wichtig beim manuellen Import: die **URL der Blueprint-Datei** verwenden
   (`https://github.com/TheRealSimon42/ha-blueprints/blob/main/automations/cover_automation_v2.yaml`),
   nicht die Adresse des Repositories — die Repo-URL liefert eine HTML-Seite und
   endet in einem YAML-Fehler ("mapping values are not allowed here").
2. **Rollladen zuordnen** (und den Fenstersensor, falls es einen gibt) — mehr braucht
   es für den Start nicht.
3. **Je nach gewünschten Features Helfer anlegen** (_Einstellungen → Geräte & Dienste →
   Helfer_):
   - Morgens öffnen: ein `input_datetime`-Helfer, **nur mit Uhrzeit, ohne Datum**
     (ein Datum+Zeit-Helfer feuert nur ein einziges Mal!). Einer für alle Instanzen.
     Alternativ oder zusätzlich: "Mit dem Sonnenaufgang öffnen" aktivieren — es gilt
     dann der spätere der beiden Zeitpunkte.
   - Nachtmodus: ein `input_boolean` (z. B. "Nacht-Modus"), ein **Zeitplan-Helfer**
     (Schedule) oder ein beliebiger Binärsensor. Einer für alle Instanzen; "an" heißt
     Nacht. Mit einem Zeitplan-Helfer schließen die Rollläden automatisch zum
     Blockbeginn — ganz ohne eigene Zusatz-Automation.
   - Sonnenschutz: ein `input_boolean` **pro Fenster** als Status-Speicher,
     Namensvorschlag: "Beschattung <Fenstername>".
   - Sonnenheizen: ein **weiterer** `input_boolean` pro Fenster (nicht denselben wie
     für den Sonnenschutz verwenden!).
4. Für Sonnenschutz/Sonnenheizen die **Fenstergeometrie** eintragen (Ausrichtung in
   Grad, Sichtfeld, Fensterhöhe, Brüstungshöhe) — Details unten.

Fehlt ein zwingend nötiger Helfer bei aktiviertem Feature, meldet sich die Automation
selbst: Eine dauerhafte Benachrichtigung in Home Assistant benennt das betroffene
Fenster, bis der Helfer gesetzt oder das Feature deaktiviert ist.

## Die Features im Überblick

| Feature             | Was es tut                                                                                                                                                               | Voraussetzung                                                        |
| ------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------- |
| Morgens öffnen      | Fährt zur eingestellten Uhrzeit und/oder zum Sonnenaufgang auf die Zielposition (nur wenn geschlossener); optional erst bei der ersten Bewegung im Raum                  | `input_datetime`-Helfer (nur Uhrzeit) und/oder Sonnenaufgangs-Option |
| Fenster-Interaktion | Kippen → Lüftungsposition, Öffnen → ganz auf (optional: wie Kippen behandeln); nach dem Schließen zurück in die Ausgangsposition                                         | Fenstersensor                                                        |
| Nachtmodus          | Schließt beim Einschalten des Helfers (wahlweise auf eine Nacht-Zielposition statt ganz zu); offene/gekippte Fenster bekommen eine Lüftungsposition                      | `input_boolean`, Zeitplan oder Binärsensor                           |
| Sturmschutz         | Fährt bei Starkwind hoch (oder im Panzer-Modus herunter)                                                                                                                 | Wetter-Entität oder Wind-Sensor                                      |
| Sonnenschutz        | Beschattet anhand des Sonnenstands so, dass die Sonne höchstens X m in den Raum fällt; öffnet nach Ende wieder; optional an eine Freigabe-Entität (PV, Lux, …) gekoppelt | Status-Helfer, Geometrie, Temperaturquelle                           |
| Sonnenheizen        | Öffnet im Winter vergessene Rollos, wenn Sonne ins Fenster scheint und es kalt ist                                                                                       | eigener Status-Helfer, Geometrie                                     |
| Frostschutz         | Begrenzt bei Frost alle automatischen Aufwärts-Fahrten auf eine schonende Maximal-Position (festgefrorener Panzer)                                                       | Außentemperatur-Sensor                                               |
| Moskito-Modus       | Schaltet beim Fensteröffnen nach Sonnenuntergang die Lichter im Raum aus (mit Ausnahmen)                                                                                 | Fenstersensor                                                        |
| Benachrichtigungen  | Meldet zu lange offene/gekippte Fenster aufs Handy, mit "Rollladen schließen"-Button; verschwindet automatisch beim Schließen                                            | Companion-App-Geräte, Fenstersensor                                  |
| Pausieren           | Hält die komplette Automation an, solange ein Helfer eingeschaltet ist — z.B. während Videoaufnahmen oder wenn Gäste schlafen                                            | `input_boolean`-Helfer (optional)                                    |
| Nach Neustart       | Holt nach einem HA-Neustart ein verpasstes Morgens-Öffnen (bis 2 h danach) nach bzw. stellt einen aktiven Nachtmodus wieder her                                          | — (Schalter, standardmäßig aus)                                      |

**Prioritäten:** Der **Sturmschutz gewinnt immer** — bei Starkwind bewegen weder
Morgens-Öffnen noch Beschattung, Sonnenheizen oder das Zurückfahren den Rollladen,
und auch der Pausier-Helfer hält ihn nicht auf (Schutz der Hardware geht vor).
Danach kommt die Pause (solange ihr Helfer an ist, passiert sonst gar nichts),
dann der Nachtmodus (nachts wird nicht beschattet, nicht geheizt und beim
Fensteröffnen nur bis zur Lüftungsposition geöffnet), dann der Frostschutz als
Begrenzer aller Öffnungs-Fahrten, dann erst die Komfort-Features.

## Verhalten verstehen

### Morgens öffnen: Uhrzeit, Sonnenaufgang, Bewegung

Der Klassiker ist die feste Uhrzeit über den `input_datetime`-Helfer. Mit
**"Mit dem Sonnenaufgang öffnen"** kommt die Astro-Variante dazu: Geöffnet wird zum
Sonnenaufgang (plus/minus einstellbarer Verschiebung), aber **nie vor** der
eingestellten Uhrzeit — es gilt der spätere der beiden Zeitpunkte. Im Sommer schützt
die Uhrzeit also vor dem 5-Uhr-Sonnenaufgang, im Winter wartet das Öffnen auf die
tatsächliche Helligkeit. Ohne gesetzten Uhrzeit-Helfer zählt allein der Sonnenaufgang.

Ein aktiver **Nachtmodus hat dabei Vorrang**: Liegt der Öffnungszeitpunkt noch im
Nacht-Block (Sommer-Sonnenaufgang um 5, Schedule sagt bis 6:30 Nacht), öffnet der
Rollladen nicht — stattdessen holt das **Ende des Nachtmodus** das verpasste Öffnen
nach. Ein Zeitplan-Helfer als Nachtmodus steuert damit beides: Schließen zum
Blockbeginn, Öffnen zum Blockende (sofern der reguläre Öffnungszeitpunkt schon
vorbei ist).

Für selten genutzte Räume (Gästezimmer, Hobbyraum) gibt es **"Morgens nur bei
Bewegung öffnen"**: Mit gesetztem Bewegungs-/Präsenzsensor öffnet der Rollladen
morgens nicht automatisch, sondern erst bei der ersten Bewegung im Raum — frühestens
zur Uhrzeit-Untergrenze, nur tagsüber, nicht bei aktivem Nachtmodus und nur, solange
der Rollladen noch (nacht-)geschlossen ist. Wird der Raum den ganzen Tag nicht
betreten, bleibt der Rollladen unten und auch die Abend-Fahrt entfällt (er ist ja
schon zu).

### Frostschutz

Bei Minusgraden frieren Rollladenpanzer gern am Fensterbrett oder in den
Führungsschienen fest; fährt der Motor dann auf Anschlag, reißen Gurt oder Lamellen.
Sobald ein Außentemperatur-Sensor im Frostschutz-Abschnitt gesetzt ist (es darf
derselbe sein wie beim Sonnenschutz), werden bei Temperaturen auf/unter der Schwelle
**alle automatischen Aufwärts-Fahrten** — Morgens-Öffnen, das Hochfahren beim Lüften,
Sonnenheizen und sogar die Sturm-Öffnung — auf die eingestellte Maximal-Position
(Standard 90 %) begrenzt. Die letzten Prozent, die den festgefrorenen Panzer
abreißen würden, entfallen. Schließen ist immer uneingeschränkt erlaubt; eine
Hysterese braucht es nicht, weil nur einzelne Fahrten begrenzt werden und nichts
zyklisch nachregelt.

### Sichtfeld und Geometrie

![Sichtfeld-Erklärung](https://cdn.jsdelivr.net/gh/TheRealSimon42/ha-blueprints@main/images/sichtfeld_beschattung.svg)

Die Ausrichtung ist die Himmelsrichtung des Fensters in Grad (180 = Süd). Das
Sichtfeld (Standard 90° je Seite) beschreibt das geometrische Maximum: Bei 90°
Abweichung steht die Sonne in der Fassadenebene und kann das Fenster gerade noch
treffen. Verkleinere es nur, wenn real etwas im Weg steht (Laibung, Balkon,
Nachbarhaus). Sehr flach einfallende Sonne wird automatisch milder behandelt — je
schräger der Winkel, desto weiter oben bleibt der Rollladen. Links/rechts gilt von
innen am Fenster stehend: Beim Südfenster ist links die Vormittagsseite (Osten).

Aus Fensterhöhe, Brüstungshöhe und der maximal erlaubten Sonneneinfall-Tiefe berechnet
die Automation alle 5 Minuten die Position, bei der die Sonne höchstens bis zur
eingestellten Tiefe auf den Boden fällt, und führt den Rollladen der Sonne nach.

Standardmäßig nimmt die Berechnung an, dass die Motor-Prozente des Rollladens linear
der freien Glasfläche entsprechen. Real hat der Laufweg aber Totzonen: Unten sitzt der
Panzer irgendwann auf und nur noch die Lamellen schließen sich, oben wird nur noch in
den Kasten eingezogen. Mit der **Glas-Kalibrierung** (Aufsetz-Punkt und oberer
Glas-Endpunkt im Sonnenschutz-Abschnitt) rechnet die Beschattung in echter Glasfläche:
Aufsetz-Punkt ermitteln = Rollladen langsam herunterfahren, bis der Lichtspalt unten
gerade verschwindet. Netter Nebeneffekt: Die Beschattung fährt dann nie unter den
Aufsetz-Punkt — die Lamellen bleiben immer offen.

### Freigabe-Entität: PV, Helligkeit & Co. an die Beschattung koppeln

Die Beschattung rechnet bewusst nur mit Sonnenstand, Temperatur und (optional)
Wetterlage. Für alles darüber hinaus gibt es die **Freigabe-Entität**: Ist dort eine
Entität gesetzt, beschattet die Automation nur, solange diese "on" ist — und beendet
eine laufende Beschattung, wenn sie mindestens 10 Minuten stabil "off" ist. Damit
lässt sich jede eigene Bedingung anbinden, ohne dass das Blueprint sie kennen muss.
Zwei Beispiele als Template-Binärsensor in der `configuration.yaml`:

```yaml
template:
  - binary_sensor:
      # Beschattung nur bei echter Einstrahlung (PV-Leistung als Sonnen-Beweis)
      - name: "Beschattung erlaubt (PV)"
        state: "{{ states('sensor.pv_leistung') | float(0) > 2000 }}"
        delay_off: "00:10:00"
      # Beschattung nur ab einer Helligkeit (Lux-Sensor)
      - name: "Beschattung erlaubt (Helligkeit)"
        state: "{{ states('sensor.helligkeit_terrasse') | float(0) > 40000 }}"
        delay_off: "00:10:00"
```

Ein `delay_off` im Sensor glättet zusätzlich; die 10-Minuten-Trägheit im Blueprint
verhindert in jedem Fall, dass eine flatternde Quelle den Rollladen im
5-Minuten-Takt fahren lässt. Bei "unavailable" startet keine neue Beschattung, eine
laufende bleibt bestehen.

### Manuelle Eingriffe während der Beschattung

Die Automation weiß nie, _wer_ den Rollladen bewegt hat — sie vergleicht bei jedem
Tick nur die Ist-Position mit ihrem berechneten Sollwert:

- Abweichung **unter 5 %**: nichts zu tun (Motorschonung).
- **5–20 %**: normales Nachführen der Sonne.
- **über 20 %**: Das kann keine Sonnenwanderung sein — ein Mensch war am Werk. Der
  Rollladen wird in Ruhe gelassen.

Diese "Sperre" gilt **bis zum Ende der laufenden Beschattungs-Episode** (Sonne
verlässt das Sichtfeld, es kühlt ab, oder der Nachtmodus kommt). Das Episoden-Ende
öffnet den Rollladen dann regulär — auch über die manuelle Position hinweg. Am
nächsten Tag beginnt alles bei null; die Anfangsbewegung ist von der Toleranz
ausgenommen. Stellst du den Rollladen manuell ungefähr dorthin, wo die Beschattung
ihn haben will, übernimmt das Nachführen wieder stillschweigend. Sturm, Lüften und
Morgens-Öffnen zählen dagegen nicht als manuelle Eingriffe — nach ihnen darf sofort
wieder beschattet werden.

Wer die Beschattung dauerhaft nicht will, deaktiviert den Schalter "Sonnenschutz
aktivieren" in der Instanz — der Status-Helfer ist **kein** Ausschalter, er ist das
interne Gedächtnis der Automation und stellt sich bei Handbetätigung einfach zurück.

### Warum die Status-Helfer nötig sind

Blueprints haben keinen eigenen Speicher, und bei Funk-Rollläden lässt sich aus den
Zustandsdaten nicht ablesen, ob die letzte Bewegung von der Automation oder vom
Wandtaster kam (die Positions-Rückmeldung kommt immer vom Gerät selbst). Ein
`input_boolean` pro Fenster ist der einzige Weg, "die Beschattung läuft gerade"
neustartfest zu speichern — und genau darauf bauen das automatische Wiederöffnen,
die Einmal-Logik des Sonnenheizens und die Eingriffs-Erkennung auf.

### Nach einem Neustart von Home Assistant

Zeitpunkt-Ereignisse gibt es nur, solange Home Assistant läuft: Fällt der
Morgens-Zeitpunkt (Uhrzeit bzw. Sonnenaufgang) in einen Neustart (typisch: ein Update
am frühen Morgen), bleibt der Rollladen an diesem Tag zu. Ebenso kann ein kurz vor
dem Herunterfahren eingeschalteter Nachtmodus seinen Fahrbefehl verlieren. Mit dem
Schalter **"Nach Neustart nachholen"** (Abschnitt "Nach HA-Neustart", standardmäßig
aus) bewertet die Automation den Zustand 60 Sekunden nach dem Start neu — dann sind
Integrationen, Rollladen und Sensoren in der Regel wieder verfügbar:

1. **Pause aktiv oder Sturm?** Dann passiert nichts.
2. **Morgens-Zeitpunkt höchstens 2 Stunden her?** Dann fährt der Rollladen wie beim
   Morgens-Öffnen auf die Zielposition, sofern er geschlossener ist. Der
   Morgens-Zeitpunkt wird dabei genauso bestimmt wie beim regulären Öffnen (im
   Sonnenaufgangs-Modus der spätere von Sonnenaufgang und Uhrzeit), und auch der
   Frostschutz begrenzt die Fahrt. Ein noch eingeschalteter Nachtmodus hat wie dort
   Vorrang: Der Rollladen bleibt zu, das Öffnen holt dann das Ende des Nachtmodus
   nach. Im Bewegungs-Modus wird nichts nachgeholt — dort öffnet die nächste Bewegung
   im Raum. Läuft gerade eine Beschattung oder hat Sonnenheizen geöffnet
   (Status-Helfer an), bleibt der Rollladen, wie er ist.
3. **Nachtmodus an und es ist Nacht?** "Nacht" heißt hier: Die Sonne steht unter dem
   Horizont, und es ist Abend oder der Morgens-Zeitpunkt steht noch bevor (ohne
   Morgens-Öffnen und im Bewegungs-Modus gilt die Nacht bis Sonnenaufgang). Dann wird
   der Nachtzustand hergestellt wie beim Einschalten des Nachtmodus — bei geschlossenem
   Fenster (oder ohne Fenstersensor) zu bzw. auf die Nacht-Zielposition, bei gekipptem
   oder offenem Fenster die Lüftungsposition.
   Anders als beim Einschalten fährt der Rollladen bei gekipptem oder offenem Fenster
   dabei nur hoch, nie herunter: Der Neustart kommt zu einem beliebigen Zeitpunkt, und
   wer gerade auf dem Balkon steht, soll nicht ausgesperrt werden. Ist ein
   Fensterkontakt ausgewählt, aber nicht verfügbar, wird nichts bewegt.

Tagsüber wird ein noch eingeschalteter Nachtmodus bewusst **nicht** wiederhergestellt:
Ist der Rollladen dann offen, hat ihn jemand trotz Nachtmodus von Hand geöffnet — ein
Neustart soll ihn nicht mitten am Tag schließen.

**Warum nur 2 Stunden?** Das Nachholen soll einen Neustart _über_ den
Morgens-Zeitpunkt hinweg abfangen. Je später der Neustart, desto wahrscheinlicher ist
ein geschlossener Rollladen Absicht — Mittagsschlaf, Kinderzimmer, Hitze. Ein Öffnen
am Nachmittag wäre dann kein Nachholen, sondern ein Fehler.

Beschattung und Sonnenheizen brauchen kein Nachholen: Ihre 5-Minuten-Durchläufe
übernehmen nach dem Start von selbst.

## Bekannte Grenzen

- **Wind-Sensor kurz nicht verfügbar** zählt als "windstill". Bewusste Entscheidung:
  Ein dauerhaft toter Sensor soll nicht sämtliche Komfort-Funktionen lahmlegen. Der
  Sturmschutz selbst hat beim Überschreiten des Grenzwerts längst ausgelöst.
- **Wetterlagen-Filter:** Flattert das Wetter zwischen zwei _nicht_ erlaubten Lagen
  (z. B. Regen ↔ Starkregen), beendet erst Sonnenstand oder Temperatur die
  Beschattung. Der Filter beendet nur bei mindestens 10 Minuten stabil schlechter Lage.
- **Cover ohne Positions-Angabe** (nur auf/zu): Morgens-Öffnen funktioniert,
  Kipp-Position, Beschattung, Nacht-Zielposition und Frost-Begrenzung werden
  übersprungen — sie brauchen Positionsdaten.
  Nach einem Neustart wird das Morgens-Öffnen bei ihnen nur nachgeholt, wenn sie als
  geschlossen gemeldet werden (nicht bei "unbekannt").
- **Windgeschwindigkeit** wird roh mit dem Grenzwert verglichen — liefert deine Quelle
  m/s statt km/h, muss der Grenzwert entsprechend gesetzt werden.
- **Sturm-Ende:** Nach dem Sturm bleibt der Rollladen in der Schutzposition, bis das
  nächste reguläre Ereignis (Nachtmodus, Morgens, Beschattung) ihn übernimmt.
- **Bewegungs-Öffnen** reagiert auf jede Bewegung, solange seine Bedingungen stimmen:
  Wird der Rollladen tagsüber von Hand wieder komplett geschlossen und dann der Raum
  betreten, öffnet er erneut. Wer das nicht will, nutzt den Pausier-Helfer.
- **Frostschutz** begrenzt die automatischen Fahrten, nicht das Zurückfahren auf eine
  gemerkte Ausgangsposition nach dem Lüften (die war ja bereits erreicht).
- **Neustart während des Lüftens:** Das Zurückfahren nach dem Schließen des Fensters
  wird nicht nachgeholt — die gemerkte Ausgangsposition und die Wartezeit gehen beim
  Neustart verloren. Der Rollladen bleibt in der Lüftungsposition, bis das nächste
  reguläre Ereignis ihn übernimmt.
- **Nachholen nach Neustart** kann nicht unterscheiden, ob ein Ereignis verpasst,
  bewusst ausgelassen oder danach von Hand rückgängig gemacht wurde: Innerhalb der
  2 Stunden nach dem Morgens-Zeitpunkt öffnet ein Neustart auch einen Rollladen, den
  jemand nach dem Morgens-Öffnen wieder geschlossen hat oder dessen Morgens-Öffnen in
  eine Pause fiel. Bei aktivem Nachtmodus fährt ein nachts von Hand geöffneter
  Rollladen bei geschlossenem Fenster wieder zu. Das ist bewusst so: Ohne den Schalter
  wertet die Automation einen Neustart gerade nicht als Einschalten des Nachtmodus —
  dessen Trigger reagiert nur auf "aus" → "an", damit ein Sensor, der beim Start von
  "unbekannt" auf "an" springt, nicht nachts alle Rollläden zufährt. Wer das Nachholen
  einschaltet, entscheidet sich ausdrücklich dafür, den Nachtzustand nach einem
  Neustart wiederherzustellen.
- **Veralteter Fensterkontakt nach Neustart:** Manche Integrationen stellen nach dem
  Start den letzten bekannten Zustand wieder her, und batteriebetriebene Kontakte
  melden sich erst bei der nächsten Änderung. Wurde die Balkontür während des
  Neustarts geöffnet und meldet der Kontakt noch "zu", schließt das Nachholen bei
  aktivem Nachtmodus den Rollladen — ⚠️ Aussperr-Gefahr.
- **Grenzen des Nachholens:** Wird der Nachtmodus-Helfer selbst zeitgesteuert
  geschaltet und fiel dieser Zeitpunkt in den Neustart, ist der Helfer noch aus — dann
  gibt es nichts nachzuholen. Endet der Nachtmodus während des Neustarts, wird das
  Öffnen nur nachgeholt, wenn der Morgens-Zeitpunkt höchstens 2 Stunden zurückliegt.
  Steht die Sonne über dem Horizont oder ist der Morgens-Zeitpunkt (nach Mitternacht)
  schon vorbei, wird ein aktiver Nachtmodus nicht wiederhergestellt — ohne die
  Integration "Sonne" (`sun.sun`) also nie. Ist der Rollladen nach 60 Sekunden noch
  nicht verfügbar, unterbleibt das Nachholen; ist ein Fensterkontakt ausgewählt, aber
  nicht verfügbar, wird der Nachtzustand nicht hergestellt. Einen zweiten Versuch gibt
  es nicht. Ein bloßes Neuladen der Automationen zählt nicht als Neustart.

## FAQ

**Der Import schlägt fehl mit "mapping values are not allowed here"?** Dann wurde die
Repository-URL statt der Blueprint-URL importiert. Richtig ist die Datei-URL:
`https://github.com/TheRealSimon42/ha-blueprints/blob/main/automations/cover_automation_v2.yaml`
— am einfachsten über den Import-Button oben.

**Was bedeuten 0 % und 100 % bei den Positionen?** Das Blueprint folgt der
Home-Assistant-Konvention: 100 % = ganz offen, 0 % = ganz geschlossen. Die Prozente
sind dabei die Werte deines Cover-Aktors, also Motor-Laufweg — nicht zwingend
Glasfläche. Für die Beschattung lässt sich dieser Unterschied über die
Glas-Kalibrierung (siehe oben) ausgleichen; alle anderen Positions-Eingaben
(morgens, Kipp-Position, Nachtlüftung) sind bewusst direkte Aktor-Werte.

**Ich habe gar keinen Fenstersensor — geht das?** Ja, das Feld einfach leer lassen.
Morgens-Öffnen, Nachtmodus, Sturmschutz, Beschattung, Sonnenheizen und Frostschutz
funktionieren ohne; nur Fenster-Interaktion, Benachrichtigungen und Moskito-Modus
brauchen den Sensor. Der früher nötige "Fake-Fensterkontakt"-Workaround ist damit
überflüssig.

**Mehrere Kontakte an einem Rollladen (Doppelflügel, Fliegengittertür)?** In Home
Assistant eine **Binärsensor-Gruppe** anlegen (_Helfer → Gruppe → Binärsensor-Gruppe_)
und der Gruppe die Geräteklasse "Fenster" geben — dann taucht sie im Sensor-Feld auf.
Die Gruppe ist "offen", sobald ein Kontakt offen ist: Der Rollladen fährt erst zu,
wenn alle Flügel (und die Fliegengittertür) geschlossen sind. Drei-Zustands-Logik
(gekippt) geht dabei verloren — die Gruppe kennt nur offen/zu.

**Mein Sensor meldet `Open`/`Closed`/`Tilted` mit Großbuchstaben?** Wird ab dieser
Version automatisch verstanden — Groß-/Kleinschreibung spielt keine Rolle mehr.

**Abends automatisch schließen — auch mit Sonnenuntergang?** Das ist die Aufgabe des
Nachtmodus-Helfers, und der kann jetzt mehr als `input_boolean`: Ein
**Zeitplan-Helfer** schließt zur festen Uhrzeit (auch mit unterschiedlichen Zeiten je
Wochentag — Wochenende!) und öffnet zum Blockende, falls der reguläre
Öffnungszeitpunkt in den Nacht-Block fiel. Für Sonnenuntergangs-Logik einen Template-Binärsensor
anlegen und als Nachtmodus-Helfer auswählen, z. B. "an ab 30 min nach Sonnenuntergang,
aus ab 07:00":

```yaml
template:
  - binary_sensor:
      - name: "Nacht (Sonnenuntergang bis 7 Uhr)"
        state: >
          {{ state_attr('sun.sun', 'elevation') | float(0) < -4
             or now().hour < 7 }}
```

**Urlaubsmodus / Anwesenheitssimulation?** Über den Pausier-Helfer lösbar: Ein
`input_boolean` "Urlaub" (von der eigenen Anwesenheits-Logik geschaltet) pausiert mit
"AN pausiert" die normale Instanz. Wer im Urlaub andere Zeiten fahren will, legt eine
zweite Instanz desselben Fensters mit eigenem Zeit-Helfer an und trägt dort denselben
Urlaubs-Helfer mit "AUS pausiert" ein — so läuft immer genau eine der beiden.

**Rauchmelder / Alarm — alle Rollos hoch?** Bewusst nicht im Blueprint: Ein Brandalarm
ist ein Haus-Ereignis, kein Pro-Fenster-Verhalten. Eine einzige kleine Automation ist
robuster: Trigger Rauchmelder → `cover.open_cover` auf alle Rollladen-Entitäten (plus
Licht an, Türen entriegeln — was immer der Fluchtweg braucht). Sie übersteuert die
Blueprint-Instanzen einfach; deren Eingriffs-Erkennung stört sich daran nicht.

**Die Beschattung tut nichts — warum?** Prüfe in dieser Reihenfolge: Gibt es eine
Benachrichtigung wegen fehlendem Status-Helfer? Ist eine Temperaturquelle gesetzt
(eigener Sensor oder Wetter-Entität im Sturmschutz-Abschnitt)? Liegt die
Außentemperatur über der Schwelle, steht die Sonne im Sichtfeld (Ausrichtung
korrekt?), ist eine gesetzte Freigabe-Entität "on", und ist das Fenster nicht
komplett offen?

**Warum fährt der Rollladen nach dem Lüften zurück?** Beim Öffnen des Fensters merkt
sich die Automation die Ausgangsposition und stellt sie nach dem Schließen wieder her
(innerhalb des einstellbaren Zeitfensters). Kam inzwischen Nachtmodus, Sturm oder das
morgendliche Öffnen, wird stattdessen deren Zustand hergestellt — die gemerkte
Position gilt als veraltet, sobald die Automatik den Rollladen aus anderem Grund
legitim bewegt hat.

**Kann ich denselben Status-Helfer für mehrere Fenster verwenden?** Nein — er
speichert den Zustand genau eines Fensters. Ein geteilter Helfer führt zu falschem
Öffnen/Schließen.

**Sonnenschutz und Sonnenheizen gleichzeitig aktiv — geht das?** Ja, das ist der
Normalfall. Die Temperatur-Schwellen trennen sie (Standard: beschatten über 25 °C,
heizen unter 12 °C); die Schwellen sollten sich nicht überlappen.

**Home Assistant hat genau zum Morgens-Zeitpunkt (Uhrzeit bzw. Sonnenaufgang) neu
gestartet — warum blieb der Rollladen zu?** Ein verpasster Zeitpunkt wird
standardmäßig nicht nachgeholt. Mit dem Schalter "Nach Neustart nachholen" (Abschnitt
"Nach HA-Neustart") öffnet die Automation nach dem Start nachträglich, sofern der
Neustart höchstens 2 Stunden nach dem Morgens-Zeitpunkt liegt — bei aktivem
Nachtmodus wird wie beim regulären Morgens-Öffnen nicht geöffnet. Details unter
[Nach einem Neustart von Home Assistant](#nach-einem-neustart-von-home-assistant).

**Die Fenster-offen-Meldung bleibt auf dem Handy stehen?** Sie verschwindet
automatisch, sobald das Fenster geschlossen wird — vorausgesetzt, die Companion-App
ist aktuell (das Aufräumen nutzt `clear_notification` mit Tags).

**Mein Kontakt kennt nur offen/geschlossen, das Fenster wird aber eigentlich nur
gekippt?** Dafür gibt es in der Fenster-Interaktion den Schalter "Öffnen wie Kippen
behandeln": Jedes "offen" gilt dann als "gekippt" — der Rollladen fährt auf die
Kipp-Position statt komplett auf, und die Beschattung läuft weiter, statt zu
pausieren. Typischer Fall: das Badfenster mit einfachem binärem Kontakt.

**Kann ich die Automation zeitweise anhalten?** Ja — im Abschnitt "Pausieren" einen
oder mehrere `input_boolean`-Helfer auswählen. Die Logik ist wählbar: "AN
pausiert" für Helfer wie "Aufnahme läuft", oder "AUS pausiert" für Aktiv-Schalter
fürs Dashboard ("Rollladensteuerung aktiv" — an heißt: die Automatik läuft). Bei
mehreren Helfern pausiert die Automatik nur, wenn alle gleichzeitig im
Pausier-Zustand stehen — bei "AUS pausiert" läuft sie also, sobald einer an ist. Während
der Pause macht die Automatik nichts:
keine Fahrten, keine Lichter, keine Meldungen. Zwei Ausnahmen: Der Sturmschutz
greift weiterhin, und der "Rollladen schließen"-Knopf einer Benachrichtigung
funktioniert wie der Wandtaster — bewusste Befehle werden nicht blockiert.
Praktisch für Videoaufnahmen (konstantes Licht!), schlafende Gäste oder den
Fensterputzer. Beim Ausschalten holt die Automation einen inzwischen aktiven
Nachtmodus nach und bewertet die Beschattung neu; verpasste Einzelereignisse
(morgendliches Öffnen, Zurückfahren nach dem Lüften) werden nicht nachgeholt.
