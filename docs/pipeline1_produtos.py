from pprint import pprint

from utils.mongodb import (
    pedidos_collection,
    db,
)


pipeline_produtos = [
    # 1. Considera somente pedidos que possuem itens.
    {
        "$match": {
            "itens": {
                "$exists": True,
                "$ne": [],
            },
            "status": {
                "$ne": "Cancelado",
            },
        }
    },

    # 2. Transforma cada item do array em um documento.
    {
        "$unwind": "$itens"
    },

    # 3. Agrupa as vendas pelo produto.
    {
        "$group": {
            "_id": {
                "produto_id": "$itens.produto_id",
                "nome": {
                    "$ifNull": [
                        "$itens.nome",
                        "$itens.produto",
                    ]
                },
            },

            "quantidade_vendida": {
                "$sum": "$itens.quantidade"
            },

            "faturamento_total": {
                "$sum": {
                    "$ifNull": [
                        "$itens.subtotal",
                        {
                            "$multiply": [
                                {
                                    "$ifNull": [
                                        "$itens.preco_unitario",
                                        0,
                                    ]
                                },
                                "$itens.quantidade",
                            ]
                        },
                    ]
                }
            },

            "preco_medio": {
                "$avg": {
                    "$ifNull": [
                        "$itens.preco_unitario",
                        0,
                    ]
                }
            },

            "pedidos": {
                "$addToSet": "$_id"
            },
        }
    },

    # 4. Cria campos calculados.
    {
        "$set": {
            "quantidade_pedidos": {
                "$size": "$pedidos"
            },

            "ticket_medio_por_item": {
                "$cond": [
                    {
                        "$gt": [
                            "$quantidade_vendida",
                            0,
                        ]
                    },
                    {
                        "$divide": [
                            "$faturamento_total",
                            "$quantidade_vendida",
                        ]
                    },
                    0,
                ]
            },
        }
    },

    # 5. Ordena do maior para o menor faturamento.
    {
        "$sort": {
            "faturamento_total": -1,
            "quantidade_vendida": -1,
        }
    },

    # 6. Seleciona e renomeia os campos da saída.
    {
        "$project": {
            "_id": 0,
            "produto_id": "$_id.produto_id",
            "produto": "$_id.nome",
            "quantidade_vendida": 1,
            "quantidade_pedidos": 1,

            "preco_medio": {
                "$round": [
                    "$preco_medio",
                    2,
                ]
            },

            "faturamento_total": {
                "$round": [
                    "$faturamento_total",
                    2,
                ]
            },

            "ticket_medio_por_item": {
                "$round": [
                    "$ticket_medio_por_item",
                    2,
                ]
            },

            "data_atualizacao": "$$NOW",
        }
    },

    # 7. Salva o resultado em uma coleção de relatório.
    {
        "$merge": {
            "into": "relatorio_produtos",
            "on": "produto_id",
            "whenMatched": "replace",
            "whenNotMatched": "insert",
        }
    },
]


print("=" * 60)
print("PIPELINE 1 - RANKING DE PRODUTOS")
print("=" * 60)

relatorio_collection = db["relatorio_produtos"]

relatorio_collection.create_index(
    "produto_id",
    unique=True,
)

# Executa o pipeline e grava em relatorio_produtos.
list(
    pedidos_collection.aggregate(
        pipeline_produtos
    )
)

resultados = list(
    relatorio_collection.find(
        {},
        {
            "_id": 0,
        },
    ).sort(
        "faturamento_total",
        -1,
    )
)

if not resultados:
    print(
        "Nenhum resultado encontrado. "
        "Verifique se existem pedidos com itens cadastrados."
    )

else:
    print(
        f"Produtos encontrados: {len(resultados)}\n"
    )

    for posicao, produto in enumerate(
        resultados,
        start=1,
    ):
        print(f"{posicao}º lugar")

        pprint(produto)

        print("-" * 60)

