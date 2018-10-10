from graph_tool.all import *
import json
import click


def analyse_graph(graph: Graph, previous: Graph = None):
    analysys = dict()
    click.secho('       Getting degree histogram', fg='yellow')
    analysys['degree_histogram'] = [array.tolist() for array in vertex_hist(graph, 'total')]
    click.secho('       Getting degree average', fg='yellow')
    analysys['degree_average'] = vertex_average(graph, 'total')
    click.secho('       Getting edge count', fg='yellow')
    analysys['edge_count'] = graph.num_edges()
    click.secho('       Getting weight average', fg='yellow')
    analysys['edge_weight_average'] = edge_average(graph, graph.edge_properties['weight'])
    click.secho('       Getting edge weight histogram', fg='yellow')
    analysys['edge_weight_histogram'] = [array.tolist() for array in edge_hist(graph, graph.edge_properties['weight'])]
    click.secho('       Getting vertex count', fg='yellow')
    analysys['vertex_count'] = graph.num_vertices()
    click.secho('       Getting density', fg='yellow')
    analysys['density'] = analysys['edge_count'] / ((analysys['vertex_count'] * (analysys['vertex_count'] - 1)) / 2)
    click.secho('       Getting clustering coefficient', fg='yellow')
    analysys['clustering_coefficient'] = global_clustering(graph)
    click.secho('       Getting similarity year before', fg='yellow')
    if previous is not None:
        analysys['similarity_year_before'] = similarity(graph,
                                                        previous,
                                                        eweight1=graph.edge_properties['weight'],
                                                        eweight2=previous.edge_properties['weight']
                                                        )
    return analysys


def analyse_networks(networks: dict, output_path):
    analysis = dict()
    previous = None
    for key, value in networks.items():
        if value.num_edges() == 0 or value.num_edges() == 0:
            continue
        analysis[key] = analyse_graph(value, previous)
        previous = value
        click.secho('   Analysing {} network'.format(key), fg='yellow')
    with open(output_path, 'w') as fp:
        json.dump(analysis, fp, indent=4, sort_keys=True)
    return analysis
