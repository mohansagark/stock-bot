import os
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import smtplib
import feedparser
from openai import OpenAI
import gspread
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from oauth2client.service_account import ServiceAccountCredentials

# Environment variables
EMAIL_ADDRESS = os.environ.get("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")
TO_EMAIL = os.environ.get("TO_EMAIL")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
GOOGLE_SHEET_ID = os.environ.get("GOOGLE_SHEET_ID")
openai_client = OpenAI(api_key=OPENAI_API_KEY)

# NIFTY 50 tickers
NIFTY50_TICKERS = [
    "RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS", "LT.NS",
    "HINDUNILVR.NS", "SBIN.NS", "ITC.NS", "BHARTIARTL.NS", "ASIANPAINT.NS", "KOTAKBANK.NS",
    "BAJFINANCE.NS", "HCLTECH.NS", "AXISBANK.NS", "SUNPHARMA.NS", "MARUTI.NS", "WIPRO.NS",
    "NESTLEIND.NS", "ULTRACEMCO.NS", "TITAN.NS", "POWERGRID.NS", "TECHM.NS", "NTPC.NS",
    "ONGC.NS", "GRASIM.NS", "JSWSTEEL.NS", "HINDALCO.NS", "CIPLA.NS", "DRREDDY.NS",
    "ADANIENT.NS", "ADANIPORTS.NS", "COALINDIA.NS", "BAJAJ-AUTO.NS", "HEROMOTOCO.NS",
    "EICHERMOT.NS", "BRITANNIA.NS", "BPCL.NS", "HDFCLIFE.NS", "DIVISLAB.NS",
    "INDUSINDBK.NS", "BAJAJFINSV.NS", "SBILIFE.NS", "UPL.NS", "TATACONSUM.NS",
    "SHREECEM.NS", "M&M.NS", "APOLLOHOSP.NS", "TATAMOTORS.NS", "ICICIPRULI.NS"
]

# 🧠 GPT Summary
def generate_gpt_summary(df):
    prompt = f"""Given the following top NIFTY stock performers today:\n\n{df.to_string(index=False)}\n\nWrite a 3-bullet point summary with tomorrow's trading suggestions."""
    response = openai_client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

# 📊 Log to Google Sheets
def log_to_google_sheets(df):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(GOOGLE_SHEET_ID).sheet1
    today = datetime.now().strftime("%d-%b-%Y")

    for _, row in df.iterrows():
        sheet.append_row([today, row['Ticker'], row['Change(%)'], row['Volume']])

# 📈 Chart generation to /tmp/
def generate_charts(tickers):
    image_paths = []
    for ticker in tickers:
        data = yf.download(ticker, period="5d", interval="1d", progress=False)
        if data.empty:
            continue
        plt.figure()
        data['Close'].plot(title=f"{ticker} (5D Close Price)")
        chart_path = f"/tmp/{ticker}_chart.png"
        plt.savefig(chart_path)
        plt.close()
        if os.path.exists(chart_path):
            print(f"✅ Saved chart: {chart_path}")
            image_paths.append(chart_path)
    return image_paths

# 📰 Get News
def get_market_news():
    feed = feedparser.parse("https://news.google.com/rss/search?q=nifty+OR+stock+market&hl=en-IN&gl=IN&ceid=IN:en")
    return [entry['title'] for entry in feed.entries[:5]]

# 📈 Top Performers
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
        except:
            continue

    df = pd.DataFrame(results, columns=['Ticker', 'Change(%)', 'Volume'])
    return df.sort_values(by='Change(%)', ascending=False).head(5)

# 📧 Send Email
def send_email(subject, body_html, attachments=[]):
    msg = MIMEMultipart()
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = TO_EMAIL
    msg['Subject'] = subject
    msg.attach(MIMEText(body_html, 'html'))

    for path in attachments:
        with open(path, 'rb') as f:
            part = MIMEApplication(f.read(), Name=os.path.basename(path))
            part['Content-Disposition'] = f'attachment; filename="{os.path.basename(path)}"'
            msg.attach(part)

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(msg)

# 🎯 Main Run Function
def run_bot():
    print("📈 Fetching top stock performers...")
    top_stocks = get_top_performers(NIFTY50_TICKERS)

    print("📊 Logging to Google Sheets...")
    log_to_google_sheets(top_stocks)

    print("📰 Fetching market news...")
    news = get_market_news()

    print("🧠 Generating GPT summary...")
    summary = generate_gpt_summary(top_stocks)

    print("📉 Generating stock charts...")
    chart_paths = generate_charts(top_stocks['Ticker'].tolist())

    print("📤 Sending email...")
    html = "<h2>📈 Top Performing Stocks Today</h2>"
    html += top_stocks.to_html(index=False)
    html += "<h3>📰 Market News</h3><ul>" + "".join(f"<li>{n}</li>" for n in news) + "</ul>"
    html += f"<h3>🤖 GPT Market Insight</h3><pre>{summary}</pre>"
    html += "<p>Sent by your AI Stock Agent 🤖</p>"

    send_email(f"📊 Daily Stock Report - {datetime.now().strftime('%d %b %Y')}", html, chart_paths)

    print("✅ Done!")

# Entry
if __name__ == "__main__":
    run_bot()
