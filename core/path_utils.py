import re
import datetime
from pathlib import Path

def sanitize_remote_path(path_str: str, strip_user: bool = True) -> str:
    """
    Sanitize remote path for FTP navigation:
    - Strips leading/trailing whitespace
    - If strip_user=True, strips Windows drive + /Users/<username> (e.g. C:/Users/user -> /)
    - Strips Windows drive letter (e.g. C:, D:)
    - Replaces backslashes with forward slashes
    - Collapses multiple slashes into single slash
    - Ensures leading slash and strips trailing slash (unless root /)
    """
    if not path_str or not path_str.strip():
        return "/"
    
    cleaned = path_str.strip()
    if strip_user:
        # Matches C:/Users/<user> or C:\Users\<user>
        cleaned = re.sub(r'^[a-zA-Z]:[/\\]Users[/\\][^/\\]+', '', cleaned, flags=re.IGNORECASE)
        # Also matches /Users/<user> or \Users\<user> without drive letter
        cleaned = re.sub(r'^[/\\]Users[/\\][^/\\]+', '', cleaned, flags=re.IGNORECASE)

    # Strip Windows drive letter like C: or c:
    cleaned = re.sub(r'^[a-zA-Z]:', '', cleaned)
    # Convert backslashes to forward slashes
    cleaned = cleaned.replace('\\', '/')
    # Collapse multiple consecutive slashes
    cleaned = re.sub(r'/+', '/', cleaned)
    # Strip trailing slash if longer than 1 character
    if len(cleaned) > 1 and cleaned.endswith('/'):
        cleaned = cleaned[:-1]
    # Ensure leading slash
    if not cleaned.startswith('/'):
        cleaned = '/' + cleaned
        
    return cleaned

def format_local_save_dir(base_dir: str, plc_name: str, sub_dir: str = "", separate_by_date: bool = True) -> Path:
    """
    Format local save directory and create parent folders if they don't exist.
    """
    target = Path(base_dir) / plc_name
    if sub_dir:
        target = target / sub_dir
    if separate_by_date:
        date_str = datetime.datetime.now().strftime("%d-%m-%Y")
        target = target / date_str
        
    target.mkdir(parents=True, exist_ok=True)
    return target
