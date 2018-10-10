from graph_tool.all import *
from tqdm.autonotebook import tqdm
import json
import numpy
from utils import clustering
from utils import mongodb_access


def get_d3_view(gt_file_path):
    g = load_graph(gt_file_path)
    nodes = []
    links = []
    bv, be = betweenness(g)
    print(bv)
    g_most = GraphView(g, vfilt=lambda v: bv[v] > numpy.percentile(bv.a, 99)).copy()
    g_most.purge_vertices()
    for vertex in tqdm(g_most.get_vertices()):
        node_id = vertex
        node_label = g_most.vertex_properties['label'][vertex]
        nodes.append(dict(id=node_id, label=node_label))
    for edge in tqdm(g_most.get_edges()):
        edge_weight = g_most.edge_properties['weight'][edge]
        links.append(dict(id=edge[2], weight=edge_weight, source=edge[0], target=edge[1]))
    return nodes, links


def get_d3_clustered(gt_file_path):
    number, grouped_ids = clustering.get_clusters('publications', 'zika', 'localhost', 27017, 2010, 1, 2018, 1)
    references = mongodb_access.get_top_references('publications', 'zika', 'localhost', 27017, 2010, 1, 2018, 1)
    references_by_id = dict()
    for reference in references:
        references_by_id[reference['id']] = reference
    g = load_graph(gt_file_path)
    nodes = []
    links = []
    group_prop = g.new_vertex_property("int")
    g.vertex_properties['group'] = group_prop
    for key, value in tqdm(grouped_ids.items()):
        for node_id in value:
            if len(find_vertex(g, g.vertex_properties['label'], node_id)) == 0:
                continue
            v = find_vertex(g, g.vertex_properties['label'], node_id)[0]
            g.vertex_properties['group'][v] = key + 1
    g_most = GraphView(g, vfilt=lambda v: g.vertex_properties['group'][v] is not 0 and g.vertex_properties['label'][v] in references_by_id.keys()).copy()
    g_most.purge_vertices()
    for vertex in tqdm(g_most.get_vertices()):
        node_id = vertex
        node_label = g_most.vertex_properties['label'][vertex]
        node_group = g_most.vertex_properties['group'][vertex]
        title = references_by_id[node_label]['title']
        nodes.append(dict(id=node_id, label=node_label, group=node_group, title=title))
    for edge in tqdm(g_most.get_edges()):
        edge_weight = g_most.edge_properties['weight'][edge]
        links.append(dict(id=edge[2], weight=edge_weight, source=edge[0], target=edge[1]))
    return nodes, links


def default(o):
    if isinstance(o, numpy.uint64) or isinstance(o, numpy.int64):
        return int(o)


# auth_nodes, auth_links = get_d3_view(
#      '/Users/federico/git/science-radar/data/sciradar/zika/gt/zika_2010-1 to 2017-12_authorship.gt')
# view = dict(nodes=auth_nodes, links=auth_links)
# with open('/Users/federico/git/science-radar/data/sciradar/zika/gt/zika_2010-1 to 2017-12_authorship.json', 'w') as fp:
#     json.dump(view, fp, indent=4, sort_keys=True, default=default)


auth_nodes, auth_links = get_d3_clustered(
     '/Users/federico/git/science-radar/data/sciradar/zika/gt/zika_2010-1 to 2017-12_co_citation.gt')
view = dict(nodes=auth_nodes, links=auth_links)
with open('/Users/federico/git/science-radar/data/sciradar/zika/gt/zika_2010-1 to 2017-12_co_citation.json', 'w') as fp:
    json.dump(view, fp, indent=4, sort_keys=True, default=default)
