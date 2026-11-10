"""CLI do pipeline de treino (conversas do Zap → curadoria → RAG → avaliação → fine-tuning).

    python -m app.interfaces.cli.treino ingerir --clinica "Secretária Ana" --clinica "Dra"
    python -m app.interfaces.cli.treino status
    python -m app.interfaces.cli.treino exportar-planilha          # revisar no Excel
    python -m app.interfaces.cli.treino importar-planilha --revisor "Dra Daiana"
    python -m app.interfaces.cli.treino revisar --revisor "Dra Daiana"   # revisão no terminal
    python -m app.interfaces.cli.treino indexar                    # embeddings Gemini → data/rag/index.json
    python -m app.interfaces.cli.treino avaliar                    # modo sombra no conjunto de avaliação
    python -m app.interfaces.cli.treino testar "tem horário amanhã?"
    python -m app.interfaces.cli.treino finetune                   # data/finetune/train.jsonl + validation.jsonl
    python -m app.interfaces.cli.treino checar-gemini

Use --fake para rodar sem chave Gemini (embeddings e LLM simulados, offline).
"""

import argparse
import json
import sys
from pathlib import Path

from app.domains.llm import writer
from app.domains.secretary.turn import process_turn
from app.domains.training import curation, finetune_export
from app.domains.training.pairs import build_pairs, dedupe
from app.domains.training.whatsapp_export import list_exports, read_export
from app.infrastructure.config.config_loader import _config_dir
from app.infrastructure.llm.providers import FakeProvider, LLMError, build_provider, load_llm_config
from app.infrastructure.memory.patient_cache import InMemoryPatientCache
from app.infrastructure.rag.vector_store import VectorStore

ROOT = _config_dir().parent
DATA = ROOT / "data"
PAIRS = DATA / "curadoria" / "pares.jsonl"
SHEET = DATA / "curadoria" / "revisao.csv"


def _provider(args):
    return FakeProvider() if args.fake else build_provider()


def _cfg(args, mode=None):
    cfg = load_llm_config()
    if mode:
        cfg["mode"] = mode
    if getattr(args, "fake", False):
        cfg["provider"] = "fake"
    return cfg


def cmd_ingerir(args):
    if not args.clinica:
        sys.exit("Informe --clinica com o(s) nome(s) que aparecem como autor das mensagens da clínica no export.")
    files = list_exports(args.pasta)
    if not files:
        sys.exit(f"Nenhum .txt/.zip em {args.pasta}. Exporte a conversa no WhatsApp (sem mídia) e coloque lá.")
    existing = curation.load(PAIRS)
    new = []
    for f in files:
        msgs = read_export(f)
        new += build_pairs(msgs, args.clinica, args.nome_extra or [], source=f.name)
    added = dedupe(new, {p["id"] for p in existing})
    curation.save(PAIRS, existing + added)
    print(f"{len(files)} arquivo(s) · {len(new)} pares encontrados · {len(added)} novos · total {len(existing) + len(added)}")
    print(f"Pares anonimizados em {PAIRS.relative_to(ROOT)}. Próximo: exportar-planilha ou revisar.")


def cmd_status(args):
    pairs = curation.load(PAIRS)
    print(json.dumps({"total": len(pairs), "por_split": curation.stats(pairs)}, ensure_ascii=False, indent=2))
    idx = VectorStore.load(load_llm_config()["rag"]["index_path"])
    print(f"índice RAG: {idx.meta.get('count', 0)} exemplos · {idx.meta.get('built_at', 'não construído')}")


def cmd_exportar(args):
    pairs = curation.load(PAIRS)
    rows = [p for p in pairs if args.status == "todos" or p["status"] == args.status]
    n = curation.export_csv(rows, args.arquivo)
    print(f"{n} linhas em {args.arquivo}. Edite as colunas status (aprovado/rejeitado), reply e reviewer; depois importar-planilha.")


def cmd_importar(args):
    pairs = curation.load(PAIRS)
    result = curation.import_csv(pairs, args.arquivo, args.revisor or "")
    curation.save(PAIRS, pairs)
    print(json.dumps(result, ensure_ascii=False))


def cmd_revisar(args):
    pairs = curation.load(PAIRS)
    pending = [i for i, p in enumerate(pairs) if p["status"] == "pendente"]
    print(f"{len(pending)} pendentes. [a]provar [r]ejeitar [e]ditar resposta [p]ular [s]air")
    for i in pending:
        p = pairs[i]
        print("\n" + "-" * 60)
        print(f"[{p['split']}] intenção={p['intent']} fatos={p['facts']} flags={p['flags']}")
        print(f"PACIENTE:   {p['patient']}")
        print(f"SECRETÁRIA: {p['reply']}")
        choice = input("> ").strip().lower()
        try:
            if choice == "a":
                pairs[i] = curation.review(p, "aprovado", args.revisor)
            elif choice == "r":
                pairs[i] = curation.review(p, "rejeitado", args.revisor)
            elif choice == "e":
                new_reply = input("nova resposta: ").strip()
                pairs[i] = curation.review(p, "aprovado", args.revisor, reply=new_reply)
            elif choice == "s":
                break
        except ValueError as exc:
            print(f"  não aplicado: {exc}")
        curation.save(PAIRS, pairs)
    print("salvo.")


def cmd_indexar(args):
    pairs = curation.approved(curation.load(PAIRS), "treino")
    if not pairs:
        sys.exit("Nenhum par aprovado no split 'treino'. Revise antes de indexar.")
    cfg = _cfg(args)
    store = VectorStore()
    try:
        n = store.build(pairs, _provider(args))
    except LLMError as exc:
        sys.exit(f"Falha nos embeddings: {exc}")
    path = store.save(cfg["rag"]["index_path"])
    writer.reset_cache()
    print(f"{n} exemplos indexados em {path.relative_to(ROOT)} ({store.meta['provider']})")


def _run(message, cfg, provider, store):
    turn = process_turn(message, "", store=InMemoryPatientCache())
    return writer.apply_llm(turn, message, provider=provider, store=store, cfg=cfg)


def cmd_avaliar(args):
    pairs = [p for p in curation.load(PAIRS) if p["split"] == "avaliacao" and p["status"] != "bloqueado"]
    if not pairs:
        sys.exit("Sem pares de avaliação. Rode ingerir primeiro.")
    cfg = _cfg(args, mode="shadow")
    cfg["shadow_log_path"] = None
    provider = _provider(args)
    store = VectorStore.load(cfg["rag"]["index_path"])
    out_dir = DATA / "avaliacao"
    out_dir.mkdir(parents=True, exist_ok=True)
    rows, ok, skipped, errors = [], 0, 0, 0
    for p in pairs[: args.limite]:
        turn = _run(p["patient"], cfg, provider, store)
        info = turn.get("llm", {})
        if info.get("skipped"):
            skipped += 1
        elif info.get("error"):
            errors += 1
        elif info.get("check", {}).get("ok"):
            ok += 1
        rows.append({"id": p["id"], "paciente": p["patient"], "clinica_real": p["reply"], "template": info.get("base_reply"),
                     "llm": info.get("candidate"), "ok": info.get("check", {}).get("ok"), "problemas": info.get("check", {}).get("problems"),
                     "pulado": info.get("skipped"), "erro": info.get("error")})
    rated = len(rows) - skipped - errors
    (out_dir / "sombra.jsonl").write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n", encoding="utf-8")
    lines = [
        "# Avaliação em modo sombra", "",
        f"- Mensagens: {len(rows)} · reescritas avaliadas: {rated} · aprovadas pelo verificador: {ok} ({(100 * ok / rated) if rated else 0:.0f}%)",
        f"- Puladas (texto fixo: escalonamento, opt-out...): {skipped} · erros de LLM: {errors}", "",
        "| Paciente | Clínica (real) | Template | LLM | OK | Problemas |", "|---|---|---|---|---|---|",
    ]
    for r in rows:
        cell = lambda v: (str(v or "")).replace("|", "/").replace("\n", " ")[:140]
        lines.append(f"| {cell(r['paciente'])} | {cell(r['clinica_real'])} | {cell(r['template'])} | {cell(r['llm'] or r['pulado'] or r['erro'])} | {'✅' if r['ok'] else ('—' if r['ok'] is None else '❌')} | {cell('; '.join(r['problemas'] or []))} |")
    (out_dir / "relatorio.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines[:4]))
    print(f"Relatório: {(out_dir / 'relatorio.md').relative_to(ROOT)}")


def cmd_testar(args):
    cfg = _cfg(args, mode="on")
    cfg["shadow_log_path"] = None
    turn = _run(args.mensagem, cfg, _provider(args), VectorStore.load(cfg["rag"]["index_path"]))
    info = turn.get("llm", {})
    print(f"intenção: {turn['intent']}")
    print(f"template: {info.get('base_reply')}")
    print(f"LLM:      {info.get('candidate') or info.get('skipped') or info.get('error')}")
    print(f"verificador: {info.get('check')}")
    print(f"paciente recebe: {turn['reply_text']}")


def cmd_finetune(args):
    result = finetune_export.export(curation.load(PAIRS), DATA / "finetune")
    print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_checar(args):
    cfg = load_llm_config()
    try:
        provider = build_provider(cfg)
        models = provider.list_models()
    except LLMError as exc:
        sys.exit(f"Gemini: {exc}")
    for key in ("model", "embedding_model"):
        name = cfg[key]
        found = name in models
        print(f"{key}: {name} → {'ok' if found else 'NÃO encontrado (ajuste config/llm.json ou GEMINI_MODEL)'}")
    print(f"{len(models)} modelos disponíveis para a chave.")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="treino", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fake", action="store_true", help="LLM/embeddings simulados (offline, sem chave)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("ingerir"); s.add_argument("--pasta", default=str(DATA / "conversas-brutas"))
    s.add_argument("--clinica", action="append", help="nome do autor da clínica no export (repita para vários)")
    s.add_argument("--nome-extra", action="append", help="nome a anonimizar além dos autores")
    s.set_defaults(fn=cmd_ingerir)
    sub.add_parser("status").set_defaults(fn=cmd_status)
    s = sub.add_parser("exportar-planilha"); s.add_argument("--arquivo", default=str(SHEET))
    s.add_argument("--status", default="pendente", choices=["pendente", "aprovado", "rejeitado", "bloqueado", "todos"]); s.set_defaults(fn=cmd_exportar)
    s = sub.add_parser("importar-planilha"); s.add_argument("--arquivo", default=str(SHEET)); s.add_argument("--revisor"); s.set_defaults(fn=cmd_importar)
    s = sub.add_parser("revisar"); s.add_argument("--revisor", required=True); s.set_defaults(fn=cmd_revisar)
    sub.add_parser("indexar").set_defaults(fn=cmd_indexar)
    s = sub.add_parser("avaliar"); s.add_argument("--limite", type=int, default=200); s.set_defaults(fn=cmd_avaliar)
    s = sub.add_parser("testar"); s.add_argument("mensagem"); s.set_defaults(fn=cmd_testar)
    sub.add_parser("finetune").set_defaults(fn=cmd_finetune)
    sub.add_parser("checar-gemini").set_defaults(fn=cmd_checar)

    args = ap.parse_args(argv)
    args.fn(args)


if __name__ == "__main__":
    main()
