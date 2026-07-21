# Parte 2 — Modelagem NoSQL do Sistema FoodTrack

## 1. Hierarquia de informações e agregações

O FoodTrack é um sistema de gerenciamento de pedidos para estabelecimentos alimentícios, tendo como principal funcionalidade permitir o cadastro de clientes, produtos e gerenciamento de pedidos.

A hierarquia de informações do sistema foi definida considerando a forma como os dados serão utilizados no MongoDB, utilizando documentos e coleções independentes, com referências entre documentos quando necessário.

A estrutura principal é:

```
Cliente
   |
   └── Pedidos
          |
          └── Itens do Pedido
                    |
                    └── Produtos
```

### Coleções principais:

```
foodtrack

├── clientes
│
├── produtos
│
└── pedidos
```
```
FoodTrack NoSQL
│
├── Clientes
│   ├── Nome
│   ├── Telefone
│   └── Endereço
│
├── Produtos
│   ├── Nome
│   ├── Categoria
│   ├── Preço
│   └── Disponibilidade
│
└── Pedidos
    ├── Cliente
    ├── Itens
    │   ├── Produto
    │   ├── Quantidade
    │   └── Observações
    ├── Status
    ├── Valor Total
    └── Data do Pedido
```
---

# Coleção clientes

A coleção `clientes` armazena as informações dos consumidores que realizam pedidos no sistema.

Cada cliente possui seus dados básicos de identificação, permitindo consultas, atualizações e associação com seus pedidos realizados.

## Exemplo de documento:

```json
{
  "_id": "65abc123",
  "nome": "João Silva",
  "telefone": "(34) 99999-9999",
  "endereco": "Uberlândia - MG",
  "data_cadastro": "2026-07-20"
}
```

---

# Coleção produtos

A coleção `produtos` representa o catálogo de produtos disponibilizados pelo estabelecimento.

Os produtos são cadastrados previamente para que possam ser selecionados durante a criação dos pedidos.

São armazenadas informações como nome, categoria, preço e tamanho da porção.

## Exemplo de documento:

```json
{
  "_id": "789xyz",
  "nome": "Hambúrguer Artesanal",
  "tipo": "Lanche",
  "preco": 25.90,
  "porcao": "Individual",
  "disponivel": true
}
```

---

# Coleção pedidos

A coleção `pedidos` armazena as informações das compras realizadas pelos clientes.

Cada pedido possui uma referência ao cliente responsável e contém uma lista de produtos adquiridos.

A estrutura utiliza documentos embutidos para armazenar os itens do pedido, característica comum em bancos NoSQL, permitindo que as informações importantes da compra estejam agrupadas em um único documento.

## Exemplo de documento:

```json
{
  "_id": "pedido001",

  "cliente_id": "65abc123",

  "itens": [
    {
      "produto_id": "789xyz",
      "nome": "Hambúrguer Artesanal",
      "quantidade": 2,
      "preco_unitario": 25.90
    }
  ],

  "valor_total": 51.80,
  "status": "Em preparo",
  "data_pedido": "2026-07-20"
}
```

---

# Justificativa da modelagem NoSQL

A modelagem foi desenvolvida utilizando conceitos de bancos de dados NoSQL orientados a documentos.

Diferente de bancos relacionais tradicionais, onde normalmente seriam utilizadas várias tabelas relacionadas, o MongoDB permite armazenar informações relacionadas dentro de documentos.

No FoodTrack foi utilizada uma abordagem híbrida:

* Referências entre documentos para relacionar pedidos aos clientes e produtos;
* Documentos embutidos para armazenar os itens pertencentes a cada pedido.

Essa estrutura facilita consultas frequentes, como:

* Buscar todos os pedidos de um cliente;
* Consultar detalhes de um pedido específico;
* Registrar uma venda mantendo o histórico dos produtos adquiridos.

---

# Principais agregações do sistema

## Agregação de clientes

Permite:

* Cadastro de novos clientes;
* Atualização de informações;
* Consulta dos dados do cliente;
* Visualização do histórico de pedidos.

---

## Agregação de produtos

Permite:

* Cadastro do cardápio;
* Atualização de preços;
* Controle de disponibilidade;
* Seleção dos produtos durante um pedido.

---

## Agregação de pedidos

Permite:

* Criar novos pedidos;
* Vincular pedidos aos clientes;
* Adicionar produtos cadastrados;
* Atualizar status do pedido;
* Consultar histórico de vendas.

---

# Fluxo principal do sistema

1. O estabelecimento cadastra seus produtos no sistema.
2. Um cliente é cadastrado ou localizado na base de dados.
3. Um novo pedido é criado selecionando o cliente e os produtos desejados.
4. O pedido é armazenado no MongoDB contendo as informações necessárias para consulta futura.
5. O sistema permite acompanhar e atualizar o status do pedido.

```
```
