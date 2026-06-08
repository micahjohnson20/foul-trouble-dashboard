import streamlit as st
import pandas as pd
from model import get_foul_targets, get_matchups, d1_df

teams = sorted(d1_df['TEAM'].unique().tolist())

def highlight_top_ranks(results_df):
    cols_to_check = ['FC40', 'PRPG', 'MIN_PCT', 'BLK', 'PERF_DROP']

    def color_cell(val, col):
        try:
            rank = (d1_df[col] >= val).sum()
            if rank <= 10:
                return 'background-color: gold'
            elif rank <= 20:
                return 'background-color: orange'
            elif rank <= 30:
                return 'background-color: lightyellow'
        except:
            pass
        return ''

    styler = results_df.style
    for col in cols_to_check:
        if col in results_df.columns:
            styler = styler.applymap(
                lambda val: color_cell(val, col), subset=[col]
            )
    return styler

st.title("Foul Trouble Leverage Dashboard")
st.write("Identify opponent players to target offensively to maximize lineup disruption.")

col1, col2 = st.columns(2)

with col1:
    team_name = st.selectbox("Select opponent team:", [""] + teams)

with col2:
    your_team = st.selectbox("Select your team:", [""] + teams)

if team_name and your_team:
    with st.spinner("Analyzing..."):
        results = get_foul_targets(team_name)

    if results is not None:
        results = get_matchups(results, your_team)
        st.success(f"Found {len(results)} foul-trouble target(s) for {team_name}")
        st.dataframe(highlight_top_ranks(results), use_container_width=True)

        st.markdown("---")
        st.markdown("**Column Guide**")
        st.markdown("- **FC40** — Personal fouls per 40 minutes")
        st.markdown("- **PRPG** — Player rating per game (overall value)")
        st.markdown("- **MIN_PCT** — Percentage of minutes played")
        st.markdown("- **PERF_DROP** — Estimated lineup quality loss when this player sits")
        st.markdown("- **BACKUP** — Player who replaces them and their PRPG")
        st.markdown("- **PERCENTILE** — Foul-trouble target rank vs all D-1 players")
        st.markdown("- **ATTACKER** — Recommended player to attack this target")
        st.markdown("- **ATTACKER_SCORE** — Attacker's foul-drawing ability score")

        st.markdown("---")
        st.markdown("**Color Guide**")
        st.markdown("🟡 Top 30 in D-1 | 🟠 Top 20 in D-1 | 🥇 Top 10 in D-1")
    else:
        st.info("No foul-prone targets found for this team — low foul risk roster.")