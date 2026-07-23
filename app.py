import streamlit as st

import re
from datetime import datetime
from pymongo.errors import PyMongoError

from utils.mongodb import (
    clientes_collection,
    produtos_collection,
    pedidos_collection,
)

if "carrinho" not in st.session_state:
    st.session_state.carrinho = []

st.set_page_config(
    page_title="FoodTrack NoSQL",
    page_icon="🍔",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ==================================================
# MENU LATERAL PRINCIPAL
# ==================================================

st.sidebar.title("🍔 FoodTrack NoSQL")

pagina = st.sidebar.radio(
    "Menu principal",
    [
        "🏠 Início",
        "👥 Clientes",
        "🍔 Produtos",
        "📦 Pedidos",
    ],
)

st.sidebar.divider()
st.sidebar.caption("Banco de dados: MongoDB Atlas")


# ==================================================
# TELA INICIAL
# ==================================================

if pagina == "🏠 Início":
    st.title("🍔 FoodTrack NoSQL")
    st.subheader("Dashboard do sistema")

    st.write(
        """
        Acompanhe os principais indicadores de clientes, produtos
        e pedidos cadastrados no MongoDB Atlas.
        """
    )

    try:
        # ==========================================
        # INDICADORES PRINCIPAIS
        # ==========================================

        total_clientes = clientes_collection.count_documents({})

        total_produtos = produtos_collection.count_documents({})

        produtos_disponiveis = produtos_collection.count_documents(
            {"disponivel": True}
        )

        total_pedidos = pedidos_collection.count_documents({})

        # Considera documentos novos com valor_total
        # e documentos antigos com valorTotal.
        pipeline_faturamento = [
            {
                "$project": {
                    "valor_pedido": {
                        "$ifNull": [
                            "$valor_total",
                            {
                                "$ifNull": [
                                    "$valorTotal",
                                    0,
                                ]
                            },
                        ]
                    }
                }
            },
            {
                "$group": {
                    "_id": None,
                    "faturamento_total": {
                        "$sum": "$valor_pedido"
                    },
                    "ticket_medio": {
                        "$avg": "$valor_pedido"
                    },
                }
            },
        ]

        resultado_faturamento = list(
            pedidos_collection.aggregate(
                pipeline_faturamento
            )
        )

        if resultado_faturamento:
            faturamento_total = resultado_faturamento[0].get(
                "faturamento_total",
                0,
            )

            ticket_medio = resultado_faturamento[0].get(
                "ticket_medio",
                0,
            )
        else:
            faturamento_total = 0
            ticket_medio = 0

        # ==========================================
        # PRIMEIRA LINHA DE MÉTRICAS
        # ==========================================

        coluna1, coluna2, coluna3, coluna4 = st.columns(4)

        with coluna1:
            st.metric(
                label="👥 Clientes",
                value=total_clientes,
            )

        with coluna2:
            st.metric(
                label="🍔 Produtos",
                value=total_produtos,
            )

        with coluna3:
            st.metric(
                label="📦 Pedidos",
                value=total_pedidos,
            )

        with coluna4:
            st.metric(
                label="💰 Faturamento",
                value=f"R$ {faturamento_total:.2f}",
            )

        # ==========================================
        # SEGUNDA LINHA
        # ==========================================

        st.divider()

        coluna5, coluna6 = st.columns(2)

        with coluna5:
            st.metric(
                label="✅ Produtos disponíveis",
                value=produtos_disponiveis,
            )

        with coluna6:
            st.metric(
                label="🧾 Ticket médio",
                value=f"R$ {ticket_medio:.2f}",
            )

        # ==========================================
        # ÚLTIMOS PEDIDOS
        # ==========================================

        st.divider()
        st.subheader("📋 Pedidos recentes")

        pedidos_recentes = list(
            pedidos_collection.find()
            .sort("data_pedido", -1)
            .limit(5)
        )

        if not pedidos_recentes:
            st.info("Ainda não existem pedidos cadastrados.")

        else:
            tabela_recentes = []

            for pedido in pedidos_recentes:
                cliente_documento = pedido.get(
                    "cliente",
                    {},
                )

                if isinstance(cliente_documento, dict):
                    nome_cliente = cliente_documento.get(
                        "nome",
                        "Cliente não identificado",
                    )
                else:
                    nome_cliente = str(cliente_documento)

                valor = pedido.get(
                    "valor_total",
                    pedido.get("valorTotal", 0),
                )

                data_pedido = pedido.get(
                    "data_pedido",
                    "",
                )

                if isinstance(data_pedido, datetime):
                    data_formatada = data_pedido.strftime(
                        "%d/%m/%Y %H:%M"
                    )
                else:
                    data_formatada = str(data_pedido)

                tabela_recentes.append(
                    {
                        "Pedido": str(pedido["_id"])[-6:],
                        "Cliente": nome_cliente,
                        "Status": pedido.get(
                            "status",
                            "",
                        ),
                        "Valor": f"R$ {valor:.2f}",
                        "Data": data_formatada,
                    }
                )

            st.dataframe(
                tabela_recentes,
                use_container_width=True,
                hide_index=True,
            )

    except PyMongoError as erro:
        st.error(
            "Não foi possível carregar os indicadores "
            "do MongoDB Atlas."
        )

        st.code(str(erro))


# ==================================================
# CLIENTES
# ==================================================

elif pagina == "👥 Clientes":
    st.title("👥 Gerenciamento de Clientes")

    operacao_cliente = st.selectbox(
        "Escolha uma operação",
        [
            "Cadastrar cliente",
            "Consultar clientes",
            "Editar cliente",
            "Excluir cliente",
        ],
    )

    # ==============================================
    # INSERT — CADASTRAR CLIENTE
    # ==============================================

    if operacao_cliente == "Cadastrar cliente":
        st.subheader("Cadastrar novo cliente")

        with st.form(
            "form_cadastrar_cliente",
            clear_on_submit=True,
        ):
            nome = st.text_input(
                "Nome completo",
                placeholder="Exemplo: Carlos Souza",
            )

            telefone = st.text_input(
                "Telefone",
                placeholder="Exemplo: (34) 99999-9999",
            )

            endereco = st.text_input(
                "Endereço",
                placeholder="Exemplo: Uberlândia - MG",
            )

            salvar_cliente = st.form_submit_button(
                "Salvar cliente",
                type="primary",
            )

        if salvar_cliente:
            if not nome.strip():
                st.error("Informe o nome do cliente.")

            elif not telefone.strip():
                st.error("Informe o telefone do cliente.")

            else:
                cliente_existente = clientes_collection.find_one(
                    {"telefone": telefone.strip()}
                )

                if cliente_existente:
                    st.warning(
                        "Já existe um cliente cadastrado com esse telefone."
                    )

                else:
                    novo_cliente = {
                        "nome": nome.strip(),
                        "telefone": telefone.strip(),
                        "endereco": endereco.strip(),
                        "data_cadastro": datetime.now(),
                    }

                    resultado = clientes_collection.insert_one(
                        novo_cliente
                    )

                    if resultado.inserted_id:
                        st.success(
                            "Cliente cadastrado com sucesso!"
                        )

    # ==============================================
    # FIND — CONSULTAR CLIENTES
    # ==============================================

    elif operacao_cliente == "Consultar clientes":
        st.subheader("Clientes cadastrados")

        pesquisa = st.text_input(
            "Pesquisar cliente",
            placeholder="Digite parte do nome ou telefone",
        )

        filtro = {}

        if pesquisa.strip():
            termo_seguro = re.escape(pesquisa.strip())

            filtro = {
                "$or": [
                    {
                        "nome": {
                            "$regex": termo_seguro,
                            "$options": "i",
                        }
                    },
                    {
                        "telefone": {
                            "$regex": termo_seguro,
                            "$options": "i",
                        }
                    },
                ]
            }

        clientes = list(
            clientes_collection.find(filtro).sort("nome", 1)
        )

        if not clientes:
            st.info("Nenhum cliente encontrado.")

        else:
            dados_clientes = []

            for cliente in clientes:
                data_cadastro = cliente.get("data_cadastro", "")

                if isinstance(data_cadastro, datetime):
                    data_formatada = data_cadastro.strftime(
                        "%d/%m/%Y"
                    )
                else:
                    data_formatada = str(data_cadastro)[:10]

                dados_clientes.append(
                    {
                        "Nome": cliente.get("nome", ""),
                        "Telefone": cliente.get("telefone", ""),
                        "Endereço": cliente.get("endereco", ""),
                        "Data de cadastro": data_formatada,
                    }
                )

            st.dataframe(
                dados_clientes,
                use_container_width=True,
                hide_index=True,
            )

            st.caption(
                f"Total de clientes encontrados: {len(clientes)}"
            )

    # ==============================================
    # UPDATE — EDITAR CLIENTE
    # ==============================================

    elif operacao_cliente == "Editar cliente":
        st.subheader("Editar cliente")

        clientes = list(
            clientes_collection.find().sort("nome", 1)
        )

        if not clientes:
            st.info("Não existem clientes cadastrados.")

        else:
            opcoes_clientes = {
                (
                    f"{cliente.get('nome', '')} — "
                    f"{cliente.get('telefone', '')}"
                ): cliente
                for cliente in clientes
            }

            cliente_escolhido = st.selectbox(
                "Selecione o cliente",
                list(opcoes_clientes.keys()),
            )

            cliente = opcoes_clientes[cliente_escolhido]

            with st.form("form_editar_cliente"):
                novo_nome = st.text_input(
                    "Nome completo",
                    value=cliente.get("nome", ""),
                )

                novo_telefone = st.text_input(
                    "Telefone",
                    value=cliente.get("telefone", ""),
                )

                novo_endereco = st.text_input(
                    "Endereço",
                    value=cliente.get("endereco", ""),
                )

                salvar_alteracoes = st.form_submit_button(
                    "Salvar alterações",
                    type="primary",
                )

            if salvar_alteracoes:
                if not novo_nome.strip():
                    st.error("Informe o nome do cliente.")

                elif not novo_telefone.strip():
                    st.error("Informe o telefone do cliente.")

                else:
                    telefone_em_uso = clientes_collection.find_one(
                        {
                            "telefone": novo_telefone.strip(),
                            "_id": {"$ne": cliente["_id"]},
                        }
                    )

                    if telefone_em_uso:
                        st.warning(
                            "Esse telefone pertence a outro cliente."
                        )

                    else:
                        resultado = clientes_collection.update_one(
                            {"_id": cliente["_id"]},
                            {
                                "$set": {
                                    "nome": novo_nome.strip(),
                                    "telefone": novo_telefone.strip(),
                                    "endereco": novo_endereco.strip(),
                                    "data_atualizacao": datetime.now(),
                                }
                            },
                        )

                        if resultado.modified_count == 1:
                            st.success(
                                "Cliente atualizado com sucesso!"
                            )
                            st.rerun()

                        else:
                            st.info(
                                "Nenhuma informação foi alterada."
                            )

    # ==============================================
    # DELETE — EXCLUIR CLIENTE
    # ==============================================

    elif operacao_cliente == "Excluir cliente":
        st.subheader("Excluir cliente")

        clientes = list(
            clientes_collection.find().sort("nome", 1)
        )

        if not clientes:
            st.info("Não existem clientes cadastrados.")

        else:
            opcoes_clientes = {
                (
                    f"{cliente.get('nome', '')} — "
                    f"{cliente.get('telefone', '')}"
                ): cliente
                for cliente in clientes
            }

            cliente_escolhido = st.selectbox(
                "Selecione o cliente",
                list(opcoes_clientes.keys()),
            )

            cliente = opcoes_clientes[cliente_escolhido]

            quantidade_pedidos = pedidos_collection.count_documents(
                {"cliente_id": cliente["_id"]}
            )

            st.write(
                f"**Nome:** {cliente.get('nome', '')}"
            )

            st.write(
                f"**Telefone:** {cliente.get('telefone', '')}"
            )

            st.write(
                f"**Pedidos vinculados:** {quantidade_pedidos}"
            )

            if quantidade_pedidos > 0:
                st.error(
                    "Este cliente possui pedidos vinculados e não pode "
                    "ser excluído. Isso preserva o histórico das vendas."
                )

            else:
                st.warning(
                    "A exclusão removerá permanentemente o cliente "
                    "da coleção."
                )

                confirmar_exclusao = st.checkbox(
                    "Confirmo que desejo excluir este cliente"
                )

                if st.button(
                    "Excluir cliente",
                    type="primary",
                    disabled=not confirmar_exclusao,
                ):
                    resultado = clientes_collection.delete_one(
                        {"_id": cliente["_id"]}
                    )

                    if resultado.deleted_count == 1:
                        st.success(
                            "Cliente excluído com sucesso!"
                        )
                        st.rerun()
# ==================================================
# PRODUTOS
# ==================================================

elif pagina == "🍔 Produtos":
    st.title("🍔 Gerenciamento de Produtos")

    operacao_produto = st.selectbox(
        "Escolha uma operação",
        [
            "Cadastrar produto",
            "Consultar produtos",
            "Editar produto",
            "Excluir produto",
        ],
    )

    # ==============================================
    # INSERT — CADASTRAR PRODUTO
    # ==============================================

    if operacao_produto == "Cadastrar produto":
        st.subheader("Cadastrar novo produto")

        with st.form(
            "form_cadastrar_produto",
            clear_on_submit=True,
        ):
            nome = st.text_input(
                "Nome do produto",
                placeholder="Exemplo: Hambúrguer Artesanal",
            )

            tipo = st.text_input(
                "Tipo do produto",
                placeholder="Exemplo: Lanche, Bebida ou Porção",
            )

            preco = st.number_input(
                "Preço",
                min_value=0.0,
                step=0.50,
                format="%.2f",
            )

            porcao = st.text_input(
                "Porção",
                placeholder="Exemplo: Individual, Média ou Grande",
            )

            disponivel = st.checkbox(
                "Produto disponível",
                value=True,
            )

            salvar_produto = st.form_submit_button(
                "Salvar produto",
                type="primary",
            )

        if salvar_produto:
            if not nome.strip():
                st.error("Informe o nome do produto.")

            elif not tipo.strip():
                st.error("Informe o tipo do produto.")

            elif preco <= 0:
                st.error("Informe um preço maior que zero.")

            else:
                produto_existente = produtos_collection.find_one(
                    {
                        "nome": {
                            "$regex": f"^{re.escape(nome.strip())}$",
                            "$options": "i",
                        }
                    }
                )

                if produto_existente:
                    st.warning(
                        "Já existe um produto cadastrado com esse nome."
                    )

                else:
                    novo_produto = {
                        "nome": nome.strip(),
                        "tipo": tipo.strip(),
                        "preco": float(preco),
                        "porcao": porcao.strip(),
                        "disponivel": disponivel,
                        "data_cadastro": datetime.now(),
                    }

                    resultado = produtos_collection.insert_one(
                        novo_produto
                    )

                    if resultado.inserted_id:
                        st.success(
                            "Produto cadastrado com sucesso!"
                        )

    # ==============================================
    # FIND — CONSULTAR PRODUTOS
    # ==============================================

    elif operacao_produto == "Consultar produtos":
        st.subheader("Produtos cadastrados")

        coluna_pesquisa, coluna_disponibilidade = st.columns(2)

        with coluna_pesquisa:
            pesquisa = st.text_input(
                "Pesquisar produto",
                placeholder="Digite parte do nome ou tipo",
            )

        with coluna_disponibilidade:
            filtro_disponibilidade = st.selectbox(
                "Disponibilidade",
                [
                    "Todos",
                    "Disponíveis",
                    "Indisponíveis",
                ],
            )

        filtro = {}

        if pesquisa.strip():
            termo_seguro = re.escape(pesquisa.strip())

            filtro["$or"] = [
                {
                    "nome": {
                        "$regex": termo_seguro,
                        "$options": "i",
                    }
                },
                {
                    "tipo": {
                        "$regex": termo_seguro,
                        "$options": "i",
                    }
                },
            ]

        if filtro_disponibilidade == "Disponíveis":
            filtro["disponivel"] = True

        elif filtro_disponibilidade == "Indisponíveis":
            filtro["disponivel"] = False

        produtos = list(
            produtos_collection.find(filtro).sort("nome", 1)
        )

        if not produtos:
            st.info("Nenhum produto encontrado.")

        else:
            dados_produtos = []

            for produto in produtos:
                dados_produtos.append(
                    {
                        "Nome": produto.get("nome", ""),
                        "Tipo": produto.get("tipo", ""),
                        "Preço": (
                            f"R$ {produto.get('preco', 0):.2f}"
                        ),
                        "Porção": produto.get("porcao", ""),
                        "Disponível": (
                            "Sim"
                            if produto.get("disponivel", False)
                            else "Não"
                        ),
                    }
                )

            st.dataframe(
                dados_produtos,
                use_container_width=True,
                hide_index=True,
            )

            st.caption(
                f"Total de produtos encontrados: {len(produtos)}"
            )

    # ==============================================
    # UPDATE — EDITAR PRODUTO
    # ==============================================

    elif operacao_produto == "Editar produto":
        st.subheader("Editar produto")

        produtos = list(
            produtos_collection.find().sort("nome", 1)
        )

        if not produtos:
            st.info("Não existem produtos cadastrados.")

        else:
            opcoes_produtos = {
                (
                    f"{produto.get('nome', '')} — "
                    f"{produto.get('tipo', '')}"
                ): produto
                for produto in produtos
            }

            produto_escolhido = st.selectbox(
                "Selecione o produto",
                list(opcoes_produtos.keys()),
            )

            produto = opcoes_produtos[produto_escolhido]

            with st.form("form_editar_produto"):
                novo_nome = st.text_input(
                    "Nome do produto",
                    value=produto.get("nome", ""),
                )

                novo_tipo = st.text_input(
                    "Tipo do produto",
                    value=produto.get("tipo", ""),
                )

                novo_preco = st.number_input(
                    "Preço",
                    min_value=0.0,
                    value=float(produto.get("preco", 0)),
                    step=0.50,
                    format="%.2f",
                )

                nova_porcao = st.text_input(
                    "Porção",
                    value=produto.get("porcao", ""),
                )

                nova_disponibilidade = st.checkbox(
                    "Produto disponível",
                    value=produto.get("disponivel", True),
                )

                salvar_alteracoes = st.form_submit_button(
                    "Salvar alterações",
                    type="primary",
                )

            if salvar_alteracoes:
                if not novo_nome.strip():
                    st.error("Informe o nome do produto.")

                elif not novo_tipo.strip():
                    st.error("Informe o tipo do produto.")

                elif novo_preco <= 0:
                    st.error("Informe um preço maior que zero.")

                else:
                    nome_em_uso = produtos_collection.find_one(
                        {
                            "nome": {
                                "$regex": (
                                    f"^{re.escape(novo_nome.strip())}$"
                                ),
                                "$options": "i",
                            },
                            "_id": {"$ne": produto["_id"]},
                        }
                    )

                    if nome_em_uso:
                        st.warning(
                            "Já existe outro produto com esse nome."
                        )

                    else:
                        resultado = produtos_collection.update_one(
                            {"_id": produto["_id"]},
                            {
                                "$set": {
                                    "nome": novo_nome.strip(),
                                    "tipo": novo_tipo.strip(),
                                    "preco": float(novo_preco),
                                    "porcao": nova_porcao.strip(),
                                    "disponivel": nova_disponibilidade,
                                    "data_atualizacao": datetime.now(),
                                }
                            },
                        )

                        if resultado.modified_count == 1:
                            st.success(
                                "Produto atualizado com sucesso!"
                            )
                            st.rerun()

                        else:
                            st.info(
                                "Nenhuma informação foi alterada."
                            )

# ==============================================
# DELETE — EXCLUIR PRODUTO
# ==============================================

    elif operacao_produto == "Excluir produto":
        st.subheader("Excluir produto")

        produtos = list(
            produtos_collection.find().sort("nome", 1)
        )

        if not produtos:
            st.info("Não existem produtos cadastrados.")

        else:
            opcoes_produtos = {
                (
                    f"{produto.get('nome', '')} — "
                    f"{produto.get('tipo', '')}"
                ): produto
                for produto in produtos
            }

            produto_escolhido = st.selectbox(
                "Selecione o produto",
                list(opcoes_produtos.keys()),
            )

            produto = opcoes_produtos[produto_escolhido]

            quantidade_pedidos = pedidos_collection.count_documents(
                {
                    "itens.produto_id": produto["_id"]
                }
            )

            st.write(
                f"**Nome:** {produto.get('nome', '')}"
            )

            st.write(
                f"**Tipo:** {produto.get('tipo', '')}"
            )

            st.write(
                f"**Preço:** R$ {produto.get('preco', 0):.2f}"
            )

            st.write(
                f"**Pedidos vinculados:** {quantidade_pedidos}"
            )

            if quantidade_pedidos > 0:
                st.error(
                    "Este produto possui pedidos vinculados e não pode "
                    "ser excluído. Para removê-lo do cardápio, edite o "
                    "produto e desmarque a opção 'Produto disponível'."
                )

            else:
                st.warning(
                    "A exclusão removerá permanentemente o produto."
                )

                confirmar_exclusao = st.checkbox(
                    "Confirmo que desejo excluir este produto"
                )

                if st.button(
                    "Excluir produto",
                    type="primary",
                    disabled=not confirmar_exclusao,
                ):
                    resultado = produtos_collection.delete_one(
                        {"_id": produto["_id"]}
                    )

                    if resultado.deleted_count == 1:
                        st.success(
                            "Produto excluído com sucesso!"
                        )
                        st.rerun()

# ==================================================
# PEDIDOS
# ==================================================

elif pagina == "📦 Pedidos":
    st.title("📦 Gerenciamento de Pedidos")

    operacao_pedido = st.selectbox(
        "Escolha uma operação",
        [
            "Novo pedido",
            "Consultar pedidos",
            "Atualizar status",
            "Excluir pedido",
            "Histórico por cliente",
        ],
    )

    # ==============================================
    # INSERT — NOVO PEDIDO
    # ==============================================

    if operacao_pedido == "Novo pedido":
        st.subheader("Registrar novo pedido")

        clientes = list(
            clientes_collection.find().sort("nome", 1)
        )

        produtos = list(
            produtos_collection.find(
                {"disponivel": True}
            ).sort("nome", 1)
        )

        # ------------------------------------------
        # CADASTRO RÁPIDO DE CLIENTE
        # ------------------------------------------

        with st.expander(
            "Cliente não encontrado? Cadastrar novo cliente"
        ):
            with st.form(
                "form_cliente_rapido",
                clear_on_submit=True,
            ):
                novo_nome = st.text_input(
                    "Nome completo",
                    key="pedido_novo_cliente_nome",
                )

                novo_telefone = st.text_input(
                    "Telefone",
                    key="pedido_novo_cliente_telefone",
                )

                novo_endereco = st.text_input(
                    "Endereço",
                    key="pedido_novo_cliente_endereco",
                )

                cadastrar_cliente = st.form_submit_button(
                    "Cadastrar cliente"
                )

            if cadastrar_cliente:
                if not novo_nome.strip():
                    st.error("Informe o nome do cliente.")

                elif not novo_telefone.strip():
                    st.error("Informe o telefone do cliente.")

                else:
                    telefone_existente = (
                        clientes_collection.find_one(
                            {
                                "telefone": (
                                    novo_telefone.strip()
                                )
                            }
                        )
                    )

                    if telefone_existente:
                        st.warning(
                            "Já existe um cliente com esse telefone."
                        )

                    else:
                        resultado_cliente = (
                            clientes_collection.insert_one(
                                {
                                    "nome": novo_nome.strip(),
                                    "telefone": (
                                        novo_telefone.strip()
                                    ),
                                    "endereco": (
                                        novo_endereco.strip()
                                    ),
                                    "data_cadastro": datetime.now(),
                                }
                            )
                        )

                        if resultado_cliente.inserted_id:
                            st.success(
                                "Cliente cadastrado com sucesso!"
                            )
                            st.rerun()

        # ------------------------------------------
        # VALIDAÇÃO DAS BASES
        # ------------------------------------------

        if not clientes:
            st.warning(
                "Não existem clientes cadastrados. "
                "Cadastre um cliente antes de criar o pedido."
            )

        elif not produtos:
            st.warning(
                "Não existem produtos disponíveis. "
                "Cadastre ou ative um produto."
            )

        else:
            # --------------------------------------
            # ESCOLHA DO CLIENTE
            # --------------------------------------

            opcoes_clientes = {
                (
                    f"{cliente.get('nome', '')} — "
                    f"{cliente.get('telefone', '')}"
                ): cliente
                for cliente in clientes
            }

            cliente_texto = st.selectbox(
                "Cliente",
                list(opcoes_clientes.keys()),
                help=(
                    "Clique no campo e digite parte do nome "
                    "para localizar o cliente."
                ),
            )

            cliente_selecionado = opcoes_clientes[
                cliente_texto
            ]

            st.divider()
            st.subheader("Adicionar produtos")

            # --------------------------------------
            # ESCOLHA DO PRODUTO
            # --------------------------------------

            opcoes_produtos = {
                (
                    f"{produto.get('nome', '')} — "
                    f"{produto.get('porcao', '')} — "
                    f"R$ {produto.get('preco', 0):.2f}"
                ): produto
                for produto in produtos
            }

            coluna_produto, coluna_quantidade = st.columns(
                [3, 1]
            )

            with coluna_produto:
                produto_texto = st.selectbox(
                    "Produto",
                    list(opcoes_produtos.keys()),
                )

            with coluna_quantidade:
                quantidade = st.number_input(
                    "Quantidade",
                    min_value=1,
                    value=1,
                    step=1,
                )

            produto_selecionado = opcoes_produtos[
                produto_texto
            ]

            if st.button("Adicionar produto"):
                produto_encontrado = False

                for item in st.session_state.carrinho:
                    if (
                        item["produto_id"]
                        == produto_selecionado["_id"]
                    ):
                        item["quantidade"] += int(quantidade)

                        item["subtotal"] = round(
                            item["quantidade"]
                            * item["preco_unitario"],
                            2,
                        )

                        produto_encontrado = True
                        break

                if not produto_encontrado:
                    preco = float(
                        produto_selecionado.get(
                            "preco",
                            0,
                        )
                    )

                    item = {
                        "produto_id": (
                            produto_selecionado["_id"]
                        ),
                        "nome": produto_selecionado.get(
                            "nome",
                            "",
                        ),
                        "tipo": produto_selecionado.get(
                            "tipo",
                            produto_selecionado.get(
                                "categoria",
                                "",
                            ),
                        ),
                        "porcao": produto_selecionado.get(
                            "porcao",
                            "",
                        ),
                        "quantidade": int(quantidade),
                        "preco_unitario": preco,
                        "subtotal": round(
                            preco * int(quantidade),
                            2,
                        ),
                    }

                    st.session_state.carrinho.append(item)

                st.success("Produto adicionado!")
                st.rerun()

            # --------------------------------------
            # CARRINHO
            # --------------------------------------

            st.divider()
            st.subheader("Itens do pedido")

            if not st.session_state.carrinho:
                st.info(
                    "Nenhum produto foi adicionado ao pedido."
                )

            else:
                tabela_carrinho = []

                for item in st.session_state.carrinho:
                    tabela_carrinho.append(
                        {
                            "Produto": item["nome"],
                            "Tipo": item["tipo"],
                            "Porção": item["porcao"],
                            "Quantidade": item["quantidade"],
                            "Preço unitário": (
                                f"R$ "
                                f"{item['preco_unitario']:.2f}"
                            ),
                            "Subtotal": (
                                f"R$ {item['subtotal']:.2f}"
                            ),
                        }
                    )

                st.dataframe(
                    tabela_carrinho,
                    use_container_width=True,
                    hide_index=True,
                )

                opcoes_remocao = {
                    (
                        f"{indice + 1} — "
                        f"{item['nome']} — "
                        f"{item['quantidade']} unidade(s)"
                    ): indice
                    for indice, item in enumerate(
                        st.session_state.carrinho
                    )
                }

                item_remover = st.selectbox(
                    "Selecione um item para remover",
                    list(opcoes_remocao.keys()),
                )

                coluna_remover, coluna_limpar = st.columns(2)

                with coluna_remover:
                    if st.button("Remover item"):
                        indice = opcoes_remocao[
                            item_remover
                        ]

                        st.session_state.carrinho.pop(
                            indice
                        )

                        st.rerun()

                with coluna_limpar:
                    if st.button("Limpar pedido"):
                        st.session_state.carrinho = []
                        st.rerun()

                valor_total = round(
                    sum(
                        item["subtotal"]
                        for item in st.session_state.carrinho
                    ),
                    2,
                )

                st.metric(
                    "Valor total",
                    f"R$ {valor_total:.2f}",
                )

                observacoes = st.text_area(
                    "Observações",
                    placeholder=(
                        "Exemplo: sem cebola, "
                        "troco para R$ 100,00..."
                    ),
                )

                status_inicial = st.selectbox(
                    "Status inicial",
                    [
                        "Recebido",
                        "Em preparo",
                        "Pronto",
                        "Saiu para entrega",
                    ],
                )

                if st.button(
                    "Finalizar e salvar pedido",
                    type="primary",
                ):
                    novo_pedido = {
                        # Referência ao cliente
                        "cliente_id": (
                            cliente_selecionado["_id"]
                        ),

                        # Resumo agregado do cliente
                        "cliente": {
                            "nome": (
                                cliente_selecionado.get(
                                    "nome",
                                    "",
                                )
                            ),
                            "telefone": (
                                cliente_selecionado.get(
                                    "telefone",
                                    "",
                                )
                            ),
                        },

                        # Documentos agregados dos produtos
                        "itens": (
                            st.session_state.carrinho.copy()
                        ),

                        "valor_total": valor_total,
                        "status": status_inicial,
                        "observacoes": observacoes.strip(),
                        "data_pedido": datetime.now(),
                    }

                    resultado = (
                        pedidos_collection.insert_one(
                            novo_pedido
                        )
                    )

                    if resultado.inserted_id:
                        st.session_state.carrinho = []

                        st.success(
                            "Pedido cadastrado com sucesso!"
                        )

    # ==============================================
    # FIND — CONSULTAR PEDIDOS
    # ==============================================

    elif operacao_pedido == "Consultar pedidos":
        st.subheader("Pedidos cadastrados")

        coluna_pesquisa, coluna_status = st.columns(2)

        with coluna_pesquisa:
            pesquisa_cliente = st.text_input(
                "Pesquisar pelo cliente",
                placeholder="Digite parte do nome",
            )

        with coluna_status:
            status_filtro = st.selectbox(
                "Filtrar por status",
                [
                    "Todos",
                    "Recebido",
                    "Em preparo",
                    "Pronto",
                    "Saiu para entrega",
                    "Finalizado",
                    "Cancelado",
                ],
            )

        filtro = {}

        if pesquisa_cliente.strip():
            termo_seguro = re.escape(
                pesquisa_cliente.strip()
            )

            filtro["cliente.nome"] = {
                "$regex": termo_seguro,
                "$options": "i",
            }

        if status_filtro != "Todos":
            filtro["status"] = status_filtro

        pedidos = list(
            pedidos_collection.find(filtro).sort(
                "data_pedido",
                -1,
            )
        )

        if not pedidos:
            st.info("Nenhum pedido encontrado.")

        else:
            dados_pedidos = []

            for pedido in pedidos:
                cliente_documento = pedido.get(
                    "cliente",
                    {},
                )

                nome_cliente = cliente_documento.get(
                    "nome",
                    pedido.get(
                        "cliente",
                        "Cliente não identificado",
                    ),
                )

                data_pedido = pedido.get(
                    "data_pedido",
                    "",
                )

                if isinstance(data_pedido, datetime):
                    data_formatada = (
                        data_pedido.strftime(
                            "%d/%m/%Y %H:%M"
                        )
                    )
                else:
                    data_formatada = str(data_pedido)

                valor = pedido.get(
                    "valor_total",
                    pedido.get("valorTotal", 0),
                )

                dados_pedidos.append(
                    {
                        "Pedido": str(
                            pedido["_id"]
                        )[-6:],
                        "Cliente": nome_cliente,
                        "Data": data_formatada,
                        "Status": pedido.get(
                            "status",
                            "",
                        ),
                        "Valor": f"R$ {valor:.2f}",
                        "Itens": len(
                            pedido.get("itens", [])
                        ),
                    }
                )

            st.dataframe(
                dados_pedidos,
                use_container_width=True,
                hide_index=True,
            )

            st.caption(
                f"Total de pedidos: {len(pedidos)}"
            )

            st.divider()
            st.subheader("Detalhes")

            for pedido in pedidos:
                cliente_documento = pedido.get(
                    "cliente",
                    {},
                )

                if isinstance(cliente_documento, dict):
                    nome_cliente = cliente_documento.get(
                        "nome",
                        "Cliente não identificado",
                    )
                else:
                    nome_cliente = str(
                        cliente_documento
                    )

                valor = pedido.get(
                    "valor_total",
                    pedido.get("valorTotal", 0),
                )

                titulo = (
                    f"Pedido {str(pedido['_id'])[-6:]} — "
                    f"{nome_cliente} — "
                    f"{pedido.get('status', '')}"
                )

                with st.expander(titulo):
                    st.write(
                        f"**Valor total:** R$ {valor:.2f}"
                    )

                    st.write(
                        "**Observações:** "
                        + (
                            pedido.get(
                                "observacoes",
                                "",
                            )
                            or "Nenhuma"
                        )
                    )

                    itens = pedido.get("itens", [])

                    for item in itens:
                        nome_produto = item.get(
                            "nome",
                            item.get(
                                "produto",
                                "Produto",
                            ),
                        )

                        quantidade_item = item.get(
                            "quantidade",
                            0,
                        )

                        preco_unitario = item.get(
                            "preco_unitario",
                            0,
                        )

                        subtotal = item.get(
                            "subtotal",
                            preco_unitario
                            * quantidade_item,
                        )

                        st.write(
                            f"- {quantidade_item}x "
                            f"{nome_produto} — "
                            f"R$ {subtotal:.2f}"
                        )

    # ==============================================
    # UPDATE — ATUALIZAR STATUS
    # ==============================================

    elif operacao_pedido == "Atualizar status":
        st.subheader("Atualizar status do pedido")

        pedidos = list(
            pedidos_collection.find().sort(
                "data_pedido",
                -1,
            )
        )

        if not pedidos:
            st.info("Não existem pedidos cadastrados.")

        else:
            opcoes_pedidos = {}

            for pedido in pedidos:
                cliente_documento = pedido.get(
                    "cliente",
                    {},
                )

                if isinstance(cliente_documento, dict):
                    nome_cliente = cliente_documento.get(
                        "nome",
                        "Cliente não identificado",
                    )
                else:
                    nome_cliente = str(
                        cliente_documento
                    )

                descricao = (
                    f"{str(pedido['_id'])[-6:]} — "
                    f"{nome_cliente} — "
                    f"{pedido.get('status', '')}"
                )

                opcoes_pedidos[descricao] = pedido

            pedido_texto = st.selectbox(
                "Selecione o pedido",
                list(opcoes_pedidos.keys()),
            )

            pedido = opcoes_pedidos[pedido_texto]

            status_disponiveis = [
                "Recebido",
                "Em preparo",
                "Pronto",
                "Saiu para entrega",
                "Finalizado",
                "Cancelado",
            ]

            status_atual = pedido.get(
                "status",
                "Recebido",
            )

            indice_atual = (
                status_disponiveis.index(status_atual)
                if status_atual in status_disponiveis
                else 0
            )

            novo_status = st.selectbox(
                "Novo status",
                status_disponiveis,
                index=indice_atual,
            )

            if st.button(
                "Atualizar status",
                type="primary",
            ):
                resultado = pedidos_collection.update_one(
                    {"_id": pedido["_id"]},
                    {
                        "$set": {
                            "status": novo_status,
                            "data_atualizacao": datetime.now(),
                        }
                    },
                )

                if resultado.modified_count == 1:
                    st.success(
                        "Status atualizado com sucesso!"
                    )
                    st.rerun()

                else:
                    st.info(
                        "O pedido já possui esse status."
                    )

    # ==============================================
    # DELETE — EXCLUIR PEDIDO
    # ==============================================

    elif operacao_pedido == "Excluir pedido":
        st.subheader("Excluir pedido")

        pedidos = list(
            pedidos_collection.find().sort(
                "data_pedido",
                -1,
            )
        )

        if not pedidos:
            st.info("Não existem pedidos cadastrados.")

        else:
            opcoes_pedidos = {}

            for pedido in pedidos:
                cliente_documento = pedido.get(
                    "cliente",
                    {},
                )

                if isinstance(cliente_documento, dict):
                    nome_cliente = cliente_documento.get(
                        "nome",
                        "Cliente não identificado",
                    )
                else:
                    nome_cliente = str(
                        cliente_documento
                    )

                valor = pedido.get(
                    "valor_total",
                    pedido.get("valorTotal", 0),
                )

                descricao = (
                    f"{str(pedido['_id'])[-6:]} — "
                    f"{nome_cliente} — "
                    f"R$ {valor:.2f}"
                )

                opcoes_pedidos[descricao] = pedido

            pedido_texto = st.selectbox(
                "Selecione o pedido",
                list(opcoes_pedidos.keys()),
            )

            pedido = opcoes_pedidos[pedido_texto]

            st.warning(
                "A exclusão removerá permanentemente "
                "o documento da coleção pedidos."
            )

            confirmar = st.checkbox(
                "Confirmo que desejo excluir este pedido"
            )

            if st.button(
                "Excluir pedido",
                type="primary",
                disabled=not confirmar,
            ):
                resultado = pedidos_collection.delete_one(
                    {"_id": pedido["_id"]}
                )

                if resultado.deleted_count == 1:
                    st.success(
                        "Pedido excluído com sucesso!"
                    )
                    st.rerun()

    # ==============================================
    # HISTÓRICO POR CLIENTE
    # ==============================================

    elif operacao_pedido == "Histórico por cliente":
        st.subheader("Histórico de pedidos")

        clientes = list(
            clientes_collection.find().sort("nome", 1)
        )

        if not clientes:
            st.info("Não existem clientes cadastrados.")

        else:
            opcoes_clientes = {
                (
                    f"{cliente.get('nome', '')} — "
                    f"{cliente.get('telefone', '')}"
                ): cliente
                for cliente in clientes
            }

            cliente_texto = st.selectbox(
                "Selecione o cliente",
                list(opcoes_clientes.keys()),
            )

            cliente = opcoes_clientes[cliente_texto]

            pedidos_cliente = list(
                pedidos_collection.find(
                    {
                        "cliente_id": cliente["_id"]
                    }
                ).sort("data_pedido", -1)
            )

            if not pedidos_cliente:
                st.info(
                    "Este cliente ainda não possui pedidos."
                )

            else:
                total_gasto = sum(
                    pedido.get(
                        "valor_total",
                        pedido.get("valorTotal", 0),
                    )
                    for pedido in pedidos_cliente
                )

                coluna_total, coluna_valor = st.columns(2)

                with coluna_total:
                    st.metric(
                        "Quantidade de pedidos",
                        len(pedidos_cliente),
                    )

                with coluna_valor:
                    st.metric(
                        "Total em pedidos",
                        f"R$ {total_gasto:.2f}",
                    )

                for pedido in pedidos_cliente:
                    valor = pedido.get(
                        "valor_total",
                        pedido.get("valorTotal", 0),
                    )

                    with st.expander(
                        (
                            f"Pedido "
                            f"{str(pedido['_id'])[-6:]} — "
                            f"{pedido.get('status', '')}"
                        )
                    ):
                        st.write(
                            f"**Valor:** R$ {valor:.2f}"
                        )

                        for item in pedido.get(
                            "itens",
                            [],
                        ):
                            nome_produto = item.get(
                                "nome",
                                item.get(
                                    "produto",
                                    "Produto",
                                ),
                            )

                            quantidade_item = item.get(
                                "quantidade",
                                0,
                            )

                            st.write(
                                f"- {quantidade_item}x "
                                f"{nome_produto}"
                            )