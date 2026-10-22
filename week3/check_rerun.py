from pathlib import Path
import pandas as pd
from clean_orders import load_raw, clean

raw = load_raw()
first = clean(raw)
second = clean(first)

print('행 수 같은가 :', len(first) == len(second))
print('내용 같은가 :', first.equals(second))

first.to_parquet('t1.parquet', index=False)
second.to_parquet('t2.parquet', index=False)

saved_first = pd.read_parquet('t1.parquet')
saved_second = pd.read_parquet('t2.parquet')
print('파일로도 같은가:', saved_first.equals(saved_second))

Path('t1.parquet').unlink()
Path('t2.parquet').unlink()
