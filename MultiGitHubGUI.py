from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import threading
import webbrowser
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk

APP_NAME = "MultiGitHubGUI"
HOST = "github.com"
CREATE_NO_WINDOW = 0x08000000 if os.name == "nt" else 0
CREATE_NEW_CONSOLE = 0x00000010 if os.name == "nt" else 0


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
        ctk.set_appearance_mode(self.cfg.get("theme", "System"))
        ctk.set_default_color_theme("blue")
        super().__init__()

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
        right.grid_rowconfigure(4, weight=1)

        self.repo_title = ctk.CTkLabel(right, text="Repository auswählen",
                                       font=ctk.CTkFont(size=26, weight="bold"), anchor="w")
        self.repo_title.grid(row=0, column=0, padx=24, pady=(22, 4), sticky="ew")
        self.repo_desc = ctk.CTkLabel(right, text="", anchor="w", justify="left", wraplength=760)
        self.repo_desc.grid(row=1, column=0, padx=24, pady=(0, 12), sticky="ew")

        a = ctk.CTkFrame(right, fg_color="transparent")
        a.grid(row=2, column=0, padx=24, pady=(0, 12), sticky="ew")
        self.web_btn = ctk.CTkButton(a, text="GitHub öffnen", width=125,
                                     command=self.open_selected_web, state="disabled")
        self.web_btn.grid(row=0, column=0, padx=(0, 7))
        self.folder_btn = ctk.CTkButton(a, text="Ordner öffnen", width=120,
                                        command=self.open_local_folder, state="disabled")
        self.folder_btn.grid(row=0, column=1, padx=7)
        ctk.CTkButton(a, text="Lokalen Ordner wählen", width=150,
                      command=self.choose_local_repo).grid(row=0, column=2, padx=7)

        self.local_label = ctk.CTkLabel(right, text="Lokaler Ordner: –", anchor="w")
        self.local_label.grid(row=3, column=0, padx=24, pady=(0, 6), sticky="ew")
        self.status_box = ctk.CTkTextbox(right, font=("Consolas", 13), wrap="none")
        self.status_box.grid(row=4, column=0, padx=24, pady=(4, 12), sticky="nsew")
        self.show_status("Noch kein lokales Repository ausgewählt.")

        commit = ctk.CTkFrame(right, fg_color="transparent")
        commit.grid(row=5, column=0, padx=24, pady=(0, 10), sticky="ew")
        commit.grid_columnconfigure(0, weight=1)
        self.commit_entry = ctk.CTkEntry(commit, placeholder_text="Commit-Nachricht …", height=40)
        self.commit_entry.grid(row=0, column=0, padx=(0, 8), sticky="ew")
        ctk.CTkButton(commit, text="Commit", width=100, command=self.commit_changes).grid(row=0, column=1)

        g = ctk.CTkFrame(right, fg_color="transparent")
        g.grid(row=6, column=0, padx=24, pady=(0, 12), sticky="ew")
        ctk.CTkButton(g, text="Pull", width=95, command=self.git_pull).grid(row=0, column=0, padx=(0, 6))
        ctk.CTkButton(g, text="Push", width=95, command=self.git_push).grid(row=0, column=1, padx=6)
        ctk.CTkButton(g, text="Status aktualisieren", width=150,
                      command=self.refresh_git_status).grid(row=0, column=2, padx=6)
        ctk.CTkButton(g, text="Terminal", width=100, command=self.open_terminal).grid(row=0, column=3, padx=6)
        self.footer = ctk.CTkLabel(right, text="", anchor="w", font=ctk.CTkFont(size=12))
        self.footer.grid(row=7, column=0, padx=24, pady=(0, 12), sticky="ew")

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
        self.repo_title.configure(text=repo.get("nameWithOwner") or repo.get("name", ""))
        self.repo_desc.configure(text=(repo.get("description") or "Keine Beschreibung") +
                                 f"   ·   {repo.get('visibility', '')}")
        self.web_btn.configure(state="normal")
        suggested = Path(self.cfg["projects_dir"]) / repo.get("name", "")
        if (suggested / ".git").exists():
            self.set_local_repo(suggested)
        else:
            self.local_dir = None
            self.local_label.configure(text="Lokaler Ordner: nicht gefunden")
            self.folder_btn.configure(state="disabled")
            self.show_status("Dieses Repository ist im Projektordner noch nicht geklont.\n\n"
                             "Mit „Klonen“ kannst du es lokal anlegen.")

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

    def set_local_repo(self, path):
        self.local_dir = Path(path)
        self.local_label.configure(text=f"Lokaler Ordner: {path}")
        self.folder_btn.configure(state="normal")
        self.refresh_git_status()

    def show_status(self, text):
        self.status_box.configure(state="normal")
        self.status_box.delete("1.0", "end")
        self.status_box.insert("1.0", text)
        self.status_box.configure(state="disabled")

    def refresh_git_status(self):
        if not self.local_dir:
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
            upstream = git_text(
                ["rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"],
                "keiner",
            )
            last_commit = git_text(
                ["log", "-1", "--pretty=format:%h  %s"],
                "noch kein Commit",
            )

            code, tracked_out, _ = run_git(
                ["ls-tree", "-r", "--name-only", "HEAD"],
                cwd=path,
                allow_error=True,
            )
            if code == 0:
                tracked_files = len(
                    [line for line in (tracked_out or "").splitlines() if line.strip()]
                )
                tracked_text = str(tracked_files)
            else:
                tracked_text = "0"

            ahead = "–"
            behind = "–"
            if upstream != "keiner":
                code, counts, _ = run_git(
                    ["rev-list", "--left-right", "--count", "HEAD...@{u}"],
                    cwd=path,
                    allow_error=True,
                )
                if code == 0 and counts:
                    parts = counts.replace("\t", " ").split()
                    if len(parts) >= 2:
                        ahead, behind = parts[0], parts[1]

            _, short_status, _ = run_git(
                ["status", "--short"],
                cwd=path,
                allow_error=True,
            )
            short_status = (short_status or "").strip()

            lines = [
                f"Branch:              {branch}",
                f"Remote origin:       {remote}",
                f"Upstream:            {upstream}",
                f"Letzter Commit:       {last_commit}",
                f"Dateien im Commit:    {tracked_text}",
                f"Zu pushen:            {ahead}",
                f"Von Remote zu holen:  {behind}",
                "",
                "Arbeitsverzeichnis:",
            ]

            if short_status:
                lines.append(short_status)
            else:
                lines.append("sauber – keine uncommitteten Änderungen")

            return "\n".join(lines)

        def done(text):
            self.show_status(text)
            self.set_footer("Git-Status aktualisiert.")

        self.threaded(work, done)

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
            run_git(["add", "-A"], cwd=path)
            run_git(["commit", "-m", msg], cwd=path)
            return True
        def done(_):
            self.commit_entry.delete(0, "end")
            self.refresh_git_status()
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

            return local_branch, default_branch

        def inspected(result):
            local_branch, default_branch = result

            if (
                local_branch
                and default_branch
                and local_branch != default_branch
            ):
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

            self.git_action(["push"], "Push abgeschlossen.")

        self.threaded(
            inspect,
            inspected,
            busy_title="Branch wird geprüft …",
            busy_detail="MultiGitHubGUI prüft den lokalen Branch und den GitHub-Standardbranch.",
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
