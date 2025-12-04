import csv

def get_bug_info(file_path = "/home/##/ttr/defects4j-bugs.csv"):
    try:
        with open(file_path, mode='r', encoding='utf-8') as file:
            csv_reader = csv.reader(file)

            # Skip the header row
            next(csv_reader)

            # Initialize separate lists for the desired columns
            col0 = []
            col1 = []
            col5 = []
            col6 = []
            col7 = []

            # Loop through the rows and populate the lists
            for row in csv_reader:
                if row[15] != '1' and  row[0] != "Mockito":  # Apply filter condition, active v1.0
                    col0.append(row[0])
                    col1.append(row[1])
                    col5.append(row[5])
                    col6.append(row[6])
                    col7.append(row[7])

            # Return the lists as a tuple
            return col0, col1, col5, col6, col7

    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
        return [], [], [], [], []
    except Exception as e:
        print(f"An error occurred: {e}")
        return [], [], [], [], []

