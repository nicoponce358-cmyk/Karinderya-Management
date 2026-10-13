import os
import json
import time
from datetime import datetime
from zoneinfo import ZoneInfo

try:
    from groq import Groq
    HAS_GROQ = True
except ImportError:
    HAS_GROQ = False

try:
    from dotenv import load_dotenv

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    ENV_PATH = os.path.join(BASE_DIR, ".env")

    load_dotenv(ENV_PATH, override=True)

except ImportError:
    print("python-dotenv is not installed.")


# ── Philippine Time ──────────────────────────────────────────────────────────

PH_TZ = ZoneInfo("Asia/Manila")


def get_ph_time():
    """Return the current Philippine date/time."""
    return datetime.now(PH_TZ)


# ── Groq Client ──────────────────────────────────────────────────────────────

def _get_client():
    """Kumuha ng Groq client kung may GROQ_API_KEY."""

    api_key = os.getenv("GROQ_API_KEY", "").strip()

    if not api_key:
        print("GROQ SETUP: No GROQ_API_KEY found in environment.")
        return None

    if not HAS_GROQ:
        print("GROQ SETUP: groq package is not installed.")
        return None

    try:
        client = Groq(api_key=api_key)
        print("Groq API key loaded:", True)
        return client

    except Exception as e:
        print("GROQ CLIENT ERROR:", repr(e))
        return None


# ── Prompt Builder ───────────────────────────────────────────────────────────

def _build_prompt(summary: dict) -> str:
    """Gumawa ng prompt mula sa summary data."""

    now_ph = get_ph_time()
    today = now_ph.strftime("%A, %B %d, %Y")
    day_name = now_ph.strftime("%A")

    prompt = f"""
Ikaw ay isang expert food-business consultant para sa maliit na Filipino karinderya.

Ngayon ay {today}.

Narito ang summary ng sales data ng karinderya:

TOTAL SALES: ₱{summary.get('total_sales', 0):,.2f}
TOTAL TRANSACTIONS: {summary.get('total_transactions', 0)}
AVERAGE DAILY SALES: ₱{summary.get('avg_daily_sales', 0):,.2f}

TOP DISHES (by revenue):
{json.dumps(summary.get('top_dishes', []), indent=2)}

LEAST-SELLING DISHES:
{json.dumps(summary.get('bottom_dishes', []), indent=2)}

HOURLY SALES PATTERN:
{json.dumps(summary.get('hourly_sales', []), indent=2)}

SALES BY DAY OF WEEK:
{json.dumps(summary.get('by_day_name', []), indent=2)}

Base sa data na ito, ibigay ang sumusunod na insights sa TAGLISH
(Tagalog-English mix), simple at madaling intindihin:

1. **📊 Buod ng Sales Patterns**
   - Ano ang trend ng benta?
   - Anong araw pinaka-malakas?
   - Anong oras ang peak?

2. **🍳 Recommendations sa Luto**
   - Anong dish ang dagdagan?
   - Alin ang bawasan?
   - Ilang servings ang ihanda bukas ({day_name})?

3. **📦 Inventory & Food Waste Tips**
   - Paano mababawasan ang food waste?
   - Anong ingredients ang dapat i-prioritize?

4. **💰 Paano Dadagdagan ang Kita**
   - Magbigay ng practical tips tulad ng combos, pricing at timing.

IMPORTANT:
- Gumamit ng 12-hour AM/PM time format.
- Halimbawa: 17:00 = 05:00 PM.
- Huwag gumamit ng military/24-hour time sa final answer.
- Gumamit ng emoji at bullet points.
- Simple at madaling maintindihan.
- Huwag masyadong mahaba.
"""

    return prompt


# ── Main Entry Point ─────────────────────────────────────────────────────────

def get_ai_insights(summary: dict) -> dict:
    """
    Kumuha ng AI insights gamit ang Groq.

    Returns:
        source: ai | rule-based
        insights: markdown string
        error: error message or None
    """

    client = _get_client()

    if client is not None:
        return _call_groq(client, summary)

    return _rule_based_insights(summary)


# ── Groq API ─────────────────────────────────────────────────────────────────

MAX_RETRIES = 3
RETRY_DELAYS = [2, 4, 6]

_RETRYABLE_KEYWORDS = [
    "429",
    "rate limit",
    "503",
    "unavailable",
    "overloaded",
    "temporarily",
    "timeout",
    "internal",
    "504",
]


def _is_retryable(error: Exception) -> bool:
    """Check kung temporary ang API error."""

    error_str = str(error).lower()

    return any(
        keyword in error_str
        for keyword in _RETRYABLE_KEYWORDS
    )


def _call_groq(client, summary: dict) -> dict:
    """Tawagan ang Groq API para gumawa ng AI insights."""

    prompt = _build_prompt(summary)
    last_error = None
    attempt = 0

    for attempt in range(1, MAX_RETRIES + 1):

        try:
            print(f"GROQ ATTEMPT {attempt}")

            response = client.chat.completions.create(
                model="openai/gpt-oss-20b",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an AI business analyst specializing "
                            "in small Filipino karinderya businesses. "
                            "Give practical, data-based recommendations."
                        ),
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],
                temperature=0.5,
                max_completion_tokens=1500,
            )

            text = response.choices[0].message.content

            print("GROQ SUCCESS")

            return {
                "source": "ai",
                "insights": text,
                "error": None,
            }

        except Exception as e:

            last_error = e

            print(
                f"GROQ ERROR "
                f"(attempt {attempt}/{MAX_RETRIES}):",
                repr(e)
            )

            if _is_retryable(e) and attempt < MAX_RETRIES:

                delay = RETRY_DELAYS[attempt - 1]

                print(
                    f"Retryable error. "
                    f"Waiting {delay}s..."
                )

                time.sleep(delay)
                continue

            break

    print(
        f"GROQ FAILED after {attempt} attempt(s). "
        "Using rule-based fallback."
    )

    result = _rule_based_insights(summary)

    result["error"] = (
        f"⚠️ Hindi ma-access ang Groq AI API "
        f"after {attempt} attempt(s).\n\n"
        f"**Error:** `{str(last_error)}`\n\n"
        f"Gamit ang rule-based analysis bilang fallback."
    )

    return result


# ── Rule-Based Fallback ──────────────────────────────────────────────────────

def _rule_based_insights(summary: dict) -> dict:
    """Fallback kung hindi available ang Groq API."""

    total = summary.get("total_sales", 0)
    avg_daily = summary.get("avg_daily_sales", 0)
    top_dishes = summary.get("top_dishes", [])
    bottom_dishes = summary.get("bottom_dishes", [])
    hourly = summary.get("hourly_sales", [])
    by_day = summary.get("by_day_name", [])
    transactions = summary.get("total_transactions", 0)

    if transactions == 0:

        return {
            "source": "rule-based",
            "insights": (
                "⚠️ **Walang sales data pa.** "
                "Mag-record muna ng mga benta o pindutin ang "
                "'Generate Sample Data' para ma-test ang system."
            ),
            "error": None,
        }

    # Peak hour
    peak_hour = None

    if hourly:
        peak = max(
            hourly,
            key=lambda x: x.get("revenue", 0)
        )

        peak_hour = peak.get("hour", 12)

    # Best day
    best_day = None

    if by_day:
        best = max(
            by_day,
            key=lambda x: x.get("avg_revenue", 0)
        )

        best_day = best.get("day_name", "N/A")

    # Top dish
    top_dish = (
        top_dishes[0]["dish_name"]
        if top_dishes
        else "N/A"
    )

    top_revenue = (
        top_dishes[0].get("revenue", 0)
        if top_dishes
        else 0
    )

    top_qty = (
        top_dishes[0].get("qty", 0)
        if top_dishes
        else 0
    )

    # Bottom dish
    bot_dish = (
        bottom_dishes[-1]["dish_name"]
        if bottom_dishes
        else "N/A"
    )

    bot_qty = (
        bottom_dishes[-1].get("qty", 0)
        if bottom_dishes
        else 0
    )

    # Suggested servings
    serving_recs = []

    for dish in top_dishes:

        name = dish.get("dish_name", "")
        qty = dish.get("qty", 0)

        num_days_data = max(
            summary.get("total_transactions", 1) // 15,
            1
        )

        avg_per_day = round(
            qty / max(num_days_data, 1)
        )

        buffer = max(
            round(avg_per_day * 0.2),
            1
        )

        serving_recs.append(
            f"- **{name}**: ~{avg_per_day} servings "
            f"+ {buffer} extra (buffer)"
        )

    # Convert peak hour to AM/PM
    if peak_hour is not None:

        peak_str = datetime.strptime(
            f"{int(peak_hour):02d}:00",
            "%H:%M"
        ).strftime("%I:%M %p")

    else:
        peak_str = "N/A"

    # Peak period
    peak_period = ""

    if peak_hour is not None:

        if 6 <= peak_hour <= 10:
            peak_period = "(umaga/breakfast)"

        elif 11 <= peak_hour <= 14:
            peak_period = "(tanghali/lunch)"

        elif 17 <= peak_hour <= 20:
            peak_period = "(gabi/dinner)"

    # Combo price estimate
    combo_price = 0

    if top_dishes and top_qty > 0:
        combo_price = (
            top_revenue / top_qty
        ) + 15

    insights = f"""
## 📊 Sales Patterns Summary

- 💰 **Total Sales:** ₱{total:,.2f}
- 📅 **Average Daily Sales:** ₱{avg_daily:,.2f}
- 📈 **Strongest Day:** **{best_day}**
- ⏰ **Peak Hours:** **{peak_str}** {peak_period}
- 🏆 **Best-seller:** **{top_dish}** — {top_qty} servings
- 📉 **Least-selling:** **{bot_dish}** — {bot_qty} servings

---

## 🍳 Cooking Recommendations

Suggested preparation:

{chr(10).join(serving_recs)}

💡 **Tips:**

- Dagdagan ang preparation ng **{top_dish}**.
- Bawasan nang kaunti ang **{bot_dish}** dahil mababa ang demand.
- Puwedeng gawing combo ang low-selling dish kasama ang rice.

---

## 📦 Inventory & Food Waste Tips

- 🥬 Prioritize ingredients para sa best-selling dishes.
- 🧊 Maghanda ng mas maraming stocks sa **{best_day}**.
- ♻️ Gumawa ng last-order promo para mabawasan ang leftovers.
- 📝 I-track ang dishes na madalas may tira.

---

## 💰 How to Increase Revenue

- 🍚 **Combo Meal:** {top_dish} + Rice ≈ ₱{combo_price:.0f}
- ⏰ Mag-offer ng specials bago o during peak hours.
- 📱 Gumamit ng simple loyalty promo tulad ng 10th order = free rice.
- 📊 Tingnan ang weekly sales trends bago mag-adjust ng menu.
- 🏷️ Puwedeng mag-test ng maliit na price adjustment sa popular dishes.

> 💡 *Rule-based analysis ito dahil hindi available ang Groq AI.*
"""

    return {
        "source": "rule-based",
        "insights": insights,
        "error": None,
    }
