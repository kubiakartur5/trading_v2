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
        if self.side == 'BUY':
            self.unrealized_pnl = (current_price - self.entry_price) * self.size
        else:
            self.unrealized_pnl = (self.entry_price - current_price) * self.size

    @property
    def required_margin(self) -> float:
        """Oblicza zamrożony kapitał pod pozycję na podstawie dźwigni"""
        return (self.entry_price * self.size) / self.leverage


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