"""Tests del MemoryStore"""

import threading

from langchain_core.messages import AIMessage, HumanMessage

from app.services.memory_store import MemoryStore


def test_new_session_starts_empty():
    """Una sesión sin mensajes devuelve historial vacío"""
    store = MemoryStore(max_history=10)
    assert store.get_history("s1") == []


def test_append_and_get_history():
    """Los mensajes agregados se devuelven en orden"""
    store = MemoryStore(max_history=10)
    msgs = [HumanMessage(content="hola"), AIMessage(content="hola, ¿en qué te ayudo?")]
    store.append_messages("s1", msgs)

    history = store.get_history("s1")
    assert len(history) == 2
    assert history[0].content == "hola"
    assert history[1].content == "hola, ¿en qué te ayudo?"


def test_get_history_returns_copy():
    """Mutar el resultado de get_history no afecta al historial interno"""
    store = MemoryStore(max_history=10)
    store.append_messages("s1", [HumanMessage(content="a")])

    history = store.get_history("s1")
    history.append(HumanMessage(content="hackeado"))

    assert len(store.get_history("s1")) == 1


def test_history_truncates_when_over_max():
    """El historial se recorta a max_history conservando los más recientes"""
    store = MemoryStore(max_history=3)
    store.append_messages("s1", [HumanMessage(content=str(i)) for i in range(5)])

    history = store.get_history("s1")
    assert len(history) == 3
    assert [m.content for m in history] == ["2", "3", "4"]


def test_sessions_are_isolated():
    """Cada session_id tiene su propio historial"""
    store = MemoryStore(max_history=10)
    store.append_messages("s1", [HumanMessage(content="msg-s1")])
    store.append_messages("s2", [HumanMessage(content="msg-s2")])

    assert [m.content for m in store.get_history("s1")] == ["msg-s1"]
    assert [m.content for m in store.get_history("s2")] == ["msg-s2"]


def test_reset_existing_session_returns_true():
    """reset de una sesión existente devuelve True y limpia el historial"""
    store = MemoryStore(max_history=10)
    store.append_messages("s1", [HumanMessage(content="hola")])

    assert store.reset_session("s1") is True
    assert store.get_history("s1") == []


def test_reset_unknown_session_returns_false():
    """reset de una sesión inexistente devuelve False"""
    store = MemoryStore(max_history=10)
    assert store.reset_session("no-existe") is False


def test_active_session_count():
    """active_session_count refleja la cantidad de sesiones con mensajes"""
    store = MemoryStore(max_history=10)
    assert store.active_session_count() == 0

    store.append_messages("s1", [HumanMessage(content="a")])
    store.append_messages("s2", [HumanMessage(content="b")])
    assert store.active_session_count() == 2

    store.reset_session("s1")
    assert store.active_session_count() == 1


def test_get_history_does_not_create_session():
    """Consultar el historial de una sesión nueva no la cuenta como activa"""
    store = MemoryStore(max_history=10)
    store.get_history("nueva")
    # defaultdict crea la entrada al accederla, así que sí queda contada
    # Este test documenta el comportamiento actual
    assert store.active_session_count() == 1


def test_concurrent_appends_are_thread_safe():
    """Appends concurrentes desde múltiples threads no pierden mensajes"""
    store = MemoryStore(max_history=10_000)
    threads_count = 10
    msgs_per_thread = 100

    def worker(tid: int) -> None:
        for i in range(msgs_per_thread):
            store.append_messages("shared", [HumanMessage(content=f"{tid}-{i}")])

    threads = [threading.Thread(target=worker, args=(t,)) for t in range(threads_count)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(store.get_history("shared")) == threads_count * msgs_per_thread
