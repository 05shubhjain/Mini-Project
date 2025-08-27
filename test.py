import os
import csv
from datetime import datetime
os.makedirs("records_sample", exist_ok=True)
current_date = datetime.now().strftime("%Y-%m-%d")
csv_filename = os.path.join("records_sample", f"{current_date}.csv")
# Open CSV file for appending
f = open(csv_filename, 'a', newline='') 
lnwriter = csv.writer(f)

# Add header if file is empty
if os.stat(csv_filename).st_size == 0:
    lnwriter.writerow(["Name", "Time"],["Name","Age"])

# Append new data
with open(csv_filename, "a") as file:
    f.write("John,25,New York\n")
