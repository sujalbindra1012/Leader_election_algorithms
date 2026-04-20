from flask import Flask, request, jsonify, render_template
import time

app = Flask(__name__)

nodes = {}
leader = None
counter = 1
TIMEOUT = 10


# 🔹 Register node (AUTO ID)
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


# 🔹 Heartbeat
@app.route('/heartbeat', methods=['POST'])
def heartbeat():
    data = request.json
    node_id = str(data['id'])

    if node_id in nodes:
        nodes[node_id]['last_seen'] = time.time()

    return {"status": "alive"}


# 🔹 Get ACTIVE + ALIVE nodes (for bully)
@app.route('/nodes', methods=['GET'])
def get_nodes():
    alive = {}

    for k, v in nodes.items():
        # ✅ FIX: active filter remove nahi, but correct logic
        if time.time() - v['last_seen'] < TIMEOUT:
            if v.get("active"):
                alive[k] = v

    return jsonify(alive)


# 🔹 Get ALL nodes (UI ke liye)
@app.route('/all_nodes', methods=['GET'])
def all_nodes():
    return jsonify(nodes)


# 🔹 Suspend node
@app.route('/suspend/<node_id>', methods=['POST'])
def suspend(node_id):
    if node_id in nodes:
        nodes[node_id]['active'] = False
        print(f"Node {node_id} suspended")
        return {"status": f"{node_id} suspended"}
    return {"error": "node not found"}


# 🔹 Resume node
@app.route('/resume/<node_id>', methods=['POST'])
def resume(node_id):
    if node_id in nodes:
        nodes[node_id]['active'] = True
        nodes[node_id]['last_seen'] = time.time()
        print(f"Node {node_id} resumed")
        return {"status": f"{node_id} resumed"}
    return {"error": "node not found"}


# 🔹 Set leader
@app.route('/leader', methods=['POST'])
def set_leader():
    global leader
    leader = str(request.json['id'])
    print(f"Leader updated: {leader}")
    return {"leader": leader}


# 🔹 Get leader
@app.route('/leader', methods=['GET'])
def get_leader():
    return {"leader": leader}


# 🔹 Dashboard UI
@app.route('/')
def dashboard():
    return render_template("index.html")


# 🔹 Run server
app.run(host="0.0.0.0", port=5000)