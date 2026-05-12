import yfinance as yf
import pandas as pd
import os
from datetime import datetime

# Universo de Reserva Institucional: ~200 Activos (Acciones, ETFs de Bonos, Materias Primas)
RESERVE_TICKERS = [
    # Megacaps & Tech
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "AVGO", "CSCO", "ADBE", 
    "CRM", "NFLX", "INTC", "AMD", "TXN", "QCOM", "IBM", "NOW", "UBER", "INTU",
    # Financials
    "JPM", "BAC", "WFC", "C", "GS", "MS", "BLK", "AXP", "V", "MA", 
    "SCHW", "SPGI", "PYPL", "CME", "CB", "PGR", "MMC", "AON", "ICE", "VTR",
    # Healthcare
    "JNJ", "UNH", "LLY", "MRK", "ABBV", "PFE", "TMO", "DHR", "ABT", "BMY", 
    "AMGN", "CVS", "SYK", "ISRG", "MDT", "GILD", "VRTX", "REGN", "HUM", "BSX",
    # Consumer (Discretionary & Staples)
    "WMT", "PG", "KO", "PEP", "COST", "MCD", "HD", "NKE", "SBUX", "TGT", 
    "LOW", "SYY", "PM", "MO", "EL", "CL", "KMB", "MDLZ", "TJX", "BKNG",
    # Industrials, Energy & Materials
    "XOM", "CVX", "COP", "SLB", "EOG", "UNP", "HON", "UPS", "LMT", "BA", 
    "CAT", "GE", "MMM", "DE", "RTX", "NOC", "GD", "LIN", "SHW", "ECL",
    # International & ADRs
    "TSM", "ASML", "NVO", "NVS", "SAP", "TM", "BABA", "BHP", "RIO", "SNY",
    "AZN", "HSBC", "UL", "TD", "RY", "SONY", "IBN", "HDB", "BUD", "DEO",
    # Renta Fija / Bonos (ETFs)
    "AGG", "BND", "TLT", "IEF", "SHY", "LQD", "HYG", "JNK", "BNDX", "EMB", 
    "MUB", "TIP", "GOVT", "VCIT", "BSV", "VCSH", "IGSB", "SPIP", "FLOT", "BKLN",
    # Broad Market & Sector ETFs
    "SPY", "QQQ", "DIA", "IWM", "VTI", "VEA", "VWO", "EEM", "EFA", "XLF",
    "XLV", "XLK", "XLE", "XLI", "XLP", "XLY", "XLU", "XLB", "XLRE", "ARKK",
    # Real Estate & Commodities
    "AMT", "PLD", "CCI", "EQIX", "PSA", "O", "SPG", "WELL", "DLR", "VNQ",
    "GLD", "SLV", "IAU", "PDBC", "USO", "UNG", "DBA", "WEAT", "CORN", "CPER"
]

def update_cache():
    print(f"[{datetime.now()}] Iniciando descarga de la Reserva Institucional (200 Activos)...")
    
    # Descargamos 5 años de datos de datos diarios
    df = yf.download(RESERVE_TICKERS, period="5y", interval="1d", progress=True)
    
    if df.empty:
        print("❌ Error: No se pudieron descargar los datos.")
        return

    # Extraemos solo los precios de cierre y aplanamos las columnas si es MultiIndex
    if isinstance(df.columns, pd.MultiIndex):
        close_data = df['Close']
    else:
        close_data = df
        
    # Limpieza: rellenar huecos (forward fill y backward fill)
    close_data = close_data.ffill().bfill()
    
    # Aseguramos que se guarde en la raíz del proyecto para que el RoboAdvisor lo encuentre
    cache_path = "roboadvisor_cache.csv"
    close_data.to_csv(cache_path)
    
    print(f"[{datetime.now()}] ✅ Caché actualizado exitosamente en '{cache_path}'")
    print(f"📊 Activos reales procesados y guardados: {len(close_data.columns)}")

if __name__ == "__main__":
    update_cache()