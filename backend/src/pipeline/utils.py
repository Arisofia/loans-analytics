import traceback
from datetime import datetime
from typing import Any, Dict

def format_error_response(error: Exception) -> Dict[str, Any]:
    return {'status': 'failed', 'error': str(error), 'traceback': traceback.format_exc(), 'timestamp': datetime.now().isoformat()}
