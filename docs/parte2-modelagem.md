FoodTrack NoSQL
│
├── Clientes
│     ├── Nome
│     ├── Telefone
│     └── Endereço
│
├── Produtos
│     ├── Nome
│     ├── Categoria
│     └── Preço
│
└── Pedidos
      ├── Cliente
      ├── Itens
      │      ├── Produto
      │      ├── Quantidade
      │      └── Observações
      ├── Status
      ├── Valor Total
      └── Data do Pedido
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
{
  "_id": "P001",
  "nome": "Hambúrguer Artesanal",
  "categoria": "Lanches",
  "preco": 25.90,
  "disponivel": true
}
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
