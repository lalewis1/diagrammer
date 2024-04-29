import re
from pathlib import Path

from rdflib import Graph, URIRef
from itertools import product

from prefixes import prefix_map


def write_progress(i: int, total: int, message: str = "") -> None:
    pc_complete = round((i / total) * 100)
    print(
        f"    {message}: [{str(pc_complete).center(5)}% ] {str(i).rjust(len(str(total)))}/{total}",
        end="\r",
        flush=True,
    )
    if i == total:
        print("\n", end="")
    return


def new_id():
    return re.sub(r"[^A-Z0-9]", "", str(next(ids)))


def parse_graphs(extension: str) -> Graph:
    g = Graph()
    paths = list(Path().glob(f"*.{extension}"))
    for path in paths:
        g.parse(path)
    print(f"    {len(g)} triples parsed from {len(paths)} files.")
    return g


def get_properties(g: Graph) -> list:
    results = g.query("select distinct ?p where {?s ?p ?o}")
    properties = list({result["p"] for result in results.bindings})
    print(f"    {len(properties)} properties found.")
    return properties


def get_label(prop: str) -> str:
    label = prop
    prefix = None
    if "#" in prop:
        uri, part = prop.split("#")
        uri += "#"
    else:
        uri = "/".join(prop.split("/")[:-1]) + "/"
        part = prop.split("/")[-1]
    for k, v in prefix_map.items():
        if v == uri:
            prefix = str(k)
    if prefix and part:
        label = prefix + ":" + part
    else:
        print(f"    no prefix found for {uri}")
    return label


def get_id(klass: str) -> str:
    klass_id = node_map.get(klass)
    if not klass_id:
        klass_id = new_id()
        node_map[klass] = klass_id
    return klass_id


def get_statements(g: Graph, prop: URIRef) -> list:
    prop_statements = []
    prop_label = get_label(prop)
    results = g.query(
        """
        prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        select distinct (?s_class as ?domain) (if(bound(?o_class), ?o_class, datatype(?o)) as ?range)
        where {
            ?s {} ?o .
            ?s rdf:type ?s_class .
            optional {
                ?o rdf:type ?o_class .
            }
        }
    """.replace("{}", "<" + str(prop) + ">")
    )
    for result in results.bindings:
        prop_domain = result.get("domain")
        prop_range = result.get("range")
        # handle xsd:text which is mapped as datatype=None
        if prop_range is None:
            prop_range = URIRef("http://www.w3.org/2001/XMLSchema#text")
        domain_label = get_label(str(prop_domain))
        range_label = get_label(prop_range)
        domain_id = get_id(domain_label)
        range_id = get_id(range_label)
        prop_statements.append(f"\t\t{domain_id} -->|{prop_label}| {range_id}\n")
    return prop_statements


def write_diagram(statements: list):
    with open("diagram.md", "w") as file:
        file.write("```mermaid\nflowchart LR\n")
        for k, v in node_map.items():
            file.write(f"\t\t{v}[{k}]\n")
        file.writelines([statement for statement in statements])
        file.write("```")


if __name__ == "__main__":
    ids = product("ABCDEFGHIJKLMNOPQSTUVWXYZ", range(1, 10))
    node_map = dict()
    print("Parsing graphs...")
    graph = parse_graphs("ttl")
    print("Querying properties...")
    properties = get_properties(graph)
    statements = []
    print("Generating Domain / Range Statements")
    for i, prop in enumerate(properties):
        write_progress(i, len(properties))
        statements += get_statements(graph, prop)
    print(f"    {len(statements)} statements generated.")
    print("Writing to diagram...")
    write_diagram(statements)
    print("    done.")
