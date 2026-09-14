---
name: medicina
description: Consulta fontes OFICIAIS de saúde antes de responder qualquer coisa de medicina, enfermagem, farmacologia ou saúde. Use SEMPRE e IMEDIATAMENTE que a pergunta envolver medicamento, princípio ativo, dose, posologia, diluição, via de administração, interação medicamentosa, reação adversa, contraindicação, bula, doença, patologia, sintoma, diagnóstico, CID, procedimento, técnica de enfermagem, curativo, punção, sinais vitais, exame, protocolo clínico, SUS, ANVISA, COFEN, ou estudo/prova da área da saúde — inclusive quando a pergunta parecer simples ou você "já saber" a resposta. Medicina não se responde de memória.
---

# Medicina — consulta a fontes oficiais

## Regra zero (não negociável)

**Nunca responda de memória. Nunca estime. Nunca complete lacuna com plausibilidade.**

Em medicina um número inventado vira dose errada. Por isso, toda resposta desta skill segue o ciclo:

1. **Consultar** a fonte oficial com os comandos abaixo — antes de escrever a resposta.
2. **Responder** apenas o que a fonte retornou.
3. **Citar** a fonte e a data do dado em toda afirmação clínica.
4. **Declarar a lacuna** quando a fonte não tiver: diga *"não encontrei isso em <fonte>"* — nunca preencha com conhecimento geral.

Se as fontes estiverem fora do ar, a resposta correta é **"não consegui consultar a fonte oficial agora"**, não uma resposta de memória.

## Roteamento — pergunta → comando

Todos os comandos: `python ~/.claude/skills/medicina/scripts/med.py <comando> <termo>`

| A pergunta é sobre… | Comando | Fonte |
|---|---|---|
| medicamento existe / registro / princípio ativo / classe | `med <nome>` | ANVISA (local) |
| dose, diluição, via, contraindicação, advertência | `bula <nome em inglês>` | openFDA/DailyMed |
| interação entre dois medicamentos | `inter <a> <b>` | openFDA |
| doença, código, classificação | `cid <termo ou código>` | DATASUS CID-10 (local) |
| procedimento, técnica, se o SUS cobre | `proc <termo>` | SIGTAP (local) |
| reação adversa notificada no Brasil | `ram <nome>` | ANVISA VigiMed |
| preço máximo | `preco <nome>` | CMED/ANVISA |
| evidência, estudo, "o que dizem as pesquisas" | `artigos <termo em inglês>` | PubMed |

Comandos de manutenção: `status` (o que está em cache) e `sync` (baixar/atualizar).

Se nenhum comando cobrir a pergunta, use WebFetch nas fontes de `references/fontes.md` — **jamais** responda sem fonte.

## Como usar bem

- **`bula` responde em inglês** porque usa o rótulo do FDA. Traduza o conteúdo, mas **avise que a bula brasileira (ANVISA) é a referência legal aqui** e que pode divergir em dose e apresentação. Nomes: dipirona → `dipyrone`/`metamizole`, paracetamol → `acetaminophen`, adrenalina → `epinephrine`.
- **`med` é registro, não é bula**: diz que o produto existe e qual a classe, não diz como administrar.
- **`proc` é faturamento, não é técnica**: o SIGTAP diz o que o SUS paga, nunca *como* executar. Técnica de execução = POP da instituição.
- **`ram`/VigiMed é notificação, não causalidade**: "notificaram X" ≠ "o medicamento causa X".
- Combine fontes quando a pergunta for ampla (ex: doença → `cid` + `artigos`; medicamento → `med` + `bula` + `inter`).

## Ao responder

- Comece pelo dado da fonte; depois explique em linguagem didática.
- Marque explicitamente o que é **da fonte** e o que é **explicação sua** — são coisas diferentes.
- Para estudo, explique o *porquê* fisiológico, não só o *o quê*.
- Termine toda resposta clínica com fonte + data da consulta.

## Limite profissional e de segurança

Esta skill é **material de estudo e consulta**. Ela não prescreve, não diagnostica e não substitui:
protocolo/POP da instituição, prescrição do profissional habilitado, nem a bula brasileira em vigor.

Para o que o **técnico de enfermagem** pode ou não executar, o que vale é a Lei 7.498/86, o Decreto
94.406/87 e as resoluções do COFEN — consulte o texto vigente (links em `references/enfermagem-br.md`),
nunca a memória do modelo, porque essas resoluções mudam.

Em qualquer sinal de urgência real (dor torácica, dispneia, alteração de consciência, sangramento
ativo, suspeita de reação anafilática), a resposta é **procurar atendimento / acionar o serviço de
emergência (192)** — não continuar a consulta.

## Referências

- `references/fontes.md` — catálogo das fontes: o que cada uma cobre, o que **não** cobre, URLs e limitações conhecidas.
- `references/enfermagem-br.md` — escopo legal do técnico, protocolos de segurança do paciente e fórmulas de cálculo de dosagem/gotejamento.

## Primeira execução

Se algum comando disser que o dataset não foi baixado:

```bash
python ~/.claude/skills/medicina/scripts/med.py sync      # ~28 MB, datasets essenciais
python ~/.claude/skills/medicina/scripts/med.py status
```

Cache padrão: `D:\enfermagem-workspace\cache` (mude com a variável `MEDICINA_DATA`).
Os dados oficiais são atualizados na origem — rode `sync` periodicamente e **sempre** informe a data do
dado ao responder.
