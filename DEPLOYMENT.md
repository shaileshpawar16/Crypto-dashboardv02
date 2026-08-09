# Streamlit Community Cloud Deployment

## Repository
Keep these in GitHub:
- appv2.py
- requirements.txt
- README.md
- .gitignore
- optional .streamlit/config.toml

Do NOT commit:
- .streamlit/secrets.toml
- API keys
- passwords/tokens

## Local secrets
Create `.streamlit/secrets.toml`:
```toml
COINGECKO_API_KEY = "YOUR_REAL_KEY"
```

Read it in Python:
```python
import streamlit as st
COINGECKO_API_KEY = st.secrets["COINGECKO_API_KEY"]
```

## Streamlit Cloud
Create the app from the GitHub repository, select the `main` branch and `appv2.py`, then add the CoinGecko key under the app's Secrets settings.

## Live test
Check API connection, ticker, search, single/multiple selection, KPIs, movers, historical charts, performance, insights, and error handling.

If a real API key was ever committed to a public repository, rotate/revoke it before deployment.
