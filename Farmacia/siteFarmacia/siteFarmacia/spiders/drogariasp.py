import json
import time
import scrapy
import os
from datetime import datetime
from scrapy.spiders import SitemapSpider
from twisted.internet import task
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

class ProdutosSpider(SitemapSpider):
    name = 'drogariasp'
    sitemap_urls = ['https://www.drogariasaopaulo.com.br/sitemap.xml']  # Sitemap principal

    sitemap_rules = [('', 'parse_product')]  # Processa todas as URLs encontradas em "product"

    def parse_product(self, response):
        # Extrair a URL da imagem
        imagem_url = response.css('#image img::attr(src)').get()

        # Extração de dados do produto
        disponibilidade = response.css('#inicio-conteudo .col-6 h2::text').get(default='').strip()
        if not disponibilidade:  # Se disponibilidade for vazio ou None
            disponibilidade = 'Em estoque'

        categoria = response.css('.last span::text').get(default='').strip()

        # Criar o dicionário com os dados do produto
        produto = {
            'farmacia': 'Drogaria São Paulo',
            'dt_coleta': time.strftime("%Y-%m-%d"),
            'nome': response.css('.productName::text').get(default='').strip(),
            'preco': response.css('.skuBestPrice::text').get(default='').strip(),
            'link': response.url,  # Adicionando o link para o produto
            'disponibilidade': disponibilidade,
            'categoria': categoria,
            'imagem': f"https://www.drogaraia.com.br{imagem_url}"  # Concatenando a URL base com o src
        }

        # Filtrar apenas produtos da categoria "medicamentos"
        if categoria.lower() == 'medicamentos':
            # Salvar o produto em um arquivo JSON com UTF-8
            file_path = "C:/Users/danie/OneDrive/Desktop/Mymeds/meu-projeto/data/p_drogariasp.json"
            if os.path.exists(file_path):
                # Se o arquivo já existir, ler e adicionar os novos produtos
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                # Se o arquivo não existir, criar uma lista vazia
                data = []

            # Adicionar o produto à lista
            data.append(produto)

            # Salvar a lista de produtos no arquivo JSON
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)  # Usando indent para melhorar a legibilidade
