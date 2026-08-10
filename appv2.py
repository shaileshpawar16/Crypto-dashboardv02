import numpy as np
import streamlit as st
from google import genai
import pandas as pd
import requests
from websockets import Data
import plotly.express as px

# Page Config
st.set_page_config(page_title="Crypto Dashboard v1.2", layout="wide")

# ==========================================================
# AI ASSISTANT
# ==========================================================

GEMINI_API_KEY = st.secrets["Gemini_api_key"]

gemini_client = genai.Client(api_key=GEMINI_API_KEY)

AI_SYSTEM_INSTRUCTION = """
You are the conversational AI assistant for Crypto Market Intelligence.

Your purpose is to help users understand cryptocurrency and the information
shown in this dashboard.

Use simple, everyday language.
Avoid technical terminology unless necessary.
If you must use a technical term, explain it immediately in simple language.
Do not make answers unnecessarily academic or complicated.
Prefer short explanations, practical examples, and simple analogies.
Write for someone who may know very little about cryptocurrency.

You can answer questions about cryptocurrency, blockchain, Bitcoin, Ethereum,
altcoins, stablecoins, DeFi, NFTs, wallets, mining, consensus mechanisms,
tokenomics, market capitalization, volume, volatility, historical performance,
and other cryptocurrency-related concepts.

Do not provide trading functionality, buy/sell signals, or personalized
trading recommendations.

When a question relates to the dashboard, use the dashboard data provided
to you. Do not invent values or market information.

If the dashboard data is insufficient to answer a question, say so.

Be conversational, friendly, clear, and easy to understand.
Prefer plain language and useful examples.

For complex concepts, explain them step by step when appropriate and asked
by the user.
"""

# ------------------------------------------------------------
# Title
# ------------------------------------------------------------
st.markdown("""
# <div style="display:flex;alighn-items: right;gap: 5px;"></div>
    
<div>
<h1> 🪙 Crypto Market Intelligence Dashboard</h1>
<h5>                                                 </h5>
</div> """, unsafe_allow_html=True) 

# -------------------------------
# Data Fetch Function
# -------------------------------
@st.cache_data(ttl=60)
def get_crypto_data():
    url = "https://api.coingecko.com/api/v3/coins/markets"

    params = {
        "vs_currency": "usd",
        "order": "market_cap_desc",
        "per_page": 10,
        "page": 1,
    }

    try:
        response = requests.get(
            url,
            params=params,
            timeout=10
        )

        # Handle rate limiting separately
        if response.status_code == 429:
            st.warning(
                "⏳ Live market data is temporarily unavailable. "
                "Please try again shortly."
            )
            return pd.DataFrame()

        response.raise_for_status()

        data = response.json()

        # Validate API response
        if not isinstance(data, list) or len(data) == 0:
            st.warning(
                "⚠️ Market data is temporarily unavailable. "
                "Please try again shortly."
            )
            return pd.DataFrame()

        df = pd.DataFrame(data)

        required_cols = [
            "id",
            "symbol",
            "name",
            "current_price",
            "price_change_percentage_24h",
            "total_volume",
        ]

        missing_cols = [
            col for col in required_cols
            if col not in df.columns
        ]

        if missing_cols:
            st.warning(
                "⚠️ Market data is temporarily unavailable. "
                "Please try again shortly."
            )
            return pd.DataFrame()

        df = df[required_cols]

        df.columns = [
            "ID",
            "Symbol",
            "Coin",
            "Price",
            "24h Change (%)",
            "Volume"
        ]

        return df

    except requests.exceptions.Timeout:
        st.warning(
            "⏳ Market data request timed out. "
            "Please try again shortly."
        )
        return pd.DataFrame()

    except requests.exceptions.ConnectionError:
        st.warning(
            "🌐 Unable to connect to the market data service. "
            "Please try again shortly."
        )
        return pd.DataFrame()

    except requests.exceptions.HTTPError:
        st.warning(
            "⚠️ Market data is temporarily unavailable. "
            "Please try again shortly."
        )
        return pd.DataFrame()

    except requests.exceptions.RequestException:
        st.warning(
            "⚠️ Unable to retrieve live market data. "
            "Please try again shortly."
        )
        return pd.DataFrame()

    except Exception:
        st.warning(
            "⚠️ Something went wrong while loading market data. "
            "Please try again shortly."
        )
        return pd.DataFrame()
# -------------------------------
# Load Data
# -------------------------------
crypto_df = get_crypto_data()

performance_df = crypto_df.copy()

performance_df = performance_df.rename(
    columns={
        "24h Change (%)": "24H Change (%)"
    }
)
@st.cache_data(ttl=300)
def get_historical_data(coin_id, days=30):
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"

    params = {
        "vs_currency": "usd",
        "days": days
    }

    try:
        response = requests.get(
            url,
            params=params,
            timeout=10
        )

        if response.status_code == 429:
            st.warning(
                "⏳ Historical market data is temporarily unavailable. "
                "Please try again shortly."
            )
            return pd.DataFrame()

        response.raise_for_status()

        data = response.json()

        if "prices" not in data or not data["prices"]:
            st.warning(f"⚠️ No historical data available for {coin_id}")
            return pd.DataFrame()

        historical_df = pd.DataFrame(
            data["prices"],
            columns=["Timestamp", "Price"]
        )

        historical_df["Date"] = pd.to_datetime(
            historical_df["Timestamp"],
            unit="ms"
        )

        historical_df["Coin"] = coin_id

        return historical_df[
            ["Date", "Coin", "Price"]
        ]

    except requests.exceptions.Timeout:
        st.error(f"⏳ Historical data request timed out for {coin_id}")
        return pd.DataFrame()

    except requests.exceptions.ConnectionError:
        st.error("🌐 Internet connection error.")
        return pd.DataFrame()

    except requests.exceptions.HTTPError as err:
        st.error(f"🚨 Historical API HTTP Error: {err}")
        return pd.DataFrame()

    except requests.exceptions.RequestException as err:
        st.error(f"⚠️ Historical API request error: {err}")
        return pd.DataFrame()

    except Exception as e:
        st.error(f"❌ Historical data error: {e}")
        return pd.DataFrame()
    
test_history = get_historical_data("bitcoin", days=30)

ticker_df=crypto_df.copy()
ticker_items = []

# ==========================================================
# BUILD TICKER
# ==========================================================
for _, row in ticker_df.iterrows():

    change = row["24h Change (%)"]

    if change > 0:
        arrow = "▲"
        css_class = "positive"
    elif change < 0:
        arrow = "▼"
        css_class = "negative"
    else:
        arrow = "N"
        css_class = "neutral"

    ticker_items.append(
        f'<span class="ticker_items {css_class}">'
        f'{row["Symbol"].upper()}: ${row["Price"]:,.2f} {arrow} {change:.2f}%'
        f'</span>'
    )

seprator = "&nbsp;" * 8 + "  " + "&nbsp;" * 8
ticker_text = seprator.join(ticker_items)

st.markdown("""
 <style>

.ticker_wrapper{
    width:100%;
    overflow:hidden;
    background-color:inherit;
    border-radius:10px;
    padding:12px 0;
}

.ticker_track{
    display:inline-block;
    width:max-content;
    white-space:nowrap;
    color:inherit;
    font-size:18px;
    font-weight:bold;
    animation:ticker 45s linear infinite;
}

@keyframes ticker{

    from{
        transform:translateX(0%);
    }

    to{
        transform:translateX(-50%);
    }

}


.ticker_items{
    font-weight:600;
    transition:color .3s ease;
}

.ticker_items.positive{
    color:#22C55E;
}

.ticker_items.negative{
    color:#EF4444;
}

.ticker_items.neutral{
    color:#87CEEB;
}
</style>
""", unsafe_allow_html=True)

# -------------------------------
# Ticker HTML
# -------------------------------
st.markdown(
    f"""
    <div class="ticker_wrapper">
        <div class="ticker_track">
            {ticker_text}
            &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
            {ticker_text}
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

if crypto_df.empty:
    st.stop()



# Breathing space before KPI Cards

st.markdown("<br>", unsafe_allow_html=True)



# ==========================================================
# KEY MARKET METRICS + COIN SELECTION PANEL
# ==========================================================

st.markdown("""
<style>

/* ==========================================================
   KPI CARD
========================================================== */

.kpi-card{
    background: transparent;
    border: 1px solid rgba(128, 128, 128, 0.25);
    border-radius: 10px;
    padding: 14px 18px;
    min-height: 110px;
    transition: all 0.25s ease;
}

/* ==========================================================
   KPI CARD HOVER
========================================================== */

.kpi-card:hover{
    border-color: #4F8EF7;
    transform: translateY(-2px);
}

/* ==========================================================
   24H PERFORMANCE CHART
========================================================== */

.performance-chart-card{
    width:100%;
    background:transparent;
    border:1px solid rgba(128,128,128,0.25);
    border-radius:10px;
    padding:18px;
    box-sizing:border-box;
    transition:all .25s ease;
}
/* ==========================================================
   KPI LABEL
========================================================== */

.kpi-label{
    color: #8B8F98;
    font-size: 15px;
    font-weight: 500;
    margin-bottom: 14px;
}

/* ==========================================================
   KPI VALUE
========================================================== */

.kpi-value{
    color: inherit;
    font-size: 28px;
    font-weight: 700;
    line-height: 1.2;
    margin-bottom: 12px;
}

/* ==========================================================
   KPI DELTA
========================================================== */

.kpi-delta{
    color: #22C55E;
    font-size: 18px;
    font-weight: 600;
}

/* ==========================================================
   MARKET MOVERS CARD
========================================================== */

.market-card{
    background: transparent;
    border: 1px solid rgba(128,128,128,0.25);
    border-radius: 10px;
    padding: 18px;
    min-height: 260px;
    transition: all .25s ease;
    box-shadow: 0 4px 12px rgba(0,0,0,0.18);
}

.market-card:hover{
    border-color:#4F8EF7;
    transform:translateY(-2px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.18);
}
/* ==========================================================
   AI SUMMARY INSIGHTS
========================================================== */

.ai-insight{
    display:flex;
    align-items:flex-start;
    gap:10px;
    background:rgba(128,128,128,0.04);
    border:1px solid rgba(128,128,128,0.12);
    border-radius:8px;
    padding:12px 14px;
    margin-bottom:8px;
    font-size:20px;
    line-height:1.5;
}
.ai-insight strong{
    font-size:20px;
}
.ai-icon{
    width:24px;
    min-width:24px;
    font-size:16px;
    line-height:1.5;
}
.ai-insight{
    background:rgba(128,128,128,0.04);
    border:1px solid rgba(128,128,128,0.12);
    border-radius:8px;
    padding:12px 14px;
    margin-bottom:8px;
}
.ai-metric-card{
    background:rgba(128,128,128,0.04);
    border:1px solid rgba(128,128,128,0.12);
    border-radius:8px;
    padding:14px;
    box-sizing:border-box;
}
.ai-metric-card strong{
    font-size:20px;
}

.ai-metric-value{
    font-size:30px;
    font-weight:600;
    margin-top:6px;
}
/* ==========================================================
   MARKET CARD TITLE
========================================================== */

.market-title{
    font-size:20px;
    font-weight:700;
    margin-bottom:20px;
    color:inherit;
}
/* ==========================================================
   MARKET ROW
========================================================== */

.market-row{
    display:flex;
    align-items:center;
    justify-content:space-between;
    padding:12px 0;
}
/* ==========================================================
   MARKET RANK
========================================================== */

.market-rank{
    width:40px;
    color:#8B8F98;
    font-size:15px;
    font-weight:600;
}
/* ==========================================================
   MARKET COIN
========================================================== */

.market-coin{
    flex:1;
    font-size:18px;
    font-weight:700;
    color:inherit;
}
/* ==========================================================
   MARKET CHANGE
========================================================== */

.market-change{
    font-size:17px;
    font-weight:700;
}
/* ==========================================================
   VIEW ALL
========================================================== */

.view-all{
margin-top:20px;
font-size:15px;
font-weight:600;
color:#4F8EF7;
cursor:pointer;
}
/* ==========================================================
   COIN SEARCH PANEL
========================================================== */

.stMultiSelect [data-baseweb="select"] > div{
background:rgba(128,128,128,0.04);
border:1px solid rgba(128,128,128,0.18);
border-radius:8px;
min-height:46px;
}
.stMultiSelect [data-baseweb="select"] input{
font-size:15px;
}

.stMultiSelect [data-baseweb="select"] input::placeholder{
opacity:0.65;
}
/* ==========================================================
   COIN SEARCH RESULTS
========================================================== */

li[role="option"]{
font-size:15px;
padding:10px 14px;
}
/* Remove selected coin tag styling */

.stMultiSelect [data-baseweb="tag"]{
background:transparent !important;
border:none !important;
box-shadow:none !important;
padding:0 !important;
}
.stMultiSelect [data-baseweb="tag"] span[title]{
background:transparent !important;
color:inherit !important;
opacity:1 !important;
-webkit-text-fill-color:currentColor !important;
}
.stMultiSelect [data-baseweb="tag"]{
color:inherit !important;
opacity:1 !important;
}
 .stMultiSelect [data-baseweb="tag"]{
 margin-right:6px !important;
 }
 /* Remove blue focus effect from KPI cards */
div[data-testid="stMetric"]:focus,
div[data-testid="stMetric"]:focus-within,
div[data-testid="stMetric"]:focus-visible {
    outline: none !important;
    box-shadow: none !important;
}

/* Keep KPI cards unchanged on hover/click */
div[data-testid="stMetric"]:hover,
div[data-testid="stMetric"]:active {
    outline: none !important;
    box-shadow: none !important;
}

/* Remove blue focus effect from Streamlit bordered containers */
div[data-testid="stVerticalBlockBorderWrapper"]:focus,
div[data-testid="stVerticalBlockBorderWrapper"]:focus-within,
div[data-testid="stVerticalBlockBorderWrapper"]:focus-visible {
    outline: none !important;
    box-shadow: none !important;
    border-color: rgba(255, 255, 255, 0.12) !important;
}

/* Keep the normal border when hovering */
div[data-testid="stVerticalBlockBorderWrapper"]:hover {
    border-color: rgba(255, 255, 255, 0.12) !important;
    box-shadow: none !important;
}
</style>
""", unsafe_allow_html=True)

# ==========================================================
# KEY MARKET METRICS
# ==========================================================

main_col, side_col = st.columns([3, 1])

# ==========================================================
# KPI CARDS
# ==========================================================

with main_col:

    kpi1, kpi2, kpi3, kpi4, control = st.columns([2,2,2,2,1])

    with kpi1:

        st.markdown("""
        <div class="kpi-card">
            <div class="kpi-label">🏆 Top Performer</div>
            <div class="kpi-value">Ethereum</div>
            <div class="kpi-delta">▲ +8.21%</div>
        </div>
        """, unsafe_allow_html=True)

    with kpi2:

        st.markdown("""
        <div class="kpi-card">
            <div class="kpi-label">💰 Market Cap</div>
            <div class="kpi-value">$2.43T</div>
            <div class="kpi-delta">▲ +2.80%</div>
        </div>
        """, unsafe_allow_html=True)

    

    with kpi3:

        st.markdown("""
        <div class="kpi-card">
            <div class="kpi-label">📊 24H Volume</div>
            <div class="kpi-value">$118B</div>
            <div class="kpi-delta">▲ +6.40%</div>
        </div>
        """, unsafe_allow_html=True)

    with kpi4:

        st.markdown("""
        <div class="kpi-card">
            <div class="kpi-label">📈 Market Mood</div>
            <div class="kpi-value">Bullish</div>
            <div class="kpi-delta">Positive</div>
        </div>
        """, unsafe_allow_html=True)



# -------------------------------
# Market Movers Section
# -------------------------------

st.subheader(" Market Movers")

st.markdown("<br>", unsafe_allow_html=True)
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
<div class="market-card">

<div class="market-title">
🟢 Top Gainers
</div>

<div class="market-row">
<div class="market-rank">01</div>
<div class="market-coin">ETH</div>
<div class="market-change positive">+8.25%</div>
</div>

<div class="market-row">
<div class="market-rank">02</div>
<div class="market-coin">SOL</div>
<div class="market-change positive">+5.60%</div>
</div>

<div class="market-row">
<div class="market-rank">03</div>
<div class="market-coin">BTC</div>
<div class="market-change positive">+3.12%</div>
</div>


</div>

""", unsafe_allow_html=True)



with col2:

    st.markdown("""
<div class="market-card">

<div class="market-title">
🔴 Top Losers
</div>

<div class="market-row">
<div class="market-rank">01</div>
<div class="market-coin">HYPE</div>
<div class="market-change negative">-3.00%</div>
</div>

<div class="market-row">
<div class="market-rank">02</div>
<div class="market-coin">BNB</div>
<div class="market-change negative">-1.60%</div>
</div>

<div class="market-row">
<div class="market-rank">03</div>
<div class="market-coin">XRP</div>
<div class="market-change negative">-1.50%</div>
</div>



</div>
""", unsafe_allow_html=True)

with col3:

    st.markdown("""
<div class="market-card">

<div class="market-title">
⚡ High Volatility
</div>

<div class="market-row">
<div class="market-rank">01</div>
<div class="market-coin">ETH</div>
<div class="market-change positive">8.25%</div>
</div>

<div class="market-row">
<div class="market-rank">02</div>
<div class="market-coin">SOL</div>
<div class="market-change positive">5.60%</div>
</div>

<div class="market-row">
<div class="market-rank">03</div>
<div class="market-coin">BTC</div>
<div class="market-change positive">3.12%</div>
</div>



</div>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)   

# -------------------------------
# Data for Performance_df
# -------------------------------


# ==========================================================
# RIGHT SIDE - COIN SELECTION PANEL
# ==========================================================

with side_col:

    st.markdown("### 🔍 Coin Search")
    selected_coins = st.multiselect(
    " ",
    crypto_df["Coin"].tolist()
)


placeholder="Search or select coins..."


def get_selected_data(selected_coins, data):
    if not selected_coins:
        return data
# convert volume to numeric
    return data[data["Coin"].isin(selected_coins)]   
performance_df["Volume_Numeric"] = (
    performance_df["Volume"] / 1_000_000_000
)
# get selected coin data
selected_data = get_selected_data(selected_coins, performance_df)

top_performer = selected_data.loc[
    selected_data["24H Change (%)"].idxmax()
]
top_performer_text = (
    f"{top_performer['Coin']} "
    f"(+{top_performer['24H Change (%)']:.2f}%)"
)
weakest_performer = selected_data.loc[
    selected_data["24H Change (%)"].idxmin()
]

weakest_performer_text = (
    f"{weakest_performer['Coin']} "
    f"({weakest_performer['24H Change (%)']:.2f}%)"
)

selected_volume = selected_data["Volume_Numeric"].sum()
volatility = selected_data["24H Change (%)"].std()
if volatility < 1:
    market_risk_text = "Low Volatility"
elif volatility < 3:
    market_risk_text = "Moderate Volatility"
else:
    market_risk_text = "High Volatility"

average_change = selected_data["24H Change (%)"].mean()
if average_change > 2:
    market_sentiment_text = "Bullish"
elif average_change < -2:
    market_sentiment_text = "Bearish"
else:
    market_sentiment_text = "Neutral"

if market_sentiment_text == "Bullish":
    ai_observation_text = (
        f"{top_performer['Coin']} is leading the selected market "
        f"while overall sentiment remains bullish."
    )

elif market_sentiment_text == "Bearish":
    ai_observation_text = (
        f"{weakest_performer['Coin']} is showing the weakest performance "
        f"while overall sentiment remains bearish."
    )

else:
    ai_observation_text = (
        f"{top_performer['Coin']} is outperforming while the "
        f"selected market remains relatively balanced."
    )

market_activity_text = (
    f"Selected coins are trading with "
    f"${selected_volume:.1f}B in volume."
)

# ---------------------------------------------------------
# 24 Hour Performance Chart
# ---------------------------------------------------------
st.subheader("24h Price Movement")

performance_fig = px.line(
    selected_data,
    x="Coin",
    y="24H Change (%)",
    markers=True
)
performance_fig.update_layout(
    title="",
    xaxis_title=None,
    yaxis_title=None,
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    margin=dict(l=20, r=20, t=20, b=20),
    dragmode=False,
    height=400
)
performance_fig.update_xaxes(
    showgrid=False,
    zeroline=False,
    showline=False,
    tickangle=0,
    ticks=""
)

performance_fig.update_yaxes(
    showgrid=False,
    zeroline=False,
    showline=False,
    ticksuffix="%"
)

performance_fig.update_traces(
    line=dict(width=2,color="rgba(128,128,128,0.45)"),
    marker=dict(size=8,
               color=[ "#22C55E"
            if value > 0
            else "#EF4444" if value < 0
            else "#3B82F6"
            for value in performance_df["24H Change (%)"]],
            line=dict(width=1,color="rgba(255,255,255,0.55)")
            ),

    customdata=performance_df[
        ["Coin", "Price", "Volume"]
    ],
    hovertemplate=
        "<b>🪙 %{customdata[0]}</b><br><br>"
        "📈 24H Change: %{y:.2f}%<br>"
        "💲 Price: $%{customdata[1]:,.2f}<br>"
        "💰 Volume: $%{customdata[2]:,.2f}"
        "<extra></extra>"
)

st.plotly_chart(
    performance_fig,
    use_container_width=True,
    config={
        "displayModeBar": False,
        "scrollZoom": False,
        "doubleClick": False
    }
)


# ==========================================================
# Historical Price Trend
# ==========================================================

st.subheader(" Historical Price Performance ")

days = 30

historical_data = []

# Use Bitcoin as default when nothing is selected
coins_to_fetch = selected_coins if selected_coins else ["Bitcoin"]

for coin in coins_to_fetch:

    # Find CoinGecko ID for the selected coin
    coin_row = crypto_df[
        crypto_df["Coin"] == coin
    ]

    if coin_row.empty:
        continue

    coin_id = coin_row.iloc[0]["ID"]

    # Fetch real historical data
    coin_history = get_historical_data(
        coin_id,
        days=days
    )

    if coin_history.empty:
        continue

    # Replace API ID with readable coin name
    coin_history["Coin"] = coin

    historical_data.append(coin_history)


if historical_data:

    historical_df = pd.concat(
        historical_data,
        ignore_index=True
    )

else:

    historical_df = pd.DataFrame(
        columns=["Date", "Coin", "Price"]
    )

# Normalize each coin to 100 at the beginning of the period
historical_df["Indexed Price"] = (
    historical_df
    .groupby("Coin")["Price"]
    .transform(lambda x: (x / x.iloc[0]) * 100)
)
historical_df["Performance (%)"] = (
    historical_df["Indexed Price"] - 100
)

fig = px.line(
    historical_df,
    x="Date",
    y="Indexed Price",
    color="Coin",
    markers=False   ,
    line_shape="spline"
)

fig.update_layout(
    title="",
    xaxis_title=None,
    yaxis_title="Indexed Price (Start = 100)",
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    margin=dict(l=20, r=20, t=20, b=20),
    hovermode="closest",
    dragmode=False,
    height=450 
    
)

fig.update_xaxes(
    showgrid=False,
    zeroline=False
)

fig.update_yaxes(
    showgrid=False,
    zeroline=False
)

fig.update_traces(
    line=dict(width=3),
    hovertemplate=
    "📅 %{x|%d %b %Y}<br>"
    "📈 Performance: %{customdata:.2f}%"
    "<extra></extra>",
    customdata=historical_df["Performance (%)"]
)



st.plotly_chart(
    fig,
    use_container_width=True,
    config={
    "displayModeBar": False,
    "scrollZoom": False,
    "doubleClick": False
    }
)

# ---------------------------------------------------------
# Dashboard Context for AI Integration
# ---------------------------------------------------------
def build_dashboard_context(selected_data, historical_df=None):
    """
    Build a compact snapshot of the dashboard data for the future AI assistant.

    This function does not call any API and does not connect to Gemini.
    It only prepares the information already available in the dashboard.
    """
    if selected_data.empty:
        return {
            "selected_coins": [],
            "coin_data": [],
            "top_performer": None,
            "weakest_performer": None,
            "market_sentiment": "No data",
            "market_risk": "No data",
        }

    coin_data = []
    for _, row in selected_data.iterrows():
        coin_data.append({
            "coin": row["Coin"],
            "symbol": row["Symbol"],
            "price_usd": float(row["Price"]),
            "change_24h_percent": float(row["24H Change (%)"]),
            "volume_usd": float(row["Volume"]),
        })

    context = {
        "selected_coins": selected_data["Coin"].tolist(),
        "coin_data": coin_data,
        "top_performer": {
            "coin": top_performer["Coin"],
            "change_24h_percent": float(top_performer["24H Change (%)"]),
        },
        "weakest_performer": {
            "coin": weakest_performer["Coin"],
            "change_24h_percent": float(weakest_performer["24H Change (%)"]),
        },
        "market_sentiment": market_sentiment_text,
        "market_risk": market_risk_text,
    }

    if historical_df is not None and not historical_df.empty:
        historical_summary = []

        for coin, group in historical_df.groupby("Coin"):
            if group.empty:
                continue

            first_price = float(group["Price"].iloc[0])
            last_price = float(group["Price"].iloc[-1])

            if first_price != 0:
                performance = ((last_price / first_price) - 1) * 100
            else:
                performance = None

            historical_summary.append({
                "coin": coin,
                "period_days": days,
                "performance_percent": performance,
            })

        context["historical_summary"] = historical_summary
    else:
        context["historical_summary"] = []

    return context




# ---------------------------------------------------------
# Build the current dashboard context for AI
# ---------------------------------------------------------
dashboard_context = build_dashboard_context(
    selected_data,
    historical_df
)

# ---------------------------------------------------------
# Market Insights
# ---------------------------------------------------------

st.markdown("### Market Insights")

# Market Sentiment
st.markdown(f"""
<div class="ai-insight">
    <span class="ai-icon">⭕</span>
    <span>
        <strong>Market Sentiment</strong><br>
        {market_sentiment_text}
    </span>
</div>
""", unsafe_allow_html=True)

# Top Performer
st.markdown(f"""
<div class="ai-insight">
    <span class="ai-icon">📈</span>
    <span>
        <strong>Top Performer</strong><br>
        {top_performer_text}
    </span>
</div>
""", unsafe_allow_html=True)

# Weakest Performer
st.markdown(f"""
<div class="ai-insight">
    <span class="ai-icon">📉</span>
    <span>
        <strong>Weakest Performer</strong><br>
        {weakest_performer_text}
    </span>
</div>
""", unsafe_allow_html=True)


# Market Risk
st.markdown(f"""
<div class="ai-insight">
    <span class="ai-icon">⚠️</span>
    <span>
        <strong>Market Risk</strong><br>
        {market_risk_text}
    </span>
</div>
""", unsafe_allow_html=True)

# ==========================================================
# ASK AI
# ==========================================================

st.markdown("<br>", unsafe_allow_html=True)

st.markdown(
    """
    <div class="section-header">
        <div class="section-title">🤖 Ask AI</div>
        <div class="section-subtitle">
            Ask about cryptocurrency or the data shown on this dashboard.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

if "ai_open" not in st.session_state:
    st.session_state.ai_open = False

if "ai_messages" not in st.session_state:
    st.session_state.ai_messages = []

col_ai, col_clear = st.columns([5, 1])

with col_ai:
    if st.button("🤖 Ask AI", key="open_ai_button"):
        st.session_state.ai_open = True

with col_clear:
    if st.session_state.ai_messages:
        if st.button("Clear", key="clear_ai_button"):
            st.session_state.ai_messages = []
            st.rerun()

if st.session_state.ai_open:

    for message in st.session_state.ai_messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    ai_prompt = st.chat_input(
        "Ask anything about cryptocurrency or this dashboard...",
        key="crypto_ai_chat_input",
    )

    if ai_prompt:

        st.session_state.ai_messages.append(
            {
                "role": "user",
                "content": ai_prompt,
            }
        )

        with st.chat_message("user"):
            st.write(ai_prompt)

        dashboard_context_text = str(dashboard_context)

        conversation = [
            {
                "role": "user",
                "parts": [
                    {
                        "text": (
                            "Here is the current dashboard data. "
                            "Use it when answering dashboard-related questions. "
                            "Do not invent or change these values.\n\n"
                            + dashboard_context_text
                        )
                    }
                ],
            }
        ]

        for message in st.session_state.ai_messages:
            conversation.append(
                {
                    "role": (
                        "user"
                        if message["role"] == "user"
                        else "model"
                    ),
                    "parts": [
                        {
                            "text": message["content"]
                        }
                    ],
                }
            )

        try:

            response = gemini_client.models.generate_content(
                model="gemini-3.5-flash",
                contents=conversation,
                config={
                    "system_instruction": AI_SYSTEM_INSTRUCTION
                },
            )

            answer = response.text or (
                "⚠️ I couldn't generate a response right now. "
                "Please try again shortly."
            )

        except Exception:

            answer = (
                "⚠️ I'm temporarily unable to respond right now. "
                "Please try again in a little while."
            )

        st.session_state.ai_messages.append(
            {
                "role": "assistant",
                "content": answer,
            }
        )

        with st.chat_message("assistant"):
            st.write(answer)


