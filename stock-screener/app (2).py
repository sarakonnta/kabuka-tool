import streamlit as st
import pandas as pd
import os
from datetime import datetime

INPUT_CSV_PATH = 'japan_stocks_indicators.csv'

st.set_page_config(page_title="株式スクリーニング結果", layout="wide")
st.title('📈 株式スクリーニング結果')
st.caption('MACDやRSIなどに基づいた分析結果')

if os.path.exists(INPUT_CSV_PATH):
    mod_time_timestamp = os.path.getmtime(INPUT_CSV_PATH)
    mod_time_dt = datetime.fromtimestamp(mod_time_timestamp)
    st.info(f"分析データ最終更新日時: {mod_time_dt.strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        df = pd.read_csv(INPUT_CSV_PATH)

        latest_date = pd.to_datetime(df['Date']).max()
        df_display = df[pd.to_datetime(df['Date']) == latest_date].copy()
        st.write(f"**表示データ: {latest_date.strftime('%Y-%m-%d')} の最新データ**")

        st.sidebar.header('スクリーニング条件')
        use_macd_cross = st.sidebar.checkbox('MACDゴールデンクロス', value=True)
        use_rsi_rising = st.sidebar.checkbox('RSIが50以下で上昇中', value=True)
        use_ma_dev_turn = st.sidebar.checkbox('25日線乖離率が0以下で上昇中', value=True)
        use_close_above_tenkan = st.sidebar.checkbox('終値が転換線を上回る', value=True)

        conditions = []
        if use_macd_cross and 'macd_golden_cross' in df_display.columns:
            conditions.append(df_display['macd_golden_cross'] == True)
        if use_rsi_rising and 'rsi_rising_below_50' in df_display.columns:
            conditions.append(df_display['rsi_rising_below_50'] == True)
        if use_ma_dev_turn and 'ma_dev_turn_positive_below_zero' in df_display.columns:
            conditions.append(df_display['ma_dev_turn_positive_below_zero'] == True)
        if use_close_above_tenkan and 'close_above_tenkan' in df_display.columns:
            conditions.append(df_display['close_above_tenkan'] == True)

        if conditions:
            combined_condition = pd.DataFrame(conditions).any()
            filtered_df = df_display[combined_condition]
        else:
            filtered_df = df_display

        st.dataframe(filtered_df)
        st.markdown(f"**絞り込み結果: {len(filtered_df)} 件**")

    except Exception as e:
        st.error(f"データの読み込みまたは表示中にエラーが発生しました: {e}")

else:
    st.warning(f"データファイル `{INPUT_CSV_PATH}` が見つかりません。")

st.markdown("---")
st.caption("このアプリケーションは投資判断を補助するものであり、投資勧誘を目的としたものではありません。投資に関する最終決定はご自身の判断でお願いします。")