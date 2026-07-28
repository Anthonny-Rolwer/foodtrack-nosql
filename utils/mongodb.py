from pathlib import Path
import os
import tomllib

from pymongo import MongoClient


def carregar_mongo_uri():
    """
    Carrega a URI por variável de ambiente ou pelo arquivo
    .streamlit/secrets.toml.

    Isso permite usar a conexão tanto no Streamlit quanto
    em scripts executados diretamente pelo terminal.
    """

    # Primeira opção: variável de ambiente
    uri_ambiente = os.getenv("MONGO_URI")

    if uri_ambiente:
        return uri_ambiente

    # Localiza a raiz do projeto:
    # mongodb.py está em foodtrack-nosql/utils/mongodb.py
    raiz_projeto = Path(__file__).resolve().parent.parent

    arquivo_secrets = (
        raiz_projeto
        / ".streamlit"
        / "secrets.toml"
    )

    if not arquivo_secrets.exists():
        raise FileNotFoundError(
            "O arquivo .streamlit/secrets.toml não foi encontrado. "
            f"Caminho procurado: {arquivo_secrets}"
        )

    with arquivo_secrets.open("rb") as arquivo:
        secrets = tomllib.load(arquivo)

    mongo_uri = secrets.get("MONGO_URI")

    if not mongo_uri:
        raise KeyError(
            'A chave MONGO_URI não foi encontrada em '
            '.streamlit/secrets.toml.'
        )

    return mongo_uri


MONGO_URI = carregar_mongo_uri()

client = MongoClient(
    MONGO_URI,
    serverSelectionTimeoutMS=10000,
)

# Força a verificação da conexão
client.admin.command("ping")
print("MongoDB conectado com sucesso!")

db = client["foodtrack"]

clientes_collection = db["clientes"]
produtos_collection = db["produtos"]
pedidos_collection = db["pedidos"]