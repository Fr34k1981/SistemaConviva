from core.state import DEFAULT_STATE


def test_default_state_has_dashboard():
    assert DEFAULT_STATE["pagina_atual"] == "🏠 Dashboard"
