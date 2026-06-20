from typing import List

class Position:
    def __init__(self, asset: str, side: str, entry_price: float, size: float, leverage: float):
        self.asset = asset
        self.side = side  # 'BUY' (Long) lub 'SELL' (Short)
        self.entry_price = entry_price
        self.size = size  # Wielkość pozycji w jednostkach (np. 100 000 = 1 lot)
        self.leverage = leverage
        self.unrealized_pnl = 0.0
        
    def update_pnl(self, current_price: float):
        """Aktualizuje pływający zysk/stratę na podstawie aktualnej ceny"""
        price_diff = current_price - self.entry_price if self.side == 'BUY' else self.entry_price - current_price
        
        if self.asset.endswith('USD=X') or self.asset.endswith('USD'):
            # Pary typu EURUSD=X: Zysk rodzi się od razu w dolarach (różnica cen * rozmiar w EUR)
            self.unrealized_pnl = price_diff * self.size
        else:
            # Pary typu CHF=X: Zysk rodzi się w walucie kwotowanej (np. w jenach), 
            # więc dzielimy przez AKTUALNY kurs, aby przeliczyć go na nasze dolary na koncie.
            self.unrealized_pnl = (price_diff / current_price) * self.size

    @property
    def required_margin(self) -> float:
        """Oblicza zamrożony kapitał pod pozycję na podstawie dźwigni"""
        if self.asset.endswith('USD=X') or self.asset.endswith('USD'):
            # EURUSD=X: Rozmiar jest w EUR, więc mnożymy przez cenę wejścia, aby poznać wartość w USD
            position_value_usd = self.entry_price * self.size
        else:
            # JPY=X, CHF=X: Ponieważ USD jest na początku (USD/JPY), rozmiar pozycji od razu podany jest w USD!
            position_value_usd = self.size
            
        return position_value_usd / self.leverage


class TradeLog:
    def __init__(self, asset: str, side: str, entry_time: str, exit_time: str, 
                 entry_price: float, exit_price: float, size: float, pnl: float):
        self.asset = asset
        self.side = side
        self.entry_time = entry_time
        self.exit_time = exit_time
        self.entry_price = entry_price
        self.exit_price = exit_price
        self.size = size
        self.pnl = pnl


class Wallet:
    def __init__(self, initial_balance: float, leverage: float = 30.0, stop_out_level: float = 50.0):
        self.balance = initial_balance
        self.leverage = leverage
        self.stop_out_level = stop_out_level  # Wartość procentowa (np. 50%)
        self.positions: List[Position] = []
        
    @property
    def total_used_margin(self) -> float:
        return sum(pos.required_margin for pos in self.positions)
        
    @property
    def total_unrealized_pnl(self) -> float:
        return sum(pos.unrealized_pnl for pos in self.positions)
        
    @property
    def equity(self) -> float:
        """Kapitał całkowity (Gotówka + Niezrealizowane zyski/straty)"""
        return self.balance + self.total_unrealized_pnl
        
    @property
    def margin_level(self) -> float:
        """Poziom zabezpieczenia (wyrażony w procentach). Poniżej stop_out_level zamyka pozycje."""
        used = self.total_used_margin
        if used == 0:
            return float('inf')
        return (self.equity / used) * 100
        
    @property
    def free_margin(self) -> float:
        """Wolne środki na otwarcie nowych pozycji"""
        return self.equity - self.total_used_margin