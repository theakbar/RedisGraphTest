import redis
from redisgraph import Node, Edge, Graph, Path
import random
import time
from collections import defaultdict

# Number of custom fields created
NUM_FIELDS = 100
# Number of users created
NUM_USERS = 10

CREATED_START = int(time.time()) - 30*24*60*60
CREATED_END = int(time.time()) - 15*24*60*60

DUE_START = int(time.time()) - 15*24*60*60
DUE_END = int(time.time()) + 15*24*60*60

redis_client = redis.Redis(host='localhost', port=6378)
redis_graph = Graph('big_tree', redis_client)

edges = []
nodes = []
batch_size = 1000

def add_nodes():
    global redis_graph
    for i, node in enumerate(nodes):
        redis_graph.add_node(node)

def add_edges():
    global redis_graph
    for i, edge in enumerate(edges):
        redis_graph.add_edge(edge)

num_strings = defaultdict(lambda: -1)
def get_id(id):
    global num_strings
    num_strings[id] += 1
    return str(num_strings[id])

def named_range(name, length):
    return map(lambda x: name + get_id(name), range(length))

def build_tree(tree_structure, branching_factors, layer=0, base_key=None):
    global nodes
    global edges
    label = base_key.split(":")[0] if base_key else None
    current_node = Node(label=label, properties={'name': label + get_id(label)}) if base_key else None
    edges = []
    for key in tree_structure:
        if type(tree_structure[key]) == dict:
            for i in range(branching_factors[layer]):
                next_node = build_tree(tree_structure[key], branching_factors, layer=layer+1, base_key=key)
                # create edge with current node
                if current_node:
                    node_type, relationship = key.split(":")
                    edges.append(Edge(current_node, relationship, next_node))

        splitted = key.split(":")
        if len(splitted) == 1:
            current_node.properties[key] = random.choice(tree_structure[key])
        elif len(splitted) == 2 and not splitted[0]:
            #left side empty
            next_nodes = tree_structure[key]
            relationship = splitted[1]
            edges.append(Edge(current_node, relationship, random.choice(next_nodes)))
        elif len(splitted) == 2 and not splitted[1]:
            #right side empty
            next_nodes = tree_structure[key]
            relationship = splitted[0]
            edges.append(Edge(random.choice(next_nodes), relationship, current_node))
    if current_node:
        nodes += [current_node]
        edges += edges
    return current_node

if __name__ == '__main__':
    print("started")
    fields = [Node(label='Field', properties={'name': field}) for field in named_range('Field', NUM_FIELDS)]
    users = [Node(label='User', properties={'name': user}) for user in named_range('User', NUM_USERS)]

    nodes += users + fields

    tree_structure = {
        'Portfolio:contains': {
            'Project:contains':{
                'Task:contains':{
                    'Subtask:contains':{
                        ':contains': fields,
                        ':contains': fields,
                        ':contains': fields,
                        ':contains': fields,
                        ':contains': fields,
                        'Created_At': range(CREATED_START, CREATED_END),
                        'Due_Date': range(DUE_START, DUE_END),
                        'created_by:': users,
                        ':assigned_to': users,
                        "Completed": [True, False],
                    },
                    ':contains': fields,
                    ':contains': fields,
                    ':contains': fields,
                    ':contains': fields,
                    ':contains': fields,
                    'created_by:': users,
                    ':assigned_to': users,
                    'Created_At': range(CREATED_START, CREATED_END),
                    'Due_Date': range(DUE_START, DUE_END),
                    "Completed": [True, False],
                },
                'created_by:': users,
                'Created_At': range(CREATED_START, CREATED_END),
            },
            'created_by:': users,
            'Created_At': range(CREATED_START, CREATED_END),
        }
    }
    branching_factors = [10, 50, 200, 10]
    build_tree(tree_structure, branching_factors)
    print("built tree")

    add_nodes()
    add_edges()
    redis_graph.commit()
