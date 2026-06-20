import sys
import pandas as pd
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QFormLayout, QComboBox, QDoubleSpinBox, 
                               QPushButton, QTextEdit, QLabel, QTabWidget)
from PySide6.QtCore import Qt


from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar # <--- DODAJ TO
from matplotlib.figure import Figure



from utils import get_real_forex_data
from strategies import SMACrossoverStrategy, RSICloseStrategy, BollingerBandsStrategy
from engine import BacktestEngine


class BacktesterGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Forex Backtester Pro - PySide6')
        self.resize(1100, 800)
        
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        
        # --- LEWY PANEL: Formularz ustawień ---
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        form_layout = QFormLayout()
        
        # Wybór Instrumentu (Waluty)
        self.asset_combo = QComboBox()
        self.asset_combo.addItems([
            'EURUSD=X (Euro / Dolar)',
            'GBPUSD=X (Funt / Dolar)',
            #'JPY=X (Dolar / Jen)',
            'AUDUSD=X (Dolar Australijski / Dolar)',
            'CHF=X (Dolar / Frank Szwajcarski)'
        ])
        
        self.strategy_combo = QComboBox()
        self.strategy_combo.addItems(['Bollinger Bands', 'SMA Crossover', 'RSI Mean Reversion'])
        
        self.balance_spin = QDoubleSpinBox()
        self.balance_spin.setRange(100, 1000000)
        self.balance_spin.setValue(5000.0)
        self.balance_spin.setPrefix('$ ')
        
        self.leverage_spin = QDoubleSpinBox()
        self.leverage_spin.setRange(1, 500)
        self.leverage_spin.setValue(30.0)
        
        self.position_size_spin = QDoubleSpinBox()
        self.position_size_spin.setRange(0.01, 10.0)  # W lotach (0.01 = 1 000, 1.0 = 100 000)
        self.position_size_spin.setSingleStep(0.01) # Krok co 0.01 lota
        self.position_size_spin.setValue(0.1) # Domyślnie 0.1 lota = 10 000 jednostek
        
        form_layout.addRow('Instrument:', self.asset_combo)
        form_layout.addRow('Strategia:', self.strategy_combo)
        form_layout.addRow('Kapitał startowy:', self.balance_spin)
        form_layout.addRow('Dźwignia (1:X):', self.leverage_spin)
        form_layout.addRow('Wielkość pozycji:', self.position_size_spin)
        
        self.run_btn = QPushButton('Uruchom Backtest')
        self.run_btn.setStyleSheet('background-color: #2e8b57; color: white; font-weight: bold; padding: 10px;')
        self.run_btn.clicked.connect(self.run_backtest)
        
        left_layout.addLayout(form_layout)
        left_layout.addWidget(self.run_btn)
        left_layout.addStretch() 
        
        # PRAWY PANEL: Zakładki (Tabs) i Konsola 
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        #System zakładek
        self.tabs = QTabWidget()
        
        # Zakładka 1: Krzywa Kapitału
        self.tab_equity = QWidget()
        self.tab_equity_layout = QVBoxLayout(self.tab_equity)
        self.fig_equity = Figure()
        self.canvas_equity = FigureCanvas(self.fig_equity)
        self.ax_equity = self.fig_equity.add_subplot(111)
        self.tab_equity_layout.addWidget(self.canvas_equity)
        
        # Zakładka 2: Wykres Świecowy
        self.tab_candles = QWidget()
        self.tab_candles_layout = QVBoxLayout(self.tab_candles)
        self.fig_candles = Figure()
        self.canvas_candles = FigureCanvas(self.fig_candles)
        
        #  Pasek narzędzi do zoomowania
        self.toolbar_candles = NavigationToolbar(self.canvas_candles, self)
        
        self.ax_candles = self.fig_candles.add_subplot(111)
        
        # Dodajemy pasek narzędzi a pod nim wykres
        self.tab_candles_layout.addWidget(self.toolbar_candles)
        self.tab_candles_layout.addWidget(self.canvas_candles)
        
        # Dodanie zakładek do głównego menu
        self.tabs.addTab(self.tab_equity, 'Krzywa Kapitału')
        self.tabs.addTab(self.tab_candles, 'Wykres Świecowy')
        
        # Konsola tekstowa na wyniki
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setMaximumHeight(150)
        self.results_text.setStyleSheet('background-color: #1e1e1e; color: #00ff00; font-family: Consolas;')
        self.results_text.setText('Gotowy do uruchomienia testu...\n')
        
        right_layout.addWidget(self.tabs)
        right_layout.addWidget(QLabel('Wyniki podsumowujące:'))
        right_layout.addWidget(self.results_text)
        
        main_layout.addWidget(left_panel, 3)
        main_layout.addWidget(right_panel, 7)

    def log(self, message):
        self.results_text.append(message)
        QApplication.processEvents()

    def run_backtest(self):
        self.results_text.clear()
        self.run_btn.setEnabled(False)
        
        # Pobieramy z ComboBoxa sam ticker (tekst przed spacją, np. "EURUSD=X")
        full_asset_text = self.asset_combo.currentText()
        ticker = full_asset_text.split(" ")[0]
        
        self.log(f'Pobieranie danych dla {ticker} (60 dni, 1h)...')
        
        try:
            # 1. Pobranie danych dla wybranej waluty
            data = get_real_forex_data(ticker=ticker, period="60d", interval="1h")
            self.log(f'Pobrano {len(data)} świec. Obliczanie wskaźników...')
            
            # 2. Wybór strategii
            strat_name = self.strategy_combo.currentText()
            if strat_name == "Bollinger Bands":
                strategy = BollingerBandsStrategy(window=20, num_std=2)
            elif strat_name == "SMA Crossover":
                strategy = SMACrossoverStrategy(short_window=10, long_window=30)
            else:
                strategy = RSICloseStrategy(periods=14, overbought=70, oversold=30)
                
            data_with_signals = strategy.generate_signals(data)
            
            
            # 3. Parametry
            init_bal = self.balance_spin.value()
            lev = float(self.leverage_spin.value())
            volume_lots = self.position_size_spin.value()
            
            current_price = data['Close'].iloc[0]
            pos_size = volume_lots * 100000  # Konwersja lotów na jednostki (np. 0.1 lota = 10 000 jednostek)
            pip_size = 0.01 if 'JPY' in ticker else 0.0001
            self.log(f'Uruchamianie silnika dla: {strat_name}...')
            
            
            if ticker.endswith('USD=X'):
                position_value_usd = pos_size * current_price
                pip_value_usd = pos_size * pip_size
            else:
                position_value_usd = pos_size
                pip_value_usd = (pos_size * pip_size) / current_price

            required_margin_usd = position_value_usd / lev
            self.log(f'--- SPECYFIKACJA POZYCJI ({ticker}) ---')
            self.log(f'Wolumen: {volume_lots:.2f} lot(ów)')
            self.log(f'Wielkość nominalna: {pos_size:,} jednostek')
            self.log(f'Wybrana Dźwignia: 1:{int(lev)}')
            self.log(f'Wartość 1 pipsa: {pip_value_usd:.2f} USD')
            self.log(f'Wymagany Margin: {required_margin_usd:.2f} USD')
            self.log(f'----------------------------------------')
            
        
            # 4. Wykonanie testu
            engine = BacktestEngine(
                df=data_with_signals, 
                initial_balance=init_bal, 
                leverage=lev, 
                position_size=pos_size
            )
            engine.run()
            
            # 5. Podsumowanie
            total_pnl = sum(t.pnl for t in engine.trade_history)
            roi = (total_pnl / init_bal) * 100
            
            self.log('--- TEST ZAKOŃCZONY ---')
            self.log(f'Końcowy kapitał: {engine.wallet.balance:.2f} USD')
            self.log(f'Liczba transakcji: {len(engine.trade_history)}')
            self.log(f'Zysk/Strata netto: {total_pnl:.2f} USD')
            self.log(f'Stopa zwrotu (ROI): {roi:.2f}%')
            
            # 6. Rysowanie WYKRESÓW na obu zakładkach
            self.plot_equity(engine)
            self.plot_candles(engine.df, ticker)
            
        except Exception as e:
            self.log(f'BŁĄD: {str(e)}')
            
        self.run_btn.setEnabled(True)

    def plot_equity(self, engine):
        self.ax_equity.clear()
        
        if not engine.trade_history:
            self.ax_equity.set_title('Brak transakcji do narysowania')
            self.canvas_equity.draw()
            return
            
        balance = self.balance_spin.value()
        equity_curve = [balance]
        
        for trade in engine.trade_history:
            balance += trade.pnl
            equity_curve.append(balance)
            
        self.ax_equity.plot(equity_curve, marker='o', linestyle='-', color='blue')
        self.ax_equity.set_title('Krzywa Kapitału (Zyski i Straty)')
        self.ax_equity.set_xlabel('Numer transakcji')
        self.ax_equity.set_ylabel('Kapitał (USD)')
        self.ax_equity.grid(True)
        
        self.canvas_equity.draw()

    def plot_candles(self, df, ticker):
        """Generuje ulepszony wykres świecowy bez luk i z możliwością zoomu"""
        self.ax_candles.clear()

        # ciemny motyw dla wykresu świecowego
        dark_bg = '#131722'      
        grid_color = '#2a2e39'   
        
        # Pobieramy figurę bezpośrednio z osi, na której rysujemy
        fig = self.ax_candles.figure
        if fig:
            fig.patch.set_facecolor(dark_bg)
            
        self.ax_candles.set_facecolor(dark_bg)
        

        # Upewniamy się, że index to czyste liczby 0, 1, 2... aby uniknąć luk weekendowych
        df = df.reset_index(drop=True)
        
        up = df[df['Close'] >= df['Open']]
        down = df[df['Close'] < df['Open']]

        #kolory
        color_up = '#26a69a'   
        color_down = '#ef5350' 

        # Rysowanie "knotów" (Cienie)
        self.ax_candles.bar(up.index, up['High'] - up['Low'], width=0.1, bottom=up['Low'], color=color_up)
        self.ax_candles.bar(down.index, down['High'] - down['Low'], width=0.1, bottom=down['Low'], color=color_down)

        # Rysowanie korpusów - zmieniliśmy ramkę (edgecolor) na ciemniejszą, pasującą do tła
        self.ax_candles.bar(up.index, up['Close'] - up['Open'], width=0.7, bottom=up['Open'], 
                            color=color_up, edgecolor='#1e534f', linewidth=0.5)
        self.ax_candles.bar(down.index, down['Open'] - down['Close'], width=0.7, bottom=down['Close'], 
                            color=color_down, edgecolor='#7a2e2d', linewidth=0.5)

        # Ustawienie kroków na osi X, aby nie było zbyt wielu etykiet
        step = max(1, len(df) // 8)
        self.ax_candles.set_xticks(df.index[::step])
        
        # STYLIZACJA OSI I NAPISÓW 
        self.ax_candles.set_xticklabels(df['Date'].iloc[::step], rotation=15, fontsize=9, color='white')
        self.ax_candles.tick_params(colors='white', which='both') # Liczby na osi Y też będą białe

        # Ustawienie limitów widoku 
        if len(df) > 100:
            self.ax_candles.set_xlim(len(df) - 100, len(df))
            # Dopasowanie wysokości (oś Y) tylko dla tych 100 widocznych świec
            visible_df = df.iloc[-100:]
            self.ax_candles.set_ylim(visible_df['Low'].min() * 0.999, visible_df['High'].max() * 1.001)

        # Tytuł i etykiety osi na biało
        self.ax_candles.set_title(f'Wykres Świecowy: {ticker}', color='white', fontsize=11, fontweight='bold')
        self.ax_candles.set_ylabel('Cena', color='white')
        
        # Siatka dostosowana do ciemnego tła
        self.ax_candles.grid(True, color=grid_color, linestyle='--', alpha=0.5)
        
        # Zmiana kolorów ramek
        for spine in self.ax_candles.spines.values():
            spine.set_color(grid_color)
       
        
        self.canvas_candles.draw()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = BacktesterGUI()
    window.show()
    sys.exit(app.exec())