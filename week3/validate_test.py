import pandas as pd
from clean_orders import load_raw, clean

VALID_CATEGORIES = ['식품', '가전', '의류', '도서']


def validate(df):
    return {
        'price_le_0': int((df['price'] <= 0).sum()),
        'quantity_le_0': int((df['quantity'] <= 0).sum()),
        'future_date': int(
            (df['order_date'] > pd.Timestamp.today().normalize()).sum()
        ),
        'unknown_cat': int(
            (~df['category'].isin(VALID_CATEGORIES)).sum()
        ),
    }


cleaned = clean(load_raw())
print('정제본 검사:', validate(cleaned))

bad = cleaned.copy()
bad.loc[bad.index[0], 'price'] = -1000
bad.loc[bad.index[0], 'category'] = '알수없음'
print('나쁜 값 주입 후:', validate(bad))
