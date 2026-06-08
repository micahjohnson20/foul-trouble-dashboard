import pandas as pd
d1_df = pd.read_csv('data/d1_players.csv')


print(d1_df['CLOSE_2_MADE_ATT'].head(10))