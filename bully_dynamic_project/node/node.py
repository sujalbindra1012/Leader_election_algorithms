import requests
import time
import threading

# 👉 APNA NGROK URL (System A wala)
REGISTRY = " https://buddy-napkin-gentleman.ngrok-free.dev"

node_id = None


# 🔹 Register and get ID from registry
def register():
    global node_id
    try:
        res = requests.post(f"{REGISTRY}/register")
        node_id = str(res.json()["id"])
        print(f"Assigned ID: {node_id}")
    except Exception as e:
        print("Register failed:", e)


# 🔹 Heartbeat (only if active)
def heartbeat():
    while True:
        try:
            if node_id:
                requests.post(f"{REGISTRY}/heartbeat", json={"id": node_id})
        except:
            pass            
        time.sleep(2)


# 🔹 Get active nodes
def get_nodes():
    try:
        return requests.get(f"{REGISTRY}/nodes").json()
    except:
        return {}


# 🔹 Get ALL nodes (for status check)
def get_all_nodes():
    try:
        return requests.get(f"{REGISTRY}/all_nodes").json()
    except:
        return {}


# 🔹 Check if this node is active (UI control)
def is_active():
    nodes = get_all_nodes()
    if node_id in nodes:
        return nodes[node_id].get("active", False)
    return False


# 🔹 Get current leader
def get_leader():
    try:
        return requests.get(f"{REGISTRY}/leader").json().get("leader")
    except:
        return None


# 🔹 Set leader in registry
def set_leader():
    try:
        requests.post(f"{REGISTRY}/leader", json={"id": node_id})
    except:
        pass


# 🔹 Bully Algorithm (highest ID wins)
def bully():
    nodes = get_nodes()

    try:
        node_ids = [int(n) for n in nodes.keys()]
        my_id = int(node_id)

        higher = [n for n in node_ids if n > my_id]

        if not higher:
            print(f"{node_id} → 👑 I AM LEADER")
            set_leader()
        else:
            print(f"{node_id} → FOLLOWER (higher: {max(higher)})")

    except:
        print("Error in bully logic")


# 🔹 Monitor leader failure
def monitor():
    while True:
        if not is_active():
            print(f"{node_id} → ⛔ SUSPENDED")
            time.sleep(5)
            continue

        leader = get_leader()
        nodes = get_nodes()

        if leader is None or leader not in nodes:
            print(f"{node_id} → Leader dead → starting election")
            bully()

        time.sleep(5)


# 🔹 MAIN
if __name__ == "__main__":
    print("Node starting...")

    register()

    # wait until ID is assigned
    while node_id is None:
        time.sleep(1)

    print(f"Node started with ID: {node_id}")

    # start background threads
    threading.Thread(target=heartbeat, daemon=True).start()
    threading.Thread(target=monitor, daemon=True).start()

    while True:
        if is_active():
            bully()
        else:
            print(f"{node_id} → ⛔ SUSPENDED")

        time.sleep(5)