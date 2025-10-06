"""Tkinter-based GUI for controlling SwitchBot devices via the Cloud API.

The application reads configuration from ``config.json`` (copy from
``config.example.json``) and creates On/Off buttons for each registered device.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import random
import string
import threading
import time
from pathlib import Path
from tkinter import BOTH, LEFT, RIGHT, TOP, Button, Frame, Label, Tk
from typing import Any, Dict, Iterable

import requests


CONFIG_PATH = Path("config.json")
API_BASE_URL = "https://api.switch-bot.com"


class ConfigurationError(RuntimeError):
    """Raised when the configuration file is missing or malformed."""


def load_config(path: Path) -> Dict[str, Any]:
    """Load configuration JSON and validate required fields."""

    if not path.exists():
        raise ConfigurationError(
            "Configuration file config.json not found. Copy config.example.json to "
            "config.json and fill in your SwitchBot credentials."
        )

    try:
        with path.open("r", encoding="utf-8") as fp:
            data = json.load(fp)
    except json.JSONDecodeError as exc:  # pragma: no cover - safety net
        raise ConfigurationError(f"Invalid JSON in {path}: {exc}") from exc

    for key in ("token", "secret", "devices"):
        if key not in data:
            raise ConfigurationError(f"Missing '{key}' in configuration file")

    if not isinstance(data["devices"], Iterable) or isinstance(data["devices"], dict):
        raise ConfigurationError("'devices' must be a list of device definitions")

    return data


def generate_nonce(length: int = 16) -> str:
    """Generate a random alphanumeric nonce string."""

    alphabet = string.ascii_letters + string.digits
    return "".join(random.choice(alphabet) for _ in range(length))


class SwitchBotClient:
    """Minimal SwitchBot Cloud API client with request signing."""

    def __init__(self, token: str, secret: str) -> None:
        self.token = token
        self.secret = secret

    def _headers(self) -> Dict[str, str]:
        timestamp = str(int(time.time() * 1000))
        nonce = generate_nonce()
        string_to_sign = f"{self.token}{timestamp}{nonce}"
        signature = base64.b64encode(
            hmac.new(
                self.secret.encode("utf-8"),
                msg=string_to_sign.encode("utf-8"),
                digestmod=hashlib.sha256,
            ).digest()
        ).decode("utf-8")

        return {
            "Authorization": self.token,
            "Content-Type": "application/json; charset=utf8",
            "t": timestamp,
            "sign": signature,
            "nonce": nonce,
        }

    def send_command(
        self,
        device_id: str,
        command_type: str,
        command: str,
        parameter: str,
    ) -> Dict[str, Any]:
        """Send a command to a SwitchBot device and return the JSON response."""

        url = f"{API_BASE_URL}/v1.1/devices/{device_id}/commands"
        payload = {
            "commandType": command_type,
            "command": command,
            "parameter": parameter,
        }
        response = requests.post(url, headers=self._headers(), json=payload, timeout=10)
        response.raise_for_status()
        return response.json()


class DeviceControl(Frame):
    """Widget containing On/Off buttons for a SwitchBot device."""

    def __init__(
        self,
        master: Tk,
        client: SwitchBotClient,
        device_config: Dict[str, Any],
        status_callback,
    ) -> None:
        super().__init__(master, borderwidth=1, relief="ridge", padx=10, pady=10)
        self.client = client
        self.device_config = device_config
        self.status_callback = status_callback

        name = device_config.get("name", "Unnamed Device")
        Label(self, text=name, font=("Segoe UI", 12, "bold")).pack(side=TOP, pady=(0, 8))

        button_frame = Frame(self)
        button_frame.pack(fill=BOTH, expand=True)

        Button(
            button_frame,
            text="ON",
            width=8,
            command=lambda: self._trigger("on"),
        ).pack(side=LEFT, padx=5)
        Button(
            button_frame,
            text="OFF",
            width=8,
            command=lambda: self._trigger("off"),
        ).pack(side=RIGHT, padx=5)

    def _trigger(self, action: str) -> None:
        commands = self.device_config.get("commands", {})
        command = commands.get(action)
        if not command:
            self.status_callback(
                f"No '{action}' command configured for {self.device_config.get('name')}"
            )
            return

        thread = threading.Thread(target=self._send_command, args=(action, command), daemon=True)
        thread.start()

    def _send_command(self, action: str, command: Dict[str, Any]) -> None:
        name = self.device_config.get("name", "Device")
        device_id = self.device_config.get("deviceId")
        if not device_id:
            self.status_callback(f"Missing deviceId for {name}")
            return

        try:
            result = self.client.send_command(
                device_id=device_id,
                command_type=command.get("commandType", "command"),
                command=command.get("command", "turnOn" if action == "on" else "turnOff"),
                parameter=command.get("parameter", "default"),
            )
        except requests.HTTPError as exc:  # pragma: no cover - network error path
            self.status_callback(f"HTTP error for {name}: {exc}")
            return
        except requests.RequestException as exc:  # pragma: no cover
            self.status_callback(f"Network error for {name}: {exc}")
            return

        status_code = result.get("statusCode")
        if status_code == 100:
            self.status_callback(f"{name}: {action.upper()} command sent successfully")
        else:
            self.status_callback(
                f"{name}: API returned statusCode {status_code} - {result.get('message')}"
            )


def build_ui(root: Tk, config: Dict[str, Any]) -> Label:
    """Create the UI and return the status label widget."""

    client = SwitchBotClient(token=config["token"], secret=config["secret"])
    status_label = Label(root, text="Ready", anchor="w", relief="sunken")
    status_label.pack(side="bottom", fill="x", padx=5, pady=5)

    container = Frame(root)
    container.pack(fill=BOTH, expand=True, padx=10, pady=10)

    def update_status(message: str) -> None:
        status_label.config(text=message)

    for device in config.get("devices", []):
        control = DeviceControl(root, client, device, status_callback=update_status)
        control.pack(fill=BOTH, expand=True, padx=5, pady=5)

    return status_label


def main() -> None:
    try:
        config = load_config(CONFIG_PATH)
    except ConfigurationError as exc:
        root = Tk()
        root.title("SwitchBot Controller - Configuration Error")
        Label(root, text=str(exc), wraplength=400, padx=20, pady=20).pack()
        root.mainloop()
        return

    root = Tk()
    root.title("SwitchBot Controller")
    root.resizable(False, False)

    status_label = build_ui(root, config)
    status_label.config(text="SwitchBot Controller Ready")

    root.mainloop()


if __name__ == "__main__":
    main()
