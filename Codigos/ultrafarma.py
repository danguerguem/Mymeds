import re
import time
import math
import json
import os
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth


def navegar_com_tentativas(page, url, tentativas=3):
    for tentativa in range(tentativas):
        try:
            print(f"Tentativa {tentativa + 1}: Acessando {url}")
            page.goto(url, timeout=60000, wait_until="domcontentloaded")
            return  # Sai da função se conseguir acessar a página
        except Exception as e:
            print(f"Erro ao acessar a página: {e}")
            time.sleep(5)  # Espera antes de tentar novamente
    raise Exception(f"Falha ao acessar {url} após {tentativas} tentativas.")

def salvar_produtos_dinamicamente(produtos_pagina):
    caminho_arquivo = "C:/Users/danie/OneDrive/Desktop/Mymeds/meu-projeto/data/p_ultrafarma.json"
    
    # Lê os produtos existentes (se o arquivo já existir)
    try:
        with open(caminho_arquivo, 'r', encoding='utf-8') as arquivo:
            produtos_existentes = json.load(arquivo)
    except (FileNotFoundError, json.JSONDecodeError):
        # Se o arquivo não existir ou estiver vazio/corrompido, inicializa uma lista vazia
        produtos_existentes = []

    # Adiciona os novos produtos, garantindo que não haja duplicatas
    for produto in produtos_pagina:
        if produto not in produtos_existentes:
            produtos_existentes.append(produto)

    # Salva a lista atualizada no arquivo
    with open(caminho_arquivo, 'w', encoding='utf-8') as arquivo:
        json.dump(produtos_existentes, arquivo, ensure_ascii=False, indent=4)

    print(f"Produtos salvos em {caminho_arquivo}")

def run():
    with sync_playwright() as p:
        # Inicializa o navegador
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        base_url = "https://www.ultrafarma.com.br/categoria/medicamentos?sortby=relevance&page="
        page_number = 1
        max_pages = None  # Inicializa o limite de páginas como indefinido

        while True:
            page_url = f"{base_url}{page_number}"
            page.set_extra_http_headers({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
            })
            page.goto(page_url, wait_until="networkidle", timeout=120000)  # Espera até que a rede esteja ociosa
            time.sleep(3)  # Aguarda a página carregar

            if max_pages is None:
                total_products_selector = ".pagination-info strong:last-child"
                total_products_text = page.locator(total_products_selector).text_content()

                if total_products_text:
                    match = re.search(r'(\d+)', total_products_text.strip())
                    if match:
                        total_products = int(match.group(1))
                        max_pages = math.ceil(total_products / 48)
                        print(f"Total de produtos: {total_products}, Páginas máximas: {max_pages}")
                    else:
                        print("Não foi possível extrair o número de produtos. Finalizando.")
                        break
                else:
                    print("Não foi possível localizar o número total de produtos. Finalizando.")
                    break

            if page_number > max_pages:
                print(f"Página {page_number} excede o número máximo de páginas ({max_pages}). Finalizando.")
                break

            product_selector = ".product-item"
            products = page.locator(product_selector)

            if products.count() == 0:
                print(f"Não foram encontrados produtos na página {page_number}. Finalizando.")
                break

            produtos_pagina = []

            for i in range(products.count()):
                product = products.nth(i)

                try:
                    link = product.locator("a[class='product-available product-item-link']").first.get_attribute("href")
                except Exception as e:
                    print(f"Erro ao obter o link do produto: {e}")
                    print(f"HTML da página atual: {page.content()}")  # Isso ajuda a entender o que está sendo carregado

                # Captura o nome do produto
                nome_produto_selector = ".product-item-info .product-item-name"
                nome_produto_locator = product.locator(nome_produto_selector)

                if nome_produto_locator.count() > 0:
                    alt_text = nome_produto_locator.text_content().strip()
                else:
                    alt_text = "Nome não encontrado"

                # Captura o preço
                preco_selector = ".product-item-price-for"
                preco_locator = product.locator(preco_selector)
                if preco_locator.count() > 0:
                    preco = preco_locator.get_attribute("data-preco")
                else:
                    preco = "Preço não encontrado"

                # Verifica a disponibilidade com base no preço
                disponibilidade = "Em estoque" if preco != "Preço não encontrado" else "Sem estoque"
                
                # Captura a imagem do produto
                # imagem_selector = ".product-image img"
                imagem = page.locator('img.product-image').first.get_attribute('src')

                produto_data = {
                    "farmacia": "Ultrafarma",
                    "dt_coleta": time.strftime("%Y-%m-%d"),
                    "url": link,
                    "nome": alt_text,
                    "preco": preco,
                    "disponibilidade": disponibilidade,
                    "categoria": "Medicamentos",
                    "imagem": imagem
                }
                produtos_pagina.append(produto_data)

            # Salva os produtos da página atual no arquivo
            salvar_produtos_dinamicamente(produtos_pagina)
            print(f"Produtos da página {page_number} salvos. Total: {len(produtos_pagina)}")

            page_number += 1

        browser.close()

if __name__ == "__main__":
    run()
