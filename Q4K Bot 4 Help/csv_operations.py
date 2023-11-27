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
    data = [{key: str(value) for key, value in row.items()} for row in data]
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

def edit_row_in_csv(csv_file, file_id_column, target_file_id, new_values):
    # Read the CSV file into a Pandas DataFrame
    df = pd.read_csv(csv_file)
    # Find the index of the row with the target 'File ID'
    row_index = df.index[df[file_id_column] == target_file_id].tolist()[0]
    # Update the values in the identified row
    for col, value in new_values.items():
        try:
            df.at[row_index, col] = value
        except Exception as e:
            pass
    # Save the modified DataFrame back to the CSV file
    df.to_csv(csv_file, index=False)

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
    

def get_row_from_csv(csv_file, file_id_column, target_file_id):
    
    # Read the CSV file into a Pandas DataFrame
    df = pd.read_csv(csv_file)
    # Filter the DataFrame based on the target File ID
    selected_row = df[df[file_id_column] == target_file_id]
    if len(selected_row) == 0: 
        return None
    # Convert the selected row to a dictionary
    result_dict = selected_row.to_dict(orient='records')[0]
    return result_dict 

def retrieve_data_advanced(file_path, condition, columne=None, similarity_threshold=90):
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
    df = pd.read_csv(file_path).astype(str) if (columne is None) else pd.read_csv(file_path)[columne]

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
            if similarity_threshold == 100:
                if keyword.lower() == str(value).lower():
                   
                    return True
            else:
                if (fuzz.ratio(keyword.lower(), str(value).lower()) >= similarity_threshold):
                    return True
        return False

    # Apply fuzzy matching for the first keyword
    filter_mask = df.apply(lambda row: fuzzy_match(search_keywords[0], row), axis=1)
    
    for i in range(len(operations)):
        # Prevent use of fuzzy matching for symboles
        try:
            if len(str(search_keywords[i + 1])) > 1 :
                    # Apply the corresponding operation based on the condition
                    if '&' == operations[i]:
                        filter_mask = filter_mask & df[filter_mask].apply(lambda row: fuzzy_match(search_keywords[i + 1], row), axis=1)
                    elif '|' == operations[i]:
                        filter_mask =  filter_mask | df.apply(lambda row: fuzzy_match(search_keywords[i + 1], row), axis=1)
                    elif '-' == operations[i]:
                        filter_mask = filter_mask & ~df[filter_mask].apply(lambda row: fuzzy_match(search_keywords[i + 1], row), axis=1)
                    else:
                        raise ValueError("Invalid condition. Please use '&' for AND, '|' for OR, or '-' for EXCEPT.")
        except Exception as e:
            pass



    # Apply the mask to get the filtered data
    filtered_rows = df[filter_mask].fillna('')

    return filtered_rows





