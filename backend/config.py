from pathlib import Path
import os
ROOT=Path(__file__).resolve().parents[1]
# Local developer convenience; never overwrites deployment environment.
if (ROOT/'.env').is_file():
    for line in (ROOT/'.env').read_text(encoding='utf-8-sig').splitlines():
        if '=' in line and not line.lstrip().startswith('#'):
            k,v=line.split('=',1); os.environ.setdefault(k.strip(),v.strip().strip('"').strip("'"))
BASE_URL=os.getenv('DEEPSEEK_BASE_URL','https://api.deepseek.com').rstrip('/')
MODEL=os.getenv('DEEPSEEK_MODEL','deepseek-chat')
API_KEY=os.getenv('DEEPSEEK_API_KEY','')
MAX_TOKENS=int(os.getenv('DEEPSEEK_MAX_TOKENS','2400'))
TEMPERATURE=float(os.getenv('DEEPSEEK_TEMPERATURE','0.2'))
