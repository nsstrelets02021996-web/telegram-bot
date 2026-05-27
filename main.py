import pandas as pd
from tvDatafeed import TvDatafeed, Interval
from telegram import Bot
import asyncio
from datetime import datetime

# =========================
# TELEGRAM
# =========================

TOKEN = "8817561227:AAHo0m5lRbUod_ytWsIS-BUkNaOlmgH-obo"
CHAT_ID = "8611901179"

bot = Bot(token=TOKEN)

async def test_message():
    await bot.send_message(
        chat_id=CHAT_ID,
        text="Бот підключений ✅"
    )

# =========================
# TRADINGVIEW
# =========================

tv = TvDatafeed()

# =========================
# TIMEFRAMES
# =========================

TIMEFRAMES = {
    "M5": Interval.in_5_minute,
    "M15": Interval.in_15_minute
}

ENABLED_TF = ["M5", "M15"]

# =========================
# EXPIRATION
# =========================

EXPIRATION = {
    "M5": "5 хв",
    "M15": "15 хв"
}

# =========================
# FOREX PAIRS
# =========================

PAIRS = [

    # MAJORS
    ("EURUSD", "OANDA"),
    ("GBPUSD", "OANDA"),
    ("USDJPY", "OANDA"),
    ("USDCHF", "OANDA"),
    ("AUDUSD", "OANDA"),
    ("USDCAD", "OANDA"),
    ("NZDUSD", "OANDA"),

    # EUR
    ("EURGBP", "OANDA"),
    ("EURJPY", "OANDA"),
    ("EURAUD", "OANDA"),
    ("EURCHF", "OANDA"),
    ("EURCAD", "OANDA"),
    ("EURNZD", "OANDA"),

    # GBP
    ("GBPJPY", "OANDA"),
    ("GBPAUD", "OANDA"),
    ("GBPCHF", "OANDA"),
    ("GBPCAD", "OANDA"),
    ("GBPNZD", "OANDA"),

    # AUD
    ("AUDJPY", "OANDA"),
    ("AUDCHF", "OANDA"),
    ("AUDCAD", "OANDA"),
    ("AUDNZD", "OANDA"),

    # CAD
    ("CADJPY", "OANDA"),
    ("CADCHF", "OANDA"),

    # CHF
    ("CHFJPY", "OANDA"),

    # NZD
    ("NZDJPY", "OANDA"),
    ("NZDCHF", "OANDA"),
    ("NZDCAD", "OANDA"),
]

# =========================
# ANTIDUPLICATE
# =========================

processed_signals = set()

# =========================
# DONCHIAN CHANNEL
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
# SIGNAL LOGIC
# =========================

def check_signal(df):

    if len(df) < 120:
        return None

    last = df.iloc[-1]

    prev = df.iloc[-2]

    # ================= BUY =================

    if (
        prev['close'] <= prev['upper']
        and last['close'] > last['upper']
        and last['cci'] > 150
    ):

        return "BUY"

    # ================= SELL =================

    if (
        prev['close'] >= prev['lower']
        and last['close'] < last['lower']
        and last['cci'] < -150
    ):

        return "SELL"

    return None

# =========================
# TELEGRAM MESSAGE
# =========================

async def send_signal(pair, tf, signal, cci):

    signal_text = "📈 BUY" if signal == "BUY" else "📉 SELL"

    text = f"""
🚨 СИГНАЛ

💱 Пара: {pair}

⏰ Таймфрейм: {tf}

{signal_text}

📊 CCI: {int(cci)}

⏳ Експірація: {EXPIRATION[tf]}

🕒 Час: {datetime.now().strftime('%H:%M:%S')}
"""

    await bot.send_message(
        chat_id=CHAT_ID,
        text=text
    )

# =========================
# MAIN LOOP
# =========================

async def run_bot():

    print("BOT STARTED")

    await bot.send_message(
        chat_id=CHAT_ID,
        text="Бот підключений ✅"
    )

    while True:

        try:

            for pair in PAIRS:

                symbol, exchange = pair

                for tf in ENABLED_TF:

                    interval = TIMEFRAMES[tf]

                    try:

                        # ================= GET DATA =================

                        df = tv.get_hist(
                            symbol=symbol,
                            exchange=exchange,
                            interval=interval,
                            n_bars=200
                        )

                        # ================= CHECK DATA =================

                        if df is None or df.empty:
                            continue

                        # ================= INDICATORS =================

                        df = calculate_donchian(df)

                        df = calculate_cci(df)

                        # ================= SIGNAL =================

                        signal = check_signal(df)

                        # ================= SEND SIGNAL =================

                        if signal:

                            last_candle_time = str(df.index[-1])

                            signal_id = (
                                f"{symbol}_{tf}_{signal}_{last_candle_time}"
                            )

                            if signal_id not in processed_signals:

                                cci_value = df.iloc[-1]['cci']

                                await send_signal(
                                    symbol,
                                    tf,
                                    signal,
                                    cci_value
                                )

                                processed_signals.add(signal_id)

                                print(
                                    f"SIGNAL: "
                                    f"{symbol} "
                                    f"{tf} "
                                    f"{signal}"
                                )

                        # ================= DELAY =================

                        await asyncio.sleep(4)

                    except Exception as e:

                        print(f"ERROR {symbol} {tf}: {e}")

            # ================= MAIN DELAY =================

            await asyncio.sleep(60)

        except Exception as e:

            print(f"MAIN ERROR: {e}")

            await asyncio.sleep(10)

# =========================
# START
# =========================

asyncio.run(run_bot())
