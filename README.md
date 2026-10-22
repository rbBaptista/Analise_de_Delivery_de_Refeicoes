# Análise de Dados de Delivery de Refeições

Análise de dados de pedidos de um delivery de refeições com **Python, Pandas e NumPy**: tratamento de valores ausentes, criação de features, agregações, evolução temporal, integração com o cardápio e cálculo de KPIs para apoiar decisões de negócio.

## Tecnologias

- Python 3.10+ (testado com Python 3.13, pandas 3.1 e NumPy 2.5)
- [pandas](https://pandas.pydata.org/)
- [NumPy](https://numpy.org/)
- matplotlib (está no `requirements.txt`, mas o script ainda não gera gráficos)

## Estrutura do projeto

```
.
├── README.md
├── requirements.txt
├── analise_delivery.py   # script com todas as etapas da análise
└── dados/
    ├── pedidos.csv
    └── cardapio.csv
```

Os arquivos em `dados/` são apenas lidos: todo o tratamento acontece em memória, nos DataFrames.

## Dados

### `dados/pedidos.csv`: 450 pedidos, de 02/01/2023 a 29/09/2025

| Coluna           | Descrição                                   |
|------------------|---------------------------------------------|
| `ID_Pedido`      | Identificador único do pedido               |
| `Data`           | Data do pedido (`AAAA-MM-DD`)               |
| `Cliente_ID`     | Identificador do cliente                    |
| `Item`           | Item pedido (cada linha tem um único item)  |
| `Quantidade`     | Quantidade pedida (19 valores ausentes)     |
| `Preco_Unitario` | Preço unitário cobrado (20 valores ausentes) |

### `dados/cardapio.csv`: 20 itens

| Coluna       | Descrição                                                  |
|--------------|------------------------------------------------------------|
| `Item`       | Nome do item (chave de ligação com os pedidos)             |
| `Categoria`  | Salgados, Doces, Oriental, Saudaveis ou Bebidas            |
| `Preco_Base` | Preço base do cardápio                                     |

## Etapas da análise

O script `analise_delivery.py` executa as etapas abaixo, nesta ordem. Cada etapa imprime seus resultados com um título próprio.

1. **Análise Exploratória (EDA):** `head()`, `tail()`, `info()` e `describe()`, mais o número de registros, as colunas e os tipos de dados.
2. **Feature Engineering:** criação de `Receita_Item = Quantidade * Preco_Unitario`.
3. **Tratamento de valores ausentes:** contagem de nulos por coluna, remoção e preenchimento (detalhes abaixo) e recálculo de `Receita_Item`.
4. **Agregações por Item:** quantidade e receita totais por item, com o top 5 por quantidade e o top 5 por receita.
5. **Análise Temporal:** receita por ano-mês com variação mensal e média móvel de 3 meses, comparação entre anos no mesmo período e sazonalidade por mês do ano.
6. **Integração de dados (Merge):** junção com o cardápio, validação do resultado e receita por categoria.
7. **Filtros e consultas:** pedidos da categoria Salgados com `Quantidade > 10`.
8. **KPIs com NumPy:** Receita Total, Total de Itens Vendidos e Ticket Médio.
9. **Desafio extra:** percentis 25%, 50% e 75% de `Preco_Unitario` e `Quantidade` com `np.percentile`.

Ao final, o script imprime um resumo com os principais insights.

## Decisões de tratamento

- **`Preco_Unitario` ausente → linha removida (20 linhas, ~4% da base).** Sem o preço não dá para saber a receita real do pedido. Preencher com uma média misturaria preços de itens muito diferentes (de água mineral a pizza).
- **`Quantidade` ausente → preenchida com a média (15,89).** A coluna não tem outliers (vai de 1 a 30, e a média é próxima da mediana). A média é calculada depois da remoção acima, só com as linhas que continuam na análise. Uma das linhas tinha os dois campos vazios, então foram 18 quantidades preenchidas.
- **Ano-mês na análise temporal.** Os dados cobrem mais de um ano, e agrupar só por `dt.month` misturaria meses de anos diferentes. A evolução usa `dt.to_period("M")`, e a sazonalidade (só o número do mês) aparece separada.
- **Validação do merge.** O merge usa `validate="many_to_one"`, e o script confere que o número de linhas não mudou, que nenhum pedido ficou sem `Categoria` e que a receita total foi preservada.

## Como executar

Na raiz do projeto:

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python analise_delivery.py
```

> Execute a partir da raiz do projeto: os caminhos dos CSVs são relativos (`dados/pedidos.csv`).

## Principais resultados

Base final: 430 pedidos, depois do tratamento dos valores ausentes.

### KPIs

| KPI                     | Valor          |
|-------------------------|----------------|
| Receita Total           | R$ 122,649.13  |
| Total de Itens Vendidos | 6,833.03       |
| Número de Pedidos       | 430            |
| Ticket Médio            | R$ 285.23      |

### Itens

| # | Mais vendidos (quantidade) | Maior receita                    |
|---|----------------------------|----------------------------------|
| 1 | Hamburguer (510.78)        | Pizza Calabresa (R$ 15,902.64)   |
| 2 | Brownie (465.89)           | Pizza Mussarela (R$ 14,148.69)   |
| 3 | Acai 300ml (402.89)        | Sushi 8 pecas (R$ 12,084.76)     |
| 4 | Cafe Expresso (392.00)     | Hamburguer (R$ 11,561.71)        |
| 5 | Sushi 8 pecas (378.89)     | Salada Caesar (R$ 9,927.96)      |

### Categorias

| Categoria | Receita        | Pedidos | Participação |
|-----------|----------------|---------|--------------|
| Salgados  | R$ 53,071.32   | 151     | 43.3%        |
| Doces     | R$ 22,293.14   | 111     | 18.2%        |
| Oriental  | R$ 21,599.40   | 43      | 17.6%        |
| Saudaveis | R$ 16,539.04   | 42      | 13.5%        |
| Bebidas   | R$ 9,146.23    | 83      | 7.5%         |

### Evolução temporal

- **Mês de maior receita:** Fev/2023 (R$ 6,646.03, 19 pedidos).
- **Mês de menor receita:** Mar/2024 (R$ 1,178.62, 5 pedidos).
- **Receita de janeiro a setembro por ano:** 2023: R$ 38,173.75 · 2024: R$ 29,789.50 (−22,0%) · 2025: R$ 34,199.21 (+14,8%).
- **Sazonalidade:** fevereiro tem a maior receita média por mês (R$ 5,337.18) e março a menor (R$ 2,661.03).

### Filtro: Salgados com Quantidade > 10

109 pedidos, que somam R$ 47,748.99. Em 9 deles a quantidade foi preenchida pela média.

### Percentis

| Percentil | Preco_Unitario | Quantidade |
|-----------|----------------|------------|
| P25       | 8.92           | 8.00       |
| P50       | 13.10          | 16.00      |
| P75       | 27.40          | 24.00      |

## Limitações

- **2025 está incompleto (até setembro).** Por isso a comparação entre anos usa o mesmo intervalo de meses, e na sazonalidade outubro a dezembro aparecem em só dois anos (a comparação usa a receita média, não a soma).
- **Pouco volume por mês (~13 pedidos).** A receita mensal oscila bastante e acompanha principalmente o número de pedidos. Por isso o script mostra também a média móvel de 3 meses.
- **Totais de quantidade com casas decimais.** As quantidades preenchidas com a média não são inteiras e foram mantidas sem arredondar, para não enviesar os totais.
