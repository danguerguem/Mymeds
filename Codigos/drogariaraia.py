import re
import time
import math
import json
import os
from playwright.sync_api import sync_playwright

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
    caminho_arquivo = "C:/Users/danie/OneDrive/Desktop/Mymeds/meu-projeto/data/p_drogaraia.json"
    
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
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        base_url = "https://www.drogaraia.com.br/medicamentos/remedios.html"
        page.set_extra_http_headers({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
        })
        page.goto(base_url, wait_until="networkidle", timeout=120000)  # Espera até que a rede esteja ociosa

        produtos_coletados = []

        while True:
            # Aguarda os produtos da página carregarem
            product_selector = ".product-item"
            page.wait_for_selector(product_selector, timeout=10000)

            # Localiza todos os produtos na página atual
            products = page.locator(product_selector)
            if products.count() == 0:
                print("Nenhum produto encontrado na página atual. Finalizando.")
                break

            produtos_pagina = []

            for i in range(products.count()):
                product = products.nth(i)

                # Extrai as informações do produto
                nome_produto_selector = "img[data-testid='product-image']"
                nome_produto = product.locator(nome_produto_selector)
                nome = nome_produto.get_attribute("alt") if nome_produto.count() > 0 else "Nome não encontrado"

                preco_selector = ".price-final .price"
                preco_locator = product.locator(preco_selector).nth(0)
                preco = preco_locator.text_content() if preco_locator.count() > 0 else "Sem preço"

                link_selector = "a[data-qa='caroussel_item_btn_buy']"
                link = product.locator(link_selector).first.get_attribute("href")

                categoria_selector = ".category-title"
                categoria = product.locator(categoria_selector).text_content() if product.locator(categoria_selector).count() > 0 else "Categoria não encontrada"
                
                # Verifica a disponibilidade com base no preço
                if preco == "Sem preço":
                    disponibilidade = "Sem estoque"
                else:
                    disponibilidade = "Em estoque"
                    
                # Localiza o elemento da imagem
                imagem_locator = page.locator('img[data-testid="product-image"]')
                imagem = imagem_locator.first.get_attribute('src')

                produto_data = {
                    "farmacia": "Droga Raia",
                    "dt_coleta": time.strftime("%Y-%m-%d"),
                    "nome": nome,
                    "preco": preco,
                    "link": link,
                    "disponibilidade": disponibilidade,
                    "categoria": "Medicamentos",
                    "imagem": "https://www.drogaraia.com.br" + imagem 
                }
                produtos_pagina.append(produto_data)

            # Salva os produtos da página atual no arquivo
            salvar_produtos_dinamicamente(produtos_pagina)
            print(f"Produtos da página salvos. Total: {len(produtos_pagina)}")

            # Tenta fechar o banner de consentimento de cookies
            try:
                consent_button_selector = "button#onetrust-accept-btn-handler"
                page.locator(consent_button_selector).click()
                print("Consentimento de cookies aceito.")
            except Exception as e:
                print("Nenhum consentimento de cookies encontrado ou já aceito.")

            # Tenta ocultar o overlay de consentimento via JavaScript (caso o clique não tenha funcionado)
            page.evaluate("""
                let consentOverlay = document.querySelector('.onetrust-pc-dark-filter');
                if (consentOverlay) {
                    consentOverlay.style.display = 'none';
                }

                // Ocultar menu que pode estar bloqueando o clique
                let menuOverlay = document.querySelector('.Menustyles__MenuSize-sc-1u1vz6z-3');
                if (menuOverlay) {
                    menuOverlay.style.display = 'none';
                }
            """)

            # Tenta localizar o botão "Próxima página"
            next_page_selector = "a[data-qa='btn_proximo']"
            next_page_produto = page.locator(next_page_selector)

            if next_page_produto.count() > 0:
                try:
                    # Tenta clicar diretamente no botão "Próxima página" via JavaScript
                    page.evaluate("""
                        document.querySelector('a[data-qa="btn_proximo"]').click();
                    """)
                    # Aguarda até que novos produtos da próxima página apareçam
                    page.wait_for_selector(product_selector, timeout=7000)
                    print("Página carregada e produtos encontrados.")
                except Exception as e:
                    print(f"Erro ao clicar na próxima página: {e}")
                    break
            else:
                print("Botão de próxima página não encontrado. Finalizando.")
                break

        browser.close()

if __name__ == "__main__":
    run()
