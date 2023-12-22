from typing import Dict, Any, Optional

def get_key_from_value(input_dict: Dict[Any, Any], search_value: Any) -> Any:
    """Get the key from a dictionary based on the specified search value."""
    for i, (key, nested_list) in enumerate(input_dict.items()):
        for inner_list in nested_list:
            if search_value in inner_list:
                return key, i
    return None, None

def get_values_from_list_of_keys(input_dict, key_list):
    """Get the values from a list of keys in a dictionary."""
    return [input_dict.get(key,"") for key in key_list]

def get_last_non_none_key_and_value(input_dict: Dict[Any, Optional[Any]]) -> Optional[Any]:
    """Get the last non-None value from a dictionary."""
    for key, value in reversed(input_dict.items()):
        if value is not None:
            return key, value

    return None, None



def create_nested_dict(rows):
    nested_dict = {}
    old_key = rows[0]['Material Type'] if rows[0]['Course Type'] != "Exams" else rows[0]['Exams Type']
    old_year = rows[0]['Year']
    i = 1
    for row in rows:
        course_name = row['Course Name']
        year = row['Year']
        course_type = row['Course Type']
        material_type = row['Material Type'] if row['Course Type'] != "Exams" else row['Exams Type']
        if old_key == material_type and old_year == year:
            i +=1
        else:
            old_key = material_type
            old_year = year
            i = 1
        lec_none = "Lec" if course_type == 'Lectures' else "Sec" if course_type == 'Sections' else "Exam"  if course_type == 'Exams' else ""
        if row['Material Type'] == "Book": lec_none = "Book"
        lecture = f"{lec_none}{i}" if row['Lecture'] in  [None,"","nan"] else row["Lecture"]
        link = row["File Link"]


        # Create or update the nested dictionary structure
        nested_dict.setdefault(course_name, {}).setdefault(year, {}).setdefault(course_type, {}).setdefault(material_type, []).append({lecture: link})

    return nested_dict