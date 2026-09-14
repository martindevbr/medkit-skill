# Catálogo de fontes oficiais

Todas as fontes abaixo foram testadas em 2026-09-14. Para cada uma: **o que cobre**, **o que NÃO cobre**
(mais importante que o resto — é onde o modelo tende a inventar) e a limitação conhecida.

---

## Brasil

### ANVISA — Dados Abertos
`https://dados.anvisa.gov.br/dados/`

| Arquivo | Conteúdo | Tamanho |
|---|---|---|
| `DADOS_ABERTOS_MEDICAMENTOS.csv` | todos os medicamentos registrados: nome, princípio ativo, classe terapêutica, categoria (genérico/similar/novo), registro, situação, detentora | 7,9 MB |
| `TA_RESTRICAO_MEDICAMENTO.csv` | restrições de uso e prescrição | 1,8 MB |
| `TA_PRECO_MEDICAMENTO.csv` | preço máximo ao consumidor (CMED) | 15,8 MB |
| `VigiMed_Reacoes.csv` | reações adversas notificadas no Brasil | 239 MB |
| `VigiMed_Medicamentos.csv` | medicamentos das notificações VigiMed | 142 MB |

- **Cobre:** existência legal do produto no Brasil, princípio ativo, classe, situação do registro.
- **NÃO cobre:** posologia, diluição, via, estabilidade, incompatibilidade. Nada de bula.
- Encoding latin-1, separador `;`. Campo `SITUACAO_REGISTRO` distingue Ativo/Inativo — **produto inativo não deve ser apresentado como disponível**.

### Bulário Eletrônico da ANVISA
`https://consulta.anvisa.gov.br/#/bulario`

- É a **referência legal** de bula no Brasil (profissional e paciente).
- **Limitação real:** o host `consulta.anvisa.gov.br` não resolve por DNS a partir desta máquina (testado). Não há dataset aberto com bula em texto.
- **Consequência prática:** o comando `bula` usa o rótulo do FDA como substituto. Isso precisa ser **declarado em toda resposta** — a bula brasileira pode divergir em dose, apresentação e indicação.
- Alternativa quando for crítico: abrir o Bulário no navegador (skill `claude-in-chrome`) e ler a bula do produto específico.

### DATASUS — CID-10
`http://www2.datasus.gov.br/cid10/V2008/downloads/CID10CSV.zip` (0,3 MB)

- **Cobre:** capítulos, categorias e subcategorias da CID-10 com descrição oficial em português.
- **NÃO cobre:** critério diagnóstico, tratamento, prognóstico. É classificação, não conduta.
- **Instável:** o servidor recusa conexões de forma intermitente — o downloader tem retry.

### DATASUS — SIGTAP (tabela unificada de procedimentos)
`ftp://ftp2.datasus.gov.br/pub/sistemas/tup/downloads/` — pegue o `TabelaUnificada_AAAAMM_v*.zip` mais recente (~2 MB)

- **Cobre:** todo procedimento que o SUS remunera, com código, complexidade, financiamento, sexo/idade permitidos, CBO habilitado.
- **NÃO cobre:** como executar o procedimento. Nenhuma técnica, nenhum passo a passo.
- Formato largura fixa; cada tabela traz o próprio `*_layout.txt` (`Coluna,Tamanho,Inicio,Fim,Tipo`) — o parser lê o layout do zip, então continua funcionando quando o DATASUS muda colunas.
- `TP_COMPLEXIDADE` (conferido na distribuição da própria tabela): `0` não se aplica · `1` atenção básica · `2` média · `3` alta.

### CONITEC / PCDT — protocolos clínicos
`https://www.gov.br/conitec/pt-br`

- Protocolos Clínicos e Diretrizes Terapêuticas: conduta oficial do Ministério da Saúde por doença.
- PDFs, sem API. Use WebFetch. **É a melhor fonte brasileira para "qual é a conduta padrão em X".**

### COFEN / COREN — legislação de enfermagem
`https://www.cofen.gov.br/` · Lei 7.498/86 · Decreto 94.406/87

- Define o que técnico e auxiliar de enfermagem podem executar e sob qual supervisão.
- **Limitação:** o site responde 418 a clientes automatizados; use o navegador quando o WebFetch falhar.
- **As resoluções mudam.** Nunca afirme escopo de prática de memória — leia o texto vigente.

### BVS / Ministério da Saúde
`https://bvsms.saude.gov.br/`

- Cadernos de Atenção Básica, manuais técnicos, protocolos de segurança do paciente.
- **Limitação:** conexão resetada em acesso automatizado a partir desta máquina; acesse pelo navegador.

---

## Internacionais

### openFDA — rótulos de medicamentos
`https://api.fda.gov/drug/label.json` — grátis, sem chave

Seções disponíveis: `boxed_warning`, `indications_and_usage`, `dosage_and_administration`,
`dosage_forms_and_strengths`, `contraindications`, `warnings_and_cautions`, `adverse_reactions`,
`drug_interactions`, `pregnancy`, `nursing_mothers`, `pediatric_use`, `geriatric_use`, `overdosage`,
`mechanism_of_action`, `clinical_pharmacology`.

- **Cobre:** farmacologia clínica completa, em inglês, do rótulo aprovado nos EUA.
- **NÃO cobre:** realidade brasileira. Apresentações, doses e até indicações divergem.
- A busca prioriza o **princípio ativo isolado**; associações só aparecem se não houver o puro.
- Limite de requisições sem chave: 1.000/dia por IP.

### PubMed — E-utilities (NLM/NCBI)
`https://eutils.ncbi.nlm.nih.gov/entrez/eutils/` — grátis, sem chave (3 req/s)

- **Cobre:** literatura científica — revisões sistemáticas, ensaios clínicos, evidência de enfermagem.
- **NÃO cobre:** texto completo (só título, autores, revista, data, link).

### RxNav / RxNorm (NLM)
`https://rxnav.nlm.nih.gov/REST/`

- Funciona: `rxcui`, `rxclass` (classes terapêuticas, mecanismo de ação).
- **DESCONTINUADO:** a API de interações (`/interaction`) foi desativada em 2024 — retorna `Not found`. **Não use.** Interações vêm do openFDA.

### OMS — CID-11
`https://id.who.int/icd/`

- Exige registro gratuito e token OAuth2 (`https://icd.who.int/icdapi`). Retorna 401 sem token.
- No Brasil o SUS ainda opera em CID-10 — use CID-11 apenas como complemento.

---

## Resumo de confiabilidade

| Fonte | Estado | Observação |
|---|---|---|
| ANVISA Dados Abertos | estável | download direto |
| SIGTAP (FTP) | estável | layout autodescrito |
| openFDA | estável | 1.000 req/dia |
| PubMed | estável | 3 req/s |
| DATASUS CID-10 | **instável** | retry obrigatório |
| Bulário ANVISA | **inacessível daqui** | DNS não resolve |
| BVS / COFEN | **bloqueia robô** | usar navegador |
