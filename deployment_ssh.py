"""Shared, environment-driven SSH configuration for deployment utilities."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import paramiko


@dataclass(frozen=True)
class SSHConfig:
    host: str
    username: str
    key_file: str | None
    password: str | None
    project_dir: str


def load_ssh_config() -> SSHConfig:
    host = os.environ.get("WELD_SSH_HOST")
    if not host:
        raise RuntimeError("WELD_SSH_HOST is required")

    key_value = os.environ.get("WELD_SSH_KEY")
    key_file = str(Path(key_value).expanduser()) if key_value else None
    password = os.environ.get("WELD_SSH_PASSWORD")
    if not key_file and not password:
        raise RuntimeError("Set WELD_SSH_KEY or WELD_SSH_PASSWORD")

    return SSHConfig(
        host=host,
        username=os.environ.get("WELD_SSH_USER", "deploy"),
        key_file=key_file,
        password=password,
        project_dir=os.environ.get("WELD_PROJECT_DIR", "/home/ubuntu/weld-system"),
    )


def connect_ssh(config: SSHConfig, timeout: int = 30) -> paramiko.SSHClient:
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.RejectPolicy())
    client.connect(
        hostname=config.host,
        username=config.username,
        password=config.password,
        key_filename=config.key_file,
        timeout=timeout,
    )
    return client
