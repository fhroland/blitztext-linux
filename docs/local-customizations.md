# Persönlicher Anpassungs-Fork

Dieses Repository erhält den funktionierenden lokalen Stand vom 28.10.2026.
Basis ist Commit `73a1e41` des MIT-lizenzierten Originals
[TimInTech/blitztext-linux](https://github.com/TimInTech/blitztext-linux).
Lizenz und Urheberhinweise bleiben erhalten. Dies ist ein persönlicher
Quellcode-Fork, keine offizielle Veröffentlichung und keine separat vertriebene
App. Für eine eigene App-Veröffentlichung sind die Vorgaben in
[TRADEMARKS.md](../TRADEMARKS.md) zu beachten.

Diese Datei ist das zentrale Änderungsprotokoll des Forks. Sie dokumentiert
auch Einrichtung außerhalb des Repositorys: Ein neuer Klon allein reproduziert
noch nicht die vollständige lokale Installation.

## Getestete Plattform

Am 28.10.2026 im echten Einsatz bestätigt: openSUSE Tumbleweed, KDE Plasma mit
Wayland, Python 3.13.16, NVIDIA GeForce GTX 1650 Ti (4 GB VRAM), faster-whisper
1.2.1 mit large-v3-turbo auf CUDA. KI-Nachbearbeitung läuft über einen
OpenAI-kompatiblen Endpunkt auf einem ASUS Ascent GX10 über Tailscale.
Auto-Paste wurde in Kate und Konsole getestet, Hotkeys und Statusbox einschließlich
Vordergrundverhalten und erhaltenem Tastaturfokus auf dem KDE-Desktop geprüft.

Das ursprüngliche `scripts/install.sh` unterstützt weiterhin nur Ubuntu/Debian;
es wurde nicht zu einem openSUSE-Installer umgebaut. Die Anpassungen für
Tumbleweed bestehen aus den unten genannten Codeänderungen und gesonderter
lokaler Einrichtung. Nicht jede Änderung ist ausschließlich für openSUSE nötig:
die PyAV-Korrektur betrifft eine Bibliotheksinkompatibilität, die KWin-Anpassung
KDE/Wayland.

## Historie

### 2026-10-28 — erster eigener Stand

- GPU-Vorladen und dauerhafter Modellcache; PyAV 18.1.0 für den funktionierenden
  faster-whisper-WAV-Decoder fixiert.
- Rechte Strg allein im Toggle-Modus, getrennte Namen für linke/rechte Strg,
  Workflow-Shortcuts D/V/S/E und passende Menüanzeigen.
- Auswahl Lokal / Mit KI einschließlich KI-Aktion als `preferred_workflow`
  gespeichert und beim Neustart wiederhergestellt; die normale Aufnahmetaste
  folgt dieser Auswahl. Explizite Workflow-Aktionen ändern die Vorgabe nicht.
- Start nur im Tray; eigenständige Statusbox auf 250 × 108 Pixel verkleinert,
  mit echtem Pegel, Gesamtzeit und tatsächlichem Tray-Symbol samt Statusfarben.
  Bleibt bei Transkription und KI-Nachbearbeitung offen und zeigt den Arbeitsschritt.
  Besonders nützlich bei ausgeblendeter Statusleiste oder unsichtbarem Systemtray.
- KDE-Fenstererkennung und Terminal-Einfügen korrigiert; Desktop-Regel und
  ydotool-Startverhalten lokal ergänzt.
- GX10-Anbindung mit eng begrenzter HTTP-Ausnahme und Erreichbarkeitsprüfung.
- In-App-Updates vorübergehend vollständig gesperrt, einschließlich manueller
  Prüfungen/Downloads und Release-Umschaltung. Kein automatisches Ablaufdatum;
  Upgrades nur bewusst nach Prüfung übernehmen.
- GitHub-Fork erstellt, Original als `upstream` behalten und den eigenen Stand
  mit `local-2026-10-28` markiert. Manuell startbare GitHub-CI ergänzt.
- README in Englisch und Deutsch auf den Fork ausgerichtet; aktuelle Screenshots
  der Statusbox in drei Zuständen, Tray-Menüs und Symbolfarben ergänzt.
- Statusfarben nach Nutzerprüfung deutlicher getrennt: Aufnahme Rot
  (`#f05c5c`), Transkription/KI-Verarbeitung Orange (`#f0ad4e`), Bereit Grün,
  Fehler Hellrot. Zentrale Theme-Werte gelten identisch für Tray und Statusbox;
  bisherige ähnliche Goldtöne ersetzt, Dokumentation und Screenshots aktualisiert.

### Validierung des ersten Stands

- Lokal unter openSUSE: 1064 Tests bestanden, 2 übersprungen; die nur für
  Ubuntu/Debian vorgesehenen Installer-Tests waren ausgenommen.
- [GitHub-CI des ersten Fork-Stands](https://github.com/fhroland/blitztext-linux/actions/runs/40767982415):
  gesamter Lauf einschließlich Installer-Tests auf Ubuntu mit Python 3.11,
  3.12 und 3.14 sowie Secret-Hygiene-Scan erfolgreich.
- Quellcode-ZIP vor dem Fork zusätzlich lokal gesichert. Zugangsschlüssel und
  private Benutzerkonfiguration bleiben außerhalb des Repositorys.

### Screenshots reproduzieren

```sh
env -u OPENAI_API_KEY PYTHONPATH=. QT_QPA_PLATFORM=offscreen \
  .venv/bin/python scripts/_make_fork_screenshots.py
```

Das Skript fotografiert die tatsächlichen Qt-Widgets in Deutsch und Englisch.
Pegel und Zeitwerte sind für die Dokumentation simuliert. Es verwendet eine
isolierte Konfiguration und greift weder auf Mikrofon, echte Hotkeys, KI-Dienste
noch andere Desktop-Fenster zu. Die Aufnahmen liegen unter
`docs/screenshots/linux/overlay-*.png`; die Tray-Menüs und vier Statussymbole
werden ebenfalls aus dem aktuellen Code erzeugt.

## Git-Struktur

- `origin`: `https://github.com/fhroland/blitztext-linux.git`
- `upstream`: `https://github.com/TimInTech/blitztext-linux.git`
- `main`: unsere angepasste Version.
- Tag `local-2026-10-28`: erster gesicherter eigener Stand.
- `upstream-main`: unveränderter Originalstand bei Erstellung des GitHub-Forks.
  Neue Originalstände werden über `upstream/main` abgerufen.

Die App-Versionsnummer bleibt beim ursprünglichen `0.9.1`. Der Git-Tag
kennzeichnet unsere Variante eindeutig, ohne ein offizielles Release vorzutäuschen.

## Anpassungen

- Start nur im Systemtray; Hauptfenster wird auf Wunsch geöffnet.
- Persistente Auswahl des Arbeitsmodus, auch für den normalen Diktier-Hotkey.
- Rechte Strg-Taste im Toggle-Modus reagiert nur bei alleiniger Betätigung,
  beim Loslassen. Tastenkombinationen mit dieser Taste lösen keine Aufnahme aus.
- Workflow-Shortcuts einschließlich Menüanzeigen:

  | Tastenkürzel | Aktion |
  |---|---|
  | Meta+Shift+D | Lokal diktieren |
  | Meta+Shift+V | Diktieren und verbessern |
  | Meta+Shift+S | Sachlich formulieren |
  | Meta+Shift+E | Emojis ergänzen |

- Kompakte Statusbox (250 × 108) in Bildschirmmitte mit echtem RMS-Pegel,
  Laufzeit, Tray-Symbol und identischen Symbolfarben. Bleibt bei Transkription
  und KI-Nachbearbeitung mit Arbeitsschrittanzeige geöffnet. KWin-Vordergrundstatus
  und Positionierung über `kdotool`, ohne Aktivierung des Fensters.
- Aufnahmeformat explizit PCM s16le; Pegel aus der bestehenden Aufnahme gelesen.
- KDE/Wayland-Fenstererkennung über `kdotool` für korrektes Einfügen in Terminals.
- faster-whisper-Modell kann beim Start in denselben Modellcache vorgeladen
  und bis Prozessende gehalten werden.
- Eng begrenzte HTTP-Ausnahme für den lokal eingerichteten GX10-Endpunkt;
  allgemeine URL-Prüfungen bleiben bestehen. KI-Erreichbarkeitsprüfung ohne Diktat.
- Updatesperre über `.updates-disabled` oder `BLITZTEXT_DISABLE_UPDATES=1`:
  Prüfung, Download, Installation und Umschaltung auf Release-Verzeichnisse
  bleiben blockiert.
- `constraints-local.txt` fixiert PyAV auf `18.1.0` für faster-whisper `1.2.1`.

## Außerhalb des Repositorys

Das Repository enthält keine Zugangsschlüssel, Benutzerkonfiguration, Diktate,
Modelldateien oder virtuelle Python-Umgebung. Es ist kein vollständiges
Installationsabbild. Die bestehende Installation verwendet außerdem:

- Einen lokalen Launcher mit CUDA-Bibliothekspfaden, `PATH` für `kdotool`,
  `BLITZTEXT_WHISPER_DEVICE=cuda`, `BLITZTEXT_PRELOAD_MODEL=1`,
  `BLITZTEXT_MODEL_CACHE_SECONDS=-1`, `BLITZTEXT_DISABLE_UPDATES=1`,
  `HF_HUB_DISABLE_XET=1` und `PIP_CONSTRAINT` auf `constraints-local.txt`.
- Benutzerkonfiguration für faster-whisper, large-v3-turbo, Deutsch, rechte Strg
  im Toggle-Modus sowie den eigenen KI-Endpunkt. Diese Einstellungen sind nicht
  die allgemeinen Programmvorgaben. Schlüssel werden separat bereitgestellt.
- Eine KWin-Regel mit exaktem Titel `Blitztext recording indicator`,
  `titlematch=1`, `acceptfocus=false`, `acceptfocusrule=2`, damit die Statusbox
  den Eingabefokus nicht übernimmt.
- Einen Benutzer-Systemd-Dienst für Blitztext und eine Startkorrektur für
  ydotool (`After=graphical-session.target`, `StartLimitIntervalSec=0`,
  `RestartSec=5s`, bestehendes `Restart=always`).

Eine neue Installation muss diese Teile gesondert einrichten. `run.sh` allein
reproduziert die lokal eingerichtete CUDA-Umgebung nicht. Die dauerhaften lokalen
ZIP-Sicherungen und Übergabenotizen bleiben zusätzlich bestehen.

## Upgrades kontrolliert übernehmen

1. Aktuellen Stand mit Git-Tag und separater Quellcode-ZIP sichern; zusätzlich
   private Konfiguration, Launcher, Dienste und Bibliotheksversionen lokal sichern.
2. `git fetch upstream --tags` ausführen. Änderungen und Abhängigkeiten seit
   der letzten gemeinsamen Basis prüfen.
3. Separates Arbeitsverzeichnis und Upgrade-Branch erstellen, zum Beispiel
   `git worktree add -b upgrade/upstream-review ../blitztext-upgrade main`.
4. Im separaten Arbeitsverzeichnis den ausgewählten Originalstand mit
   `git merge <upstream-tag-oder-commit>` übernehmen und Konflikte auflösen.
   Die laufende Installation bleibt währenddessen auf ihrem bisherigen Stand.
5. Updatesperre sowie alle lokalen Anpassungen prüfen; Tests ausführen:

   ```sh
   env -u OPENAI_API_KEY QT_QPA_PLATFORM=offscreen WHISPER_GUI_TESTS=1 \
     .venv/bin/python -m pytest tests/ -q
   git diff --check
   bash -n run.sh
   ```

   Das separate Arbeitsverzeichnis benötigt eine passende eigene Testumgebung.
   `test_install_script.py` setzt Ubuntu/Debian voraus. Unter openSUSE kann der
   übrige Gesamtlauf mit `--ignore=tests/test_install_script.py` geprüft werden;
   die Installer-Tests müssen zusätzlich auf Ubuntu/Debian laufen.
   Zusätzlich echtes Diktat, GPU, GX10, rechte Strg, Workflow-Shortcuts,
   Einfügen in Editor/Terminal und Statusbox einschließlich Fokus prüfen.
6. Nach erfolgreicher Prüfung bewusst auf den geprüften Stand umstellen und
   einen neuen eigenen Tag setzen. Ein Wechsel von `main` im laufenden Checkout
   ersetzt Dateien sofort; Dienst und laufende Aufnahmen vorher berücksichtigen.
   Bibliotheksänderungen sind separat rückgängig zu machen, falls zurückgewechselt wird.

Die Updatesperre bleibt erhalten. Neue Originalversionen werden weder automatisch
noch durch einen unkontrollierten In-App-Update übernommen.
