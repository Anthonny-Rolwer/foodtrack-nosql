# Etapa 4 — Aggregation Pipelines

Nesta etapa foram implementados dois pipelines de agregação no MongoDB para atender funcionalidades distintas do sistema FoodTrack.

Os pipelines utilizam operadores como:

- `$match`
- `$sort`
- `$lookup`
- `$project`
- `$unwind`
- `$group`
- `$set`
- `$sample`
- `$merge`

---

# Pipeline 1 — Ranking de produtos vendidos

## Funcionalidade

O primeiro pipeline gera um relatório dos produtos vendidos, permitindo identificar:

- produtos com maior quantidade vendida;
- faturamento total por produto;
- quantidade de pedidos em que o produto apareceu;
- preço médio;
- ticket médio por item.

O pipeline analisa os documentos da coleção `pedidos`, separa os itens de cada pedido e agrupa os resultados por produto.

## Coleção de origem

```text
pedidos
```

## Coleção de destino

```text
relatorio_produtos
```

## Etapas utilizadas

### `$match`

Seleciona somente pedidos que possuem itens e que não estejam cancelados.

### `$unwind`

Transforma cada item do array `itens` em um documento individual para que seja possível analisar os produtos separadamente.

### `$group`

Agrupa os itens pelo produto e calcula:

- quantidade vendida;
- faturamento total;
- preço médio;
- pedidos distintos.

### `$set`

Cria campos calculados, como quantidade de pedidos e ticket médio por item.

### `$sort`

Ordena os produtos pelo maior faturamento e pela quantidade vendida.

### `$project`

Seleciona, organiza e renomeia os campos que serão exibidos no relatório.

### `$merge`

Grava o resultado na coleção `relatorio_produtos`.

## Código principal

```python
pipeline_produtos = [
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
    {
        "$unwind": "$itens"
    },
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
    {
        "$sort": {
            "faturamento_total": -1,
            "quantidade_vendida": -1,
        }
    },
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
    {
        "$merge": {
            "into": "relatorio_produtos",
            "on": "produto_id",
            "whenMatched": "replace",
            "whenNotMatched": "insert",
        }
    },
]
```

## Resultado

O pipeline gera documentos semelhantes a:

```json
{
  "produto_id": "ObjectId(...)",
  "produto": "Hambúrguer Artesanal",
  "quantidade_vendida": 4,
  "quantidade_pedidos": 2,
  "preco_medio": 25.90,
  "faturamento_total": 103.60,
  "ticket_medio_por_item": 25.90,
  "data_atualizacao": "2026-07-21"
}
```

## Evidências

### Código

![Código do Pipeline 1](../imagens/aggregation/pipeline1-codigo.png)

### Saída no terminal

![Saída do Pipeline 1](../imagens/aggregation/pipeline1-saida-terminal.png)

### Coleção criada no MongoDB Atlas

![Coleção relatorio_produtos](../imagens/aggregation/pipeline1-colecao-relatorio.png)

---

# Pipeline 2 — Clientes para campanha promocional

## Funcionalidade

O segundo pipeline seleciona clientes para uma campanha promocional.

Ele relaciona clientes e pedidos, calcula o histórico de compras e seleciona aleatoriamente clientes elegíveis.

O pipeline permite analisar:

- quantidade de pedidos;
- total gasto;
- ticket médio;
- último pedido;
- classificação do cliente.

## Coleção de origem

```text
clientes
```

A coleção `pedidos` é relacionada utilizando `$lookup`.

## Coleção de destino

```text
campanha_clientes
```

## Etapas utilizadas

### `$lookup`

Relaciona cada cliente aos pedidos que possuem o mesmo `cliente_id`.

### `$unwind`

Transforma o array de pedidos em documentos separados.

### `$match`

Remove pedidos cancelados e mantém clientes que possuem pedidos válidos.

### `$group`

Agrupa os pedidos novamente por cliente e calcula quantidade de pedidos, total gasto e último pedido.

### `$set`

Calcula o ticket médio e atribui uma classificação ao cliente.

### `$sort`

Ordena os clientes por valor total gasto e quantidade de pedidos.

### `$sample`

Seleciona uma amostra aleatória de clientes para a campanha.

### `$project`

Seleciona e organiza os campos finais.

### `$merge`

Grava os clientes selecionados na coleção `campanha_clientes`.

## Código principal

```python
pipeline_clientes = [
    {
        "$lookup": {
            "from": "pedidos",
            "localField": "_id",
            "foreignField": "cliente_id",
            "as": "pedidos_cliente",
        }
    },
    {
        "$unwind": {
            "path": "$pedidos_cliente",
            "preserveNullAndEmptyArrays": False,
        }
    },
    {
        "$match": {
            "pedidos_cliente.status": {
                "$ne": "Cancelado",
            }
        }
    },
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
    {
        "$sort": {
            "total_gasto": -1,
            "quantidade_pedidos": -1,
        }
    },
    {
        "$sample": {
            "size": 3,
        }
    },
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
    {
        "$merge": {
            "into": "campanha_clientes",
            "on": "cliente_id",
            "whenMatched": "replace",
            "whenNotMatched": "insert",
        }
    },
]
```

## Resultado

O pipeline gera documentos semelhantes a:

```json
{
  "cliente_id": "ObjectId(...)",
  "nome": "João Silva",
  "telefone": "(34) 99999-9999",
  "endereco": "Uberlândia - MG",
  "quantidade_pedidos": 3,
  "total_gasto": 210.50,
  "ticket_medio": 70.17,
  "ultimo_pedido": "2026-07-21",
  "classificacao": "Cliente VIP",
  "selecionado_em": "2026-07-21"
}
```

## Evidências

### Código

![Código do Pipeline 2](../imagens/aggregation/pipeline2-codigo.png)

### Saída no terminal

![Saída do Pipeline 2](../imagens/aggregation/pipeline2-saida-terminal.png)

### Coleção criada no MongoDB Atlas

![Coleção campanha_clientes](../imagens/aggregation/pipeline2-colecao-campanha.png)

---

# Conclusão

Os dois pipelines implementam funcionalidades distintas do sistema FoodTrack.

O primeiro fornece informações gerenciais sobre o desempenho dos produtos, enquanto o segundo analisa o histórico de clientes e seleciona participantes para uma campanha promocional.

Dessa forma, os pipelines demonstram o uso de agregações no MongoDB para transformar dados operacionais em informações úteis para tomada de decisão.