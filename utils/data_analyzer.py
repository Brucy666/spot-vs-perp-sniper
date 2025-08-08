from utils.supabase_client import supabase
import pandas as pd

def fetch_table(table_name):
    res = supabase.table(table_name).select("*").execute()
    return pd.DataFrame(res.data) if res.data else pd.DataFrame()

def analyze_trap_performance():
    traps = fetch_table("Traps")
    if traps.empty:
        print("No trap data found.")
        return
    
    # Win rate
    win_rate = traps['outcome'].value_counts(normalize=True).get('win', 0) * 100
    print(f"📊 Win rate: {win_rate:.2f}%")
    
    # Performance by confidence score
    conf_perf = traps.groupby('confidence').outcome.value_counts(normalize=True).unstack().fillna(0) * 100
    print("\n📈 Performance by confidence:\n", conf_perf)

if __name__ == "__main__":
    analyze_trap_performance()
