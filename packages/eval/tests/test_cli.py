"""CLI safety: dry-run and a zero cost cap do not call a provider."""

from __future__ import annotations

from serqet.cli import main


def test_dry_run_and_zero_cap_do_not_call_network(monkeypatch) -> None:
    def boom(*_args, **_kwargs):
        raise AssertionError("network")

    monkeypatch.setattr("urllib.request.urlopen", boom)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    assert (
        main(
            [
                "run-models",
                "--dry-run",
                "--model",
                "openrouter/test",
                "--trials",
                "1",
                "--cost-cap-usd",
                "0",
            ]
        )
        == 0
    )
    assert (
        main(
            [
                "run-models",
                "--model",
                "openrouter/test",
                "--trials",
                "1",
                "--cost-cap-usd",
                "0",
            ]
        )
        == 2
    )
