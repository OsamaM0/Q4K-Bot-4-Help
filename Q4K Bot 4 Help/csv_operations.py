# csv_operations.py
import csv
import pandas as pd
import re
from fuzzywuzzy import fuzz

def read_csv(file_path):
    """
    Read data from a CSV file and return a list of dictionaries.
    Each dictionary represents a row with column names as keys.
    """
    with open(file_path, mode='r') as file:
        csv_reader = csv.DictReader(file)
        data = [row for row in csv_reader]
    return data

def write_csv(file_path, data, fieldnames):
    """
    Write data to a CSV file. 
    Data should be a list of dictionaries, and fieldnames is a list specifying the order of columns.
    """
    with open(file_path, mode='w', newline='') as file:
        csv_writer = csv.DictWriter(file, fieldnames=fieldnames)
        csv_writer.writeheader()
        csv_writer.writerows(data)

def add_row_to_csv(file_path, new_row):
    """
    Add a new row to a CSV file. 
    `new_row` should be a dictionary with keys matching the column names.
    """
    fieldnames = get_csv_fieldnames(file_path)
    data = read_csv(file_path)
    data.append(new_row)
    write_csv(file_path, data, fieldnames)


def get_csv_fieldnames(file_path):
    """
    Get the column names (fieldnames) from a CSV file.
    """
    with open(file_path, mode='r') as file:
        csv_reader = csv.DictReader(file)
        fieldnames = csv_reader.fieldnames
    return fieldnames

def remove_row_from_csv(file_path, name_column, row_name):
    """
    Remove a row from a CSV file based on the value in the specified column.
    """
    data = pd.read_csv(file_path)
    
    # Find the index of the row with the specified name
    index_to_remove = data.index[data[name_column] == row_name].tolist()
    
    if index_to_remove:
        # Remove the row
        data.drop(index_to_remove, inplace=True)
    
        # Save the updated data back to the CSV file
        data.to_csv(file_path, index=False)
        return (f"Message Removed successfully.")
    else:
        return (f"Message Not Found.")
    


def retrieve_data_advanced(file_path, condition, columne=None, similarity_threshold=100):
    """
    Reads a CSV file and retrieves rows based on complex conditions using '&' (AND), '|' (OR), and '-' (EXCEPT) operations.

    Parameters:
    - file_path (str): The path to the CSV file.
    - condition (str): The condition string, e.g., 'Database&2023' or 'Database|2023' or 'Database-2023'.
    - columne (str, optional): The column name to filter. Default is None.
    - similarity_threshold (int, optional): The similarity threshold for fuzzy matching. Default is 80.

    Returns:
    - pd.DataFrame: A DataFrame containing the filtered rows based on the condition.

    Example:
    >>> retrieve_data_advanced('your_file.csv', 'Database&2023')
    """

    # Read CSV file into a DataFrame and retrieve all data except file data
    df = pd.read_csv(file_path) if (columne is None) else pd.read_csv(file_path)[columne]

    # Parse the condition string
    # Split by '&' (AND), '|' (OR), and '-' (EXCEPT) without including spaces
    search_keywords = re.split(r'[&|-]', condition)
    # Remove empty strings (resulting from consecutive operators)
    search_keywords = list(filter(None, search_keywords))

    # Get the operations between keywords
    operations = re.findall(r'[&|-]', condition)

    # Define a function for fuzzy matching
    def fuzzy_match(keyword, row):
        for value in dict(row).values(): 
            if len(str(value)) > 1 :
                if similarity_threshold == 100:
                    if keyword.lower() == str(value).lower():
                        return True
                else:
                    if (fuzz.partial_ratio(keyword.lower(), str(value).lower()) >= similarity_threshold):
                        print(str(value).lower())
                        return True
        return False

    # Apply fuzzy matching for the first keyword
    filter_mask = df.apply(lambda row: fuzzy_match(search_keywords[0], row), axis=1)
    print(filter_mask)

    for i in range(len(operations)):
        # Apply the corresponding operation based on the condition
        if '&' == operations[i]:
            filter_mask = filter_mask & df[filter_mask].apply(lambda row: fuzzy_match(search_keywords[i + 1], row), axis=1)
        elif '|' == operations[i]:
            filter_mask = filter_mask | df.apply(lambda row: fuzzy_match(search_keywords[i + 1], row), axis=1)
        elif '-' == operations[i]:
            filter_mask = filter_mask & ~df[filter_mask].apply(lambda row: fuzzy_match(search_keywords[i + 1], row), axis=1)
        else:
            raise ValueError("Invalid condition. Please use '&' for AND, '|' for OR, or '-' for EXCEPT.")


    # Apply the mask to get the filtered data
    filtered_rows = df[filter_mask]

    return filtered_rows


