import discord
import requests
import sys
import logging
import os
from discord import app_commands
import datetime
import json


with open("config.json", "r") as config_file:
    config = json.load(config_file)

TOKEN = config["BOT_TOKEN"]
intents = discord.Intents.all()
GUILD = int(config["DISCORD_GUILD_ID"])

class MyClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        self.guild = None

    async def on_ready(self):
        self.guild = self.get_guild(int(GUILD))  # Convert GUILD to int if it's stored as a string in config
        if self.guild:
            await self.setup_hook()

    async def setup_hook(self):
        if not self.guild:
            return
        self.tree.copy_global_to(guild=self.guild)
        await self.tree.sync(guild=self.guild)

bot = MyClient(intents=intents)

headers = {
    'authority': 'search1web.endclothing.com',
    'accept': 'application/json',
    'accept-language': 'en-US,en;q=0.9',
    'content-type': 'application/x-www-form-urlencoded',
    'origin': 'https://launches.endclothing.com',
    'referer': 'https://launches.endclothing.com/',
    'sec-ch-ua': '"Not?A_Brand";v="8", "Chromium";v="108", "Google Chrome";v="108"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-site',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
}


def get_product_data(sku):
    data = '{"requests":[{"indexName":"catalog_products_launches_en","params":"analyticsTags=%5B%22browse%22%2C%22web%22%2C%22v3%22%2C%22gb%22%5D&ruleContexts=%5B%22browse%22%2C%22web%22%2C%22v3%22%2C%22gb%22%5D&page=0&facets=%5B%22*%22%5D&facetFilters=%5B%5B%22websites_available_at%3A1%22%5D%2C%5B%22url_key%3A'+sku+'%22%5D%5D&clickAnalytics=true&filters="},{"indexName":"catalog_products_launches_en","params":"analyticsTags=%5B%22browse%22%2C%22web%22%2C%22v3%22%2C%22gb%22%5D&ruleContexts=%5B%22browse%22%2C%22web%22%2C%22v3%22%2C%22gb%22%5D&page=0&facets=%5B%22*%22%5D&facetFilters=%5B%5B%22websites_available_at%3A1%22%5D%5D&clickAnalytics=true"},{"indexName":"catalog_products_launches_en","params":"analyticsTags=%5B%22browse%22%2C%22web%22%2C%22v3%22%2C%22gb%22%5D&ruleContexts=%5B%22browse%22%2C%22web%22%2C%22v3%22%2C%22gb%22%5D&page=0&facets=websites_available_at&facetFilters=%5B%5B%22url_key%3A'+sku+'%22%5D%5D&analytics=false&filters="},{"indexName":"catalog_products_launches_en","params":"analyticsTags=%5B%22browse%22%2C%22web%22%2C%22v3%22%2C%22gb%22%5D&ruleContexts=%5B%22browse%22%2C%22web%22%2C%22v3%22%2C%22gb%22%5D&page=0&facets=url_key&facetFilters=%5B%5B%22websites_available_at%3A1%22%5D%5D&analytics=false&filters="}]}'
    response = requests.post(
        'https://search1web.endclothing.com/1/indexes/*/queries?x-algolia-agent=Algolia%20for%20JavaScript%20(3.35.1)%3B%20Browser&x-algolia-application-id=KO4W2GBINK&x-algolia-api-key=dfa5df098f8d677dd2105ece472a44f8',
        headers=headers,
        data=data,
    )
    return response

def parse_product_data(response):
    product_url = response.json()["results"][0]["hits"][0]["launches_url"]
    product_name = response.json()["results"][0]["hits"][0]["name"]
    thumbnail = response.json()["results"][0]["hits"][0]["launches_image_thumbnail"]
    total_stock = response.json()["results"][0]["hits"][0]["stock"]
    uk_sizes = response.json()["results"][0]["hits"][0]["size"]
    sku_stock = response.json()["results"][0]["hits"][0]["sku_stock"]
    price_gbp = response.json()["results"][0]["hits"][0]["final_price_1"]
    price_usd = response.json()["results"][0]["hits"][0]["final_price_2"]
    price_eur = response.json()["results"][0]["hits"][0]["final_price_3"]

    return {
        "url": product_url,
        "name": product_name,
        "thumbnail": thumbnail,
        "stock": total_stock,
        "sizes": uk_sizes,
        "sku_stock": sku_stock,
        "price_gbp": price_gbp,
        "price_usd": price_usd,
        "price_eur": price_eur,
    }

def setup_custom_logger():
    log_format = '[%(asctime)s] %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(log_format, datefmt=date_format))

    logger.addHandler(console_handler)
    logging.getLogger('discord').setLevel(logging.CRITICAL)
    logging.getLogger('websockets').setLevel(logging.CRITICAL)

    return logger


def create_embed(product_data):
    uk_size_list = []
    for i in product_data["sizes"]:
        uk_size_list.append(i)
    uk_size_list = '\n'.join(map(str, uk_size_list))

    sku_stock_list = []
    total_stock = 0
    for key, value in product_data["sku_stock"].items():
        sku_stock_list.append(value)
        total_stock += value
    sku_stock_list = '\n'.join(map(str, sku_stock_list))

    price_gbp = product_data["price_gbp"]
    price_usd = product_data["price_usd"]
    price_eur = product_data["price_eur"]

    sku_stock_list = f'\n{sku_stock_list}'
    embed = discord.Embed(title=product_data["name"], description=f"[Product Link]({product_data['url']})", color=int(config["COLOUR"].lstrip("#"), 16))
    embed.set_author(name="End Stock Checker", url=config["URL"], icon_url=config["LOGO"])
    embed.add_field(name="***Price in £:***", value=f"`{price_gbp}`", inline=True)
    embed.add_field(name="***Price in €***", value=f"`{price_eur}`", inline=True)
    embed.add_field(name="***Price in $***", value=f"`{price_usd}`", inline=True)
    embed.add_field(name="Sizes", value=f"```{uk_size_list}```", inline=True)
    embed.add_field(name="Stock", value=f"```{sku_stock_list}```", inline=True)
    embed.set_footer(text=f"{config['NAME']} | {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", icon_url=config["LOGO"])
    embed.set_thumbnail(url=product_data["thumbnail"])
    return embed
	
def clear_console():
    if os.name == 'nt':
        os.system('cls')
    else:
        os.system('clear')

@bot.tree.command(
    name="link",
    description="Fetches product details from the given URL."
)
@app_commands.describe(
    url = "URL of the product to fetch details for."
)

async def _link(ctx: discord.Interaction, url: str):
    logger = setup_custom_logger()
    logger.info(f'Someone sent a message:')
    logger.info(f'Shoelink: {url}')
    sku = url.split("/")[-1]
    try:
        response = get_product_data(sku)
        product_data = parse_product_data(response)
        embed = create_embed(product_data)
        await ctx.response.send_message(embed=embed)
        logger.info(f'TotalStock: {product_data["stock"]}')
    except Exception as e:
        if response.status_code != 200:
            error_message = f"Error with request. Status code: {response.status_code}\nResponse text: {response.text}"
            await ctx.response.send_message(error_message)
            logger.error(error_message)
        else:
            error_message = f"Error occurred: {e}"
            await ctx.response.send_message(error_message)
            logger.error(error_message)

bot.run(TOKEN)