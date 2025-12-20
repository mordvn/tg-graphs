from datetime import datetime
import streamlit as st
import pandas as pd


def parse_date(date_str):
    return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S")


def human_readable_duration(seconds):
    """Format duration as hours and minutes"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    if hours and minutes:
        return f"{hours}h {minutes}m"
    elif hours:
        return f"{hours}h"
    elif minutes:
        return f"{minutes}m"
    else:
        return f"{int(seconds)}s"


def run_plugin(data):
    messages = data.get("messages", [])
    chat_name = data.get("name", "Chat")

    if not messages:
        st.warning("No messages in chat.")
        return

    st.subheader(f"Chat Gaps — {chat_name}")
    st.markdown("Periods with **no messages for 30+ hours**.")

    # Sort messages by time
    messages_sorted = sorted(messages, key=lambda m: m.get("date"))

    # Extract timestamps
    timestamps = []
    for msg in messages_sorted:
        try:
            dt = parse_date(msg["date"])
            timestamps.append(dt)
        except Exception:
            continue

    if len(timestamps) < 2:
        st.warning("Not enough messages for analysis.")
        return

    # Analyze gaps between messages
    SILENCE_THRESHOLD = 30 * 3600  # 30 hours in seconds
    silence_periods = []

    for i in range(1, len(timestamps)):
        prev_time = timestamps[i - 1]
        curr_time = timestamps[i]
        delta = (curr_time - prev_time).total_seconds()

        if delta >= SILENCE_THRESHOLD:
            silence_periods.append(
                {
                    "Start": prev_time.strftime("%Y-%m-%d %H:%M"),
                    "End": curr_time.strftime("%Y-%m-%d %H:%M"),
                    "Duration": human_readable_duration(delta),
                    "Seconds": int(delta),
                }
            )

    if not silence_periods:
        st.success("No gaps longer than 30 hours. Chat is active!")
        return

    # Sort by duration (descending)
    silence_periods.sort(key=lambda p: p["Seconds"], reverse=True)

    # Display table
    df = pd.DataFrame(silence_periods)
    df_display = df.drop(columns=["Seconds"])
    st.dataframe(df_display)

    st.info(f"Found {len(df)} gaps")
