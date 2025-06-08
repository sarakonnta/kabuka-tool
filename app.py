import streamlit as st
import pandas as pd
import os
from datetime import datetime

INPUT_CSV_PATH = 'japan_stocks_indicators.csv'

st.set_page_config(page_title="株式スクリーニング結果", layout="wide")
st.title('📈 株式スクリーニング結果')
st.caption('MACDやRSIなどに基づいた分析結果')

# --- データファイルの存在と最終更新日時を確認 ---
if os.path.exists(INPUT_CSV_PATH):
    mod_time_timestamp = os.path.getmtime(INPUT_CSV_PATH)
    mod_time_dt = datetime.fromtimestamp(mod_time_timestamp)
    st.info(f"分析データ最終更新日時: {mod_time_dt.strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        df = pd.read_csv(INPUT_CSV_PATH)

        # データが空っぽでないかチェック
        if df.empty:
            st.warning("現在表示できるデータがありません。これは、データ作成処理で有効な株価データが取得できなかった場合に表示されます。次回の自動更新（毎日夜8時）でデータが取得できれば、自動的に表示されます。")
        
        else:
            # 日付形式を修正し、最新の日付を取得
            df['Date'] = pd.to_datetime(df['Date'])
            latest_date = df['Date'].max()
            
            df_display = df[df['Date'] == latest_date].copy()
            st.write(f"**表示データ: {latest_date.strftime('%Y-%m-%d')} の最新データ**")

            # --- ★★★ここが新しい修正部分★★★ ---
            # --- サイドバーのフィルター設定 ---
            st.sidebar.header('スクリーニング条件')
            st.sidebar.caption('チェックを入れた条件のいずれか一つ以上に合致する銘柄が表示されます。')
            
            # 「すべて選択」チェックボックス
            select_all = st.sidebar.checkbox("すべて選択", value=True)

            # 各条件のチェックボックス (valueがselect_allに連動)
            use_macd_cross = st.sidebar.checkbox('MACDゴールデンクロス', value=select_all)
            use_macd_hist_turn = st.sidebar.checkbox('MACDヒストグラム陽転 (MACD色)', value=select_all)
            use_rsi_rising = st.sidebar.checkbox('RSIが50以下で上昇中', value=select_all)
            use_ma_dev_turn = st.sidebar.checkbox('25日線乖離率が0以下で上昇中', value=select_all)
            use_close_above_tenkan = st.sidebar.checkbox('終値が転換線を上回る (一目)', value=select_all)
            
            # フィルター条件のリスト
            conditions = []
            if use_macd_cross and 'macd_golden_cross' in df_display.columns:
                conditions.append(df_display['macd_golden_cross'] == True)
            if use_macd_hist_turn and 'macd_hist_turn_positive' in df_display.columns:
                conditions.append(df_display['macd_hist_turn_positive'] == True)
            if use_rsi_rising and 'rsi_rising_below_50' in df_display.columns:
                conditions.append(df_display['rsi_rising_below_50'] == True)
            if use_ma_dev_turn and 'ma_dev_turn_positive_below_zero' in df_display.columns:
                conditions.append(df_display['ma_dev_turn_positive_below_zero'] == True)
            if use_close_above_tenkan and 'close_above_tenkan' in df_display.columns:
                conditions.append(df_display['close_above_tenkan'] == True)
            
            # フィルターを適用
            if not any([use_macd_cross, use_macd_hist_turn, use_rsi_rising, use_ma_dev_turn, use_close_above_tenkan]):
                # 何もチェックがない場合は、何もフィルターしない（全件表示）
                filtered_df = df_display
            else:
                if conditions:
                    # チェックがある場合は、いずれかの条件に合致するものを抽出 (OR条件)
                    combined_condition = pd.DataFrame(conditions).any(axis=0)
                    filtered_df = df_display[combined_condition]
                else:
                    # チェックはあるが、データに該当列がない場合などは空のDF
                    filtered_df = pd.DataFrame()
            # ★★★ここまでが新しい修正部分★★★

            # 結果の表示
            st.dataframe(filtered_df)
            st.markdown(f"**絞り込み結果: {len(filtered_df)} 件** / {len(df_display)} 件中")
            
            if len(filtered_df) == 0 and any([use_macd_cross, use_macd_hist_turn, use_rsi_rising, use_ma_dev_turn, use_close_above_tenkan]):
                 st.info("現在のフィルター条件に合致する銘柄がありません。サイドバーのチェックをいくつか外して、条件を緩めてみてください。")

    except Exception as e:
        st.error(f"データの読み込みまたは表示中に予期せぬエラーが発生しました: {e}")

else:
    # そもそもCSVファイルが存在しない場合
    st.error(f"データファイル `{INPUT_CSV_PATH}` が見つかりません。GitHub Actionsの実行が完了するまでお待ちください。")

# --- フッター ---
st.markdown("---")
st.caption("このアプリケーションは投資判断を補助するものであり、投資勧誘を目的としたものではありません。投資に関する最終決定はご自身の判断でお願いします。")
