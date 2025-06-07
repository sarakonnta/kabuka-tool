import pandas as pd
import yfinance as yf
import datetime
import time
import ta
import sys

# ---------- 1. ティッカーリストの読み込み ----------
try:
    tickers_df = pd.read_csv('tickers_list.csv')
    tickers = tickers_df['ticker'].tolist()
    if not tickers:
        print("ティッカーリストが空です。")
        sys.exit(1)
    print(f"読み込んだティッカー数: {len(tickers)}")
except FileNotFoundError:
    print("tickers_list.csv が見つかりません。")
    sys.exit(1)

# ---------- 2. 日付設定 ----------
today = datetime.date.today()
start_date = today - datetime.timedelta(days=200)
end_date = today + datetime.timedelta(days=1)

# ---------- 3. 株価データの取得 ----------
all_data_list = []
print("株価データの取得を開始します...")
for i in range(0, len(tickers), 50):
    batch = tickers[i:i+50]
    print(f"バッチ処理中: {i+1} - {min(i+50, len(tickers))} / {len(tickers)} 銘柄")
    try:
        data = yf.download(batch, start=start_date, end=end_date, group_by='ticker', progress=False, timeout=30)
        if not data.empty:
            data_processed_list = []
            for ticker_symbol in batch:
                if isinstance(data.columns, pd.MultiIndex) and ticker_symbol in data.columns.get_level_values(0):
                    df_single_ticker = data[ticker_symbol].copy()
                    if not df_single_ticker.empty:
                        df_single_ticker['ticker'] = ticker_symbol
                        df_single_ticker.reset_index(inplace=True)
                        data_processed_list.append(df_single_ticker)
            if data_processed_list:
                all_data_list.append(pd.concat(data_processed_list, ignore_index=True))
    except Exception as e:
        print(f"バッチ処理中にエラー: {e}")
    time.sleep(5)

final_df = pd.DataFrame()

if all_data_list:
    all_data = pd.concat(all_data_list, ignore_index=True)
    if not all_data.empty:
        all_data['Date'] = pd.to_datetime(all_data['Date'])
        all_data.sort_values(by=['ticker', 'Date'], inplace=True)
        all_data.reset_index(drop=True, inplace=True)

        all_data.columns = [str(col).capitalize() for col in all_data.columns]
        all_data.rename(columns={'Ticker': 'ticker', 'Adj close': 'Adj_close'}, inplace=True)

        # ---------- 4. 指標計算 ----------
        result_df_list = []
        print("テクニカル指標の計算を開始します...")
        for ticker_name, df in all_data.groupby('ticker'):
            if len(df) < 26: continue
            df = df.copy()
            try:
                for col in ['Open', 'High', 'Low', 'Close', 'Adj_close', 'Volume']:
                    if col not in df.columns:
                        df[col] = 0 # もし列がなければ0で埋める

                df['Close'] = pd.to_numeric(df['Close'], errors='coerce')
                df.dropna(subset=['Close'], inplace=True)
                if df.empty: continue

                # MACD
                macd = ta.trend.MACD(df['Close'])
                df['macd'] = macd.macd()
                df['macd_signal'] = macd.macd_signal()
                df['macd_hist'] = macd.macd_diff()
                df['macd_golden_cross'] = (df['macd'].shift(1) < df['macd_signal'].shift(1)) & (df['macd'] > df['macd_signal'])
                # RSI
                df['rsi'] = ta.momentum.rsi(df['Close'], window=14)
                df['rsi_rising_below_50'] = (df['rsi'] < 50) & (df['rsi'] > df['rsi'].shift(1))
                # 25日線乖離率
                ma25 = ta.trend.sma_indicator(df['Close'], window=25)
                df['ma_deviation_25'] = ((df['Close'] - ma25) / ma25) * 100
                df['ma_dev_turn_positive_below_zero'] = (df['ma_deviation_25'] < 0) & (df['ma_deviation_25'] > df['ma_deviation_25'].shift(1))
                # 一目均衡表 転換線
                df['High'] = pd.to_numeric(df['High'], errors='coerce')
                df['Low'] = pd.to_numeric(df['Low'], errors='coerce')
                df.dropna(subset=['High', 'Low'], inplace=True)
                if df.empty: continue
                ichimoku = ta.trend.IchimokuIndicator(high=df['High'], low=df['Low'])
                df['tenkan_sen'] = ichimoku.ichimoku_conversion_line()
                df['close_above_tenkan'] = df['Close'] > df['tenkan_sen']

                result_df_list.append(df)
            except Exception as e:
                print(f"{ticker_name} の指標計算中にエラー: {e}")

        if result_df_list:
            final_df = pd.concat(result_df_list, ignore_index=True)

# ---------- 5. CSV出力 ----------
if final_df.empty:
    print("有効な計算結果がありませんでした。空のCSVファイルを作成します。")
    headers = ['Date', 'Open', 'High', 'Low', 'Close', 'Adj_close', 'Volume', 'ticker', 
               'macd', 'macd_signal', 'macd_hist', 'macd_golden_cross', 'rsi', 
               'rsi_rising_below_50', 'ma_deviation_25', 'ma_dev_turn_positive_below_zero', 
               'tenkan_sen', 'close_above_tenkan']
    final_df = pd.DataFrame(columns=headers)

file_name = "japan_stocks_indicators.csv"
final_df.to_csv(file_name, index=False, encoding='utf-8-sig')
print(f"完了：{file_name} に保存しました。")
