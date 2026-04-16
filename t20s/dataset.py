import yaml
import pandas as pd
import os
from collections import defaultdict

def process_t20_folder(folder_name):
    # Dictionary to store data for each year
    # Key: Year (str), Value: List of ball-by-ball dictionaries
    year_wise_data = defaultdict(list)
    
    # Check if folder exists
    if not os.path.exists(folder_name):
        print(f"Error: Folder '{folder_name}' not found.")
        return

    for filename in os.listdir(folder_name):
        if filename.endswith('.yaml'):
            file_path = os.path.join(folder_name, filename)
            
            with open(file_path, 'r') as f:
                try:
                    # Loading data safely
                    data = yaml.load(f, Loader=yaml.SafeLoader)
                    
                    # 1. Extract Match Year
                    match_dates = data.get('info', {}).get('dates', [])
                    match_year = str(match_dates[0])[:4] if match_dates else "Unknown"
                    
                    # 2. Extract Match Metadata for context
                    match_id = filename.replace('.yaml', '')
                    venue = data.get('info', {}).get('venue', 'Unknown')
                    
                    # 3. Navigate Innings
                    for inning_entry in data.get('innings', []):
                        for inning_name, content in inning_entry.items():
                            batting_team = content.get('team')
                            
                            # 4. Navigate every single delivery (Ball-by-Ball)
                            for delivery in content.get('deliveries', []):
                                for ball_num, details in delivery.items():
                                    
                                    # Construct the row
                                    ball_row = {
                                        'match_id': match_id,
                                        'year': match_year,
                                        'venue': venue,
                                        'innings': inning_name,
                                        'batting_team': batting_team,
                                        'ball': ball_num,
                                        'batsman': details.get('batsman'),
                                        'bowler': details.get('bowler'),
                                        'non_striker': details.get('non_striker'),
                                        'runs_batsman': details.get('runs', {}).get('batsman', 0),
                                        'runs_extras': details.get('runs', {}).get('extras', 0),
                                        'runs_total': details.get('runs', {}).get('total', 0),
                                        # Breakdown of extras
                                        'wides': details.get('extras', {}).get('wides', 0),
                                        'noballs': details.get('extras', {}).get('noballs', 0),
                                        'legbyes': details.get('extras', {}).get('legbyes', 0),
                                        # Wicket Data
                                        'is_wicket': 1 if 'wicket' in details else 0,
                                        'player_out': details.get('wicket', {}).get('player_out') if 'wicket' in details else None,
                                        'dismissal_kind': details.get('wicket', {}).get('kind') if 'wicket' in details else None
                                    }
                                    
                                    year_wise_data[match_year].append(ball_row)
                    
                    print(f"Successfully processed: {filename} ({match_year})")
                
                except Exception as e:
                    print(f"Skipping {filename} due to error: {e}")

    # 5. Save each year group to its own CSV
    for year, rows in year_wise_data.items():
        df = pd.DataFrame(rows)
        output_name = f"t20_ball_by_ball_{year}.csv"
        df.to_csv(output_name, index=False)
        print(f"--- Saved {len(df)} rows to {output_name} ---")

# Run the script on your folder
process_t20_folder('t20s')