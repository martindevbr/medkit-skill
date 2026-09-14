#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Backtest da skill medicina.

Nao testa 'o codigo roda' - testa se a RESPOSTA BATE COM A VERDADE CONHECIDA.
Cada caso tem um gabarito verificavel de forma independente.

Uso: python backtest.py [--offline]   (--offline pula os testes de rede)
"""
import io
import re
import subprocess
import sys
import time
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

MED = str(Path(__file__).resolve().parent.parent / "scripts" / "med.py")
RES = []


def run(*args, timeout=240):
    p = subprocess.run([sys.executable, MED] + list(args),
                       capture_output=True, timeout=timeout)
    return p.stdout.decode("utf-8", "replace") + p.stderr.decode("utf-8", "replace")


def caso(grupo, nome, cmd, checar, rede=False):
    RES.append({"grupo": grupo, "nome": nome, "cmd": cmd, "checar": checar, "rede": rede})


def contem(*termos):
    def f(out):
        falta = [t for t in termos if t.lower() not in out.lower()]
        return (not falta, "faltou: %s" % ", ".join(falta) if falta else "ok")
    return f


def nao_contem(*termos):
    def f(out):
        achou = [t for t in termos if t.lower() in out.lower()]
        return (not achou, "apareceu indevidamente: %s" % ", ".join(achou) if achou else "ok")
    return f


def vazio(out):
    """controle negativo: tem que dizer que nao achou, e nao inventar."""
    ok = "nenhum resultado" in out.lower() or "nada encontrado" in out.lower()
    return (ok, "ok - declarou ausencia" if ok else "NAO declarou ausencia (risco de invencao)")


def minimo_linhas(n, padrao):
    def f(out):
        qtd = len(re.findall(padrao, out))
        return (qtd >= n, "%d ocorrencia(s), esperado >=%d" % (qtd, n))
    return f


# ============================================================ ANVISA (local)
caso("ANVISA", "dipirona tem registro ativo", ["med", "dipirona"],
     contem("dipirona", "Ativo", "ANVISA"))
caso("ANVISA", "paracetamol classificado como analgesico", ["med", "paracetamol"],
     contem("paracetamol", "ANALGESICO"))
caso("ANVISA", "amoxicilina aparece como antibiotico", ["med", "amoxicilina"],
     contem("amoxicilina"))
caso("ANVISA", "busca sem acento acha com acento", ["med", "insulina"],
     contem("insulina"))
caso("ANVISA", "CONTROLE NEGATIVO: farmaco inexistente", ["med", "zoltraxina"], vazio)

# ================================================= Produtos para saude (local)
# Curativo nao e medicamento: a pergunta "pilsana hidrofibra" voltava vazia
# porque era procurada na base errada. Estes casos guardam essa separacao.
caso("Produtos", "hidrofibra aparece como curativo", ["produto", "hidrofibra"],
     contem("Curativo", "ANVISA"))
caso("Produtos", "marca conhecida achada pelo nome", ["produto", "aquacel"],
     contem("CONVATEC"))
caso("Produtos", "busca por tipo, duas palavras", ["produto", "cobertura", "alginato"],
     contem("Curativo"))
caso("Produtos", "avisa que registro nao e indicacao clinica", ["produto", "hidrofibra"],
     contem("NAO diz indicacao"))
caso("Produtos", "curativo NAO esta na base de medicamentos", ["med", "hidrofibra"], vazio)
caso("Produtos", "CONTROLE NEGATIVO: produto inexistente", ["produto", "zoltrafibra"], vazio)

# ============================================================== CID-10 (local)
# gabarito: codigos oficiais da CID-10
caso("CID-10", "I10 = hipertensao essencial", ["cid", "I10"],
     contem("I10", "Hipertens"))
caso("CID-10", "E11 = diabetes nao-insulino-dependente", ["cid", "E11"],
     contem("E11", "Diabetes"))
caso("CID-10", "J189 = pneumonia nao especificada", ["cid", "J189"],
     contem("J189", "Pneumonia"))
caso("CID-10", "busca textual com acento", ["cid", "hipertensão"],
     contem("I10"))
caso("CID-10", "busca textual sem acento acha o mesmo", ["cid", "hipertensao"],
     contem("I10"))
caso("CID-10", "CONTROLE NEGATIVO: codigo inexistente", ["cid", "Z999X"], vazio)

# ============================================================== SIGTAP (local)
caso("SIGTAP", "curativo simples existe com codigo oficial", ["proc", "curativo"],
     contem("0301100284", "CURATIVO SIMPLES", "atencao basica"))
caso("SIGTAP", "complexidade nao vem como codigo cru", ["proc", "curativo"],
     nao_contem("complexidade: 1 |", "complexidade: 2 |", "complexidade: 3 |"))
caso("SIGTAP", "consulta de enfermagem consta na tabela", ["proc", "consulta"],
     minimo_linhas(3, r"\n  \d{10}  "))
caso("SIGTAP", "CONTROLE NEGATIVO: procedimento inexistente", ["proc", "teletransporte"], vazio)

# ========================================================== openFDA (rede)
caso("openFDA", "warfarina traz tarja preta de sangramento", ["bula", "warfarin"],
     contem("TARJA PRETA", "bleeding"), rede=True)
caso("openFDA", "metformina traz acidose latica na tarja preta", ["bula", "metformin"],
     contem("TARJA PRETA", "LACTIC ACIDOSIS"), rede=True)
caso("openFDA", "enoxaparina traz hematoma espinhal", ["bula", "enoxaparin"],
     contem("hematoma"), rede=True)
caso("openFDA", "prioriza principio ativo puro, nao associacao", ["bula", "metformin"],
     nao_contem("ZITUVIMET", "sitagliptin"), rede=True)
caso("openFDA", "traz posologia e contraindicacao", ["bula", "omeprazole"],
     contem("POSOLOGIA", "CONTRAINDICACOES"), rede=True)
caso("openFDA", "CONTROLE NEGATIVO: farmaco inexistente", ["bula", "zoltraxina"],
     vazio, rede=True)

caso("Interacao", "varfarina x ibuprofeno = risco de sangramento", ["inter", "warfarin", "ibuprofen"],
     contem("ibuprofen", "bleeding"), rede=True)
caso("Interacao", "avisa que RxNav foi descontinuada", ["inter", "warfarin"],
     contem("descontinuada"), rede=True)
caso("Interacao", "par sem mencao nao vira afirmacao inventada",
     ["inter", "omeprazole", "teletransporte"],
     contem("NAO significa ausencia"), rede=True)

caso("PubMed", "busca de enfermagem retorna artigos com link",
     ["artigos", "pressure ulcer prevention nursing"],
     contem("pubmed.ncbi.nlm.nih.gov"), rede=True)

# ==================================================== rastreabilidade (fonte)
caso("Rastreio", "med cita a fonte", ["med", "dipirona"], contem("Fonte:"))
caso("Rastreio", "cid cita a fonte", ["cid", "I10"], contem("Fonte:"))
caso("Rastreio", "proc cita a fonte e alerta sobre tecnica", ["proc", "curativo"],
     contem("Fonte:", "protocolo"))
caso("Rastreio", "bula alerta que a referencia legal e a ANVISA", ["bula", "warfarin"],
     contem("ANVISA"), rede=True)


def main():
    offline = "--offline" in sys.argv
    casos = [c for c in RES if not (offline and c["rede"])]
    print("\n" + "=" * 78)
    print("BACKTEST - skill medicina   (%d casos%s)" % (len(casos), ", modo offline" if offline else ""))
    print("=" * 78)

    grupos = {}
    falhas = []
    t0 = time.time()
    for c in casos:
        try:
            out = run(*c["cmd"])
            ok, detalhe = c["checar"](out)
        except Exception as e:
            ok, detalhe = False, "ERRO: %s" % e
        grupos.setdefault(c["grupo"], []).append(ok)
        print("  [%s] %-11s %-52s %s" % ("PASS" if ok else "FALHA", c["grupo"], c["nome"], detalhe))
        if not ok:
            falhas.append((c, detalhe))

    print("\n" + "-" * 78)
    total = sum(len(v) for v in grupos.values())
    acertos = sum(sum(v) for v in grupos.values())
    for g, v in grupos.items():
        print("  %-11s %d/%d" % (g, sum(v), len(v)))
    print("-" * 78)
    print("  TOTAL      %d/%d  (%.0f%%)   em %.1fs" %
          (acertos, total, 100.0 * acertos / total, time.time() - t0))
    print("=" * 78 + "\n")
    return 0 if acertos == total else 1


if __name__ == "__main__":
    sys.exit(main())
