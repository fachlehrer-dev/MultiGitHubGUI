from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import threading
import webbrowser
from pathlib import Path
from tkinter import filedialog, messagebox, PhotoImage

import customtkinter as ctk

APP_NAME = "MultiGitHubGUI"
HOST = "github.com"
CREATE_NO_WINDOW = 0x08000000 if os.name == "nt" else 0
CREATE_NEW_CONSOLE = 0x00000010 if os.name == "nt" else 0

# Small runtime icon embedded directly in the application source.
# This avoids a separate icon file lookup/extraction at runtime.
APP_ICON_PNG_BASE64 = """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"""


def app_data_dir() -> Path:
    base = os.environ.get("APPDATA") or str(Path.home())
    path = Path(base) / APP_NAME
    path.mkdir(parents=True, exist_ok=True)
    return path


CONFIG_FILE = app_data_dir() / "config.json"


def resource_root() -> Path:
    return Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))


def bundled_paths() -> tuple[Path, Path]:
    root = resource_root()
    gh = root / "vendor" / "gh" / "gh.exe"
    git_candidates = [
        root / "vendor" / "mingit" / "cmd" / "git.exe",
        root / "vendor" / "mingit" / "bin" / "git.exe",
        root / "vendor" / "mingit" / "mingw64" / "bin" / "git.exe",
    ]
    git = next((p for p in git_candidates if p.exists()), git_candidates[0])
    return gh, git


GH_EXE, GIT_EXE = bundled_paths()


def default_config() -> dict:
    return {
        "theme": "System",
        "projects_dir": str(Path.home() / "Documents" / "GitHub"),
        "last_account": "",
        "repo_paths": {},
        "window": {"width": 1280, "height": 780},
    }


def load_config() -> dict:
    cfg = default_config()
    try:
        if CONFIG_FILE.exists():
            saved = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            if isinstance(saved, dict):
                cfg.update(saved)
                if isinstance(saved.get("window"), dict):
                    cfg["window"] = {**default_config()["window"], **saved["window"]}
    except Exception:
        pass
    return cfg


def save_config(cfg: dict) -> None:
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")


def tool_env() -> dict:
    env = os.environ.copy()
    root = resource_root()
    mingit = root / "vendor" / "mingit"
    gh_dir = root / "vendor" / "gh"

    prepend = [
        str(mingit / "cmd"),
        str(mingit / "bin"),
        str(mingit / "mingw64" / "bin"),
        str(mingit / "usr" / "bin"),
        str(gh_dir),
    ]
    env["PATH"] = os.pathsep.join(prepend + [env.get("PATH", "")])

    # Transient Git credential helper. This avoids persisting a path into
    # PyInstaller's temporary _MEI directory.
    gh_for_shell = str(GH_EXE).replace("\\", "/")
    # WICHTIG: Zuerst alle anderen Credential-Helper zurücksetzen.
    # Sonst kann MinGit / eine vorhandene Git-Konfiguration zusätzlich den
    # Git Credential Manager starten und einen zweiten Browser-OAuth-Flow öffnen.
    env["GIT_CONFIG_COUNT"] = "2"
    env["GIT_CONFIG_KEY_0"] = "credential.helper"
    env["GIT_CONFIG_VALUE_0"] = ""
    env["GIT_CONFIG_KEY_1"] = f"credential.https://{HOST}.helper"
    env["GIT_CONFIG_VALUE_1"] = f'!"{gh_for_shell}" auth git-credential'
    env["GIT_TERMINAL_PROMPT"] = "0"

    # MinGit in the bundled one-file build may not include the "less" pager.
    # Disable paging for all child Git/GitHub CLI processes.
    env["GIT_PAGER"] = "cat"
    env["PAGER"] = "cat"
    env["GH_PAGER"] = "cat"
    return env


def run_process(exe, args, cwd=None, timeout=120, allow_error=False):
    proc = subprocess.run(
        [str(exe), *args],
        cwd=str(cwd) if cwd else None,
        env=tool_env(),
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=timeout,
        creationflags=CREATE_NO_WINDOW,
    )
    if proc.returncode != 0 and not allow_error:
        raise RuntimeError((proc.stderr or proc.stdout or f"Exit code {proc.returncode}").strip())
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


def run_gh(args, cwd=None, **kwargs):
    return run_process(GH_EXE, args, cwd, **kwargs)


def run_git(args, cwd=None, **kwargs):
    return run_process(GIT_EXE, args, cwd, **kwargs)


def parse_accounts() -> list[dict]:
    _, out, _ = run_gh(["auth", "status", "--json", "hosts"])
    data = json.loads(out or "{}")
    entries = data.get("hosts", {}).get(HOST, [])
    if isinstance(entries, dict):
        entries = list(entries.values())

    result = []
    for item in entries if isinstance(entries, list) else []:
        if not isinstance(item, dict):
            continue
        login = item.get("login") or item.get("user") or item.get("account")
        if login:
            result.append({
                "login": str(login),
                "active": bool(item.get("active")),
                "state": str(item.get("state", "")),
            })
    return result


def active_account(accounts: list[dict]) -> str:
    for account in accounts:
        if account.get("active"):
            return account["login"]
    return accounts[0]["login"] if accounts else ""


class RepoDialog(ctk.CTkToplevel):
    def __init__(self, master, title, default_name="", init_options=True, on_submit=None):
        super().__init__(master)
        self.title(title)
        self.geometry("520x560" if init_options else "520x420")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()
        self.on_submit = on_submit
        self.init_options = init_options
        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self, text=title, font=ctk.CTkFont(size=22, weight="bold")).grid(
            row=0, column=0, padx=24, pady=(24, 14), sticky="w"
        )
        ctk.CTkLabel(self, text="Repository-Name").grid(row=1, column=0, padx=24, sticky="w")
        self.name_entry = ctk.CTkEntry(self, height=38)
        self.name_entry.insert(0, default_name)
        self.name_entry.grid(row=2, column=0, padx=24, pady=(4, 12), sticky="ew")

        ctk.CTkLabel(self, text="Beschreibung (optional)").grid(row=3, column=0, padx=24, sticky="w")
        self.desc_entry = ctk.CTkEntry(self, height=38)
        self.desc_entry.grid(row=4, column=0, padx=24, pady=(4, 12), sticky="ew")

        ctk.CTkLabel(self, text="Sichtbarkeit").grid(row=5, column=0, padx=24, sticky="w")
        self.visibility = ctk.CTkSegmentedButton(self, values=["Privat", "Öffentlich"])
        self.visibility.set("Privat")
        self.visibility.grid(row=6, column=0, padx=24, pady=(4, 14), sticky="ew")

        row = 7
        self.readme_var = ctk.BooleanVar(value=True)
        self.gitignore = None
        self.license = None

        if init_options:
            ctk.CTkCheckBox(self, text="README.md anlegen", variable=self.readme_var).grid(
                row=row, column=0, padx=24, pady=8, sticky="w"
            )
            row += 1
            ctk.CTkLabel(self, text=".gitignore-Vorlage").grid(row=row, column=0, padx=24, sticky="w")
            row += 1
            self.gitignore = ctk.CTkComboBox(
                self, values=["Keine", "Python", "VisualStudio", "Node", "Java", "C++", "CSharp"]
            )
            self.gitignore.set("Keine")
            self.gitignore.grid(row=row, column=0, padx=24, pady=(4, 10), sticky="ew")
            row += 1
            ctk.CTkLabel(self, text="Lizenz").grid(row=row, column=0, padx=24, sticky="w")
            row += 1
            self.license = ctk.CTkComboBox(
                self, values=["Keine", "MIT", "Apache-2.0", "GPL-3.0", "BSD-3-Clause"]
            )
            self.license.set("Keine")
            self.license.grid(row=row, column=0, padx=24, pady=(4, 10), sticky="ew")
            row += 1

        buttons = ctk.CTkFrame(self, fg_color="transparent")
        buttons.grid(row=row, column=0, padx=24, pady=(18, 24), sticky="ew")
        buttons.grid_columnconfigure((0, 1), weight=1)
        ctk.CTkButton(buttons, text="Abbrechen", fg_color="transparent", border_width=1,
                      command=self.destroy).grid(row=0, column=0, padx=(0, 6), sticky="ew")
        ctk.CTkButton(buttons, text="Erstellen" if init_options else "Veröffentlichen",
                      command=self.submit).grid(row=0, column=1, padx=(6, 0), sticky="ew")
        self.after(100, self.name_entry.focus_set)

    def submit(self):
        name = self.name_entry.get().strip()
        if not name or any(ch in name for ch in r'\\/:*?"<>| '):
            messagebox.showerror("Ungültiger Name",
                                 "Bitte einen Repository-Namen ohne Leerzeichen oder Windows-Sonderzeichen eingeben.",
                                 parent=self)
            return
        data = {
            "name": name,
            "description": self.desc_entry.get().strip(),
            "private": self.visibility.get() == "Privat",
            "readme": bool(self.readme_var.get()),
            "gitignore": self.gitignore.get() if self.gitignore else "Keine",
            "license": self.license.get() if self.license else "Keine",
        }
        self.destroy()
        if self.on_submit:
            self.on_submit(data)


class MultiGitHubGUI(ctk.CTk):
    def __init__(self):
        self.cfg = load_config()
        if not isinstance(self.cfg.get("repo_paths"), dict):
            self.cfg["repo_paths"] = {}
        ctk.set_appearance_mode(self.cfg.get("theme", "System"))
        ctk.set_default_color_theme("blue")
        super().__init__()

        # Runtime window icon from embedded Base64 PNG.
        try:
            self._app_icon = PhotoImage(data=APP_ICON_PNG_BASE64)
            self.iconphoto(True, self._app_icon)
        except Exception:
            self._app_icon = None

        self.title("MultiGitHubGUI")
        self.geometry(f"{self.cfg['window']['width']}x{self.cfg['window']['height']}")
        self.minsize(1080, 680)
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.accounts = []
        self.repos = []
        self.selected_repo = None
        self.local_dir = None

        self.grid_columnconfigure(0, weight=0, minsize=360)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.build_header()
        self.build_left()
        self.build_right()
        self.after(150, self.initial_load)

    def build_header(self):
        f = ctk.CTkFrame(self, corner_radius=0, height=68)
        f.grid(row=0, column=0, columnspan=2, sticky="nsew")
        f.grid_columnconfigure(4, weight=1)
        ctk.CTkLabel(f, text="MultiGitHubGUI", font=ctk.CTkFont(size=22, weight="bold")).grid(
            row=0, column=0, padx=(20, 18), pady=16)
        self.account_menu = ctk.CTkOptionMenu(f, values=["Kein Konto"], width=210,
                                              command=self.switch_account)
        self.account_menu.grid(row=0, column=1, padx=6)
        ctk.CTkButton(f, text="+ Konto", width=100, command=self.add_account).grid(row=0, column=2, padx=6)
        ctk.CTkButton(f, text="↻", width=42, command=self.refresh_everything).grid(row=0, column=3, padx=6)
        ctk.CTkButton(
            f,
            text="Info",
            width=70,
            command=self.show_about,
        ).grid(row=0, column=5, padx=6)

        self.theme_menu = ctk.CTkOptionMenu(f, values=["System", "Light", "Dark"], width=105,
                                            command=self.change_theme)
        self.theme_menu.set(self.cfg.get("theme", "System"))
        self.theme_menu.grid(row=0, column=6, padx=(6, 18))

    def build_left(self):
        left = ctk.CTkFrame(self, corner_radius=0)
        left.grid(row=1, column=0, sticky="nsew")
        left.grid_rowconfigure(3, weight=1)
        left.grid_columnconfigure(0, weight=1)

        actions = ctk.CTkFrame(left, fg_color="transparent")
        actions.grid(row=0, column=0, padx=14, pady=(14, 8), sticky="ew")
        actions.grid_columnconfigure((0, 1, 2), weight=1)
        ctk.CTkButton(actions, text="Neu", command=self.new_repository).grid(row=0, column=0, padx=(0, 4), sticky="ew")
        ctk.CTkButton(actions, text="Klonen", command=self.clone_selected).grid(row=0, column=1, padx=4, sticky="ew")
        ctk.CTkButton(actions, text="Ordner publizieren", command=self.publish_folder).grid(row=0, column=2, padx=(4, 0), sticky="ew")

        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *_: self.render_repo_list())
        ctk.CTkEntry(left, textvariable=self.search_var, placeholder_text="Repositories suchen …",
                     height=38).grid(row=1, column=0, padx=14, pady=8, sticky="ew")
        self.repo_count = ctk.CTkLabel(left, text="Repositories", anchor="w")
        self.repo_count.grid(row=2, column=0, padx=16, pady=(5, 0), sticky="ew")

        self.repo_frame = ctk.CTkScrollableFrame(left)
        self.repo_frame.grid(row=3, column=0, padx=10, pady=(6, 10), sticky="nsew")
        self.repo_frame.grid_columnconfigure(0, weight=1)

        settings = ctk.CTkFrame(left, fg_color="transparent")
        settings.grid(row=4, column=0, padx=14, pady=(0, 14), sticky="ew")
        settings.grid_columnconfigure(0, weight=1)
        self.projects_label = ctk.CTkLabel(settings, text=self.cfg["projects_dir"], anchor="w")
        self.projects_label.grid(row=0, column=0, padx=(0, 8), sticky="ew")
        ctk.CTkButton(settings, text="Projektordner …", width=120,
                      command=self.choose_projects_dir).grid(row=0, column=1)

    def build_right(self):
        right = ctk.CTkFrame(self, corner_radius=0)
        right.grid(row=1, column=1, sticky="nsew", padx=(1, 0))
        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(8, weight=1)

        self.repo_title = ctk.CTkLabel(right, text="Repository auswählen",
                                       font=ctk.CTkFont(size=26, weight="bold"), anchor="w")
        self.repo_title.grid(row=0, column=0, padx=24, pady=(22, 4), sticky="ew")
        self.repo_desc = ctk.CTkLabel(right, text="", anchor="w", justify="left", wraplength=760)
        self.repo_desc.grid(row=1, column=0, padx=24, pady=(0, 12), sticky="ew")

        a = ctk.CTkFrame(right, fg_color="transparent")
        a.grid(row=2, column=0, padx=24, pady=(0, 10), sticky="ew")
        self.web_btn = ctk.CTkButton(a, text="GitHub öffnen", width=125,
                                     command=self.open_selected_web, state="disabled")
        self.web_btn.grid(row=0, column=0, padx=(0, 7))
        self.folder_btn = ctk.CTkButton(a, text="Ordner öffnen", width=120,
                                        command=self.open_local_folder, state="disabled")
        self.folder_btn.grid(row=0, column=1, padx=7)
        ctk.CTkButton(a, text="Lokalen Ordner wählen", width=150,
                      command=self.choose_local_repo).grid(row=0, column=2, padx=7)

        self.local_label = ctk.CTkLabel(right, text="Lokaler Ordner: –", anchor="w")
        self.local_label.grid(row=3, column=0, padx=24, pady=(0, 10), sticky="ew")

        # Klarer Git-Workflow: Änderungen -> Commit -> Push
        self.workflow_frame = ctk.CTkFrame(right)
        self.workflow_frame.grid(row=4, column=0, padx=24, pady=(0, 10), sticky="ew")
        self.workflow_frame.grid_columnconfigure(0, weight=1)

        self.workflow_step1 = ctk.CTkLabel(
            self.workflow_frame, text="○  1. Änderungen prüfen\n    Status noch nicht geprüft",
            anchor="w", justify="left", font=ctk.CTkFont(size=14, weight="bold")
        )
        self.workflow_step1.grid(row=0, column=0, padx=16, pady=(12, 7), sticky="ew")

        self.workflow_step2 = ctk.CTkLabel(
            self.workflow_frame, text="○  2. Commit erstellen\n    Wartet auf Statusprüfung",
            anchor="w", justify="left", font=ctk.CTkFont(size=14, weight="bold")
        )
        self.workflow_step2.grid(row=1, column=0, padx=16, pady=7, sticky="ew")

        commit = ctk.CTkFrame(self.workflow_frame, fg_color="transparent")
        commit.grid(row=2, column=0, padx=16, pady=(0, 8), sticky="ew")
        commit.grid_columnconfigure(0, weight=1)
        self.commit_entry = ctk.CTkEntry(commit, placeholder_text="Commit-Nachricht …", height=38)
        self.commit_entry.grid(row=0, column=0, padx=(0, 8), sticky="ew")
        self.commit_btn = ctk.CTkButton(commit, text="Commit", width=100, command=self.commit_changes)
        self.commit_btn.grid(row=0, column=1)

        self.workflow_step3 = ctk.CTkLabel(
            self.workflow_frame, text="○  3. Auf GitHub pushen\n    Wartet auf Commit",
            anchor="w", justify="left", font=ctk.CTkFont(size=14, weight="bold")
        )
        self.workflow_step3.grid(row=3, column=0, padx=16, pady=(5, 7), sticky="ew")

        pushrow = ctk.CTkFrame(self.workflow_frame, fg_color="transparent")
        pushrow.grid(row=4, column=0, padx=16, pady=(0, 12), sticky="w")
        self.push_btn = ctk.CTkButton(pushrow, text="Push", width=100, command=self.git_push)
        self.push_btn.grid(row=0, column=0, padx=(0, 8))
        ctk.CTkButton(pushrow, text="Pull", width=100, command=self.git_pull).grid(row=0, column=1)

        tools = ctk.CTkFrame(right, fg_color="transparent")
        tools.grid(row=5, column=0, padx=24, pady=(0, 8), sticky="ew")
        ctk.CTkButton(tools, text="Status aktualisieren", width=150,
                      command=self.refresh_git_status).grid(row=0, column=0, padx=(0, 6))
        ctk.CTkButton(tools, text="Terminal", width=100,
                      command=self.open_terminal).grid(row=0, column=1, padx=6)

        ctk.CTkLabel(right, text="Technische Details", anchor="w",
                     font=ctk.CTkFont(size=13, weight="bold")).grid(
                         row=6, column=0, padx=24, pady=(2, 0), sticky="ew")
        self.status_box = ctk.CTkTextbox(right, font=("Consolas", 12), wrap="none", height=150)
        self.status_box.grid(row=8, column=0, padx=24, pady=(4, 8), sticky="nsew")
        self.show_status("Noch kein lokales Repository ausgewählt.")

        self.footer = ctk.CTkLabel(right, text="", anchor="w", font=ctk.CTkFont(size=12))
        self.footer.grid(row=9, column=0, padx=24, pady=(0, 10), sticky="ew")

    def update_workflow(self, changed_count=0, ahead=None, behind=None, upstream="keiner", has_commit=False):
        if not self.local_dir:
            self.workflow_step1.configure(text="○  1. Änderungen prüfen\n    Kein lokales Repository ausgewählt")
            self.workflow_step2.configure(text="○  2. Commit erstellen\n    Wartet auf Repository")
            self.workflow_step3.configure(text="○  3. Auf GitHub pushen\n    Wartet auf Repository")
            self.commit_btn.configure(state="disabled")
            self.push_btn.configure(state="disabled")
            return

        ahead_num = int(ahead) if str(ahead).isdigit() else 0
        behind_num = int(behind) if str(behind).isdigit() else 0
        no_upstream = not upstream or upstream == "keiner"

        if changed_count > 0:
            word = "Datei" if changed_count == 1 else "Dateien"
            self.workflow_step1.configure(text=f"●  1. Änderungen prüfen\n    {changed_count} {word} geändert")
            self.workflow_step2.configure(text="●  2. Commit erstellen\n    Änderungen noch nicht committed")
            self.commit_btn.configure(state="normal")
        else:
            self.workflow_step1.configure(text="✓  1. Keine offenen Änderungen\n    Arbeitsverzeichnis ist sauber")
            if has_commit:
                self.workflow_step2.configure(text="✓  2. Commit erstellt\n    Lokaler Commit ist vorhanden")
            else:
                self.workflow_step2.configure(text="○  2. Commit erstellen\n    Noch kein Commit vorhanden")
            self.commit_btn.configure(state="disabled")

        # Wichtig: Ein vorhandener lokaler Commit ohne Upstream ist NICHT synchron.
        # Das ist der typische erste Push eines neu verbundenen Repositories.
        if has_commit and no_upstream and changed_count == 0:
            self.workflow_step3.configure(text="●  3. Auf GitHub pushen\n    Initialer Push ausstehend")
            self.push_btn.configure(state="normal")
        elif ahead_num > 0:
            word = "Commit wartet" if ahead_num == 1 else "Commits warten"
            self.workflow_step3.configure(text=f"●  3. Auf GitHub pushen\n    {ahead_num} {word} auf Push")
            self.push_btn.configure(state="normal")
        elif behind_num > 0:
            self.workflow_step3.configure(text=f"○  3. Auf GitHub pushen\n    Erst Pull empfohlen ({behind_num} von GitHub zu holen)")
            self.push_btn.configure(state="disabled")
        elif changed_count > 0:
            self.workflow_step3.configure(text="○  3. Auf GitHub pushen\n    Wartet auf Commit")
            self.push_btn.configure(state="disabled")
        elif not has_commit:
            self.workflow_step3.configure(text="○  3. Auf GitHub pushen\n    Wartet auf ersten Commit")
            self.push_btn.configure(state="disabled")
        else:
            self.workflow_step3.configure(text="✓  3. Mit GitHub synchron\n    Nichts zu pushen")
            self.push_btn.configure(state="disabled")

    def set_footer(self, text):
        self.footer.configure(text=text)

    def show_busy(self, title, detail="Bitte warten …"):
        if getattr(self, "_busy_window", None) is not None:
            try:
                if self._busy_window.winfo_exists():
                    self._busy_title.configure(text=title)
                    self._busy_detail.configure(text=detail)
                    return
            except Exception:
                pass

        self._busy_window = ctk.CTkToplevel(self)
        self._busy_window.title("MultiGitHubGUI arbeitet")
        self._busy_window.geometry("520x235")
        self._busy_window.resizable(False, False)
        self._busy_window.transient(self)
        self._busy_window.grab_set()
        self._busy_window.protocol("WM_DELETE_WINDOW", lambda: None)
        self._busy_window.grid_columnconfigure(0, weight=1)

        self._busy_title = ctk.CTkLabel(
            self._busy_window,
            text=title,
            font=ctk.CTkFont(size=22, weight="bold"),
        )
        self._busy_title.grid(row=0, column=0, padx=30, pady=(30, 8), sticky="ew")

        self._busy_detail = ctk.CTkLabel(
            self._busy_window,
            text=detail,
            justify="center",
            wraplength=450,
        )
        self._busy_detail.grid(row=1, column=0, padx=30, pady=(0, 18), sticky="ew")

        self._busy_progress = ctk.CTkProgressBar(
            self._busy_window,
            mode="indeterminate",
        )
        self._busy_progress.grid(row=2, column=0, padx=45, pady=(4, 14), sticky="ew")
        self._busy_progress.start()

        ctk.CTkLabel(
            self._busy_window,
            text="Bitte MultiGitHubGUI während dieses Vorgangs geöffnet lassen.",
            font=ctk.CTkFont(size=12),
        ).grid(row=3, column=0, padx=20, pady=(0, 22))

        self._busy_window.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() - self._busy_window.winfo_width()) // 2
        y = self.winfo_y() + (self.winfo_height() - self._busy_window.winfo_height()) // 2
        self._busy_window.geometry(f"+{max(x, 0)}+{max(y, 0)}")

    def hide_busy(self):
        win = getattr(self, "_busy_window", None)
        if win is not None:
            try:
                if win.winfo_exists():
                    self._busy_progress.stop()
                    win.grab_release()
                    win.destroy()
            except Exception:
                pass
        self._busy_window = None

    def threaded(self, func, done=None, busy_title=None, busy_detail=None):
        if busy_title:
            self.show_busy(busy_title, busy_detail or "Bitte warten …")

        def worker():
            try:
                result = func()
                def success():
                    if busy_title:
                        self.hide_busy()
                    if done:
                        done(result)
                self.after(0, success)
            except Exception as exc:
                def failed():
                    if busy_title:
                        self.hide_busy()
                    messagebox.showerror("Fehler", str(exc), parent=self)
                self.after(0, failed)
        threading.Thread(target=worker, daemon=True).start()

    def initial_load(self):
        missing = []
        if not GH_EXE.exists():
            missing.append(f"GitHub CLI fehlt:\n{GH_EXE}")
        if not GIT_EXE.exists():
            missing.append(f"MinGit fehlt:\n{GIT_EXE}")
        if missing:
            messagebox.showerror("Build unvollständig", "\n\n".join(missing) +
                                 "\n\nBitte mit build_exe.bat neu erstellen.", parent=self)
            return
        self.refresh_everything()

    def refresh_everything(self):
        self.set_footer("Konten werden geladen …")
        def done(accounts):
            self.accounts = accounts
            if not accounts:
                self.account_menu.configure(values=["Kein Konto"])
                self.account_menu.set("Kein Konto")
                self.repos = []
                self.render_repo_list()
                self.set_footer("Kein GitHub-Konto angemeldet.")
                return
            names = [a["login"] for a in accounts]
            active = active_account(accounts)
            self.account_menu.configure(values=names)
            self.account_menu.set(active)
            self.cfg["last_account"] = active
            save_config(self.cfg)
            self.load_repositories()
        self.threaded(parse_accounts, done)

    def add_account(self):
        self.set_footer("GitHub-Anmeldung geöffnet …")
        def work():
            p = subprocess.Popen([str(GH_EXE), "auth", "login", "--hostname", HOST,
                                  "--web", "--git-protocol", "https"],
                                 env=tool_env(), creationflags=CREATE_NEW_CONSOLE)
            return p.wait()
        def done(code):
            self.refresh_everything() if code == 0 else self.set_footer("Anmeldung beendet oder fehlgeschlagen.")
        self.threaded(work, done)

    def switch_account(self, login):
        if not login or login == "Kein Konto":
            return
        self.set_footer(f"Wechsle zu {login} …")
        def work():
            run_gh(["auth", "switch", "--hostname", HOST, "--user", login])
            return login
        def done(name):
            self.cfg["last_account"] = name
            save_config(self.cfg)
            self.load_repositories()
        self.threaded(work, done)

    def load_repositories(self):
        login = self.account_menu.get()
        if not login or login == "Kein Konto":
            return
        self.set_footer(f"Repositories von {login} werden geladen …")
        def work():
            _, out, _ = run_gh(["repo", "list", login, "--limit", "200", "--json",
                                "name,nameWithOwner,description,visibility,url,isPrivate,updatedAt"])
            return json.loads(out or "[]")
        def done(items):
            self.repos = sorted(items, key=lambda r: r.get("name", "").lower())
            self.render_repo_list()
            self.set_footer(f"{len(self.repos)} Repository(s) · aktives Konto: {login}")
        self.threaded(work, done)

    def render_repo_list(self):
        for child in self.repo_frame.winfo_children():
            child.destroy()

        query = self.search_var.get().strip().lower()
        repos = [
            r for r in self.repos
            if not query
            or query in r.get("name", "").lower()
            or query in (r.get("description") or "").lower()
        ]

        self.repo_count.configure(text=f"Repositories ({len(repos)})")

        selected_name = ""
        if self.selected_repo:
            selected_name = (
                self.selected_repo.get("nameWithOwner")
                or self.selected_repo.get("name")
                or ""
            )

        for i, repo in enumerate(repos):
            name = repo.get("name", "")
            full_name = repo.get("nameWithOwner") or name
            visibility = (repo.get("visibility") or "").upper()
            is_selected = full_name == selected_name

            # Deutlichere Karten mit besserem Kontrast in Light- und Dark-Mode.
            card = ctk.CTkFrame(
                self.repo_frame,
                corner_radius=10,
                border_width=2 if is_selected else 1,
                border_color=("#1f6aa5", "#4ea1ff") if is_selected else ("#a9a9a9", "#555555"),
                fg_color=("#f4f4f4", "#242424") if not is_selected else ("#e8f2fb", "#17324a"),
            )
            card.grid(row=i, column=0, padx=4, pady=5, sticky="ew")
            card.grid_columnconfigure(0, weight=1)

            title = ctk.CTkLabel(
                card,
                text=name,
                anchor="w",
                font=ctk.CTkFont(size=15, weight="bold"),
                text_color=("#111111", "#f2f2f2"),
            )
            title.grid(row=0, column=0, padx=(14, 8), pady=(10, 3), sticky="ew")

            if visibility == "PUBLIC":
                badge_text = "PUBLIC"
                badge_fg = ("#dff5e5", "#153d24")
                badge_text_color = ("#126b2f", "#7ee787")
                badge_border = ("#7acb8b", "#2ea043")
            else:
                badge_text = "PRIVATE"
                badge_fg = ("#efe8ff", "#2f2442")
                badge_text_color = ("#6f42c1", "#c9a7ff")
                badge_border = ("#b49be8", "#8b5cf6")

            badge = ctk.CTkLabel(
                card,
                text=f"  {badge_text}  ",
                width=74,
                height=22,
                corner_radius=8,
                fg_color=badge_fg,
                text_color=badge_text_color,
                font=ctk.CTkFont(size=11, weight="bold"),
            )
            badge.grid(row=1, column=0, padx=14, pady=(2, 10), sticky="w")

            # Klick auf beliebige Stelle der Karte auswählbar machen.
            widgets = [card, title, badge]
            for widget in widgets:
                widget.bind(
                    "<Button-1>",
                    lambda _e, r=repo: self._select_repo_and_refresh(r),
                )

    def _select_repo_and_refresh(self, repo):
        self.select_repo(repo)
        self.render_repo_list()

    def select_repo(self, repo):
        self.selected_repo = repo
        self.repo_title.configure(
            text=repo.get("nameWithOwner") or repo.get("name", "")
        )
        self.repo_desc.configure(
            text=(repo.get("description") or "Keine Beschreibung")
            + f"   ·   {repo.get('visibility', '')}"
        )
        self.web_btn.configure(state="normal")

        repo_key = repo.get("nameWithOwner") or repo.get("name", "")
        saved_path = self.cfg.get("repo_paths", {}).get(repo_key, "")

        # Zuerst die dauerhaft gespeicherte Zuordnung verwenden.
        if saved_path:
            saved = Path(saved_path)
            if saved.exists() and (saved / ".git").exists():
                self.set_local_repo(saved, save_mapping=False)
                return

        # Fallback: klassischer Projektordner + Repository-Name.
        suggested = Path(self.cfg["projects_dir"]) / repo.get("name", "")
        if (suggested / ".git").exists():
            self.set_local_repo(suggested)
        else:
            self.local_dir = None
            self.local_label.configure(text="Lokaler Ordner: nicht zugeordnet")
            self.folder_btn.configure(state="disabled")
            self.show_status(
                "Für dieses Repository ist noch kein lokaler Ordner zugeordnet.\n\n"
                "Mit „Lokalen Ordner wählen“ kannst du eine dauerhafte Zuordnung speichern."
            )

    def choose_projects_dir(self):
        selected = filedialog.askdirectory(title="Standardordner für Projekte auswählen",
                                           initialdir=self.cfg["projects_dir"])
        if selected:
            self.cfg["projects_dir"] = selected
            Path(selected).mkdir(parents=True, exist_ok=True)
            save_config(self.cfg)
            self.projects_label.configure(text=selected)

    def new_repository(self):
        if not self.accounts:
            messagebox.showinfo("Kein Konto", "Bitte zuerst ein GitHub-Konto anmelden.", parent=self)
            return
        RepoDialog(self, "Neues Repository", init_options=True, on_submit=self.create_repository)

    def create_repository(self, data):
        projects = Path(self.cfg["projects_dir"])
        projects.mkdir(parents=True, exist_ok=True)
        self.set_footer(f"Repository {data['name']} wird erstellt …")
        def work():
            args = ["repo", "create", data["name"], "--private" if data["private"] else "--public", "--clone"]
            if data["description"]:
                args += ["--description", data["description"]]
            if data["readme"]:
                args.append("--add-readme")
            if data["gitignore"] != "Keine":
                args += ["--gitignore", data["gitignore"]]
            if data["license"] != "Keine":
                args += ["--license", data["license"]]
            run_gh(args, cwd=projects, timeout=240)
            return projects / data["name"]
        def done(path):
            self.set_footer(f"Repository erstellt: {data['name']}")
            self.load_repositories()
            if path.exists():
                self.set_local_repo(path)
        self.threaded(
            work,
            done,
            busy_title="Repository wird erstellt …",
            busy_detail="GitHub-Repository und lokaler Projektordner werden vorbereitet.",
        )

    def clone_selected(self):
        if not self.selected_repo:
            messagebox.showinfo("Repository", "Bitte ein Repository auswählen.", parent=self)
            return
        projects = Path(self.cfg["projects_dir"])
        projects.mkdir(parents=True, exist_ok=True)
        target = projects / self.selected_repo["name"]
        if target.exists() and any(target.iterdir()):
            messagebox.showerror("Ordner existiert", f"Der Zielordner ist nicht leer:\n{target}", parent=self)
            return
        full_name = self.selected_repo.get("nameWithOwner") or self.selected_repo["name"]
        self.set_footer(f"{full_name} wird geklont …")
        def work():
            run_gh(["repo", "clone", full_name, str(target)], timeout=300)
            return target
        def done(path):
            self.set_footer("Repository erfolgreich geklont.")
            self.set_local_repo(path)
        self.threaded(
            work,
            done,
            busy_title="Repository wird geklont …",
            busy_detail="Dateien werden von GitHub in den lokalen Projektordner geladen.",
        )

    def publish_folder(self):
        if not self.accounts:
            messagebox.showinfo("Kein Konto", "Bitte zuerst ein GitHub-Konto anmelden.", parent=self)
            return
        folder = filedialog.askdirectory(title="Ordner auswählen, der auf GitHub veröffentlicht werden soll")
        if not folder:
            return
        path = Path(folder)
        RepoDialog(self, "Vorhandenen Ordner veröffentlichen", default_name=path.name,
                   init_options=False, on_submit=lambda data: self.publish_selected_folder(path, data))

    def publish_selected_folder(self, folder, data):
        self.set_footer(f"{folder.name} wird vorbereitet …")
        def work():
            if not (folder / ".git").exists():
                run_git(["init"], cwd=folder)
            args = ["repo", "create", data["name"], "--private" if data["private"] else "--public",
                    "--source", str(folder), "--remote", "origin"]
            if data["description"]:
                args += ["--description", data["description"]]
            run_gh(args, cwd=folder, timeout=180)
            run_git(["add", "-A"], cwd=folder, allow_error=True)
            head_code, _, _ = run_git(["rev-parse", "--verify", "HEAD"], cwd=folder, allow_error=True)
            if head_code != 0:
                commit_code, _, commit_err = run_git(["commit", "-m", "Initial commit"], cwd=folder, allow_error=True)
                if commit_code != 0 and "nothing to commit" not in commit_err.lower():
                    return folder, "GitHub-Repository angelegt. Erster Commit noch offen (ggf. Git Name/E-Mail konfigurieren)."
            push_code, _, push_err = run_git(["push", "-u", "origin", "HEAD"], cwd=folder,
                                              allow_error=True, timeout=180)
            if push_code != 0:
                return folder, "Repository verbunden; erster Push noch offen:\n" + push_err
            return folder, "Ordner wurde erfolgreich auf GitHub veröffentlicht."
        def done(result):
            path, info = result
            self.set_local_repo(path)
            self.load_repositories()
            self.set_footer(info)
            if "erfolgreich" not in info.lower():
                messagebox.showinfo("Hinweis", info, parent=self)
        self.threaded(work, done)

    def choose_local_repo(self):
        folder = filedialog.askdirectory(title="Lokalen Projektordner auswählen")
        if not folder:
            return

        path = Path(folder)

        # Bereits ein Git-Repository -> direkt verwenden.
        if (path / ".git").exists():
            self.set_local_repo(path)
            return

        # Für einen normalen vorhandenen Projektordner muss zuerst das
        # zugehörige GitHub-Repository ausgewählt sein.
        if not self.selected_repo:
            messagebox.showinfo(
                "Kein Git-Repository",
                "Der gewählte Ordner ist noch kein Git-Repository.\n\n"
                "Bitte zuerst links das passende GitHub-Repository auswählen. "
                "Danach kann MultiGitHubGUI den Ordner initialisieren und verbinden.",
                parent=self,
            )
            return

        full_name = (
            self.selected_repo.get("nameWithOwner")
            or self.selected_repo.get("name")
            or ""
        )
        remote_url = self.selected_repo.get("url") or (
            f"https://github.com/{full_name}" if full_name else ""
        )
        if remote_url and not remote_url.endswith(".git"):
            remote_url += ".git"

        if not remote_url:
            messagebox.showerror(
                "Repository",
                "Für das ausgewählte GitHub-Repository konnte keine Remote-URL ermittelt werden.",
                parent=self,
            )
            return

        answer = messagebox.askyesno(
            "Ordner mit GitHub verbinden",
            "Im gewählten Ordner wurde noch kein .git-Verzeichnis gefunden.\n\n"
            "Soll MultiGitHubGUI den Ordner als Git-Repository initialisieren "
            f"und mit\n{full_name}\nverbinden?\n\n"
            "Vorhandene Dateien bleiben erhalten.",
            parent=self,
        )
        if not answer:
            return

        self.set_footer(f"{path.name} wird mit {full_name} verbunden …")

        def work():
            run_git(["init"], cwd=path)

            # Remote origin anlegen bzw. auf das ausgewählte Repository setzen.
            code, out, _ = run_git(
                ["remote", "get-url", "origin"],
                cwd=path,
                allow_error=True,
            )
            if code == 0 and out:
                run_git(["remote", "set-url", "origin", remote_url], cwd=path)
            else:
                run_git(["remote", "add", "origin", remote_url], cwd=path)

            # Nur Informationen vom Remote holen. Dabei werden lokale Dateien
            # weder überschrieben noch automatisch gemergt.
            run_git(
                ["fetch", "origin"],
                cwd=path,
                allow_error=True,
                timeout=180,
            )
            return path

        def done(repo_path):
            self.set_local_repo(repo_path)
            self.set_footer(f"Lokaler Ordner wurde mit {full_name} verbunden.")
            messagebox.showinfo(
                "Verbunden",
                "Der lokale Ordner wurde erfolgreich initialisiert und mit dem "
                "ausgewählten GitHub-Repository verbunden.\n\n"
                "Es wurde dabei nichts überschrieben und noch nichts automatisch gepusht.",
                parent=self,
            )

        self.threaded(work, done)

    def set_local_repo(self, path, save_mapping=True):
        path = Path(path)
        self.local_dir = path
        self.local_label.configure(text=f"Lokaler Ordner: {path}")
        self.folder_btn.configure(state="normal")

        if save_mapping and self.selected_repo:
            repo_key = (
                self.selected_repo.get("nameWithOwner")
                or self.selected_repo.get("name")
                or ""
            )
            if repo_key:
                self.cfg.setdefault("repo_paths", {})
                self.cfg["repo_paths"][repo_key] = str(path)
                save_config(self.cfg)

        self.refresh_git_status()

    def show_status(self, text):
        self.status_box.configure(state="normal")
        self.status_box.delete("1.0", "end")
        self.status_box.insert("1.0", text)
        self.status_box.configure(state="disabled")

    def refresh_git_status(self):
        if not self.local_dir:
            self.update_workflow()
            return

        path = self.local_dir
        self.set_footer("Git-Status wird aktualisiert …")

        def work():
            def git_text(args, default="–"):
                code, out, _ = run_git(args, cwd=path, allow_error=True)
                value = (out or "").strip()
                return value if code == 0 and value else default

            branch = git_text(["rev-parse", "--abbrev-ref", "HEAD"], "unbekannt")
            remote = git_text(["remote", "get-url", "origin"], "kein origin")
            git_user = git_text(["config", "--local", "user.name"], "nicht gesetzt")
            git_email = git_text(["config", "--local", "user.email"], "nicht gesetzt")
            upstream = git_text(["rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"], "keiner")
            commit_code, _, _ = run_git(["rev-parse", "--verify", "HEAD"], cwd=path, allow_error=True)
            has_commit = commit_code == 0
            last_commit = git_text(["log", "-1", "--pretty=format:%h  %s"], "noch kein Commit")

            code, tracked_out, _ = run_git(["ls-tree", "-r", "--name-only", "HEAD"], cwd=path, allow_error=True)
            tracked_text = str(len([x for x in (tracked_out or "").splitlines() if x.strip()])) if code == 0 else "0"

            ahead = "0"
            behind = "0"
            if upstream != "keiner":
                code, counts, _ = run_git(["rev-list", "--left-right", "--count", "HEAD...@{u}"], cwd=path, allow_error=True)
                if code == 0 and counts:
                    parts = counts.replace("\t", " ").split()
                    if len(parts) >= 2:
                        ahead, behind = parts[0], parts[1]

            _, short_status, _ = run_git(["status", "--short"], cwd=path, allow_error=True)
            short_status = (short_status or "").strip()
            changed_count = len([x for x in short_status.splitlines() if x.strip()])

            lines = [
                f"Branch:              {branch}",
                f"Remote origin:       {remote}",
                f"Commit-User:         {git_user}",
                f"Commit-E-Mail:       {git_email}",
                f"Upstream:            {upstream}",
                f"Letzter Commit:       {last_commit}",
                f"Dateien im Commit:    {tracked_text}",
                f"Commits zu pushen:    {'Initialer Push' if has_commit and upstream == 'keiner' else ahead}",
                f"Von Remote zu holen:  {behind}",
                "",
                "Arbeitsverzeichnis:",
                short_status if short_status else "sauber – keine uncommitteten Änderungen",
            ]
            return {
                "text": "\n".join(lines),
                "changed": changed_count,
                "ahead": ahead,
                "behind": behind,
                "upstream": upstream,
                "has_commit": has_commit,
            }

        def done(result):
            self.show_status(result["text"])
            self.update_workflow(
                result["changed"],
                result["ahead"],
                result["behind"],
                result["upstream"],
                result["has_commit"],
            )
            self.set_footer("Git-Status aktualisiert.")

        self.threaded(work, done)

    def ensure_owner_account(self):
        if not self.selected_repo:
            raise RuntimeError("Bitte zuerst ein GitHub-Repository auswählen.")

        repo_name = (
            self.selected_repo.get("nameWithOwner")
            or self.selected_repo.get("name")
            or ""
        )
        if "/" not in repo_name:
            raise RuntimeError("Der Repository-Owner konnte nicht ermittelt werden.")

        repo_owner = repo_name.split("/", 1)[0]
        selected_account = (self.account_menu.get() or "").strip()

        if not selected_account or selected_account == "Kein Konto":
            raise RuntimeError("Bitte zuerst ein GitHub-Konto auswählen.")

        if selected_account.lower() != repo_owner.lower():
            raise RuntimeError(
                "Sicherheitsprüfung fehlgeschlagen.\n\n"
                f"Ausgewählter Account: {selected_account}\n"
                f"Repository-Owner:      {repo_owner}\n\n"
                "Commit und Push sind nur mit dem Repository-Owner erlaubt."
            )

        run_gh(
            [
                "auth",
                "switch",
                "--hostname",
                HOST,
                "--user",
                repo_owner,
            ]
        )

        return repo_owner, repo_name

    def configure_commit_identity(self):
        if not self.local_dir:
            raise RuntimeError("Kein lokales Repository ausgewählt.")

        repo_owner, _ = self.ensure_owner_account()

        _, raw, _ = run_gh(["api", "user"])
        try:
            user_data = json.loads(raw or "{}")
        except Exception:
            user_data = {}

        login = str(user_data.get("login") or repo_owner).strip()
        user_id = str(user_data.get("id") or "").strip()
        display_name = str(user_data.get("name") or login).strip()

        if login.lower() != repo_owner.lower():
            raise RuntimeError(
                "GitHub CLI verwendet nicht den erwarteten Repository-Owner.\n\n"
                f"Erwartet: {repo_owner}\n"
                f"Aktiv:    {login}"
            )

        if user_id:
            email = f"{user_id}+{login}@users.noreply.github.com"
        else:
            email = f"{login}@users.noreply.github.com"

        run_git(["config", "--local", "user.name", display_name], cwd=self.local_dir)
        run_git(["config", "--local", "user.email", email], cwd=self.local_dir)

        return login, display_name, email

    def commit_changes(self):
        if not self.local_dir:
            messagebox.showinfo("Commit", "Bitte zuerst ein lokales Repository wählen.", parent=self)
            return
        msg = self.commit_entry.get().strip()
        if not msg:
            messagebox.showinfo("Commit", "Bitte eine Commit-Nachricht eingeben.", parent=self)
            return
        path = self.local_dir
        def work():
            login, display_name, email = self.configure_commit_identity()
            run_git(["add", "-A"], cwd=path)
            run_git(["commit", "-m", msg], cwd=path)
            return {
                "login": login,
                "display_name": display_name,
                "email": email,
            }
        def done(identity):
            self.commit_entry.delete(0, "end")
            self.refresh_git_status()
            if identity:
                self.set_footer(
                    f"Commit erstellt als {identity.get('login', '')}."
                )
        self.threaded(
            work,
            done,
            busy_title="Commit wird erstellt …",
            busy_detail="Änderungen werden gesammelt und lokal als Commit gespeichert.",
        )

    def git_pull(self):
        self.git_action(["pull"], "Pull abgeschlossen.")

    def git_push(self):
        if not self.local_dir:
            messagebox.showinfo(
                "Git",
                "Bitte zuerst ein lokales Repository wählen.",
                parent=self,
            )
            return

        if not self.selected_repo:
            self.git_action(["push"], "Push abgeschlossen.")
            return

        path = self.local_dir
        repo_name = (
            self.selected_repo.get("nameWithOwner")
            or self.selected_repo.get("name")
            or ""
        )

        try:
            repo_owner, _ = self.ensure_owner_account()
        except Exception as exc:
            messagebox.showerror(
                "Push blockiert",
                str(exc),
                parent=self,
            )
            self.set_footer("Push blockiert: falscher GitHub-Account.")
            return

        def inspect():
            _, local_branch, _ = run_git(
                ["rev-parse", "--abbrev-ref", "HEAD"],
                cwd=path,
                allow_error=True,
            )
            local_branch = (local_branch or "").strip()

            _, default_branch, _ = run_gh(
                [
                    "repo",
                    "view",
                    repo_name,
                    "--json",
                    "defaultBranchRef",
                    "--jq",
                    ".defaultBranchRef.name",
                ],
                allow_error=True,
            )
            default_branch = (default_branch or "").strip()

            upstream_code, upstream, _ = run_git(
                [
                    "rev-parse",
                    "--abbrev-ref",
                    "--symbolic-full-name",
                    "@{u}",
                ],
                cwd=path,
                allow_error=True,
            )
            upstream = (upstream or "").strip() if upstream_code == 0 else ""

            # Direkt beim Remote prüfen, ob der Zielbranch bereits existiert.
            _, remote_heads, _ = run_git(
                ["ls-remote", "--heads", "origin", default_branch or local_branch],
                cwd=path,
                allow_error=True,
                timeout=180,
            )
            remote_branch_exists = bool((remote_heads or "").strip())

            return local_branch, default_branch, upstream, remote_branch_exists

        def inspected(result):
            local_branch, default_branch, upstream, remote_branch_exists = result

            if not local_branch:
                messagebox.showerror(
                    "Branch nicht erkannt",
                    "Der lokale Git-Branch konnte nicht ermittelt werden.",
                    parent=self,
                )
                return

            target_branch = default_branch or local_branch

            # Fall 1: lokal master, GitHub main (oder sonst unterschiedliche Namen)
            if default_branch and local_branch != default_branch:
                answer = messagebox.askyesno(
                    "Branch an GitHub anpassen",
                    "Der lokale Branch und der GitHub-Standardbranch unterscheiden sich.\n\n"
                    f"Lokal:   {local_branch}\n"
                    f"GitHub:  {default_branch}\n\n"
                    f"Soll MultiGitHubGUI den lokalen Branch auf „{default_branch}“ "
                    "umstellen, den vorhandenen GitHub-Stand zusammenführen und "
                    "anschließend dorthin pushen?\n\n"
                    "Vorhandene lokale Dateien werden dabei nicht gelöscht.",
                    parent=self,
                )
                if answer:
                    self.reconcile_to_default_branch(
                        local_branch,
                        default_branch,
                        repo_name,
                    )
                return

            # Fall 2: Branchname ist bereits gleich (z. B. main/main), aber es
            # existiert noch kein Upstream und GitHub hat auf diesem Branch
            # bereits Commits (typisch README/Lizenz beim Erstellen des Repos).
            if not upstream and remote_branch_exists:
                answer = messagebox.askyesno(
                    "Lokalen und GitHub-Stand verbinden",
                    f"Der lokale Branch „{local_branch}“ ist noch nicht mit "
                    f"„origin/{target_branch}“ verbunden.\n\n"
                    "Auf GitHub existiert dieser Branch bereits, z. B. durch "
                    "eine dort angelegte README oder Lizenz.\n\n"
                    "Soll MultiGitHubGUI beide Stände jetzt zusammenführen "
                    "und anschließend auf GitHub veröffentlichen?\n\n"
                    "Lokale Dateien werden dabei nicht gelöscht.",
                    parent=self,
                )
                if answer:
                    self.reconcile_to_default_branch(
                        local_branch,
                        target_branch,
                        repo_name,
                    )
                return

            # Fall 3: Noch kein Upstream und Remote-Branch existiert nicht:
            # normaler erster Push.
            self.git_action(["push"], "Push abgeschlossen.")

        self.threaded(
            inspect,
            inspected,
            busy_title="Push wird vorbereitet …",
            busy_detail=(
                "MultiGitHubGUI prüft Branch, Upstream und den vorhandenen "
                "GitHub-Stand. Bitte warten."
            ),
        )

    def reconcile_to_default_branch(self, old_branch, default_branch, repo_name):
        if not self.local_dir:
            return

        path = self.local_dir
        self.set_footer(
            f"Branch wird auf {default_branch} umgestellt und zusammengeführt …"
        )

        def work():
            # Aktuellen Stand vom Remote holen.
            run_git(["fetch", "origin"], cwd=path, timeout=300)

            # Lokalen Branch auf den GitHub-Standardbranch umbenennen.
            if old_branch != default_branch:
                run_git(
                    ["branch", "-M", default_branch],
                    cwd=path,
                )

            # Prüfen, ob der Remote-Defaultbranch existiert.
            remote_code, _, _ = run_git(
                [
                    "show-ref",
                    "--verify",
                    "--quiet",
                    f"refs/remotes/origin/{default_branch}",
                ],
                cwd=path,
                allow_error=True,
            )

            if remote_code == 0:
                # GitHub-Startdateien (z. B. README/LICENSE) mit der lokalen
                # Historie zusammenführen. Bei Konflikten werden lokale Inhalte
                # bevorzugt; reine Remote-Dateien bleiben erhalten.
                merge_code, merge_out, merge_err = run_git(
                    [
                        "merge",
                        f"origin/{default_branch}",
                        "--allow-unrelated-histories",
                        "--no-edit",
                        "-X",
                        "ours",
                    ],
                    cwd=path,
                    allow_error=True,
                    timeout=300,
                )

                if merge_code != 0:
                    # Merge abbrechen, damit das Repository nicht in einem
                    # halbfertigen Zustand bleibt.
                    run_git(
                        ["merge", "--abort"],
                        cwd=path,
                        allow_error=True,
                    )
                    raise RuntimeError(
                        "Der vorhandene GitHub-Stand konnte nicht automatisch "
                        "zusammengeführt werden.\n\n"
                        + (merge_err or merge_out or "Unbekannter Merge-Fehler")
                    )

            # Jetzt explizit auf den Standardbranch pushen und Upstream setzen.
            run_git(
                ["push", "-u", "origin", default_branch],
                cwd=path,
                timeout=300,
            )

            # Prüfen, ob durch einen früheren MultiGitHubGUI-Lauf zusätzlich
            # der alte Branch auf GitHub angelegt wurde.
            _, heads, _ = run_git(
                ["ls-remote", "--heads", "origin", old_branch],
                cwd=path,
                allow_error=True,
            )
            old_remote_exists = bool((heads or "").strip()) and old_branch != default_branch

            return old_remote_exists

        def done(old_remote_exists):
            self.refresh_git_status()
            self.set_footer(
                f"Push auf {default_branch} erfolgreich abgeschlossen."
            )

            if old_remote_exists:
                remove_old = messagebox.askyesno(
                    "Alter Remote-Branch gefunden",
                    f"Der frühere Branch „{old_branch}“ existiert noch zusätzlich auf GitHub.\n\n"
                    f"Der aktuelle Stand liegt jetzt korrekt auf „{default_branch}“.\n\n"
                    f"Soll der überflüssige Remote-Branch „{old_branch}“ gelöscht werden?",
                    parent=self,
                )
                if remove_old:
                    self.delete_remote_branch(old_branch)
                    return

            messagebox.showinfo(
                "Erfolgreich",
                f"Der lokale Stand wurde erfolgreich auf „{default_branch}“ veröffentlicht.",
                parent=self,
            )

        self.threaded(
            work,
            done,
            busy_title=f"Auf {default_branch} umstellen …",
            busy_detail=(
                f"Der lokale Branch wird auf „{default_branch}“ umgestellt, "
                "mit dem vorhandenen GitHub-Stand zusammengeführt und gepusht.\n"
                "Bitte warten – dieses Fenster bleibt bis zum Abschluss geöffnet."
            ),
        )

    def delete_remote_branch(self, branch):
        if not self.local_dir:
            return

        path = self.local_dir

        def work():
            run_git(
                ["push", "origin", "--delete", branch],
                cwd=path,
                timeout=300,
            )
            run_git(
                ["fetch", "--prune", "origin"],
                cwd=path,
                allow_error=True,
                timeout=180,
            )
            return True

        def done(_):
            self.refresh_git_status()
            self.set_footer(f"Remote-Branch {branch} wurde gelöscht.")
            messagebox.showinfo(
                "Bereinigt",
                f"Der überflüssige Remote-Branch „{branch}“ wurde gelöscht.",
                parent=self,
            )

        self.threaded(
            work,
            done,
            busy_title="Remote-Branch wird gelöscht …",
            busy_detail=f"Der überflüssige Branch „{branch}“ wird von GitHub entfernt.",
        )

    def git_action(self, args, success):
        if not self.local_dir:
            messagebox.showinfo(
                "Git",
                "Bitte zuerst ein lokales Repository wählen.",
                parent=self,
            )
            return

        path = self.local_dir

        if args and args[0].lower() == "push":
            try:
                self.ensure_owner_account()
            except Exception as exc:
                messagebox.showerror(
                    "Push blockiert",
                    str(exc),
                    parent=self,
                )
                self.set_footer("Push blockiert: falscher GitHub-Account.")
                return
        action = args[0].lower() if args else "git"

        if action == "push":
            self.set_footer("git push läuft …")
            busy_title = "Push läuft …"
            busy_detail = (
                "Lokale Commits werden zu GitHub übertragen.\n"
                "Dieses Fenster bleibt geöffnet, bis der Vorgang abgeschlossen ist."
            )
        elif action == "pull":
            self.set_footer("git pull läuft …")
            busy_title = "Pull läuft …"
            busy_detail = (
                "Änderungen werden von GitHub abgerufen.\n"
                "Dieses Fenster bleibt geöffnet, bis der Vorgang abgeschlossen ist."
            )
        else:
            self.set_footer(f"git {' '.join(args)} läuft …")
            busy_title = "Git arbeitet …"
            busy_detail = "Der Git-Vorgang wird ausgeführt. Bitte warten."

        def work():
            if action == "push":
                # Prüfen, ob der aktuelle Branch bereits einen Upstream besitzt.
                code, branch, _ = run_git(
                    ["rev-parse", "--abbrev-ref", "HEAD"],
                    cwd=path,
                    allow_error=True,
                )
                branch = (branch or "").strip()
                if code != 0 or not branch or branch == "HEAD":
                    raise RuntimeError(
                        "Der aktuelle Git-Branch konnte nicht ermittelt werden."
                    )

                upstream_code, _, _ = run_git(
                    ["rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"],
                    cwd=path,
                    allow_error=True,
                )

                if upstream_code != 0:
                    # Erster Push: Upstream automatisch setzen.
                    run_git(
                        ["push", "-u", "origin", branch],
                        cwd=path,
                        timeout=300,
                    )
                    return f"Erster Push erfolgreich. Upstream: origin/{branch}"

                run_git(["push"], cwd=path, timeout=300)
                return "Push erfolgreich abgeschlossen."

            if action == "pull":
                run_git(["pull"], cwd=path, timeout=300)
                return "Pull erfolgreich abgeschlossen."

            run_git(args, cwd=path, timeout=300)
            return success

        def done(message):
            self.set_footer(message)
            self.refresh_git_status()
            messagebox.showinfo(
                "Erfolgreich",
                message,
                parent=self,
            )

        self.threaded(
            work,
            done,
            busy_title=busy_title,
            busy_detail=busy_detail,
        )

    def open_selected_web(self):
        if self.selected_repo and self.selected_repo.get("url"):
            webbrowser.open(self.selected_repo["url"])

    def open_local_folder(self):
        if self.local_dir and self.local_dir.exists():
            os.startfile(str(self.local_dir))

    def open_terminal(self):
        if not self.local_dir:
            messagebox.showinfo(
                "Terminal",
                "Bitte zuerst ein lokales Repository auswählen.",
                parent=self,
            )
            return

        repo_dir = Path(self.local_dir)
        if not repo_dir.exists():
            messagebox.showerror(
                "Terminal",
                f"Der lokale Repository-Ordner existiert nicht mehr:\n{repo_dir}",
                parent=self,
            )
            return

        # Exakt dieselbe Umgebung wie für interne Git-Aufrufe verwenden:
        # eingebettetes MinGit + eingebettete GitHub CLI + deaktivierter Pager.
        env = tool_env()
        env["GIT_PAGER"] = "cat"
        env["PAGER"] = "cat"
        env["GH_PAGER"] = "cat"

        # cmd.exe direkt mit cwd starten. Dadurch landen wir zuverlässig im
        # lokalen Ordner des aktuell ausgewählten Repositories und nicht im
        # dist-Verzeichnis der EXE.
        try:
            subprocess.Popen(
                [
                    "cmd.exe",
                    "/K",
                    (
                        'title MultiGitHubGUI - Git Terminal'
                        ' & echo.'
                        ' & echo MultiGitHubGUI Git-Terminal'
                        f' & echo Repository: {repo_dir}'
                        ' & echo.'
                        ' & git --version'
                        ' & gh --version'
                        ' & echo.'
                    ),
                ],
                cwd=str(repo_dir),
                env=env,
                creationflags=CREATE_NEW_CONSOLE,
            )
        except Exception as exc:
            messagebox.showerror(
                "Terminal konnte nicht geöffnet werden",
                str(exc),
                parent=self,
            )

    def show_about(self):
        win = ctk.CTkToplevel(self)
        win.title("Über dieses Projekt")
        win.geometry("590x500")
        win.resizable(False, False)
        win.transient(self)
        win.grab_set()
        win.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            win,
            text="Über dieses Projekt",
            font=ctk.CTkFont(size=20, weight="bold"),
            anchor="w",
        ).grid(row=0, column=0, padx=24, pady=(22, 12), sticky="ew")

        ctk.CTkFrame(win, height=1).grid(
            row=1, column=0, sticky="ew", padx=18
        )

        ctk.CTkLabel(
            win,
            text="MultiGitHubGUI",
            font=ctk.CTkFont(size=28, weight="bold"),
        ).grid(row=2, column=0, pady=(28, 10))

        ctk.CTkLabel(
            win,
            text=(
                "MultiGitHubGUI wird auf GitHub veröffentlicht und\n"
                "unter der MIT License bereitgestellt."
            ),
            justify="center",
        ).grid(row=3, column=0, padx=24, pady=(0, 18))

        links = ctk.CTkFrame(win, fg_color="transparent")
        links.grid(row=4, column=0, padx=24, pady=2)

        ctk.CTkLabel(links, text="GitHub:").grid(
            row=0, column=0, sticky="e", padx=(0, 8), pady=5
        )
        github = ctk.CTkLabel(
            links,
            text="https://github.com/fachlehrer-dev/MultiGitHubGUI",
            text_color=("#0078D4", "#4da3ff"),
            cursor="hand2",
        )
        github.grid(row=0, column=1, sticky="w", pady=5)
        github.bind(
            "<Button-1>",
            lambda _e: webbrowser.open(
                "https://github.com/fachlehrer-dev/MultiGitHubGUI"
            ),
        )

        ctk.CTkLabel(links, text="Website:").grid(
            row=1, column=0, sticky="e", padx=(0, 8), pady=5
        )
        website = ctk.CTkLabel(
            links,
            text="https://fachlehrer.dev/MultiGitHubGUI",
            text_color=("#0078D4", "#4da3ff"),
            cursor="hand2",
        )
        website.grid(row=1, column=1, sticky="w", pady=5)
        website.bind(
            "<Button-1>",
            lambda _e: webbrowser.open(
                "https://fachlehrer.dev/MultiGitHubGUI"
            ),
        )

        ctk.CTkFrame(win, height=1).grid(
            row=5, column=0, sticky="ew", padx=18, pady=(20, 16)
        )

        ctk.CTkLabel(
            win,
            text="Developed by Fred Maier",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).grid(row=6, column=0, pady=(0, 4))

        ctk.CTkLabel(
            win,
            text="Published by IFL Bayreuth",
        ).grid(row=7, column=0, pady=(0, 8))

        contact = ctk.CTkLabel(
            win,
            text="Contact: fred@fachlehrer.dev",
            text_color=("#0078D4", "#4da3ff"),
            cursor="hand2",
        )
        contact.grid(row=8, column=0, pady=(0, 16))
        contact.bind(
            "<Button-1>",
            lambda _e: webbrowser.open("mailto:fred@fachlehrer.dev"),
        )

        ctk.CTkButton(
            win,
            text="Schließen",
            width=120,
            command=win.destroy,
        ).grid(row=9, column=0, pady=(0, 20))

    def change_theme(self, theme):
        ctk.set_appearance_mode(theme)
        self.cfg["theme"] = theme
        save_config(self.cfg)

    def on_close(self):
        self.cfg["window"]["width"] = self.winfo_width()
        self.cfg["window"]["height"] = self.winfo_height()
        save_config(self.cfg)
        self.destroy()


if __name__ == "__main__":
    MultiGitHubGUI().mainloop()
