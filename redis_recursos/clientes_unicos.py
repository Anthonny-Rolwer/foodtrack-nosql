from datetime import date

from utils.redis_connection import (
    redis_client,
    testar_conexao,
)


DATA_ATUAL = date.today().isoformat()

CHAVE_CLIENTES = (
    f"foodtrack:clientes_unicos:{DATA_ATUAL}"
)


def registrar_cliente(cliente_id: str) -> None:
    """
    Registra um cliente no HyperLogLog.
    Registros repetidos não aumentam a estimativa.
    """

    redis_client.pfadd(
        CHAVE_CLIENTES,
        cliente_id,
    )


def estimar_clientes_unicos() -> int:
    """
    Retorna a estimativa de clientes únicos.
    """

    return redis_client.pfcount(
        CHAVE_CLIENTES
    )


if __name__ == "__main__":
    if not testar_conexao():
        raise SystemExit("Não foi possível acessar o Redis.")

    redis_client.delete(CHAVE_CLIENTES)

    clientes = [
        "cliente-001",
        "cliente-002",
        "cliente-003",
        "cliente-001",
        "cliente-002",
        "cliente-004",
    ]

    print("=" * 60)
    print("REDIS HYPERLOGLOG — CLIENTES ÚNICOS")
    print("=" * 60)

    print("\nRegistros recebidos:")

    for cliente_id in clientes:
        registrar_cliente(cliente_id)
        print(f"- {cliente_id}")

    estimativa = estimar_clientes_unicos()

    print(
        "\nQuantidade total de registros recebidos:",
        len(clientes),
    )

    print(
        "Estimativa de clientes únicos:",
        estimativa,
    )

    print(
        "\nOs identificadores repetidos não aumentam "
        "a estimativa de clientes únicos."
    )