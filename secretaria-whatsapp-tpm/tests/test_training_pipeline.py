"""Fase 7 · pipeline de conversas: parser, anonimização, pares, curadoria e fine-tuning."""

import json
import zipfile
from pathlib import Path

import pytest

from app.domains.llm.facts import find_facts, mask_facts
from app.domains.training import curation, finetune_export
from app.domains.training.anonymizer import anonymize, leaks
from app.domains.training.pairs import build_pairs
from app.domains.training.whatsapp_export import parse_lines, read_export

FIX = Path(__file__).parent / "fixtures" / "whatsapp"
CLINIC = ["Secretária Clínica"]


def _pairs():
    return build_pairs(read_export(FIX / "exemplo_android.txt"), CLINIC, source="android")


def test_parser_android_multiline_media_and_system():
    msgs = read_export(FIX / "exemplo_android.txt")
    assert msgs[0].author == "Joana Fictícia"  # linha de sistema ignorada
    assert any(m.kind == "media" for m in msgs)
    cpf_msg = next(m for m in msgs if "cpf" in m.text)
    assert "99911-2233" in cpf_msg.text  # continuação de linha anexada


def test_parser_ios_and_zip(tmp_path):
    msgs = read_export(FIX / "exemplo_ios.txt")
    assert [m.author for m in msgs][:2] == ["Carlos Inventado", "Secretária Clínica"]
    assert "18h" in msgs[2].text
    z = tmp_path / "conversa.zip"
    with zipfile.ZipFile(z, "w") as zf:
        zf.write(FIX / "exemplo_ios.txt", "Conversa do WhatsApp com Carlos.txt")
    assert len(read_export(z)) == len(msgs)


@pytest.mark.parametrize(
    "text,forbidden",
    [
        ("meu cpf é 123.456.789-09", "123.456.789-09"),
        ("email joana@example.com", "joana@example.com"),
        ("meu cel (46) 99911-2233", "99911-2233"),
        ("+55 16 98765-4321", "98765-4321"),
        ("moro na Rua das Flores, 123", "Flores"),
        ("Meu nome é Joana Silva", "Joana"),
        ("veja https://exemplo.com/x", "exemplo.com"),
        ("cep 85501-000", "85501-000"),
    ],
)
def test_anonymizer_removes_personal_data(text, forbidden):
    out = anonymize(text)
    assert forbidden not in out
    assert not leaks(out)


def test_anonymizer_removes_known_names_but_keeps_city_and_dra():
    out = anonymize("Oi Joana, a Dra atende em Pato Branco", ["Joana Fictícia"])
    assert "Joana" not in out and "Pato Branco" in out and "Dra" in out


def test_name_equal_to_city_is_removed_but_city_kept():
    out = anonymize("Boa tarde, Carlos! Atendemos em São Carlos. Bom dia! Meu nome é Ana", ["Carlos Inventado"])
    assert out.startswith("Boa tarde, [NOME]!") and "São Carlos" in out and "Meu nome é [NOME]" in out


def test_time_mask_keeps_spacing():
    assert mask_facts("quinta às 14h ou sexta 10:30 em Pato Branco") == "{DIA} às {HORARIO} ou {DIA} {HORARIO} em {CIDADE}"


def test_pairs_are_anonymized_masked_and_clinical_blocked():
    pairs = _pairs()
    blob = json.dumps(pairs, ensure_ascii=False)
    for secret in ("Joana", "123.456.789-09", "example.com", "99911-2233"):
        assert secret not in blob
    first = pairs[0]
    assert "{HORARIO}" in first["reply"] and "14h" not in first["reply"]
    assert "{CIDADE}" in first["reply"]
    price = next(p for p in pairs if "custa" in p["patient"])
    assert "{PRECO}" in price["reply"] and "1.200" not in price["reply"]
    clinical = next(p for p in pairs if "dor" in p["patient"])
    assert clinical["status"] == "bloqueado" and "clinico" in clinical["flags"]
    assert all(p["split"] in {"treino", "avaliacao"} for p in pairs)


def test_mask_and_find_facts():
    text = "Tenho sexta às 10:30 em São Carlos, R$ 900 no pix, preenchimento labial"
    facts = find_facts(text)
    assert {"horario", "dia", "cidade", "preco", "procedimento"} <= set(facts)
    masked = mask_facts(text)
    assert "10:30" not in masked and "900" not in masked and "São Carlos" not in masked


def test_curation_rules():
    pairs = _pairs()
    clinical = next(p for p in pairs if p["status"] == "bloqueado")
    with pytest.raises(ValueError):
        curation.review(clinical, "aprovado", "Dra")
    normal = next(p for p in pairs if p["status"] == "pendente")
    with pytest.raises(ValueError):
        curation.review(normal, "aprovado", "")  # sem revisor não vale
    with pytest.raises(ValueError):
        curation.review(normal, "aprovado", "Dra", reply="Pode tomar ibuprofeno que passa")
    ok = curation.review(normal, "aprovado", "Dra", reply="Tenho {HORARIO} sim! Quer que eu reserve?")
    assert ok["status"] == "aprovado" and ok["reviewer"] == "Dra"


def test_csv_roundtrip(tmp_path):
    pairs = _pairs()
    sheet = tmp_path / "revisao.csv"
    curation.export_csv(pairs, sheet)
    text = sheet.read_text(encoding="utf-8-sig").replace(";pendente;", ";aprovado;")
    sheet.write_text(text, encoding="utf-8-sig")
    result = curation.import_csv(pairs, sheet, default_reviewer="Secretária")
    assert result["aplicados"] >= 1
    assert all(p["status"] != "aprovado" or p["reviewer"] == "Secretária" for p in pairs)
    assert not any(p["status"] == "aprovado" and "clinico" in p["flags"] for p in pairs)


def test_finetune_export_format(tmp_path):
    pairs = _pairs()
    for i, p in enumerate(pairs):
        if p["status"] == "pendente":
            pairs[i] = curation.review(p, "aprovado", "Dra")
            pairs[i]["split"] = "treino" if i % 2 == 0 else "avaliacao"
    result = finetune_export.export(pairs, tmp_path)
    assert result["train"] >= 1 and result["warnings"]  # poucos exemplos → aviso
    line = json.loads((tmp_path / "train.jsonl").read_text(encoding="utf-8").splitlines()[0])
    assert [c["role"] for c in line["contents"]] == ["user", "model"]
    assert "systemInstruction" in line
    assert "dipirona" not in (tmp_path / "train.jsonl").read_text(encoding="utf-8")


def test_parse_lines_ignores_system_lines():
    msgs = parse_lines(["01/01/2026 10:00 - Fulano entrou usando o link", "01/01/2026 10:01 - Ana: oi"])
    assert len(msgs) == 1 and msgs[0].author == "Ana"
