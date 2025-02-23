import time
import json
from playwright.sync_api import sync_playwright

def salvar_produtos_dinamicamente(produtos_pagina):
    caminho_arquivo = "C:/Users/danie/OneDrive/Desktop/Mymeds/Dados/p_drogaraia.json"
    
    try:
        with open(caminho_arquivo, 'r', encoding='utf-8') as arquivo:
            produtos_existentes = json.load(arquivo)
    except (FileNotFoundError, json.JSONDecodeError):
        produtos_existentes = []

    for produto in produtos_pagina:
        if produto not in produtos_existentes:
            produtos_existentes.append(produto)

    with open(caminho_arquivo, 'w', encoding='utf-8') as arquivo:
        json.dump(produtos_existentes, arquivo, ensure_ascii=False, indent=4)

    print(f"Produtos salvos em {caminho_arquivo}")

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        base_url = "https://www.drogaraia.com.br/medicamentos/remedios.html"
        page.goto(base_url, wait_until="networkidle", timeout=120000)  # Espera até que a rede esteja ociosa
        
        produtos_coletados = []

        while True:
            product_selector = ".product-item"
            page.wait_for_selector(product_selector, timeout=10000)

            products = page.locator(product_selector)
            if products.count() == 0:
                print("Nenhum produto encontrado na página atual. Finalizando.")
                break

            produtos_pagina = []
            
            # Rolar para o final da página
            page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            time.sleep(2)

            for i in range(products.count()):
                product = products.nth(i)

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

                if preco == "Sem preço":
                    disponibilidade = "Sem estoque"
                else:
                    disponibilidade = "Em estoque"
                    
                # Aumentando o tempo de espera para garantir que a imagem esteja visível
                imagem_locator = product.locator('img[data-testid="product-image"]')
                imagem_locator.wait_for(state="visible", timeout=40000)  # Espera até que a imagem seja visível

                # Capturar o src ou o data-src da imagem
                imagem = imagem_locator.get_attribute('src') or imagem_locator.get_attribute('data-src') or imagem_locator.get_attribute('srcset')

                # Verificar se a imagem é válida (não base64)
                # if imagem and imagem.startswith('data:image'):
                    # print(f"Imagem de fallback detectada para o produto: {nome}")
                    # imagem = "Imagem não disponível"
                # elif not imagem or not imagem.startswith('https://'):
                #     print(f"Imagem não encontrada para o produto: {nome}")
                    # imagem = "Imagem não disponível"

                produto_data = {
                    "farmacia": "Droga Raia",
                    "dt_coleta": time.strftime("%Y-%m-%d"),
                    "nome": nome,
                    "preco": preco,
                    "link": link,
                    "disponibilidade": disponibilidade,
                    "categoria": categoria,
                    "imagem": "https://www.drogaraia.com.br" + imagem if imagem != "Imagem não disponível" else imagem
                }
                produtos_pagina.append(produto_data)

            salvar_produtos_dinamicamente(produtos_pagina)
            print(f"Produtos da página salvos. Total: {len(produtos_pagina)}")

            try:
                consent_button_selector = "button#onetrust-accept-btn-handler"
                page.locator(consent_button_selector).click()
                print("Consentimento de cookies aceito.")
            except Exception as e:
                print("Nenhum consentimento de cookies encontrado ou já aceito.")

            page.evaluate("""
                let consentOverlay = document.querySelector('.onetrust-pc-dark-filter');
                if (consentOverlay) {
                    consentOverlay.style.display = 'none';
                }

                let menuOverlay = document.querySelector('.Menustyles__MenuSize-sc-1u1vz6z-3');
                if (menuOverlay) {
                    menuOverlay.style.display = 'none';
                }
            """)

            next_page_selector = "a[data-qa='btn_proximo']"
            next_page_produto = page.locator(next_page_selector)

            if next_page_produto.count() > 0:
                try:
                    page.evaluate("""
                        document.querySelector('a[data-qa="btn_proximo"]').click();
                    """)
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
