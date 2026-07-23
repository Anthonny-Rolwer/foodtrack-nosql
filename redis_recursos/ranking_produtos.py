from utils.redis_connection import (
    redis_client,
    testar_conexao,
)


CHAVE_RANKING = "foodtrack:ranking_produtos"


def registrar_venda(
    produto: str,
    quantidade: int,
) -> None:
    """
    Incrementa a pontuação do produto no ranking.
    """

    redis_client.zincrby(
        CHAVE_RANKING,
        quantidade,
        produto,
    )


def consultar_ranking() -> list[tuple[str, float]]:
    """
    Retorna os produtos do maior para o menor número vendido.
    """

    return redis_client.zrevrange(
        CHAVE_RANKING,
        0,
        -1,
        withscores=True,
    )


if __name__ == "__main__":
    if not testar_conexao():
        raise SystemExit("Não foi possível acessar o Redis.")

    redis_client.delete(CHAVE_RANKING)

    registrar_venda(
        "Hambúrguer Artesanal",
        4,
    )

    registrar_venda(
        "Refrigerante",
        7,
    )

    registrar_venda(
        "Pizza Calabresa",
        3,
    )

    registrar_venda(
        "Batata Frita",
        5,
    )

    # Uma nova venda incrementa o valor anterior.
    registrar_venda(
        "Hambúrguer Artesanal",
        2,
    )

    print("=" * 60)
    print("REDIS SORTED SET — RANKING DE PRODUTOS")
    print("=" * 60)

    for posicao, resultado in enumerate(
        consultar_ranking(),
        start=1,
    ):
        produto, quantidade = resultado

        print(
            f"{posicao}º — {produto}: "
            f"{int(quantidade)} unidade(s)"
        )