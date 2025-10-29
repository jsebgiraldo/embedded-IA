import subprocess

def idf_doctor():
    """Run idf.py doctor to diagnose ESP-IDF environment"""
    p = subprocess.run(["bash", "-lc", "idf.py doctor"], cwd="/workspace", capture_output=True, text=True)
    return (p.stdout or "") + (p.stderr or "")
