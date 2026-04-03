import yfinance as yf
import pandas as pd
from datetime import datetime
import os
import json

def fetch_macro_data(start_date="2023-01-01"):
    end_date = datetime.now().strftime("%Y-%m-%d")
    
    bronze_path = "data/bronze"
    silver_path = "data/silver"
    os.makedirs(bronze_path, exist_ok=True)
    os.makedirs(silver_path, exist_ok=True)
    
    print(f"[*] {start_date} - {end_date} arasi makro veriler guncelleniyor...")
    
    try:
        usd_data = yf.download("USDTRY=X", start=start_date, end=end_date)
        if isinstance(usd_data.columns, pd.MultiIndex):
            usd_data.columns = usd_data.columns.get_level_values(0)
            
        usd_df = usd_data[['Close']].reset_index()
        usd_df.columns = ['tarih', 'dolar_kuru']
        
        oil_data = yf.download("BZ=F", start=start_date, end=end_date)
        if isinstance(oil_data.columns, pd.MultiIndex):
            oil_data.columns = oil_data.columns.get_level_values(0)
            
        oil_df = oil_data[['Close']].reset_index()
        oil_df.columns = ['tarih', 'brent_petrol']
        
        usd_df['tarih'] = pd.to_datetime(usd_df['tarih']).dt.tz_localize(None)
        oil_df['tarih'] = pd.to_datetime(oil_df['tarih']).dt.tz_localize(None)
        
        new_macro = pd.merge(usd_df, oil_df, on='tarih', how='outer').sort_values('tarih')
        
        output_path = os.path.join(silver_path, "macro_data.csv")
        
        if os.path.exists(output_path):
            existing_df = pd.read_csv(output_path)
            existing_df['tarih'] = pd.to_datetime(existing_df['tarih'])
            final_df = pd.concat([existing_df, new_macro]).drop_duplicates('tarih').sort_values('tarih')
        else:
            final_df = new_macro
            
        final_df = final_df.ffill().bfill()
        final_df.to_csv(output_path, index=False)
        
        print(f"[+] Makro veriler silver katmanina islendi: {output_path}")

    except Exception as e:
        print(f"[X] Hata: {e}")

if __name__ == "__main__":
    state_path = "data/state.json"
    start = "2023-01-01"
    
    if os.path.exists(state_path):
        try:
            with open(state_path, "r") as f:
                state = json.load(f)
                start = state.get("last_run", "2023-01-01")
        except:
            pass
            
    fetch_macro_data(start_date=start)