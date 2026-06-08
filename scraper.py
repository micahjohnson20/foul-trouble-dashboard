from selenium import webdriver
from selenium.webdriver.common.by import By
from urllib.parse import unquote
import time
import pandas as pd
from io import StringIO

url = "https://barttorvik.com/playerstat.php?link=y&year=2026&minmin=15"

options = webdriver.ChromeOptions()
options.add_argument("--no-sandbox")

driver = webdriver.Chrome(options=options)

try:
    driver.get(url)
    time.sleep(5)

    all_btn = driver.find_element(By.CSS_SELECTOR, "span#all")
    driver.execute_script("arguments[0].click();", all_btn)
    time.sleep(8)

    count = 0
    while True:
        try:
            prev_rows = len(driver.find_elements(By.CSS_SELECTOR, "table tr"))
            show_more = driver.find_element(By.XPATH, "//a[contains(text(), 'Show 100 more')]")
            driver.execute_script("arguments[0].click();", show_more)
            time.sleep(3)
            new_rows = len(driver.find_elements(By.CSS_SELECTOR, "table tr"))
            count += 100
            print(f"Clicked {count} times... rows: {new_rows}")
            if new_rows == prev_rows:
                print("No new rows, stopping")
                break
        except:
            print("All players loaded")
            break

    print("Extracting team names...")
    tables = driver.find_elements(By.TAG_NAME, "table")
    table = tables[-1]

    teams = []
    for row in table.find_elements(By.TAG_NAME, "tr"):
        team = ""
        for link in row.find_elements(By.TAG_NAME, "a"):
            href = link.get_attribute("href")
            if href and "team=" in href:
                team = href.split("team=")[1].split("&")[0]
                break
        teams.append(team)

    print("Extracting table HTML...")
    table_html = table.get_attribute("outerHTML")

finally:
    driver.quit()

print("Parsing table...")
df = pd.read_html(StringIO(table_html))[0]

# insert team column
df.insert(5, 'TEAM', teams[1:len(df)+1])

# drop unnamed columns
df = df.loc[:, ~df.columns.str.startswith('Unnamed')]

# rename columns
df = df.rename(columns={
    'Player': 'YR',
    'Player.1': 'HT',
    'Player.2': 'PLAYER',
    'Player.3': 'BLANK',
    'Team': 'CONF',
    'Conf': 'G',
    'G': 'ROLE',
    'Role': 'MIN_PCT',
    'Min%': 'PRPG',
    'PRPG!': 'D_PRPG',
    'D-PRPG': 'BPM',
    'BPM': 'OBPM',
    'OBPM': 'DBPM',
    'DBPM': 'ORTG',
    'ORtg': 'DRTG',
    'D-Rtg': 'USG',
    'Usg': 'EFG',
    'eFG': 'TS',
    'TS': 'OR',
    'OR': 'DR',
    'DR': 'AST',
    'Ast': 'TO',
    'TO': 'A_TO',
    'A/TO': 'BLK',
    'Blk': 'STL',
    'Stl': 'FTR',
    'FTR': 'FC40',
    'FC/40': 'DUNKS_MADE_ATT',
    'Dunks': 'DUNKS_PCT',
    'Dunks.1': 'CLOSE_2_MADE_ATT',
    'Close 2': 'CLOSE_2_PCT',
    'Close 2.1': 'FAR_2_MADE_ATT',
    'Far 2': 'FAR_2_PCT',
    'Far 2.1': 'FT_MADE_ATT',
    'FT': 'FT_PCT',
    'FT.1': '2P_MADE_ATT',
    '2P': '2P_PCT',
    '2P.1': '3PR',
    '3PR': '3P_PER_100',
    '3P/100': '3P_MADE_ATT',
    '3P': '3P_PCT',
})

df = df.drop(columns=['BLANK', '3P.1'], errors='ignore')
df = df[~df['PLAYER'].isin(['Show 100 more', 'Show Chart'])]
df = df.dropna(subset=['PLAYER'])

# fix team name encoding
df['TEAM'] = df['TEAM'].apply(unquote)

print(df.shape)
print(df[['PLAYER', 'TEAM', 'CONF', 'FC40']].head(10).to_string())
df.to_csv("d1_players.csv", index=False)
print("Saved!")