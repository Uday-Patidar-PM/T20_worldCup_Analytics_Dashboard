import pandas as pd
import os

print("Loading massive CSV...")
df = pd.read_csv('d:/t20_DEA/t20_ball_by_ball.csv', low_memory=False)

print("Compressing to GZIP...")
df.to_csv('d:/t20_DEA/t20_ball_by_ball.csv.gz', compression='gzip', index=False)

print("Compression successful!")
old_size = os.path.getsize('d:/t20_DEA/t20_ball_by_ball.csv') / (1024 * 1024)
new_size = os.path.getsize('d:/t20_DEA/t20_ball_by_ball.csv.gz') / (1024 * 1024)
print(f"Old size: {old_size:.2f} MB")
print(f"New size: {new_size:.2f} MB")
