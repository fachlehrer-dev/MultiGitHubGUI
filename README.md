# MultiGitHubGUI

**MultiGitHubGUI** ist eine schlanke Windows-Oberfläche für Git und die GitHub CLI mit besonderem Fokus auf die Arbeit mit **mehreren GitHub-Konten**.

Die Anwendung bündelt beim Build Python, CustomTkinter, GitHub CLI und MinGit zu einer einzelnen Windows-EXE. Auf dem Zielrechner müssen daher weder Python noch Git noch die GitHub CLI separat installiert werden.

## Funktionen

- mehrere GitHub-Konten verwenden und wechseln
- weitere GitHub-Konten per Browser-Anmeldung hinzufügen
- Repositories des aktiven Kontos anzeigen und durchsuchen
- neue private oder öffentliche Repositories erstellen
- optional README, `.gitignore` und Lizenz beim Erstellen hinzufügen
- vorhandene GitHub-Repositories klonen
- lokale Projektordner auf GitHub veröffentlichen
- lokalen Git-Status anzeigen
- Änderungen committen
- Pull und Push ausführen
- Repository auf GitHub öffnen
- lokalen Projektordner und Terminal öffnen
- Light-, Dark- und System-Theme
- portable Ein-Datei-EXE

## Zugangsdaten

MultiGitHubGUI speichert **keine GitHub-Passwörter und keine GitHub-Tokens in der eigenen Konfigurationsdatei**. Die Anmeldung und Verwaltung der Zugangsdaten erfolgt über die GitHub CLI bzw. die Windows-Anmeldeinformationsverwaltung.

## EXE erstellen

Zum Bauen wird nur auf dem **Build-PC** eine aktuelle Python-Installation benötigt.

1. `MultiGitHubGUI.py` und `build_multigithubgui_exe.bat` in denselben Ordner legen.
2. Die BAT starten.
3. Das Skript installiert die benötigten Python-Pakete und lädt GitHub CLI und MinGit.
4. PyInstaller erstellt anschließend eine einzelne EXE.

Ergebnis:

```text
dist\MultiGitHubGUI.exe
```

Auf dem Zielrechner ist keine separate Python-, Git- oder GitHub-CLI-Installation erforderlich.

## Lokale Einstellungen

Benutzerspezifische Einstellungen werden unter Windows hier gespeichert:

```text
%APPDATA%\MultiGitHubGUI\
```

## Veröffentlichung

Projekt und Download:  
https://github.com/fachlehrer-dev/MultiGitHubGUI

Weitere Informationen:  
https://fachlehrer.dev/MultiGitHubGUI

## Autor

Entwickelt von **Fred Maier**  
Veröffentlicht von **IFL Bayreuth**  
Kontakt: fred@fachlehrer.dev

## Lizenz

Dieses Projekt steht unter der **MIT License**. Siehe [LICENSE](LICENSE).

Die mit einer erzeugten EXE gebündelten Drittanbieter-Komponenten unterliegen zusätzlich ihren jeweiligen eigenen Lizenzbedingungen.
