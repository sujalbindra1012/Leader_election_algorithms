import requests
import time
import threading

# 👉 PUT YOUR NGROK URL HERE (NO SPACE)
REGISTRY = "https://buddy-napkin-gentleman.ngrok-free.dev"

node_id = None


# -----------------------------
# Register
# -----------------------------
def register():
    global node_id
    try:
        res = requests.post(f"{REGISTRY}/register")
        node_id = str(res.json()["id"])
        print(f"Assigned ID: {node_id}")
    except Exception as e:
        print("Register failed:", e)


# -----------------------------
# Heartbeat (with print)
# -----------------------------
def heartbeat():
    while True:
        try:
            if node_id:
                res = requests.post(
                    f"{REGISTRY}/heartbeat",
                    json={"id": node_id},
                    timeout=3
                )

                if res.status_code == 200:
                    print(f"{node_id} → 💓 Heartbeat sent")

        except Exception as e:
            print(f"{node_id} → ⚠️ Connection lost, retrying...")

        time.sleep(2)


# -----------------------------
# Get ring
# -----------------------------
def get_ring():
    try:
        ring = requests.get(f"{REGISTRY}/node_ids").json()
        return ring
    except:
        return []


# -----------------------------
# Get next node (using fixed ring)
# -----------------------------
def get_next_node(ring):
    my_id = int(node_id)

    if my_id not in ring:
        return None

    idx = ring.index(my_id)
    return str(ring[(idx + 1) % len(ring)])


# -----------------------------
# Send message
# -----------------------------
def send_message(msg):
    try:
        requests.post(f"{REGISTRY}/message", json=msg)
    except:
        pass


# -----------------------------
# Wait for stable ring
# -----------------------------
def wait_for_ring():
    print(f"{node_id} → Waiting for ring...")

    prev = []
    stable = 0

    while True:
        current = get_ring()
        print(f"{node_id} sees ring:", current)

        if current == prev and len(current) > 1:
            stable += 1
        else:
            stable = 0

        if stable >= 3:
            print(f"{node_id} → Ring stabilized:", current)
            break

        prev = current
        time.sleep(2)


# -----------------------------
# Start election
# -----------------------------
def start_election():
    ring = get_ring()
    next_node = get_next_node(ring)

    if next_node:
        print(f"{node_id} → 🚀 Starting election with ring {ring}")

        send_message({
            "type": "ELECTION",
            "from": node_id,
            "to": next_node,
            "participants": [int(node_id)],
            "ring": ring
        })


# -----------------------------
# Listen messages
# -----------------------------
def listen():
    while True:
        try:
            msgs = requests.get(f"{REGISTRY}/inbox/{node_id}").json()

            for msg in msgs:

                # -------- ELECTION --------
                if msg["type"] == "ELECTION":
                    participants = msg["participants"]
                    ring = msg["ring"]

                    print(f"{node_id} → received ELECTION | ring={ring}")

                    if int(node_id) not in participants:
                        participants.append(int(node_id))

                    # If message returned to initiator
                    if msg["from"] == node_id:
                        leader_id = str(max(participants))
                        print(f"{node_id} → 👑 Leader elected: {leader_id}")

                        # update registry
                        requests.post(f"{REGISTRY}/leader", json={"id": leader_id})

                        # send coordinator
                        send_message({
                            "type": "COORDINATOR",
                            "leader": leader_id,
                            "to": get_next_node(ring),
                            "ring": ring
                        })

                    else:
                        send_message({
                            "type": "ELECTION",
                            "from": msg["from"],
                            "to": get_next_node(ring),
                            "participants": participants,
                            "ring": ring
                        })

                # -------- COORDINATOR --------
                elif msg["type"] == "COORDINATOR":
                    leader = msg["leader"]
                    ring = msg["ring"]

                    print(f"{node_id} → 👑 Leader is {leader}")

                    if leader != node_id:
                        send_message({
                            "type": "COORDINATOR",
                            "leader": leader,
                            "to": get_next_node(ring),
                            "ring": ring
                        })

        except:
            pass

        time.sleep(2)


# -----------------------------
# MAIN
# -----------------------------
if __name__ == "__main__":
    print("Node starting...")

    register()

    while node_id is None:
        time.sleep(1)

    print(f"Node started with ID: {node_id}")

    threading.Thread(target=heartbeat, daemon=True).start()
    threading.Thread(target=listen, daemon=True).start()

    # 🔥 IMPORTANT FIX
    wait_for_ring()

    start_election()

    while True:
        time.sleep(5)