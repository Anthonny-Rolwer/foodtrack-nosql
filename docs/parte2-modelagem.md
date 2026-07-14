# Parte 2 – Modelagem do Banco de Dados NoSQL

## 1. Hierarquia de Informações

A principal funcionalidade do sistema FoodTrack NoSQL é o gerenciamento de pedidos de pequenos restaurantes. Para atender essa funcionalidade, as informações são organizadas na seguinte hierarquia:

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

### Agregações

A coleção **Pedidos** é a principal do sistema. Nela, os itens do pedido são armazenados dentro do próprio documento, juntamente com informações do cliente, status, valor total e data do pedido. Essa agregação permite recuperar todas as informações necessárias em uma única consulta, reduzindo a necessidade de acessar diversas coleções.

---

## 2. Coleção Clientes

### Descrição

Armazena as informações cadastrais dos clientes que realizam pedidos no restaurante.

### Exemplo de documento

```json
{
  "_id": "C001",
  "nome": "João Silva",
  "telefone": "(34) 99999-9999",
  "endereco": {
    "rua": "Rua das Flores",
    "numero": 120,
    "bairro": "Centro",
    "cidade": "Uberlândia"
  }
}
```

---

## 3. Coleção Produtos

### Descrição

Armazena os produtos disponíveis no cardápio do restaurante.

### Exemplo de documento

```json
{
  "_id": "P001",
  "nome": "Hambúrguer Artesanal",
  "categoria": "Lanches",
  "preco": 25.90,
  "disponivel": true
}
```

---

## 4. Coleção Pedidos

### Descrição

Armazena os pedidos realizados pelos clientes. Cada documento contém as informações do cliente, os itens solicitados, o status do pedido, a data e o valor total.

### Exemplo de documento

```json
{
  "_id": "PED001",
  "cliente": {
    "id": "C001",
    "nome": "João Silva"
  },
  "itens": [
    {
      "produto": "Hambúrguer Artesanal",
      "quantidade": 2,
      "observacoes": "Sem cebola"
    },
    {
      "produto": "Refrigerante",
      "quantidade": 1
    }
  ],
  "status": "Em preparo",
  "valorTotal": 59.80,
  "dataPedido": "2026-07-14"
}
```
