"""End-to-end smoke test for the todolist demo: auth + ownership + admin gate."""
import json
import time
import urllib.error
import urllib.request

BASE = "http://localhost:8000/admin/api/v1"


def call(method, path, token=None, body=None):
    url = BASE + path
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status, json.loads(r.read() or "null")
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or "null")


def wait_health():
    for _ in range(20):
        try:
            with urllib.request.urlopen("http://localhost:8000/health", timeout=5) as r:
                if r.status == 200:
                    return True
        except Exception:
            pass
        time.sleep(3)
    return False


def tok(resp):
    return (resp.get("data") or {}).get("access_token")


assert wait_health(), "API never became healthy"
print("health: OK")

# 1. Register two users
s, alice = call("POST", "/auth/register", body={"email": "alice@demo.io", "password": "Secret123!"})
print("register alice:", s)
s, bob = call("POST", "/auth/register", body={"email": "bob@demo.io", "password": "Secret123!"})
print("register bob:", s)
alice_t, bob_t = tok(alice), tok(bob)
assert alice_t and bob_t, f"missing tokens: {alice} {bob}"

# 2. Alice creates two todos
s, t1 = call("POST", "/todo/", alice_t, {"title": "Buy milk", "description": "2 liters"})
print("alice create todo1:", s, "->", (t1.get("data") or {}))
s, t2 = call("POST", "/todo/", alice_t, {"title": "Write LinkedIn post"})
print("alice create todo2:", s)
todo1_id = (t1.get("data") or {}).get("id")

# 3. Alice lists her todos
s, lst = call("GET", "/todo/", alice_t)
items = (lst.get("data") or {}).get("items", lst.get("data"))
print("alice list todos:", s, "count=", len(items) if isinstance(items, list) else items)

# 4. Alice updates todo1 -> completed
s, _ = call("PUT", f"/todo/{todo1_id}", alice_t, {"completed": True})
print("alice complete todo1:", s)
s, got = call("GET", f"/todo/{todo1_id}", alice_t)
print("alice get todo1 completed=", (got.get("data") or {}).get("completed"))

# 5. Ownership: Bob cannot see Alice's todo
s, denied = call("GET", f"/todo/{todo1_id}", bob_t)
print("bob get alice todo (expect 403):", s)

# 6. Bob's own list is empty
s, blst = call("GET", "/todo/", bob_t)
bitems = (blst.get("data") or {}).get("items", blst.get("data"))
print("bob list todos count=", len(bitems) if isinstance(bitems, list) else bitems)

# 7. Admin gate: normal user denied on /todo/all
s, adm = call("GET", "/todo/all", alice_t)
print("alice GET /todo/all (expect 403):", s)

print("\nSUMMARY: auth + per-user CRUD + ownership + admin-gate all exercised.")
