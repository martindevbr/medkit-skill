# Enfermagem no Brasil — escopo legal e cálculos

Dois tipos de conteúdo convivem aqui, e a diferença importa:

- **O que se consulta** (escopo legal, protocolos): muda com o tempo → sempre ler a fonte vigente.
- **O que se deriva** (cálculo de dose e gotejamento): é aritmética → confere-se pela própria conta.

Nada aqui substitui o POP da instituição nem a prescrição do profissional habilitado.

---

## 1. Escopo de prática — como verificar, nunca de memória

Base legal: **Lei 7.498/86** (exercício da enfermagem), **Decreto 94.406/87** (regulamentação),
**Resoluções do COFEN** (atualizam-se com frequência).

Fluxo obrigatório antes de afirmar que um técnico "pode" ou "não pode" fazer algo:

1. Buscar a resolução vigente no COFEN (`https://www.cofen.gov.br/` — se bloquear robô, abrir no navegador).
2. Verificar se foi revogada ou alterada por resolução posterior.
3. Citar número da resolução e ano.
4. Se não achar o texto vigente: dizer que não foi possível confirmar. **Não deduza por analogia.**

Motivo: pontos como sondagem, administração de quimioterápicos, punção e atividades privativas do
enfermeiro já mudaram de tratamento normativo. Resposta desatualizada aqui é risco legal para a
profissional, não apenas erro de estudo.

---

## 2. Cálculo de dosagem — regra de três

A dose desejada está para o volume procurado assim como a dose disponível está para o volume da apresentação:

```
volume a administrar = (dose prescrita × volume da apresentação) / dose da apresentação
```

**Exemplo conferível:** prescrito 250 mg; ampola de 500 mg/2 mL.
`(250 × 2) / 500 = 1 mL`
Confere: 1 mL de uma solução de 250 mg/mL = 250 mg. ✓

---

## 3. Gotejamento — derivado das definições

Duas definições de equipo, e todo o resto sai delas:

- **Macrogotas:** 1 mL = **20 gotas**
- **Microgotas:** 1 mL = **60 microgotas**

### Macrogotas por minuto

```
gotas/min = (volume em mL × 20) / (tempo em minutos)
```

Com o tempo em horas, `minutos = horas × 60`, então `20/60 = 1/3` e a fórmula encurta para:

```
gotas/min = volume (mL) / (tempo em horas × 3)
```

**Exemplo conferível:** 500 mL em 6 h → `500 / (6 × 3) = 27,7` ≈ **28 gotas/min**.
Conferindo pelo caminho longo: `500 × 20 = 10.000 gotas` em `360 min` = `27,8 gotas/min`. ✓

### Microgotas por minuto

```
microgotas/min = (volume em mL × 60) / (tempo em minutos)
```

Com tempo em horas, `60/60 = 1`, logo:

```
microgotas/min = volume (mL) / tempo (h)
```

**Exemplo conferível:** 500 mL em 6 h → **83 microgotas/min**.
Note que é exatamente 3× o valor em macrogotas — coerente com `60/20 = 3`. ✓

### Bomba de infusão

```
mL/h = volume total (mL) / tempo (h)
```

500 mL em 6 h → **83 mL/h**. (Mesmo número das microgotas/min, porque 1 microgota/min = 1 mL/h.)

> **Sempre refaça a conta na resposta.** Mostre os números substituídos, não só a fórmula — é assim que
> o erro aparece antes de chegar no paciente.

---

## 4. Protocolos de segurança do paciente

Base normativa: **RDC ANVISA 36/2013** (Programa Nacional de Segurança do Paciente) e os protocolos
básicos do Ministério da Saúde — identificação do paciente, segurança na prescrição e administração de
medicamentos, cirurgia segura, higiene das mãos, prevenção de quedas e de lesão por pressão.

Ao responder sobre qualquer um deles: **buscar o texto do protocolo** (CONITEC/BVS/ANVISA) e citar.
O número de "certos" da administração de medicamentos varia conforme a instituição e a versão do
protocolo adotado — confirme na fonte que a instituição dela usa, em vez de fixar uma lista.

---

## 5. Consulta rápida

```bash
S=~/.claude/skills/medicina/scripts/med.py
python $S med dipirona                  # registro ANVISA
python $S bula dipyrone                 # farmacologia (rótulo FDA — checar bula BR)
python $S inter warfarin ibuprofen      # interação
python $S cid "diabetes mellitus"       # classificação
python $S proc curativo                 # procedimento no SUS
python $S artigos "pressure ulcer prevention nursing"
```
