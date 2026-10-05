# MultiGitHubGUI

**MultiGitHubGUI** ist eine kompakte Windows-GUI für Git und die GitHub CLI mit besonderem Fokus auf die Arbeit mit **mehreren GitHub-Konten**.

Die Anwendung wird als einzelne Windows-EXE gebaut und enthält Python, CustomTkinter, GitHub CLI sowie MinGit. Auf dem Zielrechner müssen daher weder Python noch Git noch die GitHub CLI separat installiert werden.

## Funktionen

- mehrere GitHub-Konten anmelden und wechseln
- Repositories des gewählten Accounts anzeigen und durchsuchen
- dauerhafte Zuordnung von GitHub-Repositories zu lokalen Projektordnern
- Repository-Owner-Schutz für Commit und Push
- repositorybezogene Git-Commit-Identität für den gewählten Owner
- klarer Workflow **Änderungen → Commit → Push**
- neue private oder öffentliche Repositories erstellen
- vorhandene Repositories klonen
- lokale Projektordner mit bestehenden GitHub-Repositories verbinden
- `main`/`master`-Unterschiede und vorhandene Remote-Historien berücksichtigen
- Pull, Commit und Push
- technischer Git-Status mit Branch, Remote, Upstream und Commit-Identität
- integriertes Terminal mit dem eingebetteten MinGit und `gh`
- Light-, Dark- und System-Theme
- portable **1-Datei-EXE**

## Workflow

MultiGitHubGUI stellt den normalen Git-Ablauf als drei Schritte untereinander dar:

1. **Änderungen prüfen** – neue, geänderte oder gelöschte Dateien erkennen
2. **Commit erstellen** – lokale Änderungen mit einer Nachricht speichern
3. **Auf GitHub pushen** – lokale Commits zum Repository übertragen

Damit ist klar erkennbar, ob Dateien nur geändert wurden oder ob bereits ein lokaler Commit auf den Push wartet.

## Mehrere GitHub-Konten und Repository-Owner

Die Anmeldung erfolgt über die GitHub CLI. MultiGitHubGUI speichert selbst **keine GitHub-Passwörter und keine GitHub-Tokens**.

Vor Commit und Push wird geprüft, ob der in der GUI ausgewählte Account dem Owner des Repositories entspricht. Neue Commits erhalten repositorybezogen die Identität dieses Accounts.

## Lokale Ordner

Repository-Zuordnungen werden dauerhaft gespeichert, z. B.:

```json
{
  "repo_paths": {
    "fachlehrer-dev/MultiGitHubGUI": "C:\\Projekte\\MultiGitHubGUI"
  }
}
```

Die Konfiguration liegt unter:

```text
%APPDATA%\MultiGitHubGUI\config.json
```

Sie bleibt deshalb auch bei einem Austausch der EXE erhalten.

## Icon

Im Repository liegen:

- `MultiGitHubGUI.png`
- `MultiGitHubGUI.ico`

Die ICO-Datei wird beim Build als Windows-EXE-Icon gesetzt. Für das Fenster zur Laufzeit enthält `MultiGitHubGUI.py` zusätzlich eine kleine PNG-Version **direkt als Base64**. Dadurch muss dafür beim Start keine zusätzliche Bilddatei aus der Onefile-EXE geladen werden.

## EXE erstellen

Auf dem **Build-PC** wird Python benötigt. Auf dem Zielrechner nicht.

1. Repository herunterladen oder klonen.
2. `build_exe.bat` starten.
3. Beim ersten Build werden GitHub CLI und MinGit geladen.
4. Bei späteren Builds fragt die BAT, ob vorhandene Downloads aus `build_tmp` wiederverwendet werden sollen.
5. PyInstaller erzeugt:

```text
dist\MultiGitHubGUI.exe
```

## Startzeit

MultiGitHubGUI bleibt bewusst eine PyInstaller-**Onefile-EXE**. Die enthaltenen Git-Komponenten müssen beim Start technisch entpackt werden; das ist der größte verbleibende Startzeitfaktor.

Der Build wurde dennoch auf unnötigen Overhead reduziert:

- CustomTkinter-Ressourcen werden nur **einmal** eingebunden
- UPX wird deaktiviert
- das Runtime-Icon wird aus einer kleinen eingebetteten Base64-PNG geladen
- GitHub-/Repository-Abfragen laufen erst nach dem Aufbau der Oberfläche

Eine `onedir`-Version könnte grundsätzlich noch schneller starten, würde aber dem Ziel einer einzelnen EXE widersprechen.

## Build-Cache

Die BAT behält heruntergeladene Archive in:

```text
build_tmp\
```

Vorhandene `gh.zip` und `mingit.zip` können beim nächsten Build wiederverwendet werden.

## Veröffentlichung

GitHub:  
https://github.com/fachlehrer-dev/MultiGitHubGUI

Weitere Informationen:  
https://fachlehrer.dev/MultiGitHubGUI

## Autor

Developed by **Fred Maier**  
Published by **IFL Bayreuth**  
Contact: fred@fachlehrer.dev

## Lizenz

MultiGitHubGUI steht unter der **MIT License**. Siehe [LICENSE](LICENSE).

Die mit der erzeugten EXE gebündelten Drittanbieter-Komponenten unterliegen zusätzlich ihren jeweiligen eigenen Lizenzbedingungen.
