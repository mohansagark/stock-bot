import yfinance as yf
import pandas as pd
import smtplib
from datetime import datetime
import feedparser
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Email config
EMAIL_ADDRESS = 'mohansgr3@gmail.com'
EMAIL_PASSWORD = 'qcxq gmnw sinf omhr'  # <-- Replace this with your Gmail App Password
TO_EMAIL = 'mohansgr3@gmail.com'

NIFTY50_TICKERS = [
    "RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS",
    "LT.NS", "HINDUNILVR.NS", "SBIN.NS", "ITC.NS", "BHARTIARTL.NS",
    "ASIANPAINT.NS", "KOTAKBANK.NS", "BAJFINANCE.NS", "HCLTECH.NS", "AXISBANK.NS",
    "SUNPHARMA.NS", "MARUTI.NS", "WIPRO.NS", "NESTLEIND.NS", "ULTRACEMCO.NS",
    "TITAN.NS", "POWERGRID.NS", "TECHM.NS", "NTPC.NS", "ONGC.NS",
    "GRASIM.NS", "JSWSTEEL.NS", "HINDALCO.NS", "CIPLA.NS", "DRREDDY.NS",
    "ADANIENT.NS", "ADANIPORTS.NS", "COALINDIA.NS", "BAJAJ-AUTO.NS", "HEROMOTOCO.NS",
    "EICHERMOT.NS", "BRITANNIA.NS", "BPCL.NS", "HDFCLIFE.NS", "DIVISLAB.NS",
    "INDUSINDBK.NS", "BAJAJFINSV.NS", "SBILIFE.NS", "UPL.NS", "TATACONSUM.NS",
    "SHREECEM.NS", "M&M.NS", "APOLLOHOSP.NS", "TATAMOTORS.NS", "ICICIPRULI.NS"
]

def get_top_performers(tickers):
    data = yf.download(tickers, period="1d", interval="1d", group_by='ticker', progress=False)
    results = []

    for ticker in tickers:
        try:
            close = data[ticker]['Close'].iloc[0]
            open_ = data[ticker]['Open'].iloc[0]
            volume = data[ticker]['Volume'].iloc[0]
            change_pct = ((close - open_) / open_) * 100
            results.append((ticker, round(change_pct, 2), volume))
        except Exception as e:
            print(f"Error fetching data for {ticker}: {e}")

    df = pd.DataFrame(results, columns=['Ticker', 'Change(%)', 'Volume'])
    return df.sort_values(by='Change(%)', ascending=False).head(5)

def get_market_news():
    rss_url = "https://news.google.com/rss/search?q=nifty+OR+stock+market&hl=en-IN&gl=IN&ceid=IN:en"
    feed = feedparser.parse(rss_url)
    return [entry['title'] for entry in feed.entries[:5]]

def create_email_body(stocks_df, news_list):
    html = "<h2>📈 Top Performing NIFTY 50 Stocks Today</h2>"
    html += stocks_df.to_html(index=False)
    html += "<h3>📰 Market News Summary</h3><ul>"
    for news in news_list:
        html += f"<li>{news}</li>"
    html += "</ul><p>Sent by your automated stock agent 🤖</p>"
    return html

def send_email(subject, html):
    msg = MIMEMultipart()
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = TO_EMAIL
    msg['Subject'] = subject
    msg.attach(MIMEText(html, 'html'))

    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(msg)

def run_agent():
    stock_df = get_top_performers(NIFTY50_TICKERS)
    news = get_market_news()
    content = create_email_body(stock_df, news)
    subject = f"📊 Daily Stock Report - {datetime.now().strftime('%d %b %Y')}"
    send_email(subject, content)
    print("✅ Email sent!")

if __name__ == "__main__":
    run_agent()
