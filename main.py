from src import ingestion

if __name__ == "__main__":
    df = ingestion.load_and_preview("data/input_sample.csv")
    print(df.head())
