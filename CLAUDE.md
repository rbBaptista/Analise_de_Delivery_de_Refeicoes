# CLAUDE.md — Análise de Dados de Delivery de Refeições

## Visão geral

Projeto de análise de dados reais de um delivery de refeições, usando **Python, Pandas e NumPy**.
O objetivo é atuar como analista de dados: tratar os dados, criar features, agregar, analisar a evolução temporal, integrar pedidos com cardápio e calcular KPIs para apoiar decisões estratégicas do negócio.

O cardápio possui categorias como Salgados, Bebidas, Doces, Saudaveis e Oriental.

## Stack

- Python 3.10+
- pandas
- numpy
- (opcional) matplotlib para gráficos da análise temporal
- (opcional) Jupyter Notebook ou script `.py`

## Estrutura do projeto

```
.
├── CLAUDE.md
├── requirements.txt
├── dados/
│   ├── pedidos.csv
│   └── cardapio.csv
└── analise_delivery.py   # ou analise_delivery.ipynb
```

Os dois CSVs ficam **sempre** na pasta `dados/`. Nunca altere os arquivos originais: todo tratamento é feito em memória nos DataFrames.

## Dados

### `dados/pedidos.csv` (450 linhas, 6 colunas)

| Coluna           | Tipo (ao carregar) | Descrição                          |
|------------------|--------------------|------------------------------------|
| `ID_Pedido`      | int64              | Identificador único do pedido      |
| `Data`           | str (texto)        | Data do pedido (`AAAA-MM-DD`)      |
| `Cliente_ID`     | int64              | Identificador do cliente           |
| `Item`           | str                | Nome do item pedido                |
| `Quantidade`     | float64            | Quantidade pedida                  |
| `Preco_Unitario` | float64            | Preço unitário cobrado             |

Características conhecidas:

- Período coberto: 2023-01-02 a 2025-09-29 (**mais de um ano**).
- `Quantidade` tem 19 nulos e `Preco_Unitario` tem 20 nulos.
- Cada linha é um pedido de um único item; `ID_Pedido` é único.

### `dados/cardapio.csv` (20 linhas, 3 colunas)

| Coluna       | Tipo    | Descrição                |
|--------------|---------|--------------------------|
| `Item`       | str     | Nome do item (chave)     |
| `Categoria`  | str     | Categoria do item        |
| `Preco_Base` | float64 | Preço base do cardápio   |

Todos os itens de `pedidos.csv` existem em `cardapio.csv` (merge sem perda de linhas).

## Requisitos da análise

Implementar as etapas abaixo, nesta ordem, com comentários em português e saídas impressas (`print`) com títulos claros para cada etapa.

### 1. Análise Exploratória (EDA)
- Carregar `dados/pedidos.csv` com `pd.read_csv`.
- Explorar com `head()`, `tail()`, `info()` e `describe()`.
- Informar quantidade de registros, colunas e tipos de dados.

### 2. Feature Engineering
- Criar a coluna `Receita_Item = Quantidade * Preco_Unitario`.

### 3. Tratamento de valores ausentes
- Identificar nulos por coluna (`isnull().sum()`).
- Preencher nulos de `Quantidade` com a **média** da coluna.
- Remover linhas com nulos em `Preco_Unitario` (`dropna(subset=["Preco_Unitario"])`).
- Ordem recomendada: tratar os nulos **antes** de calcular `Receita_Item`, para que a receita não fique `NaN` (ou recalcular a coluna após o tratamento).

### 4. Agregações por Item
- Agrupar por `Item` e calcular quantidade total vendida e receita total.
- Top 5 itens mais vendidos (por quantidade).
- Top 5 itens com maior receita.

### 5. Análise Temporal
- Converter `Data` com `pd.to_datetime`.
- Extrair o mês de cada pedido.
- Calcular a receita total por mês.
- Analisar a evolução das vendas ao longo do tempo.
- **Atenção:** como os dados cobrem mais de um ano, extrair apenas `dt.month` mistura meses de anos diferentes. Para a evolução temporal, use ano-mês (`dt.to_period("M")`) e, se quiser, mostre também o agrupamento só pelo número do mês (sazonalidade).

### 6. Integração de dados (Merge)
- Carregar `dados/cardapio.csv`.
- `pedidos.merge(cardapio, on="Item", how="left")`.
- Calcular a receita total por `Categoria` e identificar a categoria que mais gera receita.

### 7. Filtros e consultas
- Filtrar pedidos da categoria `Salgados` com `Quantidade > 10`.
- Exibir o resultado filtrado.

### 8. KPIs com NumPy
- **Receita Total:** soma de `Receita_Item`.
- **Total de Itens Vendidos:** soma de `Quantidade`.
- **Ticket Médio:** receita total ÷ número de pedidos.
- Usar funções do NumPy (`np.sum`, `np.mean`, etc.) sobre os arrays das colunas (`.to_numpy()`).

### Desafio extra (opcional)
- Percentis 25%, 50% e 75% de `Preco_Unitario` e `Quantidade` com `np.percentile`.

## Convenções de código

- Nomes de colunas exatamente como nos CSVs (`Preco_Unitario`, `Receita_Item`, `Categoria`, etc.), mantendo o padrão com iniciais maiúsculas e underscores.
- Variáveis e funções em `snake_case`; comentários e textos de saída em português.
- Preferir operações vetorizadas do pandas/NumPy; evitar `for` sobre linhas do DataFrame.
- Não usar `inplace=True`; atribuir o resultado a uma variável ou reatribuir o DataFrame.
- Ao filtrar ou tratar dados, trabalhar em cópias (`.copy()`) para evitar `SettingWithCopyWarning`.
- Formatar valores monetários com 2 casas decimais (`f"R$ {valor:,.2f}"`).
- Caminhos de arquivo relativos à raiz do projeto (`dados/pedidos.csv`).

## Como executar

```bash
pip install -r requirements.txt
python analise_delivery.py
```

`requirements.txt`:

```
pandas
numpy
matplotlib
```

## Regras para o Claude neste projeto

- Seguir as etapas na ordem descrita acima; cada etapa deve ser uma seção separada no código (ou célula, se for notebook).
- Não inventar colunas ou dados: usar apenas o que existe nos CSVs.
- Sempre validar o resultado do merge (por exemplo, conferir que o número de linhas se manteve e que não há `Categoria` nula).
- Explicar brevemente, em comentários, as decisões de tratamento (por que média, por que remover linhas).
- Ao final, apresentar um resumo com os principais insights: itens e categoria líderes, mês de maior receita e os KPIs.
- Não modificar os arquivos em `dados/`.
