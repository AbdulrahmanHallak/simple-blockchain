import hashlib
import json
import requests
from time import time
from typing import List, Set
from dataclasses import dataclass, asdict


@dataclass
class Transaction:
    sender: str
    recipient: str
    amount: int


@dataclass
class Block:
    index: int
    transactions: List[Transaction]
    prev_hash: str
    proof: int = 0
    _hash: str = ""
    _timestamp: float = time()


def mine_block(index: int, transactions: List[Transaction], prev_hash: str) -> Block:
    block = Block(index, transactions, prev_hash)

    while True:
        block_str = json.dumps(asdict(block), sort_keys=True)
        hash_guess = hashlib.sha256(block_str.encode()).hexdigest()
        if hash_guess[:4] == "0000":
            break
        else:
            block.proof += 1

    block._hash = hash_guess

    return block


def resolve_conflicting_nodes(
    self_chain: List[Block], neighboring_nodes: Set[str]
) -> List[Block] | None:
    new_chain = None
    max_length = len(self_chain)

    for node in neighboring_nodes:
        response = requests.get(f"http://{node}/chain")
        if response.status_code != 200:
            raise RuntimeError

        length = int(response.json()["length"])
        json_chain = response.json()["chain"]
        chain = [Block(**block) for block in json_chain]

        valid = _valid_chain(chain)
        if length > max_length and valid:
            max_length = length
            new_chain = chain

    if new_chain:
        return new_chain
    else:
        return None


def _valid_chain(chain: List[Block]) -> bool:
    prev_block = chain[0]
    index = 1

    while index < len(chain):
        block = chain[index]
        if block.prev_hash != prev_block._hash:
            return False

        if not _valid_block(chain[index]):
            return False

        prev_block = block
        index += 1

    return True


def _valid_block(block: Block):
    # Set the block hash to default since it is not part of the hash.
    hashless_block = Block(
        block.index,
        block.transactions,
        block.prev_hash,
        block.proof,
        "",
        block._timestamp,
    )
    block_str = json.dumps(asdict(hashless_block), sort_keys=True)
    hash_guess = hashlib.sha256(block_str.encode()).hexdigest()
    return hash_guess[:4] == "0000"
