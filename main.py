from src.data_automation.reader import read_file

df = read_file("data/input/customers.csv")

print(df)
print("\nDataset information:")
print(df.info())