"""Uniform result type for fallible forensic operations.

Modules previously returned ad-hoc dicts — some ``{'success': bool, 'error': ...}``,
others ``{'error': ...}`` with no success flag, others raw data — and callers had
to special-case each shape (``result.get('success')`` here, ``'error' not in
result`` there). :class:`OperationResult` gives operations one return type.

It is intentionally **backward-compatible** with the old dicts: it supports
``result.get(key)``, ``result[key]``, ``key in result``, ``bool(result)`` and
``to_dict()``. That lets modules adopt it incrementally without breaking any
existing CLI or web consumer.

Convention: *operations* that can fail (imaging, carving, captures) return an
``OperationResult``. Pure *data accessors* (list devices, calculate hashes) may
still return their natural value or raise.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class OperationResult:
    success: bool
    data: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def ok(cls, data=None, **metadata):
        """A successful result. ``data`` is the payload; ``metadata`` captures
        cross-cutting detail (command line, timestamps, hashes…)."""
        return cls(success=True, data=data, metadata=dict(metadata))

    @classmethod
    def fail(cls, error, data=None, **metadata):
        """A failed result carrying an error message (and optional partial data)."""
        return cls(success=False, data=data, error=str(error), metadata=dict(metadata))

    def to_dict(self) -> Dict[str, Any]:
        """Flatten to a JSON-friendly dict matching the old return shapes.

        A dict payload is spread to the top level (so ``result['output']`` works
        as before); a non-dict payload is exposed under ``'data'``. Metadata is
        merged last.
        """
        out: Dict[str, Any] = {'success': self.success}
        if self.error is not None:
            out['error'] = self.error
        if isinstance(self.data, dict):
            out.update(self.data)
        elif self.data is not None:
            out['data'] = self.data
        out.update(self.metadata)
        return out

    # ── mapping-style compatibility shims ─────────────────────────────────────
    def get(self, key, default=None):
        return self.to_dict().get(key, default)

    def __getitem__(self, key):
        return self.to_dict()[key]

    def __contains__(self, key):
        return key in self.to_dict()

    def __bool__(self):
        return self.success


def to_jsonable(value):
    """Return a JSON-serialisable view of ``value``.

    Converts an :class:`OperationResult` (or anything exposing ``to_dict``) to a
    plain dict; leaves everything else untouched. Used at serialisation
    boundaries (task records, socket payloads, ``jsonify``).
    """
    to_dict = getattr(value, 'to_dict', None)
    if callable(to_dict):
        return value.to_dict()
    return value
