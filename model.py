import pandas as pd
from sklearn.preprocessing import StandardScaler
from scipy.stats import percentileofscore

# ── 1. Load data ──────────────────────────────────────────────
d1_df = pd.read_csv('data/d1_players.csv')

# ── 2. Map positions ──────────────────────────────────────────
role_map = {
    'Combo G': 'Guard',
    'Scoring PG': 'Guard',
    'Pure PG': 'Guard',
    'Wing G': 'Guard',
    'Stretch 4': 'Forward',
    'Wing F': 'Forward',
    'PF/C': 'Big',
    'C': 'Big'
}
d1_df['POSITION'] = d1_df['ROLE'].map(role_map)
d1_df['CLOSE_2_ATT'] = d1_df['CLOSE_2_MADE_ATT'].str.split('-').str[1].astype(float)

# ── 3. Replacement gap function ───────────────────────────────
def get_replacement_gap(player_row, team_df):
    position = player_row['POSITION']
    player_min = player_row['MIN_PCT']
    player_prpg = player_row['PRPG']

    same_position = team_df[
        (team_df['POSITION'] == position) &
        (team_df['MIN_PCT'] < player_min * 0.85)
    ]

    if len(same_position) == 0:
        return 0

    backup_prpg = same_position['PRPG'].max()
    return player_prpg - backup_prpg

# ── 4. Performance drop function ─────────────────────────────
def get_performance_drop(player_row, team_df):
    position = player_row['POSITION']
    player_min = player_row['MIN_PCT']
    player_prpg = player_row['PRPG']

    same_position = team_df[
        (team_df['POSITION'] == position) &
        (team_df['MIN_PCT'] < player_min * 0.85)
    ]

    if len(same_position) == 0:
        backup_prpg = 0
    else:
        backup_prpg = same_position['PRPG'].max()

    return round((player_prpg - backup_prpg) * (player_min / 100), 2)

# ── 5. Backup name function ───────────────────────────────────
def get_backup_name(player_row, team_df):
    position = player_row['POSITION']
    player_min = player_row['MIN_PCT']

    same_position = team_df[
        (team_df['POSITION'] == position) &
        (team_df['MIN_PCT'] < player_min * 0.85)
    ]

    if len(same_position) == 0:
        return 'No backup'

    backup = same_position.loc[same_position['PRPG'].idxmax()]
    return f"{backup['PLAYER']} ({backup['PRPG']})"

# ── 6. Calculate PERF_DROP and FOUL_IMPACT for all D-1 players
d1_df['PERF_DROP'] = d1_df.apply(
    lambda row: get_performance_drop(
        row, d1_df[d1_df['TEAM'] == row['TEAM']]
    ),
    axis=1
)
d1_df['FOUL_IMPACT'] = d1_df['FC40'] * (d1_df['MIN_PCT'] / 100)

# ── 7. Fit scaler on full D-1 data ────────────────────────────
features = ['FOUL_IMPACT', 'PRPG', 'PERF_DROP', 'USG', 'BLK', 'MIN_PCT']
scaler = StandardScaler()
scaler.fit(d1_df[features])

# ── 8. Calculate TARGET_SCORE for all D-1 foul-prone players ──
d1_targets = d1_df[d1_df['FC40'] >= 4.0].copy()
d1_targets_normalized = d1_targets.copy()
d1_targets_normalized[features] = scaler.transform(d1_targets[features])

weights = {
    'FOUL_IMPACT': 0.40,
    'PRPG': 0.15,
    'PERF_DROP': 0.20,
    'USG': 0.05,
    'BLK': 0.05,
    'MIN_PCT': 0.15
}

d1_targets['TARGET_SCORE'] = sum(
    d1_targets_normalized[col] * weight
    for col, weight in weights.items()
)

# ── 9. Matchup function ───────────────────────────────────────
def get_matchups(targets_df, your_team):
    your_team_df = d1_df[d1_df['TEAM'] == your_team].copy()
    your_team_df['POSITION'] = your_team_df['ROLE'].map(role_map)
    your_team_df['CLOSE_2_ATT'] = your_team_df['CLOSE_2_MADE_ATT'].str.split('-').str[1].astype(float)

    matchups = []
    attacker_scores = []

    for _, target in targets_df.iterrows():
        position = target['POSITION']

        same_pos = your_team_df[your_team_df['POSITION'] == position].copy()

        if len(same_pos) == 0:
            matchups.append('No direct matchup found')
            attacker_scores.append(None)
        else:
            same_pos['ATTACKER_SCORE'] = (
                same_pos['FTR'] +
                (same_pos['CLOSE_2_ATT'] / same_pos['CLOSE_2_ATT'].max())
            )
            best_attacker = same_pos.loc[same_pos['ATTACKER_SCORE'].idxmax()]
            matchups.append(best_attacker['PLAYER'])
            attacker_scores.append(round(best_attacker['ATTACKER_SCORE'], 2))

    targets_df = targets_df.copy()
    targets_df['ATTACKER'] = matchups
    targets_df['ATTACKER_SCORE'] = attacker_scores
    return targets_df

# ── 10. Main function ─────────────────────────────────────────
def get_foul_targets(team_name):
    team_df = d1_df[d1_df['TEAM'] == team_name].copy()

    if len(team_df) == 0:
        print(f"Team '{team_name}' not found in dataset")
        return None

    team_df['PERF_DROP'] = team_df.apply(
        lambda row: get_performance_drop(row, team_df), axis=1
    )
    team_df['FOUL_IMPACT'] = team_df['FC40'] * (team_df['MIN_PCT'] / 100)
    team_df['BACKUP'] = team_df.apply(
        lambda row: get_backup_name(row, team_df), axis=1
    )

    targets = team_df[team_df['FC40'] >= 4.0].copy()

    if len(targets) == 0:
        return None

    targets_display = targets[['PLAYER', 'POSITION', 'FC40', 'PRPG',
                                'MIN_PCT', 'USG', 'BLK',
                                'PERF_DROP', 'BACKUP']].copy()

    targets_normalized = targets.copy()
    targets_normalized[features] = scaler.transform(targets[features])

    targets_normalized['TARGET_SCORE'] = sum(
        targets_normalized[col] * weight
        for col, weight in weights.items()
    )

    targets_display['PERCENTILE'] = targets_normalized['TARGET_SCORE'].apply(
        lambda x: round(percentileofscore(d1_targets['TARGET_SCORE'], x), 1)
    )

    results = targets_display.sort_values('PERCENTILE', ascending=False)
    return results