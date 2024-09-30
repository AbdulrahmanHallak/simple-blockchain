from uuid import uuid4
from flask import Flask, jsonify, request
from blockchain import (
    Block,
    Transaction,
    mine_block,
    resolve_conflicting_nodes,
)
from urllib.parse import urlparse


app = Flask(__name__)

node_id = str(uuid4()).replace("-", "")
genesis = Block(0, [], "", 0)
blockchain = [
    genesis,
]
nodes = set()
transactions = []


@app.route("/mine", methods=["GET"])
def mine():
    # This is the reward.
    new_tran = Transaction("0", node_id, 1)
    global transactions
    block_transactions = transactions.copy()
    block_transactions.append(new_tran)

    global blockchain
    new_block = mine_block(len(blockchain), block_transactions, blockchain[-1]._hash)
    blockchain.append(new_block)

    # Clear transaction for the new block
    transactions = []

    response = {
        "message": "New Block Forged",
        "index": new_block.index,
        "transactions": new_block.transactions,
        "proof": new_block.proof,
        "previous_hash": new_block.prev_hash,
    }
    return jsonify(response), 200


@app.route("/transaction", methods=["POST"])
def new_transaction():
    values = request.get_json()
    required = ["sender", "recipient", "amount"]
    if not all(k in values for k in required):
        return "Missing fields", 400

    new_tran = Transaction(values["sender"], values["recipient"], values["amount"])
    global transactions
    transactions.append(new_tran)

    response = {"message": f"Transaction will be added to Block {len(blockchain)}"}
    return response, 201


@app.route("/chain", methods=["GET"])
def full_chain():
    response = {"chain": blockchain, "length": len(blockchain)}
    return jsonify(response), 200


@app.route("/node", methods=["POST"])
def register_node():
    values = request.get_json()
    new_nodes = values.get("nodes")
    if new_nodes is None:
        return "Error. supply a valid list of nodes", 400

    for node in new_nodes:
        url = urlparse(node)
        global nodes
        nodes.add(url.netloc)

    return "registered successfully", 200


@app.route("/node/resolve", methods=["GET"])
def resolve():
    global blockchain, nodes
    new_chain = resolve_conflicting_nodes(blockchain, nodes)

    if new_chain:
        blockchain = new_chain
        response = {"message": "Our chain was replaced", "chain": blockchain}
    else:
        response = {"message": "Our chain rules supreme", "chain": blockchain}

    return jsonify(response, 200)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
