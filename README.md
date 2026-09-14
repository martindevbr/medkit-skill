<div align="center">

# 🩺 MedKit Skill

**Uma skill do Claude Code que consulta fontes oficiais de saúde antes de responder — porque medicina não se responde de memória.**

[![Fontes](https://img.shields.io/badge/fontes-ANVISA%20%C2%B7%20DATASUS%20%C2%B7%20openFDA%20%C2%B7%20PubMed-0a7?style=flat-square)](#-fontes)
[![Backtest](https://img.shields.io/badge/backtest-29%2F29%20(100%25)-2c8?style=flat-square)](#-backtest)
[![Dependências](https://img.shields.io/badge/depend%C3%AAncias-nenhuma-555?style=flat-square)](#-instalação)
[![Licença](https://img.shields.io/badge/licen%C3%A7a-MIT-555?style=flat-square)](LICENSE)

</div>

---

## O problema

Perguntar sobre medicamento a um LLM é perigoso pelo motivo errado: ele quase sempre responde. Com
fluência, com estrutura, com uma dose plausível. E "plausível" em farmacologia é exatamente o tipo de
erro que ninguém percebe a tempo.

A MedKit inverte isso. Ela não deixa a resposta sair de dentro do modelo — **obriga a resposta a sair de
uma fonte oficial, citada, com data.** Quando a fonte não tem o dado, a resposta certa passa a ser *"não
encontrei"*, e não um chute bem escrito.

Foi construída para uma técnica de enfermagem estudar com dado real: medicamentos, doenças,
procedimentos, interações e evidência científica.

## ✨ O que ela faz

| Pergunta | Comando | Fonte |
|---|---|---|
| Esse medicamento existe? Qual o princípio ativo e a classe? | `med dipirona` | ANVISA — 🔌 offline |
| Qual a dose, contraindicação, advertência? | `bula dipyrone` | openFDA / DailyMed |
| Esses dois remédios interagem? | `inter warfarin ibuprofen` | openFDA |
| Qual o código e a descrição dessa doença? | `cid "diabetes mellitus"` | DATASUS CID-10 — 🔌 offline |
| Esse procedimento existe no SUS? | `proc curativo` | SIGTAP — 🔌 offline |
| Que reações adversas foram notificadas no Brasil? | `ram dipirona` | ANVISA VigiMed — 🔌 offline |
| Qual o preço máximo? | `preco dipirona` | CMED/ANVISA — 🔌 offline |
| O que a literatura diz? | `artigos "pressure ulcer prevention"` | PubMed |

🔌 = funciona **sem internet** depois do `sync` inicial (~28 MB).

## 🚀 Instalação

Sem dependências — só Python 3 e a biblioteca padrão.

```bash
git clone https://github.com/martindevbr/medkit-skill.git ~/.claude/skills/medicina
python ~/.claude/skills/medicina/scripts/med.py sync     # ~28 MB
python ~/.claude/skills/medicina/scripts/med.py status
```

O Claude Code carrega a skill automaticamente quando o assunto for saúde. Para usar o CLI direto:

```bash
python scripts/med.py med dipirona
python scripts/med.py bula warfarin
python scripts/med.py inter warfarin ibuprofen
```

O cache fica em `D:\enfermagem-workspace\cache` por padrão — mude com a variável `MEDICINA_DATA`.

## 🧭 As quatro regras

Estão no `SKILL.md` e valem para toda resposta:

1. **Consultar antes de responder** — nunca de memória, mesmo que a pergunta pareça trivial.
2. **Responder só o que a fonte retornou** — sem completar lacuna com plausibilidade.
3. **Citar fonte e data** em toda afirmação clínica.
4. **Declarar a lacuna** — *"não encontrei em ⟨fonte⟩"* é uma resposta válida; inventar não é.

Se as fontes estiverem fora do ar, a resposta certa é *"não consegui consultar agora"*.

## 📚 Fontes

Cada fonte está documentada em [`references/fontes.md`](references/fontes.md) com o que cobre, **o que
não cobre** e a limitação conhecida. O "não cobre" é a parte que importa — é onde o modelo escorrega.

| Fonte | Cobre | Não cobre |
|---|---|---|
| **ANVISA Dados Abertos** | registro, princípio ativo, classe terapêutica | posologia, diluição, bula |
| **DATASUS CID-10** | classificação oficial de doenças | critério diagnóstico, conduta |
| **SIGTAP** | procedimentos que o SUS remunera | **como executar** a técnica |
| **openFDA / DailyMed** | farmacologia clínica completa | realidade brasileira (dose/apresentação divergem) |
| **PubMed** | literatura científica | texto completo dos artigos |
| **VigiMed** | reações adversas notificadas | causalidade — notificação não é prova |

Descobertas durante a construção, já tratadas no código:

- A API de interações do **RxNav foi descontinuada em 2024** — a skill não aponta para ela.
- O **Bulário da ANVISA não tem dataset aberto**; a skill usa o rótulo do FDA e **avisa em toda resposta** que a bula brasileira é a referência legal.
- O **DATASUS oscila** — o downloader tem retry com backoff.
- O **SIGTAP é largura fixa**, mas traz o próprio layout no zip — o parser lê o layout, então sobrevive a mudanças de coluna.

## 🧪 Backtest

Não testa "o código roda". Testa se **a resposta bate com a verdade conhecida** — e, sobretudo, se a
skill **admite quando não sabe**.

```bash
python tests/backtest.py             # 29 casos
python tests/backtest.py --offline   # só os que não dependem de rede
```

```
  ANVISA      5/5      CID-10      6/6      SIGTAP      4/4
  openFDA     6/6      Interacao   3/3      PubMed      1/1
  Rastreio    4/4
  ------------------------------------------------------------
  TOTAL      29/29  (100%)
```

Quatro categorias, com destaque para a terceira:

- **Verdade conhecida** — `I10` tem que voltar *hipertensão essencial*; metformina tem que trazer *lactic acidosis* na tarja preta; curativo simples tem que ser o código `0301100284`.
- **Robustez** — acento, maiúscula e busca parcial precisam achar o mesmo registro.
- **Controle negativo** — para fármaco, código e procedimento inexistentes, a skill **tem que dizer que não achou**. É o teste antialucinação, e é o que mais importa.
- **Rastreabilidade** — toda saída precisa citar a fonte.

Dois casos falharam na primeira rodada e viraram correção real: entre rótulos do mesmo princípio ativo, a
skill escolhia o de um genérico com seções faltando. Hoje ela prioriza o **rótulo mais completo**.

## 🗂 Estrutura

```
medicina/
├── SKILL.md                      # regras e roteamento (o que o Claude lê)
├── scripts/med.py                # CLI de consulta — só biblioteca padrão
├── references/
│   ├── fontes.md                 # catálogo: cobre / não cobre / limitação
│   └── enfermagem-br.md          # escopo legal + cálculo de dose e gotejamento
└── tests/backtest.py             # 29 casos com gabarito
```

## ⚠️ Limites

Material de **estudo e consulta**. Não prescreve, não diagnostica e não substitui protocolo
institucional, prescrição de profissional habilitado ou a bula brasileira vigente.

O escopo de prática do técnico de enfermagem (Lei 7.498/86, Decreto 94.406/87, resoluções do COFEN)
**muda com o tempo** — a skill manda ler o texto vigente em vez de afirmar de memória.

Em urgência real, a resposta é acionar o **192**, não consultar uma skill.

## 📄 Licença

MIT — veja [LICENSE](LICENSE).

Os dados consultados pertencem às respectivas fontes oficiais (ANVISA, DATASUS/Ministério da Saúde, FDA,
NLM) e mantêm seus próprios termos de uso.
