from flask import Flask, request, jsonify, render_template
import json
import os
from fuzzywuzzy import fuzz
import unicodedata

app = Flask(__name__)

# Função para normalizar os textos (remover acentuação)
def normalizar_texto(texto):
    return ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')

# Carregando as bases JSON na inicialização
data_folder = "./data"
bases = []
for file in os.listdir(data_folder):
    if file.endswith(".json"):
        with open(os.path.join(data_folder, file), 'r', encoding='utf-8') as f:
            content = f.read()
            decoder = json.JSONDecoder(strict=False)
            bases.append(decoder.decode(content))

# Função para buscar o medicamento nas bases com fuzzy matching
def buscar_medicamento(nome_produto):
    resultados = []
    nome_produto_normalizado = normalizar_texto(nome_produto.lower())  # Nome da pesquisa normalizado
    for base in bases:
        for produto in base:
            nome_base_normalizado = normalizar_texto(produto["nome"].lower())  # Nome do produto na base normalizado
            # Compara com a palavra-chave usando fuzzywuzzy
            if fuzz.partial_ratio(nome_base_normalizado, nome_produto_normalizado) >= 80:  # Ajuste o valor de threshold conforme necessário
                resultados.append(produto)
    return resultados

# Função para comparar preços entre as bases e listar as farmácias
def comparar_precos(nome_produto):
    precos_comparados = {}

    # Buscar o medicamento com base na palavra-chave
    produtos_encontrados = buscar_medicamento(nome_produto)

    for produto in produtos_encontrados:
        nome = produto["nome"]
        preco = float(produto["preco"].replace(",", "."))  # Converter preço para float
        farmacia = produto.get("farmacia", "Desconhecida")

        # Se o produto já estiver na lista
        if nome in precos_comparados:
            # Se o preço atual for menor que o registrado
            if preco < precos_comparados[nome]["preco"]:
                precos_comparados[nome] = {"preco": preco, "farmacia": [farmacia]}
            # Se o preço for igual ao menor preço, adicionar a farmácia
            elif preco == precos_comparados[nome]["preco"]:
                precos_comparados[nome]["farmacia"].append(farmacia)
        else:
            # Se o produto ainda não estiver na lista, adiciona
            precos_comparados[nome] = {"preco": preco, "farmacia": [farmacia]}

    return precos_comparados

# Rota principal para renderizar a interface
@app.route("/")
def index():
    return render_template("index.html")

# Rota de pesquisa
@app.route("/buscar", methods=["GET"])
def buscar():
    nome = request.args.get("nome")
    if not nome:
        return jsonify({"erro": "Nome do produto é obrigatório"}), 400
    resultados = buscar_medicamento(nome)
    return jsonify(resultados)

# Rota de comparação de preços
@app.route("/comparar", methods=["GET"])
def comparar():
    nome_produto = request.args.get("nome")
    if not nome_produto:
        return jsonify({"erro": "Nome do produto é obrigatório para comparação"}), 400
    precos = comparar_precos(nome_produto)
    return jsonify(precos)

if __name__ == "__main__":
    app.run(debug=True)
