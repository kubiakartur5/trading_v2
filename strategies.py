import pandas as pd

class BaseStrategy:
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        raise NotImplementedError


class SMACrossoverStrategy(BaseStrategy):
    """Strategia podążania za trendem: Przecięcie średnich kroczących"""
    def __init__(self, short_window=10, long_window=30):
        self.short_window = short_window
        self.long_window = long_window

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        
        # Obliczanie średnich SMA
        df['sma_short'] = df['Close'].rolling(window=self.short_window).mean()
        df['sma_long'] = df['Close'].rolling(window=self.long_window).mean()
        
        df['signal'] = 0
        df.loc[df['sma_short'] > df['sma_long'], 'signal'] = 1  
        df.loc[df['sma_short'] < df['sma_long'], 'signal'] = -1 
        return df


class RSICloseStrategy(BaseStrategy):
    """Strategia Mean Reversion: Wskaźnik RSI"""
    def __init__(self, periods=14, overbought=70, oversold=30):
        self.periods = periods
        self.overbought = overbought
        self.oversold = oversold

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        
        # Obliczanie RSI
        delta = df['Close'].diff()
        
        # Oddzielenie wzrostów od spadków
        gain = delta.where(delta > 0, 0.0)
        loss = -delta.where(delta < 0, 0.0)
        
        # Wyliczenie średniej kroczącej ze wzrostów i spadków
        avg_gain = gain.rolling(window=self.periods, min_periods=self.periods).mean()
        avg_loss = loss.rolling(window=self.periods, min_periods=self.periods).mean()
        
        # Wzór na Relative Strength (RS)
        rs = avg_gain / avg_loss
        
        # Wzór na RSI
        df['rsi'] = 100 - (100 / (1 + rs))
        
        df['signal'] = 0
        df.loc[df['rsi'] < self.oversold, 'signal'] = 1   
        df.loc[df['rsi'] > self.overbought, 'signal'] = -1 
        return df


class BollingerBandsStrategy(BaseStrategy):
    """Strategia wybiciowa: Wstęgi Bollingera"""
    def __init__(self, window=20, num_std=2):
        self.window = window
        self.num_std = num_std

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        
        # Obliczanie Wstęg Bollingera
        df['sma'] = df['Close'].rolling(window=self.window).mean()
        df['std'] = df['Close'].rolling(window=self.window).std()
        
        df['lower'] = df['sma'] - (self.num_std * df['std'])
        df['upper'] = df['sma'] + (self.num_std * df['std'])
        
        df['signal'] = 0
        df.loc[df['Close'] < df['lower'], 'signal'] = 1  
        df.loc[df['Close'] > df['upper'], 'signal'] = -1 
            
        return df