import urllib.request
import json
import os
from datetime import datetime, timezone
import update_commits

print("Today STR UTC:", datetime.now(timezone.utc).strftime('%Y-%m-%d'))
print("Today STR Local:", datetime.now().strftime('%Y-%m-%d'))

update_commits.get_stats('suchirreddy')
