import sqlite3

def fix_missing_dates():
    conn = sqlite3.connect("job_market_research.db")
    cursor = conn.cursor()
    
    # Update any rows that don't have a date_scraped
    cursor.execute("UPDATE jobs SET date_scraped = CURRENT_TIMESTAMP WHERE date_scraped IS NULL OR date_scraped = ''")
    
    # Check how many rows were fixed
    print(f"Updated {cursor.rowcount} rows with missing timestamps.")
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    fix_missing_dates()