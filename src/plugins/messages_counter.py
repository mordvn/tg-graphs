from collections import defaultdict

import streamlit as st


def run_plugin(data):
    messages = data.get("messages", [])
    if not messages:
        st.warning("No messages in chat.")
        return

    count = defaultdict(int)
    for msg in messages:
        if "from" in msg:
            count[msg["from"]] += 1

    st.write("### Messages per User")
    for user, c in count.items():
        st.write(f"**{user}**: {c} messages")
