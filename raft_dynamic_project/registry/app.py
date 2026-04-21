from flask import Flask, request, jsonify, render_template
import time

app = Flask(__name__)

# -----------------------------
# Global Data
# -----------------------------
nodes = {}
messages = {}
states = {}
leader = None
counter = 1
TIMEOUT = 10


# -----------------------------
# Home (UI)
# -----------------------------
@app.route('/')
def dashboard():
    return render_template("index.html")


# -----------------------------
# Register Node
# -----------------------------
@app.route('/register', methods=['POST'])
def register():
    global counter

    node_id = str(counter)
    counter += 1

    nodes[node_id] = {
        "last_seen": time.time()
    }

    print(f"Node {node_id} registered")
    return {"id": node_id}


# -----------------------------
# Heartbeat
# -----------------------------
@app.route('/heartbeat', methods=['POST'])
def heartbeat():
    data = request.json
    node_id = str(data['id'])

    if node_id in nodes:
        nodes[node_id]['last_seen'] = time.time()

    return {"status": "alive"}


# -----------------------------
# Get ACTIVE Nodes
# -----------------------------
@app.route('/nodes', methods=['GET'])
def get_nodes():
    alive = []

    # Remove dead nodes
    to_remove = []

    for k, v in nodes.items():
        if time.time() - v['last_seen'] < TIMEOUT:
            alive.append(int(k))
        else:
            to_remove.append(k)

    # cleanup dead nodes
    for k in to_remove:
        print(f"Removing dead node {k}")
        nodes.pop(k, None)
        states.pop(k, None)

    return jsonify(sorted(alive))


# -----------------------------
# Messaging System
# -----------------------------
@app.route('/message', methods=['POST'])
def message():
    data = request.json
    to = data["to"]

    if to not in messages:
        messages[to] = []

    messages[to].append(data)
    return {"status": "sent"}


@app.route('/inbox/<node_id>', methods=['GET'])
def inbox(node_id):
    msgs = messages.get(node_id, [])
    messages[node_id] = []
    return jsonify(msgs)


# -----------------------------
# Leader Management
# -----------------------------
@app.route('/leader', methods=['POST'])
def set_leader():
    global leader
    leader = str(request.json["id"])
    print(f"Leader updated: {leader}")
    return {"leader": leader}


@app.route('/leader', methods=['GET'])
def get_leader():
    return {"leader": leader}


# -----------------------------
# State Management (Raft)
# -----------------------------
@app.route('/state', methods=['POST'])
def update_state():
    data = request.json
    node_id = str(data["id"])
    states[node_id] = data["state"]
    return {"status": "ok"}


@app.route('/state', methods=['GET'])
def get_states():
    return jsonify(states)


# -----------------------------
# Run Server
# -----------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)