# RedisGraphTest

## Setting Up
1) First run a docker container with redis graph, ideally running on port 638 as the script assumes.
```
docker run -p 6378:6379 -it --rm redislabs/redisgraph
```
2) Then clone this git repository and run ```pip install -e redisgraph-py```within the directory. 
3) You can connect to the redisgraph with ```redis-cli -p 6378``` to run queries.
Example Query: return the most popular task or subtask in project comparing primarily on number of distinct users commenting and then number of likes on the most liked comment.
```GRAPH.QUERY big_tree "MATCH (p:Project)-[:contains*..2]->(t)-[:contains]->(c:Comment)<-[:created_by]-(u:User) WHERE p.name='Project1' RETURN t, MAX(c.likes) ORDER BY COUNT(DISTINCT(u)) DESC, MAX(c.likes) DESC LIMIT 1"```
- ```(p:Project)-[:contains*..2]->(t)```: Some node two or less contains edges from a project
- ```(t)-[:contains]->(c:Comment)```: comment contained in that node (in our example on subtasks and tasks match this pattern)
- ```(c:Comment)<-[:created_by]-(u:User)```: User node that created that comment

## Using Your Own Schema
populate_redis_graph.py creates and stores dummy data in the redisgraph cache according to the schema defined in ```tree_structure``` and ```branching_factors```. Let's say you'd like to record views of subtasks by users. The default schema currently used is:
```
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
                    'Completed': [True, False],
                    'Comment:contains': {
                        'created_by:': users,
                        'likes': range(20),
                        'Created_At': range(CREATED_START, CREATED_END),
                    }
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
                'Completed': [True, False],
                'Comment:contains': {
                    'created_by:': users,
                    'likes': range(20),
                    'Created_At': range(CREATED_START, CREATED_END),
                }
            },
            'created_by:': users,
            'Created_At': range(CREATED_START, CREATED_END),
        },
        'created_by:': users,
        'Created_At': range(CREATED_START, CREATED_END),
    }
}
branching_factors = {
    'Portfolio:contains': [3], 
    'Project:contains': [4], 
    'Task:contains': [100], 
    'Subtask:contains': [5], 
    'Comment:contains': range(20)
}
```
First, We'd add a new child subtree in the Subtask subtrees. The syntax is 'Node_Names:Edge_Name'. In the above example
```
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
    'Completed': [True, False],
    'Comment:contains': {
        'created_by:': users,
        'likes': range(20),
        'Created_At': range(CREATED_START, CREATED_END),
    },
    'View:contains': {}
}
```
For each Subtask node we will create View children nodes with a contains relationship, i.e. ```(:Subtask) -[:contains]->(:View)```.
Specify the branching factor. For every child node type, we have to specify a list detailing how many children we might create
```
branching_factors = {
    'Portfolio:contains': [3], 
    'Project:contains': [4], 
    'Task:contains': [100], 
    'Subtask:contains': [5], 
    'Comment:contains': range(20),
    'View:contains': range(100)
}
```
So, each Subtask will have up to 100 views
There are three kinds of properties we can include: outgoing edges, incoming edges, and node properties. For outgoing edges the syntax is ```(:edge_type)``` and incoming we do ```(edge_type:)``` and for the value we provide a list of predefined nodes. For properties, we just don't add a ':' and the value is a list of options for that property.
```
'View:contains': {
    'viewed:': users,
    'created_at': range(int(time.time()) - 30*24*60*60, int(time.time()))
}
```
For adding predefined edges you can follow the example here: ```users = [Node(label='User', properties={'name': user}) for user in named_range('User', NUM_USERS)]```.
