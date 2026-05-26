import pandas as pd
from tvDatafeed import TvDatafeed, Interval
from telegram import Bot
import asyncio
from datetime import datetime
import os

# =========================
# TELEGRAM
# =========================

TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

bot = Bot(token=TOKEN)

# =========================
# TRADINGVIEW
# =========================

tv = TvDatafeed()

TIMEFRAMES = {
    "M3": Interval.in_3_minute,
    "M5": Interval.in_5_minute,
    "M10": Interval.in_10_minute,
    "M15": Interval.in_15_minute
}

ENABLED_TF = ["M3", "M5", "M10", "M15"]

PAIRS = [
    "EURUSD",
    "GBPUSD",
    "USDJPY",
    "AUDUSD",
    "USDCHF"
]

# =========================
# АНТИДУБЛЬ
# =========================

processed_signals = set()

# =========================
# DONCHIAN
# =========================

def calculate_donchian(df, period=100):
    df['upper'] = df['high'].rolling(period).max()
    df['lower'] = df['low'].rolling(period).min()
    return df

# =========================
# CCI
# =========================

def calculate_cci(df, period=50):

    tp = (df['high'] + df['low'] + df['close']) / 3

    sma = tp.rolling(period).mean()

    mad = tp.rolling(period).apply(
        lambda x: pd.Series(x).mad()
    )

    df['cci'] = (tp - sma) / (0.015 * mad)

    return df

# =========================
# SIGNAL
# =========================

def check_signal(df):

    last = df.iloc[-1]

    candle_size = last['high'] - last['low']

    # SELL
    if last['close'] > last['upper']:

        breakout = last['close'] - last['upper']

        if breakout >= candle_size * 0.2 and last['cci'] > 150:
            return "SELL", last

    # BUY
    if last['close'] < last['lower']:

        breakout = last['lower'] - last['close']

        if breakout >= candle_size * 0.2 and last['cci'] < -150:
            return "BUY", last

    return None, None

# =========================
# MESSAGE
# =========================

def format_message(pair, tf, signal, data):

    price = round(data['close'], 5)

    cci = int(data['cci'])

    current_time = datetime.now().strftime("%H:%M:%S")

    strong = abs(cci) > 200

    if signal == "SELL":

        text = f"""
🚨 СИГНАЛ НА ПРОДАЖ 🚨

📉 {pair}
━━━━━━━━━━━━━━━

⏱ Таймфрейм: {tf}

🔴⬇️ ВХІД ВНИЗ ⬇️🔴

💰 Ціна: {price}
📊 CCI: {cci} {"🔥" if strong else ""}

📌 Умова:
Пробій верхнього каналу (20%+)

{"⚡ СИЛЬНИЙ СИГНАЛ ⚡" if strong else ""}

⏰ Час: {current_time}
⏳ Експірація: {tf.replace("M", "")} хв
"""

    else:

        text = f"""
🚨 СИГНАЛ НА ПОКУПКУ 🚨

📈 {pair}
━━━━━━━━━━━━━━━

⏱ Таймфрейм: {tf}

🟢⬆️ ВХІД ВГОРУ ⬆️🟢

💰 Ціна: {price}
📊 CCI: {cci} {"🔥" if strong else ""}

📌 Умова:
Пробій нижнього каналу (20%+)

{"⚡ СИЛЬНИЙ СИГНАЛ ⚡" if strong else ""}

⏰ Час: {current_time}
⏳ Експірація: {tf.replace("M", "")} хв
"""

    return text

# =========================
# MAIN LOOP
# =========================

async def run_bot():

    print("BOT STARTED")

    while True:

        for pair in PAIRS:

            for tf_name, tf_value in TIMEFRAMES.items():

                if tf_name not in ENABLED_TF:
                    continue

                try:

                    df = tv.get_hist(
                        symbol=pair,
                        exchange='FX_IDC',
                        interval=tf_value,
                        n_bars=150
                    )

                    if df is None or len(df) < 120:
                        continue

                    df = calculate_donchian(df)

                    df = calculate_cci(df)

                    signal, data = check_signal(df)

                    if signal:

                        unique_signal = f"{pair}_{tf_name}_{signal}_{data.name}"

                        # антидубль
                        if unique_signal in processed_signals:
                            continue

                        processed_signals.add(unique_signal)

                        message = format_message(
                            pair,
                            tf_name,
                            signal,
                            data
                        )

                        await bot.send_message(
                            chat_id=CHAT_ID,
                            text=message
                        )

                        print(f"SENT: {unique_signal}")

                except Exception as e:

                    print(f"ERROR: {e}")

        await asyncio.sleep(10)

# =========================
# START
# =========================

asyncio.run(run_bot())
