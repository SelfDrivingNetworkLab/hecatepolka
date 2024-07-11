
def read_json_file(filename):
    path_to_file = os.getcwd()# + '/gym_deeproute_stat/envs/'
    NetworkDict={}
    with open(filename, "r") as stream:
        NetworkDict = json.load(stream)
        nodes = NetworkDict['data']['mapTopology']['nodes']
        edges = NetworkDict['data']['mapTopology']['edges']
        print(NetworkDict)
    return(nodes, edges)