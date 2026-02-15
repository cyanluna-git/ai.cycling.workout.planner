"""Simple power conversion utility."""
import copy
from typing import List, Dict, Any

def convert_power_to_watts(steps: List[Dict[str, Any]], ftp: int) -> List[Dict[str, Any]]:
    """Recursively convert power from %FTP to watts.
    
    Args:
        steps: List of workout steps (nested format)
        ftp: User's FTP in watts
        
    Returns:
        Steps with power converted to watts
    """
    steps_copy = copy.deepcopy(steps)
    
    for step in steps_copy:
        # Handle nested repeat blocks
        if 'repeat' in step and 'steps' in step:
            step['steps'] = convert_power_to_watts(step['steps'], ftp)
        
        # Convert power values
        if 'power' in step:
            power = step['power']
            units = power.get('units', '%ftp')
            
            if units == '%ftp':
                if 'value' in power:
                    power['value'] = int(power['value'] * ftp / 100)
                if 'start' in power:
                    power['start'] = int(power['start'] * ftp / 100)
                if 'end' in power:
                    power['end'] = int(power['end'] * ftp / 100)
                power['units'] = 'watts'
    
    return steps_copy
