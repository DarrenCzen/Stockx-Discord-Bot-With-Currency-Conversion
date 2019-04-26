import discord
from discord.ext import commands
import json
import requests
from currency_converter import CurrencyConverter

c = CurrencyConverter()

# The currency which you want to change to from USD, see CurrencyConverter python package for shortcut of currency
convertedCurrency = 'SGD'
token = 'Insert Discord Token Here'
# Change the prefix if you want
client = commands.Bot(command_prefix = '!')
client.remove_command('help')

@client.event
async def on_ready():
    print('Bot is ready.')

@client.command(pass_context=True)
async def logout(ctx):
    await client.logout()
    exit()

@client.command(pass_context=True)
async def sx(ctx, *args):
    keywords = ''
    for word in args:
        keywords += word + '%20'
    json_string = json.dumps({"params": f"query={keywords}&hitsPerPage=20&facets=*"})
    byte_payload = bytes(json_string, 'utf-8')
    algolia = {"x-algolia-agent": "Algolia for vanilla JavaScript 3.32.0", "x-algolia-application-id": "XW7SBCT9V6", "x-algolia-api-key": "6bfb5abee4dcd8cea8f0ca1ca085c2b3"}
    with requests.Session() as session:
        r = session.post("https://xw7sbct9v6-dsn.algolia.net/1/indexes/products/query", params=algolia, verify=False, data=byte_payload, timeout=30)
        results = r.json()["hits"][0]
        apiurl = f"https://stockx.com/api/products/{results['url']}?includes=market,360&currency=USD"
        header = {
            'accept': '*/*',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'en-US,en;q=0.9,ja-JP;q=0.8,ja;q=0.7,la;q=0.6',
            'appos': 'web',
            'appversion': '0.1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'
        }
        response = requests.get(apiurl, verify=False, headers=header)

    prices = response.json()
    general = prices['Product']
    market = prices['Product']['market']
    sizes = prices['Product']['children']
   
    bidasks = ''
    for size in sizes:
        sgdAsk = int(c.convert(sizes[size]['market']['lowestAsk'], 'USD', convertedCurrency))
        sgdBid = int(c.convert(sizes[size]['market']['highestBid'], 'USD', convertedCurrency))
        usdValue = (int(sizes[size]['market']['highestBid']) * 0.875) - 30 
        sgdAfter = int(c.convert(usdValue, 'USD', convertedCurrency))
        bidasks +=f"{sizes[size]['shoeSize']} | {convertedCurrency} {sgdAsk} | {convertedCurrency} {sgdBid} ({sizes[size]['market']['highestBid']}) | {convertedCurrency} {sgdAfter} \n"

    embed = discord.Embed(title='StockX Checker', color=0x13e79e)
    embed.set_thumbnail(url=results['thumbnail_url'])
    embed.add_field(name=general['title'], value='https://stockx.com/' + general['urlKey'], inline=False)
    if 'styleId' in general:
        embed.add_field(name='SKU/PID:', value=general['styleId'], inline=True)
    else:
        embed.add_field(name='SKU/PID:', value='None', inline=True)
    if 'colorway' in general:
        embed.add_field(name='Colorway:', value=general['colorway'], inline=True)
    else:
        embed.add_field(name='Colorway:', value='None', inline=True)
    if 'retailPrice' in general:
        embed.add_field(name='Retail Price:', value=f"${general['retailPrice']}", inline=True)
    else:
        for trait in general['traits']:
            try:
                embed.add_field(name='Retail Price:', value=f"${int(trait['value'])}")
            except:
                pass

    embed.add_field(name='Total Asks:', value=market['numberOfAsks'], inline=True)
    embed.add_field(name='Total Bids:', value=market['numberOfBids'], inline=True)
    embed.add_field(name='Total Sold:', value=market['deadstockSold'], inline=True)
    embed.add_field(name='Sizes | Low Ask | High Bid:', value=bidasks, inline=False)
    await ctx.send(embed=embed)

if __name__ == "__main__":
    client.run(token)
