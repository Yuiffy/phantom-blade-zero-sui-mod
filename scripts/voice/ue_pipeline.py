"""Read-only process check retained from the local pipeline."""
import csv
import io
import re
import subprocess

def game_pids():
    result=subprocess.run(['tasklist.exe','/FO','CSV','/NH'],
                          check=True,capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW)
    rows=csv.reader(io.StringIO(result.stdout.decode('utf-8',errors='replace')))
    return [int(row[1]) for row in rows if len(row)>1
            and re.fullmatch(r'(?:Project)?PBZ(?:-Win64-(?:Shipping|Development))?\.exe',row[0],re.I)]
