import pandas as pd
import yfinance as yf

def get_real_forex_data(ticker: str = "EURUSD=X", period: str = "1mo", interval: str = "1h") -> pd.DataFrame:
    """
    Pobiera realne dane historyczne z Yahoo Finance.
    Dla Forexu przykładowe interwały to:
    - period="1mo", interval="1h"
    - period="1y", interval="1d"
    """
    print(f"Pobieranie danych dla {ticker} z Yahoo Finance...")
    
    # Pobieranie danych
    df = yf.download(tickers=ticker, period=period, interval=interval, progress=False)
    
    # Spłaszczenie nazw kolumn, jeśli yfinance zwróci MultiIndex
    df.columns = [col[0] if isinstance(col, tuple) else col for col in df.columns]
    
    # Reset indeksu, aby Data/Czas znalazła się w zwykłej kolumnie
    df = df.reset_index()
    
    # Zmiana nazwy pierwszej kolumny na 'Date' (zależnie od interwału może to być 'Datetime')
    df.rename(columns={df.columns[0]: 'Date'}, inplace=True)
    
    # Formatowanie daty do czytelnego stringa dla logów
    df['Date'] = df['Date'].dt.strftime('%Y-%m-%d %H:%M')
    
    # Upewniamy się, że nie ma pustych wierszy na początku lub końcu
    df.dropna(inplace=True)
    
    return df