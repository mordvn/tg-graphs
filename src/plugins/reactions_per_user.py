from collections import defaultdict, Counter
import streamlit as st
import pandas as pd


def run_plugin(data):
    messages = data.get("messages", [])
    chat_name = data.get("name", "Chat")

    if not messages:
        st.warning("No messages to analyze.")
        return

    st.subheader(f"Reactions — {chat_name}")

    # Counters
    total_emoji_counts = Counter()
    user_emoji_counts = defaultdict(Counter)

    for msg in messages:
        for reaction in msg.get("reactions", []):
            emoji = reaction.get("emoji")
            count = reaction.get("count", 0)
            total_emoji_counts[emoji] += count

            # Use recent for user attribution
            for entry in reaction.get("recent", []):
                user = entry.get("from")
                if user and emoji:
                    user_emoji_counts[user][emoji] += 1

    # Top reactions
    st.markdown("### 🔝 Top Reactions")
    if total_emoji_counts:
        df_total = pd.DataFrame(total_emoji_counts.items(), columns=["Emoji", "Total"])
        df_total = df_total.sort_values("Total", ascending=False).reset_index(drop=True)
        st.dataframe(df_total)
    else:
        st.info("No reactions in chat.")

    # Reactions by user
    st.markdown("### 👥 Reactions by User")
    if user_emoji_counts:
        users = sorted(user_emoji_counts.keys())
        all_emojis = sorted(
            {emoji for counter in user_emoji_counts.values() for emoji in counter}
        )

        table = []
        for user in users:
            row = {"User": user}
            for emoji in all_emojis:
                row[emoji] = user_emoji_counts[user].get(emoji, 0)
            table.append(row)

        df_users = pd.DataFrame(table)
        st.dataframe(df_users.set_index("User"))
    else:
        st.info("No user reaction data available.")

    # Individual analysis
    st.markdown("### 🔍 User Details")
    selected_user = st.selectbox("Select user", [""] + users)
    if selected_user:
        top_emojis = user_emoji_counts[selected_user].most_common()
        if top_emojis:
            df_user = pd.DataFrame(top_emojis, columns=["Emoji", "Count"])
            st.dataframe(df_user)
        else:
            st.write("No reactions from this user.")
