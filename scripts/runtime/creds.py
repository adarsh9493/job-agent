#!/usr/bin/env python
"""Read-only-by-default access to the credential vault (`data/vault/credentials.txt`).

    python scripts/runtime/creds.py list
    python scripts/runtime/creds.py get --domain generalmotors
    printf '%s' "$PW" | python scripts/runtime/creds.py set --key workday_foo_password --password-stdin
    python scripts/runtime/creds.py new --key workday_foo --username adarsh.9493@gmail.com

Secrets are always masked. `new` generates a 24-character password, stores it, and never prints it.
There is no command-line option that reveals a password.
"""
from __future__ import annotations

import argparse
import os
import re
import secrets
import string
import sys
import tempfile
from pathlib import Path

from _common import DATA, emit, norm

VAULT = DATA / "vault" / "credentials.txt"


def _parse(text: str):
    sections = {}
    portals = []
    current = None
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("[") and line.endswith("]"):
            current = line[1:-1].strip()
            sections.setdefault(current, {})
            continue
        if current is None:
            current = "DEFAULT"
            sections.setdefault(current, {})
        if " | " in line:
            parts = [part.strip() for part in line.split("|")]
            if len(parts) >= 3:
                portals.append({
                    "name": parts[0],
                    "url": parts[1],
                    "username": parts[2],
                    "date": parts[3] if len(parts) > 3 else "",
                })
            continue
        if "=" in line:
            key, value = line.split("=", 1)
            sections.setdefault(current, {})[key.strip()] = value.strip()
    shared = sections.get("SHARED", sections.get("DEFAULT", {}))
    return shared, portals


def _load():
    if not VAULT.is_file():
        return {}, []
    return _parse(VAULT.read_text(encoding="utf-8-sig"))


def _tenants(shared):
    tenants = []
    for key in shared:
        match = re.fullmatch(r"workday_(.+)_email", key)
        if match:
            tenants.append(match.group(1))
    return tenants


def _get(domain: str):
    shared, portals = _load()
    domain_norm = norm(domain)
    password_shared = shared.get("password")
    username_shared = shared.get("username")

    for tenant in _tenants(shared):
        if tenant and (tenant in domain_norm or domain_norm in tenant):
            email = shared.get(f"workday_{tenant}_email") or username_shared
            password = shared.get(f"workday_{tenant}_password") or password_shared
            return _result(domain, email, password, f"workday:{tenant}")

    for portal in portals:
        if domain_norm and (domain_norm in norm(portal["url"])
                            or domain_norm in norm(portal["name"])):
            return _result(domain, portal["username"], password_shared, "portal")

    return _result(domain, username_shared, password_shared, "shared")


def _result(domain, username, password, source):
    return {
        "domain": domain,
        "username": username,
        "password": "********" if password else None,
        "source": source,
        "has_password": bool(password),
    }


def _list():
    shared, portals = _load()
    tenants = []
    for tenant in _tenants(shared):
        tenants.append({
            "tenant": tenant,
            "email": shared.get(f"workday_{tenant}_email"),
            "has_password": bool(shared.get(f"workday_{tenant}_password")),
        })
    return {
        "shared": {
            "username": shared.get("username"),
            "has_password": bool(shared.get("password")),
        },
        "workday": tenants,
        "portals": [
            {"name": p["name"], "url": p["url"], "username": p["username"],
             "date": p["date"]}
            for p in portals
        ],
    }


def _set_key(key: str, value: str) -> None:
    if not key or "\n" in key or "\r" in key or "\n" in value or "\r" in value:
        raise ValueError("credential keys/values must be single-line text")
    text = VAULT.read_text(encoding="utf-8-sig") if VAULT.is_file() else ""
    lines = text.splitlines()
    pattern = re.compile(r"^\s*" + re.escape(key) + r"\s*=")
    for index, line in enumerate(lines):
        if pattern.match(line):
            lines[index] = f"{key} = {value}"
            _write_vault("\n".join(lines) + "\n")
            return
    # append (create a SHARED section if the file is empty)
    if not any(line.strip() == "[SHARED]" for line in lines):
        lines.append("[SHARED]")
    lines.append(f"{key} = {value}")
    _write_vault("\n".join(lines) + "\n")


def _write_vault(text: str) -> None:
    VAULT.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n",
                                         dir=VAULT.parent, prefix=f".{VAULT.name}.",
                                         suffix=".tmp", delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, VAULT)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def _generate_password(length: int = 24) -> str:
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*()-_=+"
    while True:
        value = "".join(secrets.choice(alphabet) for _ in range(length))
        if (any(c.islower() for c in value) and any(c.isupper() for c in value)
                and any(c.isdigit() for c in value)):
            return value


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("list", help="list stored credential keys (secrets masked)")

    getter = sub.add_parser("get", help="get a credential for a domain")
    getter.add_argument("--domain", required=True)

    setter = sub.add_parser("set", help="set one key from stdin")
    setter.add_argument("--key", required=True)
    setter.add_argument("--password-stdin", action="store_true", required=True)

    creator = sub.add_parser("new", help="create a new portal account entry")
    creator.add_argument("--key", required=True)
    creator.add_argument("--username", required=True)

    args = parser.parse_args(argv)

    if args.command == "list":
        emit(_list())
        return 0

    if args.command == "get":
        emit(_get(args.domain))
        return 0

    if args.command == "set":
        if not args.password_stdin:
            print("ERROR: --password-stdin is required", file=sys.stderr)
            return 2
        value = sys.stdin.read()
        # accept either a trailing newline or a bare value
        if value.endswith("\n"):
            value = value[:-1]
        if value.endswith("\r"):
            value = value[:-1]
        if not value or "\n" in value or "\r" in value:
            print("ERROR: no password received on stdin", file=sys.stderr)
            return 2
        try:
            _set_key(args.key, value)
        except (OSError, ValueError) as error:
            print(f"ERROR: unable to store credential: {error}", file=sys.stderr)
            return 1
        emit({"ok": True, "key": args.key, "stored": True})
        return 0

    if args.command == "new":
        key = args.key
        if key.endswith("_password"):
            pwd_key = key
            email_key = key[:-len("_password")] + "_email"
        elif key.endswith("_email"):
            pwd_key = key[:-len("_email")] + "_password"
            email_key = key
        else:
            pwd_key = key + "_password"
            email_key = key + "_email"
        generated = _generate_password()
        try:
            _set_key(email_key, args.username)
            _set_key(pwd_key, generated)
        except (OSError, ValueError) as error:
            print(f"ERROR: unable to store credential: {error}", file=sys.stderr)
            return 1
        emit({"ok": True, "key": key, "username": args.username,
              "generated": True, "password_length": len(generated)})
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
