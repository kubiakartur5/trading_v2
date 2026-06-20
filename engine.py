import pandas as pd
from models import Wallet, Position, TradeLog

class BacktestEngine:
    def __init__(self, df: pd.DataFrame, initial_balance: float, leverage: float = 30.0, position_size: float = 100000, ticker: str = "EURUSD=X"):
        self.df = df.reset_index(drop=True)
        self.wallet = Wallet(initial_balance=initial_balance, leverage=leverage)
        self.position_size = position_size
        self.ticker = ticker.upper()  # Upewniamy się, że ticker jest w formacie wielkich liter
        self.trade_history = []

    def run(self):
        for i in range(len(self.df)):
            row = self.df.iloc[i]
            current_price = row['Close']
            current_time = str(row.get('Date', i))
            
            # Wskaźniki na początku potrzebują kilku świec (NaN), pomijamy je
            if pd.isna(row.get('signal')):
                continue
                
            signal = int(row['signal'])

            # 1. Aktualizacja wyceny otwartych pozycji
            for pos in self.wallet.positions:
                pos.update_pnl(current_price)

            # 2. Sprawdzenie mechanizmu Stop-out (Margin Call z automatycznym zamknięciem)
            self._check_stop_out(current_price, current_time)

            # 3. Egzekucja sygnałów strategii
            self._handle_signal(signal, current_price, current_time)


        # Zamknięcie wszystkich otwartych pozycji na koniec danych historycznych
        last_price = self.df.iloc[-1]['Close']
        last_time = str(self.df.iloc[-1].get('Date', 'End'))
        self._close_all_positions(last_price, f'End of Data ({last_time})')

    def _handle_signal(self, signal: int, price: float, time_str: str):
        # Jeśli mamy pozycję przeciwnego znaku do sygnału - zamykamy ją
        for pos in list(self.wallet.positions):
            if (signal == 1 and pos.side == 'SELL') or (signal == -1 and pos.side == 'BUY'):
                self._close_position(pos, price, time_str)

        # Otwieranie nowej pozycji, jeśli portfel jest pusty, a mamy sygnał
        if len(self.wallet.positions) == 0 and signal != 0:
            side = 'BUY' if signal == 1 else 'SELL'
            
            if self.ticker.endswith('USD=X'):
                adjusted_size = self.position_size
            else:
                adjusted_size = self.position_size / price
            

            new_pos = Position(
                asset=self.ticker, # Przekazujemy aktualną nazwę instrumentu
                side=side, 
                entry_price=price, 
                size=self.position_size, # Wstrzykujemy dostosowaną wielkość
                leverage=self.wallet.leverage
            )
            
            # Weryfikacja czy starczy nam środków (Free Margin) na otworzenie pozycji
            if self.wallet.free_margin >= new_pos.required_margin:
                self.wallet.positions.append(new_pos)
            else:
                print(f'Odrzucono sygnał: Za mały Free Margin! Posiadasz: {self.wallet.free_margin:.2f} USD, wymagano: {new_pos.required_margin:.2f} USD')

    def _check_stop_out(self, price: float, time_str: str):
        # Pętla while ubezpiecza sytuację, gdzie zamknięcie jednej pozycji wciąż nie ratuje wymogu depozytu
        while self.wallet.margin_level < self.wallet.stop_out_level and len(self.wallet.positions) > 0:
            # Szukamy najbardziej stratnej pozycji i zamykamy ją z przymusu
            self.wallet.positions.sort(key=lambda p: p.unrealized_pnl)
            worst_position = self.wallet.positions[0]
            print(f'!!! STOP-OUT NASTĄPIŁ: Zamykanie przymusowe dla {time_str} !!!')
            self._close_position(worst_position, price, f'STOP-OUT ({time_str})')

    def _close_position(self, pos: Position, price: float, time_str: str):
        pos.update_pnl(price)
        self.wallet.balance += pos.unrealized_pnl
        self.wallet.positions.remove(pos)
        
        log = TradeLog(
            asset=pos.asset, side=pos.side, entry_time='N/A', exit_time=time_str,
            entry_price=pos.entry_price, exit_price=price, size=pos.size, pnl=pos.unrealized_pnl
        )
        self.trade_history.append(log)

    def _close_all_positions(self, price: float, time_str: str):
        for pos in list(self.wallet.positions):
            self._close_position(pos, price, time_str)