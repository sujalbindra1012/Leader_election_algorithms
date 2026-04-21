from flask import Flask, request, jsonify
import time

app = Flask(__name__)

nodes = {}
messages = {}
leader = None
counter = 1
TIMEOUT = 10

# -----------------------------
# HOME (Fix 404 issue)
# -----------------------------
from flask import render_template

@app.route('/')
def dashboard():
    return render_template("index.html")


# -----------------------------
# Register node
# -----------------------------
@app.route('/register', methods=['POST'])
def register():
    global counter
    node_id = str(counter)
    counter += 1

    nodes[node_id] = {
        "last_seen": time.time(),
        "active": True
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
# Get ACTIVE nodes (for ring)
# -----------------------------
@app.route('/node_ids', methods=['GET'])
def node_ids():
    alive = []
    for k, v in nodes.items():
        if time.time() - v['last_seen'] < TIMEOUT and v.get("active"):
            alive.append(int(k))
    return jsonify(sorted(alive))


# -----------------------------
# Get ACTIVE nodes (Bully style)
# -----------------------------
@app.route('/nodes', methods=['GET'])
def nodes_list():
    alive = {}
    for k, v in nodes.items():
        if time.time() - v['last_seen'] < TIMEOUT and v.get("active"):
            alive[k] = v
    return jsonify(alive)


# -----------------------------
# Messaging system
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
# Leader
# -----------------------------
@app.route('/leader', methods=['POST'])
def set_leader():
    global leader
    leader = str(request.json['id'])
    print(f"Leader updated: {leader}")
    return {"leader": leader}


@app.route('/leader', methods=['GET'])
def get_leader():
    return {"leader": leader}


# -----------------------------
# Suspend / Resume (optional)
# -----------------------------
@app.route('/suspend/<node_id>', methods=['POST'])
def suspend(node_id):
    if node_id in nodes:
        nodes[node_id]['active'] = False
        print(f"Node {node_id} suspended")
        return {"status": "suspended"}
    return {"error": "not found"}


@app.route('/resume/<node_id>', methods=['POST'])
def resume(node_id):
    if node_id in nodes:
        nodes[node_id]['active'] = True
        nodes[node_id]['last_seen'] = time.time()
        print(f"Node {node_id} resumed")
        return {"status": "resumed"}
    return {"error": "not found"}


# -----------------------------
# Run
# -----------------------------
app.run(host="0.0.0.0", port=5000)