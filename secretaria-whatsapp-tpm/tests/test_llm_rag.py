"""Fase 7 · LLM + RAG: o LLM só reescreve; o verificador barra qualquer fato inventado."""

import json
from pathlib import Path

import pytest

from app.domains.llm import claim_checker
from app.domains.llm.writer import apply_llm, build_prompt
from app.domains.secretary.turn import process_turn
from app.infrastructure.llm.providers import FakeProvider, LLMError
from app.infrastructure.memory.patient_cache import InMemoryPatientCache
from app.infrastructure.rag.vector_store import VectorStore

SCENARIOS = json.loads((Path(__file__).parent / "scenarios" / "conversations.json").read_text(encoding="utf-8"))


def _cfg(mode="on"):
    from app.infrastructure.llm.providers import load_llm_config

    cfg = load_llm_config()
    cfg.update(mode=mode, provider="fake", shadow_log_path=None)
    return cfg


def _turn(msg):
    return process_turn(msg, "5546999990000", store=InMemoryPatientCache())


def test_default_mode_is_off_and_changes_nothing():
    from app.infrastructure.llm.providers import load_llm_config

    assert load_llm_config()["mode"] in {"off", "shadow", "on"}
    turn = _turn("oi")
    before = turn["reply_text"]
    out = apply_llm(turn, "oi", provider=FakeProvider(script="XYZ"), store=VectorStore(), cfg=_cfg("off"))
    assert out["reply_text"] == before and "llm" not in out


@pytest.mark.parametrize(
    "injected",
    [
        "Claro! Tenho amanhã às 14h, pode ser?",
        "A dra está em São Carlos hoje, quer marcar?",
        "O botox sai por R$ 900, quer marcar?",
        "Fica tranquila, é normal, toma dipirona. Algo mais?",
        "Prontinho, sua consulta está agendada! Algo mais?",
        "Me chama no 46 99911-2233?",
        "Tenho {HORARIO} livre, pode ser?",
    ],
)
def test_adversarial_llm_is_blocked_and_template_kept(injected):
    for msg in ["tem horário amanhã?", "oi, tudo bem?", "a dra está em pato branco?"]:
        turn = _turn(msg)
        base = turn["reply_text"]
        out = apply_llm(turn, msg, provider=FakeProvider(script=injected), store=VectorStore(), cfg=_cfg("on"))
        assert out["reply_text"] == base, (msg, injected, out["llm"])
        assert out["llm"]["check"]["ok"] is False


def test_safe_rewrite_is_used_in_on_mode():
    turn = _turn("oi")
    rewrite = "Oii! Aqui é a assistente virtual da dra. 😊 Posso te ajudar a confirmar, reagendar, cancelar ou ver horário?"
    out = apply_llm(turn, "oi", provider=FakeProvider(script=rewrite), store=VectorStore(), cfg=_cfg("on"))
    assert out["llm"]["check"]["ok"], out["llm"]["check"]
    assert out["reply_text"] == rewrite and out["llm"]["used"]


def test_shadow_mode_never_changes_patient_reply():
    turn = _turn("oi")
    base = turn["reply_text"]
    out = apply_llm(turn, "oi", provider=FakeProvider(script="Oii! Em que posso ajudar?"), store=VectorStore(), cfg=_cfg("shadow"))
    assert out["reply_text"] == base and out["llm"]["candidate"]


def test_escalation_and_opt_out_are_never_rewritten():
    for msg in ["estou com muita dor", "quero falar com uma atendente", "parar"]:
        turn = _turn(msg)
        base = turn["reply_text"]
        out = apply_llm(turn, msg, provider=FakeProvider(script="qualquer coisa"), store=VectorStore(), cfg=_cfg("on"))
        assert out["reply_text"] == base and out["llm"].get("skipped")


def test_llm_error_falls_back_to_template():
    class Broken(FakeProvider):
        def generate(self, *a, **k):
            raise LLMError("fora do ar")

    turn = _turn("oi")
    base = turn["reply_text"]
    out = apply_llm(turn, "oi", provider=Broken(), store=VectorStore(), cfg=_cfg("on"))
    assert out["reply_text"] == base and "fora do ar" in out["llm"]["error"]


def test_rag_retrieves_similar_examples_and_prompt_is_anonymized():
    fake = FakeProvider()
    store = VectorStore()
    store.build(
        [
            {"id": "a", "intent": "AVAILABILITY", "patient": "tem horário essa semana?", "reply": "Tenho {DIA} às {HORARIO}, quer?"},
            {"id": "b", "intent": "THANKS", "patient": "obrigada!!", "reply": "Imagina! Estamos por aqui 💜"},
        ],
        fake,
    )
    hits = store.search(fake.embed(["obrigada"])[0], top_k=1)
    assert hits[0]["id"] == "b"
    msg = "oi, sou a Maria, meu cel 46 99911-2233"
    out = apply_llm(_turn(msg), msg, provider=fake, store=store, cfg=_cfg("shadow"))
    assert "99911-2233" not in fake.calls[-1]
    assert out["llm"]["check"]["ok"]  # fake devolve a própria base → passa


def test_all_scenarios_hold_with_adversarial_llm_on():
    """Os cenários anti-alucinação continuam valendo com um LLM que tenta inventar tudo."""
    evil = FakeProvider(script="Tenho amanhã às 9h em São Carlos por R$ 500, já está agendado! Pode tomar dipirona.")
    from app.infrastructure.mcp.calendar import build_calendar_gateway

    checked = 0
    for sc in SCENARIOS["scenarios"]:
        cache = InMemoryPatientCache()
        number = sc.get("number", "5546999990000")
        calendar = build_calendar_gateway(sc.get("calendar_mode", "missing"), sc.get("fixture_city") or None)
        for step in sc["turns"]:
            msg = step.get("say", "")
            turn = process_turn(msg, number, calendar=calendar, store=cache, message_type=step.get("message_type", "text"))
            checked += 1
            base = turn["reply_text"]
            out = apply_llm(turn, msg, provider=evil, store=VectorStore(), cfg=_cfg("on"))
            assert out["reply_text"] == base, (sc.get("id"), msg)
    assert checked >= 15


def test_checker_keeps_facts_present_in_base():
    base = "Na agenda da unidade encontrei: 2026-11-04T14:00. Quer esse?"
    assert claim_checker.check("Achei aqui na agenda: 2026-11-04T14:00 😊 Quer esse?", base)["ok"]


def test_prompt_contains_base_and_examples():
    prompt = build_prompt("oi", "Olá! Posso ajudar?", [{"patient": "oi", "reply": "Oii!"}], "GREETING")
    assert "RESPOSTA-BASE:\nOlá! Posso ajudar?" in prompt and "Oii!" in prompt
