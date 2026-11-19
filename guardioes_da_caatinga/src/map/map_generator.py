from collections import deque
from src.state import NodeType
from config import ELITE_SPAWN_CHANCE, ELITE_MIN_FLOOR, LEGENDARY_MIN_FLOOR
import random


class MapNode:
    def __init__(self, node_id, floor, position, node_type, legendary_id=None):
        self.node_id = node_id
        self.floor = floor
        self.position = position
        self.node_type = node_type
        self.legendary_id = legendary_id
        self.connections = []
        self.parents = []
        self.visited = False
        self.available = False
        self.blocked = False

    def to_dict(self):
        return {
            "node_id": self.node_id,
            "floor": self.floor,
            "position": self.position,
            "node_type": self.node_type.value,
            "legendary_id": self.legendary_id,
            "connections": self.connections,
            "parents": self.parents,
            "visited": self.visited,
            "available": self.available,
            "blocked": self.blocked,
        }

    @classmethod
    def from_dict(cls, data):
        node = cls(data["node_id"], data["floor"], data["position"],
                    NodeType(data["node_type"]),
                    data.get("legendary_id"))
        node.connections = data["connections"]
        node.parents = data.get("parents", [])
        node.visited = data["visited"]
        node.available = data["available"]
        node.blocked = data.get("blocked", False)
        return node


# 10-floor funnel: 1→2→3→4→4→4→4→3→2→1 = 28 nodes
_FIXED_MAP_TEMPLATE = {
    "layers": [
        [{"type": NodeType.COMBAT}],
        [{"type": NodeType.COMBAT}, {"type": NodeType.COMBAT}],
        [{"type": NodeType.EVENT}, {"type": NodeType.SHOP}, {"type": NodeType.COMBAT}],
        [{"type": NodeType.SHOP}, {"type": NodeType.EVENT}, {"type": NodeType.COMBAT}, {"type": NodeType.EVENT}],
        [{"type": NodeType.COMBAT}, {"type": NodeType.EVENT}, {"type": NodeType.SHOP}, {"type": NodeType.COMBAT}],
        [{"type": NodeType.EVENT}, {"type": NodeType.COMBAT}, {"type": NodeType.EVENT}, {"type": NodeType.SHOP}],
        [{"type": NodeType.COMBAT}, {"type": NodeType.EVENT}, {"type": NodeType.SHOP}, {"type": NodeType.COMBAT}],
        [{"type": NodeType.EVENT}, {"type": NodeType.SHOP}, {"type": NodeType.COMBAT}],
        [{"type": NodeType.ELITE}, {"type": NodeType.EVENT}],
        [{"type": NodeType.BOSS}],
    ],
    "connections": [
        [1, 2],       # 0→floor2
        [3, 4],       # 1→floor3
        [4, 5],       # 2→floor3
        [6, 7],       # 3→floor4
        [7, 8],       # 4→floor4
        [8, 9],       # 5→floor4
        [10, 11],     # 6→floor5
        [11, 12],     # 7→floor5
        [12, 13],     # 8→floor5
        [12, 13],     # 9→floor5
        [14, 15],     # 10→floor6
        [15, 16],     # 11→floor6
        [16, 17],     # 12→floor6
        [16, 17],     # 13→floor6
        [18, 19],     # 14→floor7
        [19, 20],     # 15→floor7
        [20, 21],     # 16→floor7
        [20, 21],     # 17→floor7
        [22, 23],     # 18→floor8
        [23, 24],     # 19→floor8
        [23, 24],     # 20→floor8
        [23, 24],     # 21→floor8
        [25, 26],     # 22→floor9
        [25, 26],     # 23→floor9
        [25, 26],     # 24→floor9
        [27],         # 25→floor10
        [27],         # 26→floor10
        [],           # 27 boss
    ],
}


class MapGenerator:
    def __init__(self, biome_id):
        self.biome_id = biome_id
        self.nodes = {}
        self.current_node_id = None

    def generate(self, locked_legendaries=None):
        self.nodes = {}
        self.current_node_id = None
        template = _FIXED_MAP_TEMPLATE
        node_id = 0

        for layer_idx, layer_nodes in enumerate(template["layers"]):
            for pos, node_def in enumerate(layer_nodes):
                node = MapNode(node_id, layer_idx, pos, node_def["type"])
                self.nodes[node_id] = node
                node_id += 1

        for nid, conn_targets in enumerate(template["connections"]):
            if nid not in self.nodes:
                continue
            for target_id in conn_targets:
                if target_id in self.nodes:
                    self.nodes[nid].connections.append(target_id)
                    self.nodes[target_id].parents.append(nid)

        self._recompute_available()
        self._insert_elite_nodes()
        self._insert_rescue_nodes()
        self._insert_legendary_nodes(locked_legendaries or [])
        return self.nodes

    def _recompute_available(self):
        for node in self.nodes.values():
            if node.visited:
                node.available = False
                node.blocked = False
                continue

        if self.current_node_id is None:
            for node in self.nodes.values():
                if not node.visited and not node.parents:
                    node.available = True
                    node.blocked = False
                elif not node.visited and node.parents:
                    node.available = False
                    node.blocked = True
            return

        current = self.nodes[self.current_node_id]
        reachable = self._get_reachable_from(current.node_id)

        for node in self.nodes.values():
            if node.visited or node.node_id == self.current_node_id:
                node.available = False
                node.blocked = False
                continue
            if node.node_id in current.connections:
                node.available = True
                node.blocked = False
            elif node.node_id in reachable:
                node.available = False
                node.blocked = False
            else:
                node.available = False
                node.blocked = True

    def _insert_elite_nodes(self):
        eligible = [n for n in self.nodes.values()
                    if n.node_type == NodeType.COMBAT
                    and n.floor >= ELITE_MIN_FLOOR]
        max_conversions = max(1, len(eligible) * 3 // 5)
        to_replace = [n for n in eligible if random.random() < ELITE_SPAWN_CHANCE]
        to_replace = random.sample(to_replace, min(len(to_replace), max_conversions))
        for node in to_replace:
            node.node_type = NodeType.ELITE

    def _insert_rescue_nodes(self):
        eligible = [n for n in self.nodes.values()
                    if n.node_type in (NodeType.COMBAT, NodeType.EVENT)
                    and n.node_type not in (NodeType.BOSS, NodeType.ELITE)]
        count = max(1, int(len(eligible) * random.uniform(0.05, 0.10)))
        count = min(count, len(eligible))
        to_replace = random.sample(eligible, count)
        for node in to_replace:
            node.node_type = NodeType.RESCUE_ANIMAL

    def _insert_legendary_nodes(self, locked_legendaries):
        """Place at most one legendary node on the map.

        A legendary node always belongs to a still-locked legendary animal.
        The current biome is preferred, but any locked legendary can appear so
        the player is never blocked by the biome order.
        """
        locked = [aid for aid in locked_legendaries if aid]
        if not locked:
            return

        from config import load_animals
        animals = load_animals()
        preferred = [
            aid for aid in locked
            if animals.get(aid, {}).get("legendary_biome") == self.biome_id
        ]
        chosen = random.choice(preferred or locked)

        eligible = [n for n in self.nodes.values()
                    if n.node_type in (NodeType.COMBAT, NodeType.EVENT)
                    and n.floor >= LEGENDARY_MIN_FLOOR]
        if not eligible:
            eligible = [n for n in self.nodes.values()
                        if n.node_type not in (
                            NodeType.BOSS, NodeType.ELITE,
                            NodeType.RESCUE_ANIMAL, NodeType.LEGENDARY)
                        and n.floor >= max(2, LEGENDARY_MIN_FLOOR - 2)]
        if not eligible:
            return

        node = random.choice(eligible)
        node.node_type = NodeType.LEGENDARY
        node.legendary_id = chosen

    def _get_reachable_from(self, start_id):
        reachable = set()
        queue = deque([start_id])
        visited = set()
        while queue:
            nid = queue.popleft()
            if nid in visited:
                continue
            visited.add(nid)
            node = self.nodes.get(nid)
            if not node:
                continue
            for child_id in node.connections:
                if child_id not in reachable:
                    reachable.add(child_id)
                    queue.append(child_id)
        return reachable

    def visit_node(self, node_id):
        if node_id not in self.nodes:
            return None
        node = self.nodes[node_id]
        if not node.available:
            return None

        node.visited = True
        node.available = False
        self.current_node_id = node_id

        self._recompute_available()
        return node

    def get_available_nodes(self):
        return [n for n in self.nodes.values() if n.available]

    def is_map_complete(self):
        boss_nodes = [n for n in self.nodes.values()
                      if n.node_type == NodeType.BOSS]
        return any(n.visited for n in boss_nodes)

    def to_dict(self):
        return {
            "biome_id": self.biome_id,
            "current_node_id": self.current_node_id,
            "nodes": {str(k): v.to_dict() for k, v in self.nodes.items()},
        }

    @classmethod
    def from_dict(cls, data):
        gen = cls(data["biome_id"])
        gen.current_node_id = data.get("current_node_id")
        gen.nodes = {int(k): MapNode.from_dict(v)
                     for k, v in data["nodes"].items()}
        return gen
