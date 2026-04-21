import requests
import time
import threading
import random

# 👉 PUT YOUR NGROK URL HERE (NO SPACE)
REGISTRY = "https://buddy-napkin-gentleman.ngrok-free.dev"

node_id = None

# -----------------------------
# Raft State Variables
# -----------------------------
state = "FOLLOWER"
current_term = 0
voted_for = None
votes = 0

last_heartbeat = time.time()


# -----------------------------
# Register
# -----------------------------
def register():
    global node_id
    try:
        res = requests.post(f"{REGISTRY}/register")
        node_id = str(res.json()["id"])
        print(f"Node {node_id} registered")
    except Exception as e:
        print("Register failed:", e)


# -----------------------------
# Update state (for UI)
# -----------------------------
def update_state():
    try:
        requests.post(f"{REGISTRY}/state", json={
            "id": node_id,
            "state": state
        })
    except:
        pass


# -----------------------------
# Heartbeat (to registry)
# -----------------------------
def heartbeat():
    while True:
        try:
            if node_id:
                requests.post(f"{REGISTRY}/heartbeat", json={"id": node_id})
                print(f"{node_id} → 💓 Heartbeat")
        except:
            print(f"{node_id} → ⚠️ Connection issue")
        time.sleep(2)


# -----------------------------
# Get active nodes
# -----------------------------
def get_nodes():
    try:
        return requests.get(f"{REGISTRY}/nodes").json()
    except:
        return []


# -----------------------------
# Send message
# -----------------------------
def send(msg):
    try:
        requests.post(f"{REGISTRY}/message", json=msg)
    except:
        pass


# -----------------------------
# Election Timer
# -----------------------------
def election_timer():
    global state

    while True:
        timeout = random.randint(5, 10)

        if time.time() - last_heartbeat > timeout:
            if state != "LEADER":
                print(f"{node_id} → ⏳ Timeout → Starting Election")
                start_election()

        time.sleep(1)


# -----------------------------
# Start Election
# -----------------------------
def start_election():
    global state, current_term, voted_for, votes

    state = "CANDIDATE"
    current_term += 1
    voted_for = node_id
    votes = 1

    update_state()

    nodes = get_nodes()

    print(f"{node_id} → 🗳️ CANDIDATE (term {current_term})")

    for n in nodes:
        if str(n) != node_id:
            send({
                "type": "REQUEST_VOTE",
                "term": current_term,
                "candidate": node_id,
                "to": str(n)
            })


# -----------------------------
# Leader Heartbeat (to followers)
# -----------------------------
def leader_heartbeat():
    global state

    while True:
        if state == "LEADER":
            nodes = get_nodes()

            for n in nodes:
                if str(n) != node_id:
                    send({
                        "type": "HEARTBEAT",
                        "leader": node_id,
                        "term": current_term,
                        "to": str(n)
                    })

        time.sleep(2)


# -----------------------------
# Listen for messages
# -----------------------------
def listen():
    global state, votes, voted_for, current_term, last_heartbeat

    while True:
        try:
            msgs = requests.get(f"{REGISTRY}/inbox/{node_id}").json()

            for msg in msgs:

                # -----------------------------
                # REQUEST VOTE
                # -----------------------------
                if msg["type"] == "REQUEST_VOTE":

                    term = msg["term"]
                    candidate = msg["candidate"]

                    if term > current_term:
                        current_term = term
                        voted_for = None
                        state = "FOLLOWER"

                    if voted_for is None:
                        voted_for = candidate
                        update_state()

                        print(f"{node_id} → ✅ Voted for {candidate}")

                        send({
                            "type": "VOTE",
                            "to": candidate,
                            "term": current_term
                        })


                # -----------------------------
                # VOTE RECEIVED
                # -----------------------------
                elif msg["type"] == "VOTE":

                    votes += 1
                    nodes = get_nodes()

                    if votes > len(nodes) // 2:
                        state = "LEADER"
                        update_state()

                        print(f"{node_id} → 👑 LEADER (term {current_term})")

                        # update registry leader
                        requests.post(f"{REGISTRY}/leader", json={"id": node_id})


                # -----------------------------
                # LEADER HEARTBEAT RECEIVED
                # -----------------------------
                elif msg["type"] == "HEARTBEAT":

                    leader = msg["leader"]
                    term = msg["term"]

                    if term >= current_term:
                        current_term = term
                        state = "FOLLOWER"
                        voted_for = None
                        last_heartbeat = time.time()
                        update_state()

                        print(f"{node_id} → 🟢 Following Leader {leader}")

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

    print(f"Node {node_id} started")

    update_state()

    threading.Thread(target=heartbeat, daemon=True).start()
    threading.Thread(target=listen, daemon=True).start()
    threading.Thread(target=election_timer, daemon=True).start()
    threading.Thread(target=leader_heartbeat, daemon=True).start()

    while True:
        time.sleep(5)