# Persönlicher Anpassungs-Fork

Dieses Repository erhält den funktionierenden lokalen Stand vom 28.10.2026.
Basis ist Commit `73a1e41` des MIT-lizenzierten Originals
[TimInTech/blitztext-linux](https://github.com/TimInTech/blitztext-linux).
Lizenz und Urheberhinweise bleiben erhalten. Dies ist ein persönlicher
Quellcode-Fork, keine offizielle Veröffentlichung und keine separat vertriebene
App. Für eine eigene App-Veröffentlichung sind die Vorgaben in
[TRADEMARKS.md](../TRADEMARKS.md) zu beachten.

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
