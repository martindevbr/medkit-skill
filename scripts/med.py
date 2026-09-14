#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Consulta fontes OFICIAIS de saude (Brasil + internacionais).
Somente biblioteca padrao. Uso: python med.py <comando> [args]

Comandos:
  sync [nome...]        baixa/atualiza os datasets locais
  status                mostra o que ja esta em cache
  med   <termo>         medicamentos registrados na ANVISA
  bula  <termo>         secoes clinicas da bula (openFDA/DailyMed, ingles)
  inter <a> [b]         interacoes medicamentosas (openFDA)
  cid   <termo|codigo>  CID-10 (DATASUS)
  proc  <termo>         procedimentos do SUS (SIGTAP)
  ram   <termo>         reacoes adversas notificadas no Brasil (VigiMed)
  preco <termo>         preco maximo ao consumidor (CMED/ANVISA)
  produto <termo>       curativos, coberturas e dispositivos (ANVISA, produtos para saude)
  artigos <termo>       literatura (PubMed E-utilities)
"""
import csv
import io
import json
import os
import re
import sys
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

# console do Windows costuma ser cp1252 e engasga com acento vindo dos CSVs oficiais
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

DATA = Path(os.environ.get("MEDICINA_DATA", r"D:\enfermagem-workspace\cache"))
UA = {"User-Agent": "Mozilla/5.0 (compatible; skill-medicina/1.0)"}
ANVISA = "https://dados.anvisa.gov.br/dados/"
SIGTAP_FTP = "ftp://ftp2.datasus.gov.br/pub/sistemas/tup/downloads/"

# nome -> (url, arquivo local, descricao, pesado?)
SOURCES = {
    "medicamentos": (ANVISA + "DADOS_ABERTOS_MEDICAMENTOS.csv", "anvisa_medicamentos.csv",
                     "Medicamentos registrados na ANVISA", False),
    "restricao": (ANVISA + "TA_RESTRICAO_MEDICAMENTO.csv", "anvisa_restricao.csv",
                  "Restricoes/tarjas de medicamentos", False),
    "precos": (ANVISA + "TA_PRECO_MEDICAMENTO.csv", "anvisa_precos.csv",
               "Precos maximos (CMED)", False),
    "cid10": ("http://www2.datasus.gov.br/cid10/V2008/downloads/CID10CSV.zip", "cid10.zip",
              "CID-10 completa (DATASUS)", False),
    "sigtap": (SIGTAP_FTP, "sigtap.zip",
               "Procedimentos do SUS (tabela unificada)", False),
    "produtos": (ANVISA + "TA_PRODUTO_SAUDE_SITE.csv", "anvisa_produtos_saude.csv",
                 "Produtos para saude: curativos, coberturas, dispositivos", False),
    "vigimed_r": (ANVISA + "VigiMed_Reacoes.csv", "vigimed_reacoes.csv",
                  "Reacoes adversas notificadas (239 MB)", True),
    "vigimed_m": (ANVISA + "VigiMed_Medicamentos.csv", "vigimed_medicamentos.csv",
                  "Medicamentos das notificacoes VigiMed (142 MB)", True),
}


# ---------------------------------------------------------------- utilidades
def norm(s):
    """minusculas, sem acento - para busca tolerante."""
    s = unicodedata.normalize("NFKD", str(s))
    return "".join(c for c in s if not unicodedata.combining(c)).lower()


def get(url, timeout=60, tentativas=4):
    """Servidores publicos (DATASUS em especial) oscilam - tenta de novo antes de desistir."""
    import time
    erro = None
    for i in range(tentativas):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            # 404 e 400 sao resposta definitiva ("nao existe"), nao oscilacao:
            # repetir so atrasa. Foi isso que deixava a bula de um remedio
            # inexistente nos EUA (dipirona) levar quase um minuto.
            if e.code in (400, 404):
                raise
            erro = e
            if i < tentativas - 1:
                espera = 3 * (i + 1)
                print("    tentativa %d falhou (HTTP %d); repetindo em %ds..." % (i + 1, e.code, espera))
                time.sleep(espera)
        except Exception as e:
            erro = e
            if i < tentativas - 1:
                espera = 3 * (i + 1)
                print("    tentativa %d falhou (%s); repetindo em %ds..."
                      % (i + 1, type(e).__name__, espera))
                time.sleep(espera)
    raise erro


def get_json(url, timeout=60):
    return json.loads(get(url, timeout).decode("utf-8", "replace"))


def local(name):
    return DATA / SOURCES[name][1]


def need(name):
    p = local(name)
    if not p.exists():
        sys.exit("[!] dataset '%s' nao baixado. Rode:  python med.py sync %s" % (name, name))
    return p


def latest_sigtap():
    """descobre a competencia mais recente no FTP do DATASUS."""
    listing = get(SIGTAP_FTP, timeout=180).decode("latin1", "replace")
    zips = re.findall(r"TabelaUnificada_\d{6}_v\d+\.zip", listing)
    if not zips:
        sys.exit("[!] nao encontrei tabela SIGTAP no FTP")
    return SIGTAP_FTP + sorted(zips)[-1]


def read_csv_rows(path, encoding="latin1", delim=";"):
    with open(path, "r", encoding=encoding, errors="replace", newline="") as f:
        for row in csv.DictReader(f, delimiter=delim):
            yield row


def show(rows, fields, limit, header):
    rows = list(rows)
    if not rows:
        print("nenhum resultado.")
        return
    print("\n%s  (%d resultado(s), mostrando ate %d)\n" % (header, len(rows), limit))
    for r in rows[:limit]:
        for label, key in fields:
            v = (r.get(key) or "").strip().strip('"')
            if v:
                print("  %-22s %s" % (label, v))
        print()


# -------------------------------------------------------------------- sync
def cmd_sync(args):
    DATA.mkdir(parents=True, exist_ok=True)
    names = args or [k for k, v in SOURCES.items() if not v[3]]
    for n in names:
        if n not in SOURCES:
            print("[?] fonte desconhecida: %s" % n)
            continue
        url, fname, desc, heavy = SOURCES[n]
        if n == "sigtap":
            url = latest_sigtap()
            print("    competencia: %s" % url.rsplit("/", 1)[-1])
        dest = DATA / fname
        print("[>] %s: %s" % (n, desc))
        try:
            data = get(url, timeout=900)
            dest.write_bytes(data)
            print("    ok -> %s  (%.1f MB)" % (dest, len(data) / 1048576))
        except Exception as e:
            print("    FALHOU: %s" % e)


def cmd_status(args):
    import datetime
    print("\ncache: %s\n" % DATA)
    for n, (url, fname, desc, heavy) in SOURCES.items():
        p = DATA / fname
        if p.exists():
            mb = p.stat().st_size / 1048576
            dt = datetime.datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y-%m-%d")
            print("  [ok]  %-14s %7.1f MB   baixado em %s" % (n, mb, dt))
        else:
            extra = "  (opcional, pesado)" if heavy else ""
            print("  [--]  %-14s ausente%s  - %s" % (n, extra, desc))
    print()


# ------------------------------------------------------------- consultas BR
def cmd_med(args):
    termo = norm(" ".join(args))
    p = need("medicamentos")
    hits = [r for r in read_csv_rows(p)
            if termo in norm(r.get("NOME_PRODUTO", "")) or termo in norm(r.get("PRINCIPIO_ATIVO", ""))]
    ativos = [r for r in hits if norm(r.get("SITUACAO_REGISTRO", "")) == "ativo"]
    show(ativos or hits, [
        ("Produto", "NOME_PRODUTO"),
        ("Principio ativo", "PRINCIPIO_ATIVO"),
        ("Classe terapeutica", "CLASSE_TERAPEUTICA"),
        ("Categoria", "CATEGORIA_REGULATORIA"),
        ("Registro", "NUMERO_REGISTRO_PRODUTO"),
        ("Situacao", "SITUACAO_REGISTRO"),
        ("Detentora", "EMPRESA_DETENTORA_REGISTRO"),
    ], 15, "ANVISA - registros para '%s' (ativos primeiro)" % " ".join(args))
    print("Fonte: ANVISA, Dados Abertos - DADOS_ABERTOS_MEDICAMENTOS.csv")


def cmd_preco(args):
    termo = norm(" ".join(args))
    p = need("precos")
    with open(p, "r", encoding="latin1", errors="replace", newline="") as f:
        rdr = csv.DictReader(f, delimiter=";")
        cols = rdr.fieldnames or []
        hits = [r for r in rdr if any(termo in norm(r.get(c, "")) for c in cols[:6])]
    if not hits:
        print("nenhum resultado.")
        return
    print("\nCMED/ANVISA - precos para '%s' (%d resultado(s))\n" % (" ".join(args), len(hits)))
    for r in hits[:12]:
        print("  " + " | ".join("%s=%s" % (k, v) for k, v in list(r.items())[:8] if v and v.strip()))
    print("\nFonte: ANVISA/CMED - TA_PRECO_MEDICAMENTO.csv")


def cmd_produto(args):
    """Curativo, cobertura, cateter, seringa: nada disso e medicamento.

    Material de curativo e registrado na ANVISA como PRODUTO PARA SAUDE
    (correlato), numa base separada. Procurar "hidrofibra" na base de
    medicamentos nao acha nada, e a ausencia ali nao significa que o produto
    nao exista, significa que ele nao mora la.
    """
    termos = [norm(a) for a in args if a.strip()]
    if not termos:
        sys.exit("[!] uso: python med.py produto <nome comercial ou tipo>")
    p = need("produtos")

    # Nome comercial de curativo costuma ser uma frase inteira ("Aquacel Extra
    # curativo de hidrofibra com fibra de reforco"). Casar substring da frase
    # toda nao acha nada; casar TODAS as palavras acha.
    vistos = set()
    hits = []
    for r in read_csv_rows(p):
        texto = norm("%s %s" % (r.get("NOME_COMERCIAL", ""), r.get("NOME_TECNICO", "")))
        if not all(x in texto for x in termos):
            continue
        chave = (r.get("NUMERO_REGISTRO_CADASTRO", ""), r.get("NOME_COMERCIAL", ""))
        if chave in vistos:
            continue      # a base repete a mesma linha
        vistos.add(chave)
        hits.append(r)

    # Registro vencido continua no arquivo. O que esta valendo vem primeiro.
    hits.sort(key=lambda r: 0 if vigente(r.get("VALIDADE_REGISTRO_CADASTRO", "")) else 1)
    show(hits, [
        ("Produto", "NOME_COMERCIAL"),
        ("Tipo (nome tecnico)", "NOME_TECNICO"),
        ("Classe de risco", "CLASSE_RISCO"),
        ("Registro/cadastro", "NUMERO_REGISTRO_CADASTRO"),
        ("Detentora", "DETENTOR_REGISTRO_CADASTRO"),
        ("Fabricante", "NOME_FABRICANTE"),
        ("Validade", "VALIDADE_REGISTRO_CADASTRO"),
    ], 15, "ANVISA - produtos para saude com '%s'" % " ".join(args))
    if not hits:
        print("Procure tambem pelo TIPO em vez da marca: 'produto curativo hidrofibra',")
        print("'produto cobertura alginato', 'produto espuma prata'.")
    print("Fonte: ANVISA, Dados Abertos - TA_PRODUTO_SAUDE_SITE.csv")
    print("Registro diz que o produto e regularizado no Brasil e para que tipo de uso.")
    print("NAO diz indicacao clinica, tempo de permanencia nem tecnica: isso e protocolo.")


def vigente(validade):
    """'VIGENTE' ou data futura. Data vem em dd/mm/aaaa."""
    v = (validade or "").strip().upper()
    if v.startswith("VIGENTE"):
        return True
    m = re.match(r"(\d{2})/(\d{2})/(\d{4})", v)
    if not m:
        return False
    import datetime
    d, mes, a = (int(x) for x in m.groups())
    try:
        return datetime.date(a, mes, d) >= datetime.date.today()
    except ValueError:
        return False


def cmd_cid(args):
    termo = norm(" ".join(args))
    z = zipfile.ZipFile(need("cid10"))
    alvo = [n for n in z.namelist() if "SUBCATEGORIAS" in n.upper()]
    alvo += [n for n in z.namelist() if "CATEGORIAS" in n.upper() and n not in alvo]
    out = []
    for nome in alvo:
        txt = z.read(nome).decode("latin1", "replace")
        for r in csv.DictReader(io.StringIO(txt), delimiter=";"):
            cod = (r.get("SUBCAT") or r.get("CAT") or "").strip()
            desc = (r.get("DESCRICAO") or "").strip()
            if termo in norm(cod) or termo in norm(desc):
                out.append((cod, desc))
    if not out:
        print("nenhum resultado.")
        return
    print("\nCID-10 - '%s' (%d resultado(s))\n" % (" ".join(args), len(out)))
    for cod, desc in out[:25]:
        print("  %-8s %s" % (cod, desc))
    print("\nFonte: DATASUS - CID-10 v2008")


def sigtap_table(z, base):
    """le uma tabela largura-fixa do SIGTAP usando o layout do proprio zip."""
    layout = z.read("%s_layout.txt" % base).decode("latin1", "replace")
    campos = []
    for r in csv.DictReader(io.StringIO(layout)):
        campos.append((r["Coluna"], int(r["Inicio"]) - 1, int(r["Fim"])))
    for linha in z.read("%s.txt" % base).decode("latin1", "replace").splitlines():
        yield dict((c, linha[i:j].strip()) for c, i, j in campos)


def cmd_proc(args):
    termo = norm(" ".join(args))
    z = zipfile.ZipFile(need("sigtap"))
    hits = [r for r in sigtap_table(z, "tb_procedimento") if termo in norm(r["NO_PROCEDIMENTO"])]
    if not hits:
        print("nenhum resultado.")
        return
    # codigos conferidos na propria tabela (distribuicao e exemplos por codigo)
    compl = {"0": "nao se aplica", "1": "atencao basica",
             "2": "media complexidade", "3": "alta complexidade"}
    fin = {}
    try:
        for r in sigtap_table(z, "tb_financiamento"):
            fin[r["CO_FINANCIAMENTO"]] = r["NO_FINANCIAMENTO"]
    except Exception:
        pass
    print("\nSIGTAP - procedimentos do SUS para '%s' (%d resultado(s))\n" % (" ".join(args), len(hits)))
    for r in hits[:20]:
        print("  %s  %s" % (r["CO_PROCEDIMENTO"], r["NO_PROCEDIMENTO"]))
        print("              complexidade: %s | financiamento: %s | competencia: %s"
              % (compl.get(r["TP_COMPLEXIDADE"], r["TP_COMPLEXIDADE"]),
                 fin.get(r["CO_FINANCIAMENTO"], r["CO_FINANCIAMENTO"]),
                 r["DT_COMPETENCIA"]))
    print("\nFonte: Ministerio da Saude / DATASUS - SIGTAP")
    print("Obs: o SIGTAP diz o que o SUS FATURA, nao como executar. Tecnica = protocolo/POP institucional.")


def cmd_ram(args):
    termo = norm(" ".join(args))
    p = need("vigimed_r")
    print("varrendo %s (arquivo grande, aguarde)..." % p.name)
    achados = []
    with open(p, "r", encoding="latin1", errors="replace", newline="") as f:
        for r in csv.DictReader(f, delimiter=";"):
            if any(termo in norm(v) for v in r.values() if v):
                achados.append(r)
                if len(achados) >= 15:
                    break
    if not achados:
        print("nenhum resultado.")
        return
    print("\nVigiMed - notificacoes com '%s' (primeiras %d)\n" % (" ".join(args), len(achados)))
    for r in achados:
        print("  " + " | ".join("%s=%s" % (k, v) for k, v in r.items() if v and v.strip())[:400])
    print("\nFonte: ANVISA - VigiMed (farmacovigilancia)")
    print("Obs: notificacao NAO prova causalidade.")


# ---------------------------------------------------------- consultas intl
LABEL_SECOES = [
    ("boxed_warning", "TARJA PRETA / ADVERTENCIA GRAVE"),
    ("indications_and_usage", "INDICACOES"),
    ("dosage_and_administration", "POSOLOGIA E ADMINISTRACAO"),
    ("dosage_forms_and_strengths", "APRESENTACOES"),
    ("contraindications", "CONTRAINDICACOES"),
    ("warnings_and_cautions", "ADVERTENCIAS E PRECAUCOES"),
    ("adverse_reactions", "REACOES ADVERSAS"),
    ("drug_interactions", "INTERACOES"),
    ("pregnancy", "GRAVIDEZ"),
    ("nursing_mothers", "LACTACAO"),
    ("pediatric_use", "USO PEDIATRICO"),
    ("geriatric_use", "USO GERIATRICO"),
    ("overdosage", "SUPERDOSAGEM"),
    ("mechanism_of_action", "MECANISMO DE ACAO"),
]


def fetch_label(termo):
    """Prefere o principio ativo isolado; associacoes so entram se nao houver puro."""
    q = urllib.parse.quote('"%s"' % termo)
    alvo = norm(termo)
    for campo in ("openfda.generic_name", "openfda.brand_name", "openfda.substance_name"):
        url = "https://api.fda.gov/drug/label.json?search=%s:%s&limit=20" % (campo, q)
        try:
            res = get_json(url)["results"]
        except Exception:
            continue
        if not res:
            continue

        def ingredientes(d):
            # normaliza ANTES de separar: a openFDA devolve tudo em maiusculas
            g = norm((d.get("openfda", {}).get("generic_name") or [""])[0])
            return [x.strip() for x in re.split(r"[,;/]|\band\b|\bwith\b", g) if x.strip()]

        def riqueza(d):
            """quantas secoes clinicas o rotulo realmente preenche."""
            return sum(1 for chave, _ in LABEL_SECOES if d.get(chave))

        # 1) principio ativo isolado; entre eles, o rotulo mais completo
        #    (rotulo de generico costuma vir com secoes faltando - ruim para estudo)
        puros = [d for d in res if len(ingredientes(d)) == 1 and alvo in ingredientes(d)[0]]
        if puros:
            return sorted(puros, key=lambda d: (-riqueza(d), len(ingredientes(d)[0])))[0]
        # 2) senao, menos ingredientes e, em empate, rotulo mais completo
        return sorted(res, key=lambda d: (len(ingredientes(d)), -riqueza(d)))[0]
    return None


def cmd_bula(args):
    termo = " ".join(args)
    d = fetch_label(termo)
    if not d:
        print("nada encontrado no openFDA para '%s'. Tente o nome em ingles "
              "(ex: dipirona -> metamizole/dipyrone)." % termo)
        return
    trunc = int(os.environ.get("MED_TRUNC", "900"))
    print("\n=== BULA (rotulo FDA/DailyMed) - %s ===" % termo)
    for chave, titulo in LABEL_SECOES:
        v = d.get(chave)
        if v:
            txt = " ".join(v) if isinstance(v, list) else str(v)
            txt = re.sub(r"\s+", " ", txt).strip()
            corte = "..." if len(txt) > trunc else ""
            print("\n## %s\n%s%s" % (titulo, txt[:trunc], corte))
    print("\n\nFonte: openFDA / DailyMed (rotulo aprovado nos EUA).")
    print("ATENCAO: a bula brasileira e a REFERENCIA legal aqui - confira no Bulario da ANVISA.")


def cmd_inter(args):
    if not args:
        sys.exit("uso: med.py inter <medicamento> [outro]")
    a = args[0]
    d = fetch_label(a)
    if not d:
        print("nada encontrado para '%s'." % a)
        return
    txt = " ".join(d.get("drug_interactions") or []) or "(rotulo sem secao de interacoes)"
    txt = re.sub(r"\s+", " ", txt).strip()
    if len(args) > 1:
        b = args[1]
        print("\n=== %s x %s - trechos do rotulo que citam '%s' ===\n" % (a.upper(), b.upper(), b))
        frases = [s.strip() for s in re.split(r"(?<=[.;])\s+", txt) if norm(b) in norm(s)]
        if frases:
            print("\n".join("- %s" % s for s in frases))
        else:
            print("O rotulo de %s nao menciona %s explicitamente. "
                  "Isso NAO significa ausencia de interacao." % (a, b))
    else:
        print("\n=== INTERACOES - %s ===\n%s" % (a.upper(), txt[:4000]))
    print("\nFonte: openFDA (rotulo). A API de interacoes do RxNav foi descontinuada em 2024.")
    print("Confirme sempre na bula brasileira e no protocolo da instituicao.")


def cmd_artigos(args):
    termo = " ".join(args)
    q = urllib.parse.quote(termo)
    base = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    ids = get_json("%s/esearch.fcgi?db=pubmed&term=%s&retmax=8&retmode=json"
                   % (base, q))["esearchresult"].get("idlist", [])
    if not ids:
        print("nenhum artigo.")
        return
    res = get_json("%s/esummary.fcgi?db=pubmed&id=%s&retmode=json" % (base, ",".join(ids)))["result"]
    print("\nPubMed - '%s'\n" % termo)
    for i in ids:
        a = res.get(i, {})
        autores = ", ".join(x["name"] for x in a.get("authors", [])[:3])
        print("  %s" % a.get("title", ""))
        print("    %s - %s %s" % (autores, a.get("source", ""), a.get("pubdate", "")))
        print("    https://pubmed.ncbi.nlm.nih.gov/%s/\n" % i)
    print("Fonte: NLM/NCBI PubMed")


CMDS = {"sync": cmd_sync, "status": cmd_status, "med": cmd_med, "bula": cmd_bula,
        "inter": cmd_inter, "cid": cmd_cid, "proc": cmd_proc, "ram": cmd_ram,
        "preco": cmd_preco, "artigos": cmd_artigos, "produto": cmd_produto}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in CMDS:
        print(__doc__)
        sys.exit(0 if len(sys.argv) < 2 else 1)
    try:
        CMDS[sys.argv[1]](sys.argv[2:])
    except KeyboardInterrupt:
        sys.exit(130)
