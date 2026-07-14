# core/i18n.py
from core.settings import get_settings, save_settings

DEFAULT_LANGUAGE = "en"

TRANSLATIONS = {
    "en": {
        "tab.discovery": "Discovery",
        "tab.mounted": "Mounted",
        "tab.settings": "Settings",
        "tab.diagnostics": "Diagnostics",

        "wizard.scan_button": "Scan network",
        "wizard.host_placeholder": "IP address or hostname (e.g. nas.local)",
        "wizard.add_button": "Add server",
        "wizard.tree_header": "SMB Hosts / Shares",
        "wizard.loading": "Loading...",
        "wizard.remove_tooltip": "Remove this server from the list",
        "wizard.scan_warning_title": "Scan network",
        "wizard.login_required": "Login required",
        "wizard.unavailable": "Unavailable",
        "wizard.no_shares": "No shares",
        "wizard.mount_button": "Mount",
        "wizard.mounted_button": "Mounted",
        "wizard.persist_checkbox": "Persist",
        "wizard.persist_tooltip": (
            "Adds a permanent entry to /etc/fstab - the share will mount "
            "itself automatically after a reboot."
        ),
        "wizard.invalid_data_title": "Invalid data",
        "wizard.invalid_data_message": "Bad mount args:\n{h}\n{s}",
        "wizard.mounted_title": "Mounted",
        "wizard.mounted_message": "Mounted:\n\n{path}",
        "wizard.mount_failed_title": "Mount failed",
        "wizard.unknown_error": "Unknown error",
        "wizard.host_unreachable": "Server {host} is not reachable right now (port 445 did not respond).",
        "wizard.open_tooltip": "Open in file manager (without mounting)",
        "wizard.open_failed_title": "Open failed",
        "wizard.open_failed_message": "xdg-open is not available - install it to open shares directly in your file manager.",
        "wizard.open_encryption_warning": "This server likely can't be browsed without mounting (often caused by mandatory SMB3 encryption, which the file manager's smb:// browsing doesn't support as well as a real mount does). Try 'Mount' instead.",

        "mounted.header_source": "Source",
        "mounted.header_target": "Mountpoint",
        "mounted.header_usage": "Usage",
        "mounted.usage_unknown": "N/A",
        "mounted.refresh_button": "Refresh",
        "mounted.remove_fstab_checkbox": "Also remove persistent entry (fstab)",
        "mounted.remove_fstab_tooltip": (
            "Check this if the share was mounted with the 'Persist' option "
            "and you want it to stop mounting automatically after a reboot."
        ),
        "mounted.unmount_button": "Unmount selected",
        "mounted.error_title": "Error",
        "mounted.unmount_failed_title": "Unmount failed",
        "mounted.unknown_error": "Unknown error",
        "mounted.select_share_not_server": "Select a specific share to unmount, not the whole server group.",

        "settings.mount_location_label": "Default mount location",
        "settings.save_button": "Save",
        "settings.note": (
            "Note: this applies to newly mounted shares.\n"
            "Already mounted shares stay where they are."
        ),
        "settings.error_title": "Error",
        "settings.path_empty": "Path cannot be empty",
        "settings.saved_title": "Saved",
        "settings.saved_message": "Default mount location: {path}",
        "settings.language_label": "Language",
        "settings.language_note": "Takes effect immediately.",
        "settings.version_label": "Version {version}",
        "settings.check_updates_button": "Check for updates",
        "settings.checking_updates": "Checking...",
        "settings.up_to_date": "You have the latest version.",
        "settings.update_available": "A newer version is available: {version} (see GitHub).",
        "settings.update_check_failed": "Could not check (offline, or the repo is private).",
        "settings.smb_version_label": "SMB protocol version",
        "settings.smb_version_note": (
            "Auto (recommended) lets mount.cifs negotiate the best version "
            "with the server. Force an older version only if a specific "
            "NAS fails to connect otherwise."
        ),
        "settings.smb_version_auto": "Auto (recommended)",

        "diagnostics.title": "Required system tools",
        "diagnostics.header_tool": "Tool",
        "diagnostics.header_package": "Package",
        "diagnostics.header_status": "Status",
        "diagnostics.header_purpose": "Purpose",
        "diagnostics.status_ok": "OK",
        "diagnostics.status_missing": "MISSING",
        "diagnostics.refresh_button": "Refresh",
        "diagnostics.install_button": "Install missing",
        "diagnostics.output_placeholder": "Installation output will appear here...",
        "diagnostics.already_installed": "Everything is already installed.",
        "diagnostics.confirm_title": "Package installation",
        "diagnostics.confirm_message": "Install the following packages via apt?\n\n{packages}",
        "diagnostics.done": "Installation finished.",
        "diagnostics.failed": "Installation failed - see the log below.",
        "diagnostics.purpose.nmap": "Network scanning (Discovery tab)",
        "diagnostics.purpose.smbclient": "Listing SMB shares on a host",
        "diagnostics.purpose.cifs_utils": "Mounting SMB shares",
        "diagnostics.purpose.pkexec": "Privilege escalation for mount / fstab writes",
        "diagnostics.purpose.secret_tool": "Remembering SMB credentials between sessions (KWallet / Secret Service)",
        "diagnostics.purpose.nmblookup": "Showing computer names next to LAN addresses (NetBIOS lookup)",
        "diagnostics.optional_title": "Recommended",
        "diagnostics.install_optional_button": "Install optional",

        "auth.title": "SMB Login - {host}",
        "auth.username_placeholder": "Username",
        "auth.password_placeholder": "Password",
        "auth.login_button": "Login",
        "auth.forget_button": "Forget saved credentials",
    },
    "pl": {
        "tab.discovery": "Wykrywanie",
        "tab.mounted": "Zamontowane",
        "tab.settings": "Ustawienia",
        "tab.diagnostics": "Diagnostyka",

        "wizard.scan_button": "Skanuj sieć",
        "wizard.host_placeholder": "Adres IP lub nazwa hosta (np. nas.local)",
        "wizard.add_button": "Dodaj serwer",
        "wizard.tree_header": "Hosty SMB / Udziały",
        "wizard.loading": "Ładowanie...",
        "wizard.remove_tooltip": "Usuń ten serwer z listy",
        "wizard.scan_warning_title": "Skanowanie sieci",
        "wizard.login_required": "Wymagane logowanie",
        "wizard.unavailable": "Niedostępne",
        "wizard.no_shares": "Brak udziałów",
        "wizard.mount_button": "Zamontuj",
        "wizard.mounted_button": "Zamontowano",
        "wizard.persist_checkbox": "Na stałe",
        "wizard.persist_tooltip": (
            "Dodaje trwały wpis w /etc/fstab - udział zamontuje się sam "
            "po restarcie systemu."
        ),
        "wizard.invalid_data_title": "Nieprawidłowe dane",
        "wizard.invalid_data_message": "Błędne argumenty montowania:\n{h}\n{s}",
        "wizard.mounted_title": "Zamontowano",
        "wizard.mounted_message": "Zamontowano:\n\n{path}",
        "wizard.mount_failed_title": "Błąd montowania",
        "wizard.unknown_error": "Nieznany błąd",
        "wizard.host_unreachable": "Serwer {host} jest teraz nieosiągalny (port 445 nie odpowiada).",
        "wizard.open_tooltip": "Otwórz w menedżerze plików (bez montowania)",
        "wizard.open_failed_title": "Nie udało się otworzyć",
        "wizard.open_failed_message": "xdg-open jest niedostępne - zainstaluj je, żeby otwierać udziały bezpośrednio w menedżerze plików.",
        "wizard.open_encryption_warning": "Ten serwer najprawdopodobniej nie da się przeglądać bez montowania (często powoduje to wymuszone szyfrowanie SMB3, którego przeglądanie smb:// w menedżerze plików nie obsługuje tak dobrze jak prawdziwe montowanie). Spróbuj zamiast tego 'Zamontuj'.",

        "mounted.header_source": "Źródło",
        "mounted.header_target": "Punkt montowania",
        "mounted.header_usage": "Zajętość",
        "mounted.usage_unknown": "Brak danych",
        "mounted.refresh_button": "Odśwież",
        "mounted.remove_fstab_checkbox": "Usuń też trwały wpis (fstab)",
        "mounted.remove_fstab_tooltip": (
            "Zaznacz, jeśli ten udział był zamontowany opcją 'Na stałe' "
            "i chcesz, żeby przestał się montować po restarcie."
        ),
        "mounted.unmount_button": "Odmontuj zaznaczone",
        "mounted.error_title": "Błąd",
        "mounted.unmount_failed_title": "Błąd odmontowania",
        "mounted.unknown_error": "Nieznany błąd",
        "mounted.select_share_not_server": "Zaznacz konkretny udział do odmontowania, nie całą grupę serwera.",

        "settings.mount_location_label": "Domyślna lokalizacja montowania",
        "settings.save_button": "Zapisz",
        "settings.note": (
            "Uwaga: dotyczy nowo montowanych udziałów.\n"
            "Już zamontowane zostają tam, gdzie są."
        ),
        "settings.error_title": "Błąd",
        "settings.path_empty": "Ścieżka nie może być pusta",
        "settings.saved_title": "Zapisano",
        "settings.saved_message": "Domyślna lokalizacja: {path}",
        "settings.language_label": "Język",
        "settings.language_note": "Działa natychmiast.",
        "settings.version_label": "Wersja {version}",
        "settings.check_updates_button": "Sprawdź aktualizacje",
        "settings.checking_updates": "Sprawdzanie...",
        "settings.up_to_date": "Masz najnowszą wersję.",
        "settings.update_available": "Dostępna jest nowsza wersja: {version} (zobacz na GitHubie).",
        "settings.update_check_failed": "Nie udało się sprawdzić (brak sieci albo repo jest prywatne).",
        "settings.smb_version_label": "Wersja protokołu SMB",
        "settings.smb_version_note": (
            "Auto (zalecane) pozwala mount.cifs samemu wynegocjować najlepszą "
            "wersję z serwerem. Wymuś starszą wersję tylko jeśli konkretny "
            "NAS inaczej nie chce się połączyć."
        ),
        "settings.smb_version_auto": "Auto (zalecane)",

        "diagnostics.title": "Wymagane narzędzia systemowe",
        "diagnostics.header_tool": "Narzędzie",
        "diagnostics.header_package": "Pakiet",
        "diagnostics.header_status": "Status",
        "diagnostics.header_purpose": "Do czego służy",
        "diagnostics.status_ok": "OK",
        "diagnostics.status_missing": "BRAK",
        "diagnostics.refresh_button": "Sprawdź ponownie",
        "diagnostics.install_button": "Zainstaluj brakujące",
        "diagnostics.output_placeholder": "Wynik instalacji pojawi się tutaj...",
        "diagnostics.already_installed": "Wszystko już zainstalowane.",
        "diagnostics.confirm_title": "Instalacja pakietów",
        "diagnostics.confirm_message": "Zainstalować przez apt następujące pakiety?\n\n{packages}",
        "diagnostics.done": "Instalacja zakończona.",
        "diagnostics.failed": "Instalacja nie powiodła się - zobacz log poniżej.",
        "diagnostics.purpose.nmap": "Skanowanie sieci (zakładka Discovery)",
        "diagnostics.purpose.smbclient": "Listowanie udziałów SMB na hoście",
        "diagnostics.purpose.cifs_utils": "Montowanie udziałów SMB",
        "diagnostics.purpose.pkexec": "Podniesienie uprawnień do montowania / zapisu fstab",
        "diagnostics.purpose.secret_tool": "Zapamiętywanie danych logowania między sesjami (KWallet / Secret Service)",
        "diagnostics.purpose.nmblookup": "Pokazywanie nazw komputerów obok adresów LAN (zapytanie NetBIOS)",
        "diagnostics.optional_title": "Zalecane",
        "diagnostics.install_optional_button": "Zainstaluj opcjonalne",

        "auth.title": "Logowanie SMB - {host}",
        "auth.username_placeholder": "Nazwa użytkownika",
        "auth.password_placeholder": "Hasło",
        "auth.login_button": "Zaloguj",
        "auth.forget_button": "Zapomnij zapisane dane",
    },
}


def available_languages():
    return [
        ("en", "English"),
        ("pl", "Polski"),
    ]


def get_language():
    return get_settings().get("language", DEFAULT_LANGUAGE)


def set_language(lang_code):
    settings = get_settings()
    settings["language"] = lang_code
    save_settings(settings)


def tr(key, **kwargs):
    lang = get_language()
    table = TRANSLATIONS.get(lang, TRANSLATIONS[DEFAULT_LANGUAGE])

    text = table.get(key)
    if text is None:
        text = TRANSLATIONS[DEFAULT_LANGUAGE].get(key, key)

    if kwargs:
        try:
            return text.format(**kwargs)
        except Exception:
            return text

    return text
