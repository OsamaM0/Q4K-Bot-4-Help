from typing import Dict, Any, Optional

def get_key_from_value(input_dict: Dict[Any, Any], search_value: Any) -> Any:
    """Get the key from a dictionary based on the specified search value."""
    for i, (key, nested_list) in enumerate(input_dict.items()):
        for inner_list in nested_list:
            if search_value in inner_list:
                return key, i
    return None, None

def get_last_non_none_key_and_value(input_dict: Dict[Any, Optional[Any]]) -> Optional[Any]:
    """Get the last non-None value from a dictionary."""
    for key, value in reversed(input_dict.items()):
        if value is not None:
            return key, value
            
    return None, None
