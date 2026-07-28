from pathlib import Path
import os
import tomllib
from urllib.parse import urlparse

import redis
from redis.exceptions import RedisError


def carregar_redis_url() -> str:
    """
    Carrega a URL de conexão do Redis.

    Prioridade:
    1. Variável de ambiente REDIS_URL;
    2. Arquivo .streamlit/secrets.toml.
    """

    url_ambiente = os.getenv("REDIS_URL")

    if url_ambiente:
        return url_ambiente.strip()

    raiz_projeto = Path(__file__).resolve().parent.parent

    caminho_secrets = (
        raiz_projeto
        / ".streamlit"
        / "secrets.toml"
    )

    if not caminho_secrets.exists():
        raise FileNotFoundError(
            "O arquivo .streamlit/secrets.toml não foi encontrado.\n"
            f"Caminho esperado: {caminho_secrets}"
        )

    try:
        with caminho_secrets.open("rb") as arquivo:
            secrets = tomllib.load(arquivo)

    except tomllib.TOMLDecodeError as erro:
        raise ValueError(
            "O arquivo .streamlit/secrets.toml possui uma sintaxe inválida.\n"
            "Confirme se os textos estão entre aspas e se foi usado '='.\n"
            f"Detalhes: {erro}"
        ) from erro

    redis_url = secrets.get("REDIS_URL")

    if not redis_url:
        raise KeyError(
            'A chave REDIS_URL não foi encontrada em '
            '.streamlit/secrets.toml.'
        )

    if not isinstance(redis_url, str):
        raise TypeError(
            "REDIS_URL deve ser um texto entre aspas."
        )

    redis_url = redis_url.strip()

    if redis_url.startswith("redis-cli"):
        raise ValueError(
            "REDIS_URL não pode conter o comando 'redis-cli -u'. "
            "Informe somente a URL iniciada por redis:// ou rediss://."
        )

    url_analisada = urlparse(redis_url)

    if url_analisada.scheme not in {"redis", "rediss"}:
        raise ValueError(
            "REDIS_URL deve começar com redis:// ou rediss://."
        )

    if not url_analisada.hostname:
        raise ValueError(
            "O host não foi encontrado na REDIS_URL."
        )

    if not url_analisada.port:
        raise ValueError(
            "A porta não foi encontrada na REDIS_URL."
        )

    return redis_url


REDIS_URL = carregar_redis_url()

redis_client = redis.Redis.from_url(
    REDIS_URL,
    decode_responses=True,
    socket_connect_timeout=20,
    socket_timeout=20,
    health_check_interval=30,
)


def testar_conexao() -> bool:
    """Testa a conexão com o Redis."""

    try:
        resposta = redis_client.ping()

        if resposta:
            print("Redis conectado com sucesso!")

        return bool(resposta)

    except RedisError as erro:
        print("Erro ao conectar ao Redis.")
        print(f"Detalhes: {erro}")
        return False