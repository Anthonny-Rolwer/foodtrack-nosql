from pprint import pprint

from utils.mongodb import (
    clientes_collection,
    db,
)


pipeline_clientes = [
    # 1. Relaciona clientes aos seus pedidos.
    {
        "$lookup": {
            "from": "pedidos",
            "localField": "_id",
            "foreignField": "cliente_id",
            "as": "pedidos_cliente",
        }
    },

    # 2. Separa os pedidos encontrados.
    {
        "$unwind": {
            "path": "$pedidos_cliente",
            "preserveNullAndEmptyArrays": False,
        }
    },

    # 3. Remove pedidos cancelados.
    {
        "$match": {
            "pedidos_cliente.status": {
                "$ne": "Cancelado",
            }
        }
    },

    # 4. Agrupa os dados por cliente.
    {
        "$group": {
            "_id": "$_id",

            "nome": {
                "$first": "$nome"
            },

            "telefone": {
                "$first": "$telefone"
            },

            "endereco": {
                "$first": "$endereco"
            },

            "quantidade_pedidos": {
                "$sum": 1
            },

            "total_gasto": {
                "$sum": {
                    "$ifNull": [
                        "$pedidos_cliente.valor_total",
                        {
                            "$ifNull": [
                                "$pedidos_cliente.valorTotal",
                                0,
                            ]
                        },
                    ]
                }
            },

            "ultimo_pedido": {
                "$max": "$pedidos_cliente.data_pedido"
            },
        }
    },

    # 5. Cria ticket médio e classificação.
    {
        "$set": {
            "ticket_medio": {
                "$cond": [
                    {
                        "$gt": [
                            "$quantidade_pedidos",
                            0,
                        ]
                    },
                    {
                        "$divide": [
                            "$total_gasto",
                            "$quantidade_pedidos",
                        ]
                    },
                    0,
                ]
            },

            "classificacao": {
                "$switch": {
                    "branches": [
                        {
                            "case": {
                                "$gte": [
                                    "$total_gasto",
                                    200,
                                ]
                            },
                            "then": "Cliente VIP",
                        },
                        {
                            "case": {
                                "$gte": [
                                    "$total_gasto",
                                    100,
                                ]
                            },
                            "then": "Cliente frequente",
                        },
                    ],
                    "default": "Cliente regular",
                }
            },
        }
    },

    # 6. Mantém clientes que atendem à campanha.
    {
        "$match": {
            "quantidade_pedidos": {
                "$gte": 1,
            },
            "total_gasto": {
                "$gt": 0,
            },
        }
    },

    # 7. Organiza antes da seleção.
    {
        "$sort": {
            "total_gasto": -1,
            "quantidade_pedidos": -1,
        }
    },

    # 8. Seleciona uma amostra aleatória.
    {
        "$sample": {
            "size": 3,
        }
    },

    # 9. Define os campos da saída.
    {
        "$project": {
            "_id": 0,
            "cliente_id": "$_id",
            "nome": 1,
            "telefone": 1,
            "endereco": 1,
            "quantidade_pedidos": 1,

            "total_gasto": {
                "$round": [
                    "$total_gasto",
                    2,
                ]
            },

            "ticket_medio": {
                "$round": [
                    "$ticket_medio",
                    2,
                ]
            },

            "ultimo_pedido": 1,
            "classificacao": 1,
            "selecionado_em": "$$NOW",
        }
    },

    # 10. Grava a amostra em uma nova coleção.
    {
        "$merge": {
            "into": "campanha_clientes",
            "on": "cliente_id",
            "whenMatched": "replace",
            "whenNotMatched": "insert",
        }
    },
]


print("=" * 60)
print("PIPELINE 2 - CLIENTES PARA CAMPANHA")
print("=" * 60)

campanha_collection = db["campanha_clientes"]

campanha_collection.create_index(
    "cliente_id",
    unique=True,
)

# Limpa a seleção anterior para que a coleção represente
# somente a amostra da execução atual.
campanha_collection.delete_many({})

list(
    clientes_collection.aggregate(
        pipeline_clientes
    )
)

resultados = list(
    campanha_collection.find(
        {},
        {
            "_id": 0,
        },
    ).sort(
        "total_gasto",
        -1,
    )
)

if not resultados:
    print(
        "Nenhum cliente elegível foi encontrado. "
        "Cadastre pedidos válidos antes de executar."
    )

else:
    print(
        f"Clientes selecionados: {len(resultados)}\n"
    )

    for posicao, cliente in enumerate(
        resultados,
        start=1,
    ):
        print(f"Cliente selecionado {posicao}")

        pprint(cliente)

        print("-" * 60)