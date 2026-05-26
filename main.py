import pandas as pd
from tvDatafeed import TvDatafeed, Interval
from telegram import Bot
import asyncio
from datetime import datetime

# =========================
# TELEGRAM
# =========================

TOKEN = "8817561227:AAHo0m5lRbUod_ytWsIS-BUkNaOlmgH-obo"
CHAT_ID = "8817561227"

bot = Bot(token=TOKEN)

# =========================
# TRADINGVIEW
# =========================

tv = TvDatafeed()

TIMEFRAMES = {
    "M5": Interval.in_5_minute
}

ENABLED_TF = ["M5"]

# =========================
# FOREX PAIRS
# =========================

PAIRS = [
    ("EURUSD", "OANDA"),
    ("GBPUSD", "OANDA"),
    ("USDJPY", "OANDA"),
    ("AUDUSD", "OANDA"),
    ("USDCAD", "OANDA"),
    ("USDCHF", "OANDA"),
    ("NZDUSD", "OANDA")
]

# =========================
# АНТИДУБЛЬ
# =========================

processed_signals = set()

# =========================
# DONCHIAN
# =========================

def calculate_donchian(df, period=20):
    df['upper'] = df['high'].rolling(period).max()
    df['lower'] = df['low'].rolling(period).min()
    return df

# =========================
# SIGNAL
# =========================

def check_signal(df):
    if len(df) < 25:
        return None

    last = df.iloc[-1]
    prev = df.iloc[-2]

    # BUY
    if prev['close'] <= prev['upper'] and last['close'] > last['upper']:
        return "BUY"

    # SELL
    if prev['close'] >= prev['lower'] and last['close'] < last['lower']:
        return "SELL"

    return None

# =========================
# SEND TELEGRAM
# =========================

async def send_signal(pair, tf, signal):

    text = f"""
🚨 СИГНАЛ

💱 Пара: {pair}
⏰ Таймфрейм: {tf}

📈 Сигнал: {signal}

🕒 Время: {datetime.now().strftime('%H:%M:%S')}
"""

    await bot.send_message(
        chat_id=CHAT_ID,
        text=text
    )

# =========================
# MAIN LOOP
# =========================

async def run_bot():

    while True:

        try:

            for pair in PAIRS:

                symbol, exchange = pair

                for tf in ENABLED_TF:

                    interval = TIMEFRAMES[tf]

                    try:

                        df = tv.get_hist(
                            symbol=symbol,
                            exchange=exchange,
                            interval=interval,
                            n_bars=200
                        )

                        if df is None or df.empty:
                            continue

                        df = calculate_donchian(df)

                        signal = check_signal(df)

                        if signal:

                            signal_id = f"{symbol}_{tf}_{signal}"

                            if signal_id not in processed_signals:

                                await send_signal(
                                    symbol,
                                    tf,
                                    signal
                                )

                                processed_signals.add(signal_id)

                        await asyncio.sleep(2)

                    except Exception as e:
                        print(f"ERROR {symbol} {tf}: {e}")

            await asyncio.sleep(30)

        except Exception as e:
            print(f"MAIN ERROR: {e}")
            await asyncio.sleep(10)

# =========================
# START
# =========================

asyncio.run(run_bot())
