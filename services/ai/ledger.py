# Token ledger for the demo user.
# Balances persist in data/processed/ai-tokens.json relative to the repo root.
# A new user starts with 10 tokens. Pack sizes are 10, 50 and 200.

import json
import os
from pathlib import Path

DEMO_USER = 'demo-user'
DEFAULT_BALANCE = 10
PACK_SIZES = (10, 50, 200)


def default_ledger_path():
    override = os.environ.get('AI_TOKEN_LEDGER_PATH') or os.environ.get('AI_TOKEN_FILE')
    if override:
        return Path(override)
    root = Path(__file__).resolve().parents[2]
    return root / 'data' / 'processed' / 'ai-tokens.json'


class TokenLedger:
    def __init__(self, path=None):
        self.path = Path(path) if path else default_ledger_path()

    def _load(self):
        try:
            raw = self.path.read_text(encoding='utf-8')
            data = json.loads(raw)
            if not isinstance(data, dict):
                return {DEMO_USER: DEFAULT_BALANCE}
            cleaned = {}
            for key, value in data.items():
                try:
                    cleaned[str(key)] = int(value)
                except (TypeError, ValueError):
                    continue
            if DEMO_USER not in cleaned:
                cleaned[DEMO_USER] = DEFAULT_BALANCE
            return cleaned
        except (OSError, ValueError):
            return {DEMO_USER: DEFAULT_BALANCE}

    def _save(self, data):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        text = json.dumps(data, indent=2, sort_keys=True)
        self.path.write_text(text, encoding='utf-8')

    def balance(self, user=DEMO_USER):
        return int(self._load().get(user, DEFAULT_BALANCE))

    def set_balance(self, user, value):
        data = self._load()
        data[user] = int(value)
        self._save(data)
        return int(value)

    def deduct(self, user=DEMO_USER, amount=1):
        data = self._load()
        current = int(data.get(user, DEFAULT_BALANCE))
        if current < amount:
            return current, False
        current = current - amount
        data[user] = current
        self._save(data)
        return current, True

    def grant(self, user, pack_size):
        if pack_size not in PACK_SIZES:
            raise ValueError('pack size must be 10, 50 or 200')
        data = self._load()
        current = int(data.get(user, DEFAULT_BALANCE)) + int(pack_size)
        data[user] = current
        self._save(data)
        return current


def get_ledger(path=None):
    return TokenLedger(path=path)
