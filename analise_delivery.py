"""
Análise de Dados de Delivery de Refeições.

Etapas, na ordem definida no CLAUDE.md:
    1. Análise Exploratória (EDA)
    2. Feature Engineering
    3. Tratamento de valores ausentes
    4. Agregações por Item
    5. Análise Temporal
    6. Integração de dados (Merge)
    7. Filtros e consultas
    8. KPIs com NumPy
    Extra: percentis com NumPy
    Resumo com os principais insights

Os arquivos em dados/ são apenas lidos; todo o tratamento acontece em memória.
"""

import numpy as np
import pandas as pd

CAMINHO_PEDIDOS = "dados/pedidos.csv"
CAMINHO_CARDAPIO = "dados/cardapio.csv"

NOMES_MESES = {
    1: "Jan", 2: "Fev", 3: "Mar", 4: "Abr", 5: "Mai", 6: "Jun",
    7: "Jul", 8: "Ago", 9: "Set", 10: "Out", 11: "Nov", 12: "Dez",
}

# Tabelas largas sem quebra de colunas e números com 2 casas decimais
pd.set_option("display.width", 140)
pd.set_option("display.max_columns", None)
pd.set_option("display.float_format", "{:,.2f}".format)


def titulo(texto):
    print("\n" + "=" * 80)
    print(texto)
    print("=" * 80)


def formatar_moeda(valor):
    return f"R$ {valor:,.2f}"


def formatar_ano_mes(periodo):
    return f"{NOMES_MESES[periodo.month]}/{periodo.year}"


# =============================================================================
# 1. ANÁLISE EXPLORATÓRIA (EDA)
# =============================================================================
titulo("1. ANÁLISE EXPLORATÓRIA (EDA)")

pedidos = pd.read_csv(CAMINHO_PEDIDOS)

print("\nPrimeiras linhas (head):")
print(pedidos.head())

print("\nÚltimas linhas (tail):")
print(pedidos.tail())

print("\nInformações gerais (info):")
pedidos.info()

print("\nEstatísticas descritivas (describe):")
print(pedidos.describe())

n_registros, n_colunas = pedidos.shape
print(f"\nQuantidade de registros: {n_registros}")
print(f"Quantidade de colunas: {n_colunas}")
print("Tipos de dados por coluna:")
print(pedidos.dtypes.to_string())


# =============================================================================
# 2. FEATURE ENGINEERING
# =============================================================================
titulo("2. FEATURE ENGINEERING")

# Cada linha é um pedido de um único item, então a receita do pedido é
# Quantidade * Preco_Unitario. Calculada aqui sobre os dados brutos: onde há
# nulo em um dos fatores a receita fica NaN. Por isso a coluna é recalculada
# na etapa 3, depois do tratamento dos nulos.
pedidos["Receita_Item"] = pedidos["Quantidade"] * pedidos["Preco_Unitario"]

print("Coluna Receita_Item criada:")
print(pedidos[["ID_Pedido", "Item", "Quantidade", "Preco_Unitario", "Receita_Item"]].head())
print(f"\nLinhas com Receita_Item nula (antes do tratamento): {pedidos['Receita_Item'].isnull().sum()}")


# =============================================================================
# 3. TRATAMENTO DE VALORES AUSENTES
# =============================================================================
titulo("3. TRATAMENTO DE VALORES AUSENTES")

print("Nulos por coluna (antes do tratamento):")
print(pedidos.isnull().sum().to_string())

# Preco_Unitario nulo -> remover a linha. Sem o preço não há como saber a
# receita real do pedido, e preencher com uma média misturaria preços de itens
# muito diferentes (de água mineral a pizza), distorcendo receita e ticket.
# São poucas linhas (~4% da base), então a perda é pequena.
pedidos_tratado = pedidos.dropna(subset=["Preco_Unitario"]).copy()
linhas_removidas = len(pedidos) - len(pedidos_tratado)

# Quantidade nula -> preencher com a média. A remoção acima vem antes para que
# a média seja calculada só com as linhas que continuam na análise. A coluna não
# tem outliers (vai de 1 a 30, com média próxima da mediana), então a média é
# um valor representativo, e assim aproveitamos pedidos que têm preço válido.
# O valor preenchido não é inteiro; ele é mantido sem arredondar para não
# enviesar os totais.
mascara_quantidade_nula = pedidos_tratado["Quantidade"].isnull()
ids_quantidade_preenchida = pedidos_tratado.loc[mascara_quantidade_nula, "ID_Pedido"]
media_quantidade = pedidos_tratado["Quantidade"].mean()
mediana_quantidade = pedidos_tratado["Quantidade"].median()
pedidos_tratado["Quantidade"] = pedidos_tratado["Quantidade"].fillna(media_quantidade)

# Recalcula a receita agora que nenhum dos fatores tem nulo
pedidos_tratado["Receita_Item"] = pedidos_tratado["Quantidade"] * pedidos_tratado["Preco_Unitario"]

print(f"\nLinhas removidas por Preco_Unitario nulo: {linhas_removidas}")
print(f"Quantidades preenchidas com a média: {len(ids_quantidade_preenchida)}")
print(f"Média de Quantidade usada no preenchimento: {media_quantidade:.2f} (mediana: {mediana_quantidade:.2f})")
print(f"Registros após o tratamento: {len(pedidos_tratado)}")

print("\nNulos por coluna (após o tratamento):")
print(pedidos_tratado.isnull().sum().to_string())
assert pedidos_tratado.isnull().sum().sum() == 0, "Ainda há valores nulos após o tratamento"


# =============================================================================
# 4. AGREGAÇÕES POR ITEM
# =============================================================================
titulo("4. AGREGAÇÕES POR ITEM")

vendas_por_item = (
    pedidos_tratado.groupby("Item")
    .agg(Quantidade_Total=("Quantidade", "sum"), Receita_Total=("Receita_Item", "sum"))
    .sort_values("Receita_Total", ascending=False)
)
print("Quantidade total vendida e receita total por item:")
print(vendas_por_item)

top5_quantidade = vendas_por_item.nlargest(5, "Quantidade_Total")
print("\nTop 5 itens mais vendidos (por quantidade):")
print(top5_quantidade)

top5_receita = vendas_por_item.nlargest(5, "Receita_Total")
print("\nTop 5 itens com maior receita:")
print(top5_receita)


# =============================================================================
# 5. ANÁLISE TEMPORAL
# =============================================================================
titulo("5. ANÁLISE TEMPORAL")

pedidos_tratado["Data"] = pd.to_datetime(pedidos_tratado["Data"], format="%Y-%m-%d")
pedidos_tratado["Mes"] = pedidos_tratado["Data"].dt.month
# Os dados cobrem de 2023 a 2025: agrupar só pelo número do mês juntaria, por
# exemplo, Jan/2023, Jan/2024 e Jan/2025. Para a evolução no tempo usamos ano-mês.
pedidos_tratado["Ano_Mes"] = pedidos_tratado["Data"].dt.to_period("M")

data_inicial = pedidos_tratado["Data"].min()
data_final = pedidos_tratado["Data"].max()
print(f"Período analisado: {data_inicial:%d/%m/%Y} a {data_final:%d/%m/%Y}")

# Evolução mês a mês. Com ~13 pedidos por mês a receita oscila muito de um mês
# para o outro, então a média móvel de 3 meses ajuda a enxergar a tendência.
evolucao_mensal = pedidos_tratado.groupby("Ano_Mes").agg(
    Receita=("Receita_Item", "sum"), Pedidos=("ID_Pedido", "count")
)
evolucao_mensal["Variacao_%"] = evolucao_mensal["Receita"].pct_change() * 100
evolucao_mensal["Media_Movel_3M"] = evolucao_mensal["Receita"].rolling(3).mean()
print("\nReceita total por mês (ano-mês):")
print(evolucao_mensal)

mes_maior_receita = evolucao_mensal["Receita"].idxmax()
mes_menor_receita = evolucao_mensal["Receita"].idxmin()
print(f"\nMês de maior receita: {formatar_ano_mes(mes_maior_receita)} "
      f"({formatar_moeda(evolucao_mensal.loc[mes_maior_receita, 'Receita'])})")
print(f"Mês de menor receita: {formatar_ano_mes(mes_menor_receita)} "
      f"({formatar_moeda(evolucao_mensal.loc[mes_menor_receita, 'Receita'])})")

# Receita por ano. O último ano não está completo, então a comparação justa
# entre os anos é feita no mesmo intervalo de meses (Jan até o último mês com dados).
ano_final = data_final.year
ultimo_mes = data_final.month
pedidos_tratado["Ano"] = pedidos_tratado["Data"].dt.year
receita_por_ano = pedidos_tratado.groupby("Ano")["Receita_Item"].sum()
receita_mesmo_periodo = (
    pedidos_tratado[pedidos_tratado["Mes"] <= ultimo_mes]
    .groupby("Ano")["Receita_Item"].sum()
)
comparacao_anual = pd.DataFrame({
    "Receita_Ano": receita_por_ano,
    f"Receita_Jan_a_{NOMES_MESES[ultimo_mes]}": receita_mesmo_periodo,
})
comparacao_anual["Variacao_%_Mesmo_Periodo"] = receita_mesmo_periodo.pct_change() * 100
print(f"\nReceita por ano ({ano_final} contém dados só até {NOMES_MESES[ultimo_mes]}):")
print(comparacao_anual)

# Sazonalidade (só o número do mês). Os meses depois do último mês com dados
# aparecem em um ano a menos, então a soma favoreceria os demais meses; por isso
# a comparação usa a receita média por ocorrência do mês.
sazonalidade = evolucao_mensal.groupby(evolucao_mensal.index.month).agg(
    Receita_Total=("Receita", "sum"),
    Receita_Media=("Receita", "mean"),
    Anos_Com_Dados=("Receita", "count"),
)
sazonalidade.index = sazonalidade.index.map(NOMES_MESES)
sazonalidade.index.name = "Mes"
print("\nSazonalidade (agrupado só pelo número do mês):")
print(sazonalidade)

mes_sazonal_lider = sazonalidade["Receita_Media"].idxmax()
mes_sazonal_fraco = sazonalidade["Receita_Media"].idxmin()
print(f"\nMês do ano com maior receita média: {mes_sazonal_lider} "
      f"({formatar_moeda(sazonalidade.loc[mes_sazonal_lider, 'Receita_Media'])})")
print(f"Mês do ano com menor receita média: {mes_sazonal_fraco} "
      f"({formatar_moeda(sazonalidade.loc[mes_sazonal_fraco, 'Receita_Media'])})")


# =============================================================================
# 6. INTEGRAÇÃO DE DADOS (MERGE)
# =============================================================================
titulo("6. INTEGRAÇÃO DE DADOS (MERGE)")

cardapio = pd.read_csv(CAMINHO_CARDAPIO)
print("Cardápio:")
print(cardapio)

# how="left" mantém todos os pedidos. validate="many_to_one" garante que cada
# Item aparece uma única vez no cardápio, o que impede o merge de duplicar pedidos.
pedidos_completo = pedidos_tratado.merge(cardapio, on="Item", how="left", validate="many_to_one")

# Validação do merge: mesmo número de linhas, nenhum pedido sem categoria e
# receita total preservada
linhas_antes_merge = len(pedidos_tratado)
linhas_depois_merge = len(pedidos_completo)
categorias_nulas = pedidos_completo["Categoria"].isnull().sum()
print("\nValidação do merge:")
print(f"  Linhas antes do merge:  {linhas_antes_merge}")
print(f"  Linhas depois do merge: {linhas_depois_merge}")
print(f"  Pedidos sem Categoria:  {categorias_nulas}")
assert linhas_depois_merge == linhas_antes_merge, "O merge alterou o número de linhas"
assert categorias_nulas == 0, "Há pedidos com item que não existe no cardápio"
assert np.isclose(pedidos_completo["Receita_Item"].sum(), pedidos_tratado["Receita_Item"].sum()), \
    "O merge alterou a receita total"
print("  Merge validado: nenhuma linha perdida ou duplicada e todos os itens com categoria.")

receita_por_categoria = (
    pedidos_completo.groupby("Categoria")
    .agg(Receita_Total=("Receita_Item", "sum"), Pedidos=("ID_Pedido", "count"))
    .sort_values("Receita_Total", ascending=False)
)
receita_por_categoria["Participacao_%"] = (
    receita_por_categoria["Receita_Total"] / receita_por_categoria["Receita_Total"].sum() * 100
)
print("\nReceita total por categoria:")
print(receita_por_categoria)

categoria_lider = receita_por_categoria["Receita_Total"].idxmax()
print(f"\nCategoria que mais gera receita: {categoria_lider} "
      f"({formatar_moeda(receita_por_categoria.loc[categoria_lider, 'Receita_Total'])}, "
      f"{receita_por_categoria.loc[categoria_lider, 'Participacao_%']:.1f}% do total)")


# =============================================================================
# 7. FILTROS E CONSULTAS
# =============================================================================
titulo("7. FILTROS E CONSULTAS")

salgados_acima_10 = pedidos_completo[
    (pedidos_completo["Categoria"] == "Salgados") & (pedidos_completo["Quantidade"] > 10)
].copy()

# Pedidos com Quantidade preenchida pela média (> 10) também entram no filtro
salgados_preenchidos = salgados_acima_10["ID_Pedido"].isin(ids_quantidade_preenchida).sum()

print("Pedidos da categoria Salgados com Quantidade > 10:")
colunas_exibidas = ["ID_Pedido", "Data", "Cliente_ID", "Item", "Quantidade", "Preco_Unitario", "Receita_Item"]
print(salgados_acima_10.sort_values("Data")[colunas_exibidas].to_string(index=False))
print(f"\nTotal de pedidos encontrados: {len(salgados_acima_10)} "
      f"({salgados_preenchidos} com Quantidade preenchida pela média)")
print(f"Receita desses pedidos: {formatar_moeda(salgados_acima_10['Receita_Item'].sum())}")


# =============================================================================
# 8. KPIs COM NUMPY
# =============================================================================
titulo("8. KPIs COM NUMPY")

receitas = pedidos_completo["Receita_Item"].to_numpy()
quantidades = pedidos_completo["Quantidade"].to_numpy()
ids_pedidos = pedidos_completo["ID_Pedido"].to_numpy()

receita_total = np.sum(receitas)
total_itens_vendidos = np.sum(quantidades)
numero_pedidos = np.unique(ids_pedidos).size
ticket_medio = receita_total / numero_pedidos

# Conferência: como cada linha é um pedido, o ticket médio deve ser igual à
# média da receita por linha
assert np.isclose(ticket_medio, np.mean(receitas)), "Ticket médio inconsistente"

print(f"Receita Total:           {formatar_moeda(receita_total)}")
# O total não é inteiro porque as quantidades ausentes foram preenchidas com a média
print(f"Total de Itens Vendidos: {total_itens_vendidos:,.2f}")
print(f"Número de Pedidos:       {numero_pedidos}")
print(f"Ticket Médio:            {formatar_moeda(ticket_medio)}")


# =============================================================================
# DESAFIO EXTRA: PERCENTIS COM NUMPY
# =============================================================================
titulo("DESAFIO EXTRA: PERCENTIS (25%, 50%, 75%)")

percentis = [25, 50, 75]
tabela_percentis = pd.DataFrame(
    {
        coluna: np.percentile(pedidos_completo[coluna].to_numpy(), percentis)
        for coluna in ["Preco_Unitario", "Quantidade"]
    },
    index=[f"P{p}" for p in percentis],
)
print(tabela_percentis)


# =============================================================================
# RESUMO: PRINCIPAIS INSIGHTS
# =============================================================================
titulo("RESUMO: PRINCIPAIS INSIGHTS")

item_mais_vendido = top5_quantidade.index[0]
item_maior_receita = top5_receita.index[0]

print("Itens líderes")
print(f"  - Mais vendido em quantidade: {item_mais_vendido} "
      f"({top5_quantidade.loc[item_mais_vendido, 'Quantidade_Total']:,.0f} unidades)")
print(f"  - Maior receita: {item_maior_receita} "
      f"({formatar_moeda(top5_receita.loc[item_maior_receita, 'Receita_Total'])})")
print(f"  - Top 5 em quantidade: {', '.join(top5_quantidade.index)}")
print(f"  - Top 5 em receita:    {', '.join(top5_receita.index)}")

print("\nCategoria líder")
print(f"  - {categoria_lider}: {formatar_moeda(receita_por_categoria.loc[categoria_lider, 'Receita_Total'])} "
      f"({receita_por_categoria.loc[categoria_lider, 'Participacao_%']:.1f}% da receita)")
print(f"  - Ranking: {' > '.join(receita_por_categoria.index)}")

print("\nEvolução temporal")
print(f"  - Mês de maior receita: {formatar_ano_mes(mes_maior_receita)} "
      f"({formatar_moeda(evolucao_mensal.loc[mes_maior_receita, 'Receita'])})")
print(f"  - Mês de menor receita: {formatar_ano_mes(mes_menor_receita)} "
      f"({formatar_moeda(evolucao_mensal.loc[mes_menor_receita, 'Receita'])})")
print(f"  - Sazonalidade: {mes_sazonal_lider} tem a maior receita média e "
      f"{mes_sazonal_fraco} a menor")
periodo_comparado = f"Jan a {NOMES_MESES[ultimo_mes]}"
receitas_periodo = ", ".join(
    f"{ano}: {formatar_moeda(valor)}" for ano, valor in receita_mesmo_periodo.items()
)
print(f"  - Receita de {periodo_comparado} por ano: {receitas_periodo}")

print("\nKPIs")
print(f"  - Receita Total:           {formatar_moeda(receita_total)}")
print(f"  - Total de Itens Vendidos: {total_itens_vendidos:,.2f}")
print(f"  - Ticket Médio:            {formatar_moeda(ticket_medio)} ({numero_pedidos} pedidos)")

print("\nTratamento dos dados")
print(f"  - {linhas_removidas} pedidos removidos por falta de preço; "
      f"{len(ids_quantidade_preenchida)} quantidades preenchidas com a média ({media_quantidade:.2f})")
