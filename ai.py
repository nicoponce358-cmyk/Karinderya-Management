"""
ai.py — AI Insights module para sa Karinderya Management System.
Gumagamit ng Anthropic API kung may key; kung wala, rule-based fallback.
"""

import os
import json
from datetime import datetime

try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def _get_client():
    """Kumuha ng Anthropic client kung may API key."""
    api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    if not api_key or Anthropic is None:
        return None
    try:
        return Anthropic(api_key=api_key)
    except Exception:
        return None


def _build_prompt(summary: dict) -> str:
    """Gumawa ng prompt mula sa summary data."""
    today = datetime.now().strftime("%A, %B %d, %Y")
    day_name = datetime.now().strftime("%A")

    prompt = f"""Ikaw ay isang expert food-business consultant para sa maliit na Filipino karinderya.
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

Base sa data na ito, ibigay ang sumusunod na insights sa TAGLISH (Tagalog-English mix), simple at madaling intindihin:

1. **📊 Buod ng Sales Patterns** — Ano ang trend ng benta? Anong araw pinaka-malakas? Anong oras peak?

2. **🍳 Recommendations sa Luto** — Anong dish ang dagdagan ng luto? Alin ang bawasan? Ilang servings ang ihanda bukas ({day_name}) base sa average ng parehong araw ng linggo?

3. **📦 Inventory & Food Waste Tips** — Paano mababawasan ang nasasayang na pagkain? Anong ingredients ang i-prioritize?

4. **💰 Paano Dadagdagan ang Kita** — Practical tips para sa maliit na karinderya — combos, pricing, timing, etc.

Gumamit ng emoji at bullet points. Simple lang ang salita, para maintindihan ng karaniwang tindero/tindera.
Huwag masyadong mahaba — mga 400-600 words lang."""

    return prompt


def get_ai_insights(summary: dict) -> dict:
    """
    Kumuha ng AI insights. Returns dict na may:
      - "source": "ai" | "rule-based"
      - "insights": str (markdown)
      - "error": str | None
    """
    client = _get_client()

    if client is not None:
        return _call_anthropic(client, summary)
    else:
        return _rule_based_insights(summary)


def _call_anthropic(client, summary: dict) -> dict:
    """Tawagan ang Anthropic API para sa insights."""
    try:
        prompt = _build_prompt(summary)
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}],
        )
        text = response.content[0].text
        return {"source": "ai", "insights": text, "error": None}
    except Exception as e:
        # Fallback sa rule-based kung may error
        result = _rule_based_insights(summary)
        result["error"] = f"Hindi ma-access ang AI API ({str(e)[:80]}). Gamit ang rule-based analysis."
        return result


def _rule_based_insights(summary: dict) -> dict:
    """Rule-based fallback kung walang API key."""

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
            "insights": "⚠️ **Walang sales data pa.** Mag-record muna ng mga benta o pindutin ang 'Generate Sample Data' para ma-test ang system.",
            "error": None,
        }

    # Find peak hour
    peak_hour = None
    if hourly:
        peak = max(hourly, key=lambda x: x.get("revenue", 0))
        peak_hour = peak.get("hour", 12)

    # Find best day
    best_day = None
    if by_day:
        best = max(by_day, key=lambda x: x.get("avg_revenue", 0))
        best_day = best.get("day_name", "N/A")

    # Top dish
    top_dish = top_dishes[0]["dish_name"] if top_dishes else "N/A"
    top_revenue = top_dishes[0].get("revenue", 0) if top_dishes else 0
    top_qty = top_dishes[0].get("qty", 0) if top_dishes else 0

    # Bottom dish
    bot_dish = bottom_dishes[-1]["dish_name"] if bottom_dishes else "N/A"
    bot_qty = bottom_dishes[-1].get("qty", 0) if bottom_dishes else 0

    # Build avg servings per dish
    serving_recs = []
    for d in top_dishes:
        name = d.get("dish_name", "")
        qty = d.get("qty", 0)
        num_days_data = max(summary.get("total_transactions", 1) // 15, 1)
        avg_per_day = round(qty / max(num_days_data, 1))
        buffer = max(round(avg_per_day * 0.2), 1)
        serving_recs.append(f"  - **{name}**: ~{avg_per_day} servings + {buffer} extra (buffer)")

    peak_str = f"{peak_hour}:00" if peak_hour is not None else "N/A"
    peak_period = ""
    if peak_hour is not None:
        if 6 <= peak_hour <= 10:
            peak_period = "(umaga/breakfast)"
        elif 11 <= peak_hour <= 14:
            peak_period = "(tanghali/lunch)"
        elif 17 <= peak_hour <= 20:
            peak_period = "(gabi/dinner)"

    insights = f"""## 📊 Sales Patterns Summary

- 💰 **Total Sales**: ₱{total:,.2f} — average of **₱{avg_daily:,.2f} per day**
- 📈 **Strongest day**: **{best_day}** — most customers
- ⏰ **Peak hours**: **{peak_str}** {peak_period} — highest sales volume
- 🏆 **Best-seller**: **{top_dish}** — {top_qty} servings, ₱{top_revenue:,.2f} total revenue
- 📉 **Least-selling**: **{bot_dish}** — only {bot_qty} servings

---

## 🍳 Cooking Recommendations

Based on sales trends, here is the suggested preparation for tomorrow:

{chr(10).join(serving_recs)}

💡 **Tips**:
- Increase preparation for **{top_dish}** — it's always selling out
- Consider reducing **{bot_dish}** — low demand
- If there's excess {bot_dish}, offer it as a promo combo with Rice

---

## 📦 Inventory & Food Waste Tips

- 🥬 **Prioritize ingredients for top-sellers** — lower risk of waste
- 🧊 **Prepare more on weekends** ({best_day} is the peak!) and less on weekdays
- ♻️ If there are leftover dishes, offer a **"last order" promo** before closing — half price
- 📝 Track which dishes always have leftovers — reduce their preparation

---

## 💰 How to Increase Revenue

- 🍚 **Combo Meals**: {top_dish} + Rice = ₱{(top_dishes[0].get('revenue',0)/max(top_qty,1) + 15):.0f} combo — cheaper per item but higher volume
- ⏰ **Lunch Specials**: Offer a discounted combo during 11AM-1PM to maximize peak hours
- 📱 **Loyalty card**: 10th order = free Rice — to encourage repeat customers
- 📊 Study weekly trends — adjust the menu based on actual demand
- 🏷️ **Slightly increase** (₱5-10) the price of best-sellers — customers won't notice much but it adds up significantly

> 💡 *This is a rule-based analysis. For more detailed insights, set up an Anthropic API key in the `.env` file.*
"""

    return {"source": "rule-based", "insights": insights, "error": None}
