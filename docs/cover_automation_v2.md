# Intelligente Rollladensteuerung — Dokumentation

**Blueprint:** `automations/cover_automation_v2.yaml` · Mindestversion: Home Assistant 2024.10

[![Import Blueprint](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https://github.com/TheRealSimon42/ha-blueprints/blob/main/automations/cover_automation_v2.yaml)

## Konzept

**Eine Automation pro Fenster/Rollladen-Paar.** Du legst für jedes Fenster eine eigene
Instanz aus diesem Blueprint an und wählst dort genau einen Rollladen und genau einen
Fensterkontakt aus. Als Fensterkontakt funktionieren klassische binäre Sensoren
(offen/geschlossen) genauso wie Drei-Zustands-Sensoren (offen/gekippt/geschlossen). Gemeinsame Einstellungen — die Uhrzeiten fürs
morgendliche Öffnen, der Nachtmodus-Schalter, die Wetter-Entität — sind Helfer, die du
einfach in allen Instanzen identisch auswählst.

Warum so? Weil jedes Fenster eigene Eigenschaften hat (Ausrichtung, Größe, Balkontür
oder nicht) und weil damit jede Instanz für sich verständlich, testbar und abschaltbar
bleibt. Nur zwei Felder sind Pflicht: Rollladen und Fenstersensor. Jedes Feature
darüber hinaus ist per Schalter zuschaltbar.

## Einrichtung

1. **Blueprint importieren** (Button oben) und unter _Einstellungen → Automatisierungen
   & Szenen → Blueprints_ eine Instanz pro Fenster anlegen.
2. **Rollladen + Fenstersensor** zuordnen — mehr braucht es für den Start nicht.
3. **Je nach gewünschten Features Helfer anlegen** (_Einstellungen → Geräte & Dienste →
   Helfer_):
   - Morgens öffnen: ein `input_datetime`-Helfer, **nur mit Uhrzeit, ohne Datum**
     (ein Datum+Zeit-Helfer feuert nur ein einziges Mal!). Einer für alle Instanzen.
     Optional kann ein zweiter `input_datetime`-Helfer als **Wochenend-Uhrzeit**
     ausgewählt werden. Dann gilt die normale Uhrzeit Montag bis Freitag und die
     separate Uhrzeit Samstag und Sonntag. Ohne Wochenend-Helfer gilt die normale
     Uhrzeit weiterhin an allen Tagen.
   - Nachtmodus: ein `input_boolean`, z. B. "Nacht-Modus". Einer für alle Instanzen;
     wie er geschaltet wird (Zeitplan, Guten-Nacht-Szene, von Hand), bleibt dir überlassen.
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

| Feature             | Was es tut                                                                                                                       | Voraussetzung                              |
| ------------------- | -------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------ |
| Morgens öffnen      | Fährt zur eingestellten Uhrzeit auf die Zielposition; optional mit separater Uhrzeit für Samstag/Sonntag (nur wenn geschlossener) | `input_datetime`-Helfer (nur Uhrzeit)      |
| Fenster-Interaktion | Kippen → Lüftungsposition, Öffnen → ganz auf (optional: wie Kippen behandeln); nach dem Schließen zurück in die Ausgangsposition | — (immer aktiv)                            |
| Nachtmodus          | Schließt beim Einschalten des Helfers; offene/gekippte Fenster bekommen eine Lüftungsposition                                    | `input_boolean`-Helfer                     |
| Sturmschutz         | Fährt bei Starkwind hoch (oder im Panzer-Modus herunter)                                                                         | Wetter-Entität oder Wind-Sensor            |
| Sonnenschutz        | Beschattet anhand des Sonnenstands so, dass die Sonne höchstens X m in den Raum fällt; öffnet nach Ende wieder                   | Status-Helfer, Geometrie, Temperaturquelle |
| Sonnenheizen        | Öffnet im Winter vergessene Rollos, wenn Sonne ins Fenster scheint und es kalt ist                                               | eigener Status-Helfer, Geometrie           |
| Moskito-Modus       | Schaltet beim Fensteröffnen nach Sonnenuntergang die Lichter im Raum aus (mit Ausnahmen)                                         | — (Bereich kommt vom Fenstersensor)        |
| Benachrichtigungen  | Meldet zu lange offene/gekippte Fenster aufs Handy, mit "Rollladen schließen"-Button; verschwindet automatisch beim Schließen    | Companion-App-Geräte                       |
| Pausieren           | Hält die komplette Automation an, solange ein Helfer eingeschaltet ist — z.B. während Videoaufnahmen oder wenn Gäste schlafen    | `input_boolean`-Helfer (optional)          |

**Prioritäten:** Der **Sturmschutz gewinnt immer** — bei Starkwind bewegen weder
Morgens-Öffnen noch Beschattung, Sonnenheizen oder das Zurückfahren den Rollladen,
und auch der Pausier-Helfer hält ihn nicht auf (Schutz der Hardware geht vor).
Danach kommt die Pause (solange ihr Helfer an ist, passiert sonst gar nichts),
dann der Nachtmodus (nachts wird nicht beschattet, nicht geheizt und beim
Fensteröffnen nur bis zur Lüftungsposition geöffnet), dann erst die Komfort-Features.

## Verhalten verstehen

### Unterschiedliche Morgen-Uhrzeit am Wochenende

Für Samstag und Sonntag kann optional ein zweiter `input_datetime`-Helfer ausgewählt
werden. Sobald dieser gesetzt ist, verwendet die Automation montags bis freitags die
normale **Uhrzeit für morgendliches Hochfahren** und samstags/sonntags die
**Wochenend-Uhrzeit**.

Bleibt das Wochenend-Feld leer, ändert sich nichts am bisherigen Verhalten: Die normale
Morgen-Uhrzeit gilt an allen sieben Tagen. Damit bleiben bestehende Blueprint-Instanzen
ohne Anpassung kompatibel.

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

## Bekannte Grenzen

- **Wind-Sensor kurz nicht verfügbar** zählt als "windstill". Bewusste Entscheidung:
  Ein dauerhaft toter Sensor soll nicht sämtliche Komfort-Funktionen lahmlegen. Der
  Sturmschutz selbst hat beim Überschreiten des Grenzwerts längst ausgelöst.
- **Wetterlagen-Filter:** Flattert das Wetter zwischen zwei _nicht_ erlaubten Lagen
  (z. B. Regen ↔ Starkregen), beendet erst Sonnenstand oder Temperatur die
  Beschattung. Der Filter beendet nur bei mindestens 10 Minuten stabil schlechter Lage.
- **Cover ohne Positions-Angabe** (nur auf/zu): Morgens-Öffnen funktioniert,
  Kipp-Position und Beschattung werden übersprungen — sie brauchen Positionsdaten.
- **Windgeschwindigkeit** wird roh mit dem Grenzwert verglichen — liefert deine Quelle
  m/s statt km/h, muss der Grenzwert entsprechend gesetzt werden.
- **Sturm-Ende:** Nach dem Sturm bleibt der Rollladen in der Schutzposition, bis das
  nächste reguläre Ereignis (Nachtmodus, Morgens, Beschattung) ihn übernimmt.

## FAQ

**Kann der Rollladen am Wochenende später öffnen?** Ja. Im Abschnitt "Morgens öffnen"
kannst du optional einen zweiten `input_datetime`-Helfer als Wochenend-Uhrzeit
auswählen. Dieser gilt ausschließlich Samstag und Sonntag. Bleibt das Feld leer,
wird die normale Morgen-Uhrzeit an allen Tagen verwendet.

**Was bedeuten 0 % und 100 % bei den Positionen?** Das Blueprint folgt der
Home-Assistant-Konvention: 100 % = ganz offen, 0 % = ganz geschlossen. Die Prozente
sind dabei die Werte deines Cover-Aktors, also Motor-Laufweg — nicht zwingend
Glasfläche. Für die Beschattung lässt sich dieser Unterschied über die
Glas-Kalibrierung (siehe oben) ausgleichen; alle anderen Positions-Eingaben
(morgens, Kipp-Position, Nachtlüftung) sind bewusst direkte Aktor-Werte.

**Die Beschattung tut nichts — warum?** Prüfe in dieser Reihenfolge: Gibt es eine
Benachrichtigung wegen fehlendem Status-Helfer? Ist eine Temperaturquelle gesetzt
(eigener Sensor oder Wetter-Entität im Sturmschutz-Abschnitt)? Liegt die
Außentemperatur über der Schwelle, steht die Sonne im Sichtfeld (Ausrichtung
korrekt?), und ist das Fenster nicht komplett offen?

**Warum fährt der Rollladen nach dem Lüften zurück?** Beim Öffnen des Fensters merkt
sich die Automation die Ausgangsposition und stellt sie nach dem Schließen wieder her
(innerhalb des einstellbaren Zeitfensters). Kam inzwischen Nachtmodus oder Sturm,
wird stattdessen deren Zustand hergestellt.

**Kann ich denselben Status-Helfer für mehrere Fenster verwenden?** Nein — er
speichert den Zustand genau eines Fensters. Ein geteilter Helfer führt zu falschem
Öffnen/Schließen.

**Sonnenschutz und Sonnenheizen gleichzeitig aktiv — geht das?** Ja, das ist der
Normalfall. Die Temperatur-Schwellen trennen sie (Standard: beschatten über 25 °C,
heizen unter 12 °C); die Schwellen sollten sich nicht überlappen.

**Die Fenster-offen-Meldung bleibt auf dem Handy stehen?** Sie verschwindet
automatisch, sobald das Fenster geschlossen wird — vorausgesetzt, die Companion-App
ist aktuell (das Aufräumen nutzt `clear_notification` mit Tags).

**Mein Kontakt kennt nur offen/geschlossen, das Fenster wird aber eigentlich nur
gekippt?** Dafür gibt es in der Fenster-Interaktion den Schalter "Öffnen wie Kippen
behandeln": Jedes "offen" gilt dann als "gekippt" — der Rollladen fährt auf die
Kipp-Position statt komplett auf, und die Beschattung läuft weiter, statt zu
pausieren. Typischer Fall: das Badfenster mit einfachem binärem Kontakt.

**Kann ich die Automation zeitweise anhalten?** Ja — im Abschnitt "Pausieren" einen
einen oder mehrere `input_boolean`-Helfer auswählen. Die Logik ist wählbar: "AN
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
