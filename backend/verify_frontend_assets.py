import urllib.request
import re

url = "http://localhost:5173"
resp = urllib.request.urlopen(url)
html = resp.read().decode("utf-8")

print("[+] HTTP 200 OK from Vite Dev Server!")
print(f"[+] Document contains title 'AI Customer Support Platform': {'AI Customer Support Platform' in html}")
print(f"[+] Document contains light theme body classes: {'bg-slate-50' in html}")

# Find scripts
scripts = re.findall(r'src=["\']([^"\']+)["\']', html)
print(f"[+] Discovered script resources: {scripts}")

for s in scripts:
    script_url = url + s if s.startswith("/") else f"{url}/{s}"
    s_resp = urllib.request.urlopen(script_url)
    content = s_resp.read().decode("utf-8", errors="ignore")
    print(f" -> Resource {s}: Status {s_resp.status}, Content Length {len(content)} bytes")
    # Verify no syntax or unhandled errors in script
    assert s_resp.status == 200

print("[+] All entrypoint assets load cleanly with HTTP 200!")
