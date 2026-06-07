from utils import get_real_forex_data
from strategies import SMACrossoverStrategy, RSICloseStrategy, BollingerBandsStrategy
from engine import BacktestEngine

def main():
    # 1. Pobranie danych rynkowych
    # EUR/USD na wykresie godzinowym z ostatnich 60 dni (yfinance dopuszcza "60d" dla 1h)
    data = get_real_forex_data(ticker="EURUSD=X", period="60d", interval="1h")
    print(f"Pobrano {len(data)} świec historycznych.\n")

    # 2. Wybór i konfiguracja strategii (odkomentuj tę, którą chcesz przetestować)
    # strategy = SMACrossoverStrategy(short_window=10, long_window=30)
    # strategy = RSICloseStrategy(periods=14, overbought=70, oversold=30)
    strategy = BollingerBandsStrategy(window=20, num_std=2)
    
    print(f"Generowanie sygnałów dla: {strategy.__class__.__name__}...")
    data_with_signals = strategy.generate_signals(data)

    # 3. Konfiguracja i uruchomienie Silnika (Backtestera)
    # Kapitał: 5 000 USD, Dźwignia: 1:30 (standard ESMA w UE), Pozycja: 0.5 lota (50 000 jednostek)
    print("Uruchamianie silnika backtestera...\n")
    engine = BacktestEngine(
        df=data_with_signals, 
        initial_balance=5000.0, 
        leverage=30.0, 
        position_size=50000 
    )
    engine.run()

    # 4. Podsumowanie wyników
    print("================ WYNIKI SYMULACJI ================")
    print(f"Początkowy depozyt:      5000.00 USD")
    print(f"Końcowy stan konta:      {engine.wallet.balance:.2f} USD")
    print(f"Zamknięte transakcje:    {len(engine.trade_history)}")
    
    total_pnl = sum(t.pnl for t in engine.trade_history)
    print(f"Wygenerowany zysk netto: {total_pnl:.2f} USD")
    
    if total_pnl > 0:
        print(f"Stopa zwrotu (ROI):      +{(total_pnl/5000)*100:.2f}%")
    else:
        print(f"Stopa zwrotu (ROI):      {(total_pnl/5000)*100:.2f}%")
    print("==================================================")

if __name__ == "__main__":
    main()