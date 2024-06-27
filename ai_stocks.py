import requests
import pandas as pd
from bs4 import BeautifulSoup
import yfinance as yf
from collections import defaultdict
import spacy

# Load spaCy model
nlp = spacy.load("en_core_web_sm")

# Initialize known AI companies for validation
known_ai_companies = {
    "nvidia", "microsoft", "google", "ibm", "amazon", "tesla", "intel", "amd", "apple", "meta", 
    "openai", "qualcomm", "salesforce", "baidu", "oracle", "sap", "huawei", "alibaba", "tencent"
}

# Function to add companies from an HTML table
def add_companies_from_html(url, table_index=0, column_name='Name', ticker_column=None):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    tables = pd.read_html(str(soup))
    print(f"Tables found: {len(tables)}")
    df = tables[table_index]
    print(f"Columns in table: {df.columns}")
    if ticker_column:
        df = df[df[ticker_column].notnull()]
    companies = df[column_name].tolist()
    known_ai_companies.update([company.lower() for company in companies])

# Scrape holdings from various ETF lists
# IGPT - Invesco AI and Next Gen Software ETF
add_companies_from_html('https://www.invesco.com/us/financial-products/etfs/holdings?audienceType=Investor&ticker=IGPT', table_index=0, column_name='Name')

# AIQ - Artificial Intelligence & Technology ETF
add_companies_from_html('https://www.globalxetfs.com/funds/aiq/', table_index=0, column_name='Name', ticker_column='Ticker')

# BOTZ - Robotics & Artificial Intelligence ETF
add_companies_from_html('https://www.globalxetfs.com/funds/botz/', table_index=0, column_name='Name', ticker_column='Ticker')

# Roundhill Generative AI & Technology ETF
add_companies_from_html('https://www.etf.com/CHAT#holdings', table_index=0, column_name='Name')

# ROBT - First Trust Nasdaq Artificial Intelligence and Robotics ETF
add_companies_from_html('https://www.ftportfolios.com/Retail/Etf/EtfHoldings.aspx?Ticker=ROBT', table_index=1, column_name='Company Name')

# IRBO - iShares Robotics and Artificial Intelligence Multisector ETF
add_companies_from_html('https://stockanalysis.com/etf/irbo/holdings/', table_index=0, column_name='Holding')

# Function to get news articles for AI-related keywords
def get_news_articles(keyword):
    url = f"https://news.google.com/search?q={keyword}&hl=en-US&gl=US&ceid=US:en"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    articles = soup.find_all('article')
    return articles

# List of AI-related keywords
ai_keywords = [
    "artificial intelligence", "machine learning", "deep learning", "neural networks",
    "natural language processing", "computer vision", "robotics", "autonomous vehicles",
    "AI chip", "AI software", "cloud AI", "AI healthcare", "AI finance", "GPT-3", "BERT"
]

# Dictionary to hold mentions for each stock
stock_mentions = defaultdict(int)

# Get news mentions for each keyword and identify companies
for keyword in ai_keywords:
    articles = get_news_articles(keyword)
    for article in articles:
        text = article.get_text()
        doc = nlp(text)
        for ent in doc.ents:
            if ent.label_ == "ORG":  # Look for organizations
                company = ent.text.lower()
                if company in known_ai_companies:
                    stock_mentions[company] += 1

# Sort the stocks by the number of mentions
sorted_stock_mentions = sorted(stock_mentions.items(), key=lambda item: item[1], reverse=True)

# Select the top N most mentioned stocks
top_n = 40
top_ai_stocks = sorted_stock_mentions[:top_n]

# Print out the top AI stocks to verify
print("Top AI Stocks by Mentions:")
for stock, mentions in top_ai_stocks:
    print(f"{stock}: {mentions} mentions")

# Function to get stock exchange and Bloomberg ticker
def get_stock_exchange_and_ticker(ticker):
    stock = yf.Ticker(ticker)
    exchange = stock.info.get('exchange')
    bloomberg_ticker = f"{ticker.upper()}:{exchange}" if exchange else ticker.upper()
    return exchange, bloomberg_ticker

# Gather financial data for the top AI stocks
ai_stocks_data = []
for stock, mentions in top_ai_stocks:
    try:
        stock_data = yf.Ticker(stock.upper())
        exchange, bloomberg_ticker = get_stock_exchange_and_ticker(stock.upper())
        data = {
            "ticker": stock.upper(),
            "name": stock_data.info['shortName'],
            "category": "AI",
            "news_mentions": mentions,
            "market_cap": stock_data.info['marketCap'],
            "pe_ratio": stock_data.info['trailingPE'],
            "price": stock_data.info['currentPrice'],
            "ytd_change": (stock_data.history(period='ytd')['Close'][-1] / stock_data.history(period='ytd')['Close'][0]) - 1,
            "exchange": exchange,
            "bloomberg_ticker": bloomberg_ticker
        }
        ai_stocks_data.append(data)
        print(f"Added data for {stock.upper()}")
    except Exception as e:
        print(f"Could not retrieve data for {stock}: {e}")

# Create a pandas DataFrame
df = pd.DataFrame(ai_stocks_data)

# Check if DataFrame is empty
if df.empty:
    print("DataFrame is empty. No valid stock data retrieved.")
else:
    # Save to Excel using the context manager to ensure proper saving and closing
    with pd.ExcelWriter('AI_Stocks.xlsx', engine='openpyxl') as excel_writer:
        df.to_excel(excel_writer, index=False, sheet_name='Top AI Stocks')
    print("AI Stocks data has been successfully saved to AI_Stocks.xlsx")
