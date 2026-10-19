"""The API key, in Windows' credential manager (v0.18, D-137).

One entry per address, named "ddict:<address>" (for instance "ddict:https://api.anthropic.com"),
so that the uninstaller finds them with `cmdkey /list`. The key is typed by the person
(the AI page, or `ddict ia cle` without echo), read only when a request leaves, and written
nowhere else: not in a project, not in the settings, not in the exchange log, not in a
message. This module never prints it, and says only whether one is recorded.

The Windows backend of keyring is used by name: a keyring configuration on this computer
cannot send the key to another store (a plain-text file, for instance). The tests replace it
with a store in memory (`use_backend`), and never touch the real one.

keyring is an optional dependency (`ddict[ia]`): it is imported here only.
"""

from __future__ import annotations

from collections.abc import Callable

from keyring.backend import KeyringBackend
from keyring.errors import PasswordDeleteError

SERVICE_PREFIX = "ddict:"
USER_NAME = "api-key"

_override: KeyringBackend | None = None


class KeyStoreError(RuntimeError):
    """Windows' credential manager did not answer."""


def use_backend(backend: KeyringBackend | None) -> None:
    """Another store (the tests); None goes back to Windows' credential manager."""
    global _override
    _override = backend


def _backend() -> KeyringBackend:
    if _override is not None:
        return _override
    from keyring.backends.Windows import WinVaultKeyring

    return WinVaultKeyring()


def target(endpoint: str) -> str:
    """The name of the entry in the credential manager."""
    return SERVICE_PREFIX + endpoint.rstrip("/")


def _clean(key: str) -> str:
    key = key.strip()
    if not key:
        raise ValueError("empty")
    if any(c.isspace() or not c.isprintable() for c in key):
        raise ValueError("spaces")  # two keys pasted, or a line break: not a key
    return key


def save(endpoint: str, key: str) -> None:
    """Record the key of an address, replacing the one recorded. Raises ValueError for an
    empty key or one with spaces, KeyStoreError when the manager does not answer."""
    key = _clean(key)
    store = _backend()
    try:
        # Replace, not add: on Windows, keyring would keep the former key under another
        # name ("api-key@ddict:…") if an entry of the same name were still there.
        _delete(store, endpoint)
        store.set_password(target(endpoint), USER_NAME, key)
    except Exception as error:  # the manager's own errors, whatever their class
        raise KeyStoreError("Windows' credential manager did not record the key") from error


def _delete(store: KeyringBackend, endpoint: str) -> bool:
    deleted = False
    for _copy in range(3):  # every copy, the compound name of an older keyring included
        try:
            store.delete_password(target(endpoint), USER_NAME)
        except PasswordDeleteError:
            break
        deleted = True
    return deleted


def forget(endpoint: str) -> bool:
    """Erase the key of an address; False when none was recorded."""
    try:
        return _delete(_backend(), endpoint)
    except Exception as error:
        raise KeyStoreError("Windows' credential manager did not erase the key") from error


def _read(endpoint: str) -> str | None:
    try:
        return _backend().get_password(target(endpoint), USER_NAME) or None
    except Exception as error:
        raise KeyStoreError("Windows' credential manager did not answer") from error


def is_recorded(endpoint: str) -> bool:
    """Whether a key is recorded for this address; never the key itself."""
    return _read(endpoint) is not None


def reader(endpoint: str) -> Callable[[], str | None]:
    """What a client asks the key from, at each request (`client.KeySource`)."""
    return lambda: _read(endpoint)
