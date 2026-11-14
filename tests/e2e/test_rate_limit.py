import pytest

LEDGER_REASON = (
    'token ledger not on main yet, owner wave-1 worker a-5, see gaps.md'
)


@pytest.mark.skip(reason=LEDGER_REASON)
def test_rate_limit_exceeded_returns_429():
    raise AssertionError('rate limiting not implemented')


@pytest.mark.skip(reason=LEDGER_REASON)
def test_token_ledger_balance_decreases_on_ai_call():
    raise AssertionError('token ledger not implemented')


@pytest.mark.skip(reason=LEDGER_REASON)
def test_token_ledger_rejects_call_at_zero_balance():
    raise AssertionError('token ledger not implemented')
