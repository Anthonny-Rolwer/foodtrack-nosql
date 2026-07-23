import json

from utils.redis_connection import (
    redis_client,
    testar_conexao,
)


CHAVE_FILA = "foodtrack:fila_cozinha"


def adicionar_pedido(
    pedido_id: str,
    cliente: str,
    itens: list[str],
) -> None:
    """
    Adiciona um pedido ao final da fila da cozinha.
    """

    pedido = {
        "pedido_id": pedido_id,
        "cliente": cliente,
        "itens": itens,
        "status": "Aguardando preparo",
    }

    redis_client.rpush(
        CHAVE_FILA,
        json.dumps(
            pedido,
            ensure_ascii=False,
        ),
    )


def listar_fila() -> list[dict]:
    """
    Recupera todos os pedidos, respeitando a ordem da fila.
    """

    registros = redis_client.lrange(
        CHAVE_FILA,
        0,
        -1,
    )

    return [
        json.loads(registro)
        for registro in registros
    ]


def atender_proximo_pedido() -> dict | None:
    """
    Remove e retorna o primeiro pedido da fila.
    """

    registro = redis_client.lpop(CHAVE_FILA)

    if registro is None:
        return None

    return json.loads(registro)


if __name__ == "__main__":
    if not testar_conexao():
        raise SystemExit("Não foi possível acessar o Redis.")

    # Limpa apenas a chave usada por esta demonstração.
    redis_client.delete(CHAVE_FILA)

    adicionar_pedido(
        pedido_id="PED001",
        cliente="João Silva",
        itens=[
            "2x Hambúrguer Artesanal",
            "1x Refrigerante",
        ],
    )

    adicionar_pedido(
        pedido_id="PED002",
        cliente="Maria Oliveira",
        itens=[
            "1x Pizza Calabresa",
        ],
    )

    adicionar_pedido(
        pedido_id="PED003",
        cliente="Carlos Souza",
        itens=[
            "1x Batata Frita",
            "2x Refrigerante",
        ],
    )

    print("=" * 60)
    print("REDIS LIST — FILA DA COZINHA")
    print("=" * 60)

    print("\nPedidos aguardando preparo:")

    for posicao, pedido in enumerate(
        listar_fila(),
        start=1,
    ):
        print(
            f"{posicao}. {pedido['pedido_id']} — "
            f"{pedido['cliente']} — "
            f"{', '.join(pedido['itens'])}"
        )

    proximo = atender_proximo_pedido()

    print("\nPróximo pedido retirado da fila:")
    print(proximo)

    print("\nFila após o atendimento:")

    for posicao, pedido in enumerate(
        listar_fila(),
        start=1,
    ):
        print(
            f"{posicao}. {pedido['pedido_id']} — "
            f"{pedido['cliente']}"
        )