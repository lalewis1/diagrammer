import argparse
import json
import os
from pathlib import Path
from subprocess import check_output
from urllib.parse import urlparse

import requests
from pyvis.network import Network

try:
    from .prefixes import prefix_map
except ImportError:
    from prefixes import prefix_map


def get_label(uri: str) -> str:
    # handle xsd:text which comes through as ""
    if uri == "":
        uri = "http://www.w3.org/2001/XMLSchema#string"
    if "#" in uri:
        base, term = uri.split("#")
        base += "#"
    else:
        base = "/".join(uri.split("/")[:-1]) + "/"
        term = uri.split("/")[-1]
    prefix = prefix_map.get(base)
    if prefix and term:
        label = prefix + ":" + term
    else:
        label = uri
    return label


def run_query(source: str, input_format: str, iri: str) -> dict:
    schema_query_path = Path(__file__).parent / "schema_query.sparql"
    instance_query_path = Path(__file__).parent / "instance_query.sparql"
    parsed_source = urlparse(str(source))
    if iri:
        query_str = instance_query_path.read_text().replace("{}", iri)
        query_path = Path.home() / "digrdf/tmp.sparql"
        with open(query_path, "w") as file:
            file.write(query_str)
    else:
        query_path = schema_query_path
    # if source doesnt look like a url assume its a local dir/file path
    if not all([parsed_source.scheme, parsed_source.netloc]):
        input_path = Path(source)
        if input_path.is_dir():
            datastrs = [
                f"--data={path}" for path in input_path.glob(f"*.{input_format}")
            ]
        elif input_path.is_file():
            datastrs = [f"--data={input_path}"]
        else:
            raise FileNotFoundError(f"Could not resolve file/folder path: {input_path}")
        cmd = [
            "sparql",
            f"--query={query_path}",
            "--results=json",
        ] + datastrs
        query_results = json.loads(check_output(cmd).decode().strip())
        if iri:
            os.remove(query_path)
    else:
        # otherwise assume it is a sparql endpoint
        if not (
            parsed_source.path.endswith("sparql")
            or parsed_source.path.endswith("sparql/")
        ):
            raise ValueError(
                f"{source} must be a sparql endpoint ending with 'sparql' or 'sparql/'"
            )
        if iri:
            query_str = instance_query_path.read_text().replace("{}", iri)
        else:
            query_str = schema_query_path.read_text()
        response = requests.get(
            str(source),
            headers={"Accept": "application/json"},
            params={"query": query_str},
        )
        query_results = response.json()
    return query_results


def process_schema_results(results) -> Network:
    net = Network(
        height=str(height) + "px",
        width="100%",
        neighborhood_highlight=True,
        directed=True,
        select_menu=True,
        filter_menu=True,
    )
    net.set_edge_smooth("cubicBezier")
    for result in results["results"]["bindings"]:
        prop_label = get_label(result["p"]["value"])
        domain_label = get_label(result["domain"]["value"])
        range_obj = result.get("range")
        if range_obj:
            range_label = get_label(range_obj["value"])
        else:
            range_label = "xsd:string"
        isliteral = result["isliteral"]["value"] == "true"
        shape = "box" if isliteral else "dot"
        color = (
            {"background": "#e8e6e3", "border": "#97c2fc"}
            if isliteral
            else {"background": "#97c2fc", "border": "#97c2fc"}
        )
        net.add_node(domain_label, label=domain_label)
        net.add_node(range_label, label=range_label, shape=shape, color=color)
        edges = net.get_edges()
        duplicate_edge = False
        for edge in edges:
            if edge["from"] == domain_label and edge["to"] == range_label:
                duplicate_edge = True
                edge["title"] += f"\n{prop_label}"
                edge["width"] += 0.2
        if not duplicate_edge:
            net.add_edge(
                domain_label, range_label, title=prop_label, physics=False, width=1
            )
    return net


def process_instance_results(results):
    net = Network(
        height=str(height + 200) + "px",
        width="100%",
        neighborhood_highlight=True,
        directed=True,
    )
    net.set_edge_smooth("cubicBezier")
    for result in results["results"]["bindings"]:
        isblank = result['isblank']['value'] == 'true'
        if isblank:
            color = {"background": "#6b6767", "border": "#97c2fc"}
            b_subject_label = get_label(result['o']['value'])
            b_property_label = get_label(result['bp']['value'])
            b_object_label = get_label(result['bo']['value'])
            b_object_title = b_object_label
            if len(b_object_label) > 100:
                b_object_label = b_object_label[0:35] + " ..."
            net.add_node(b_subject_label, label=b_subject_label, color=color)
            net.add_node(b_object_label, label=b_object_label, title=b_object_title)
            net.add_edge(b_subject_label, b_object_label, title=b_property_label, physics=False)
        subject_label = get_label(result["s"]["value"])
        property_label = get_label(result["p"]["value"])
        object_label = get_label(result["o"]["value"])
        object_title = object_label
        if len(object_label) > 100:
            object_label = object_label[0:35] + " ..."
        isliteral = result["isliteral"]["value"] == "true"
        shape = "box" if isliteral else "dot"
        if isliteral:
            color = {"background": "#e8e6e3", "border": "#97c2fc"}
        else:
            color = {"background": "#97c2fc", "border": "#97c2fc"}
        net.add_node(subject_label, label=subject_label, color={"background": "#d70e5d", "border": "#97c2fc"})
        net.add_node(
            object_label,
            title=object_title,
            label=object_label,
            shape=shape,
            color=color,
        )
        net.add_edge(subject_label, object_label, title=property_label, physics=False)
    return net


def get_graph(
    source: str,
    input_format: str = "ttl",
    output_dir: Path = Path("./"),
    height: int = 800,
    return_json: bool = False,
    iri: str | None = None,
    _cache: bool = False,
):
    _cache_file = Path().home() / "digrdf/results.json"
    if _cache and _cache_file.exists():
        query_results = json.loads(_cache_file.read_text())
    else:
        query_results = run_query(source=source, input_format=input_format, iri=iri)
    with open(_cache_file, "w") as file:
        json.dump(query_results, file)
    if iri:
        net = process_instance_results(results=query_results)
    else:
        net = process_schema_results(results=query_results)

    if return_json:
        print(net.to_json())
    else:
        net.show(str(output_dir / "diagram.html"), notebook=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-s",
        "--source",
        action="store",
        type=str,
        required=True,
        dest="source",
        help="RDF Input path. Can be HTTP(S) SPARQL endpoint or RDF File or Directory containing RDF files",
    )
    parser.add_argument(
        "-f",
        "--format",
        action="store",
        type=str,
        required=False,
        dest="format",
        default="ttl",
        help="Format of input file(s). defaults to ttl, must be a valid RDF format.",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        action="store",
        type=str,
        required=False,
        dest="output_dir",
        default="./",
        help="Directory to store the result graph. default is current directory.",
    )
    parser.add_argument(
        "--height",
        action="store",
        type=int,
        required=False,
        dest="height",
        default=800,
        help="Height of the generated diagram in pixels. defaults to 1000",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        required=False,
        dest="return_json",
        default=False,
        help="Return json to stdout, don't render the graph to html",
    )
    parser.add_argument(
        "-i",
        "--iri",
        action="store",
        type=str,
        required=False,
        dest="iri",
        default=None,
        help="IRI of subject to generate a graph for. Do not include surrounding <> tags.",
    )
    parser.add_argument(
        "-c",
        "--cache",
        action="store_true",
        required=False,
        dest="cache",
        default=False,
        help="Use the cached query results from the last run if they exist",
    )
    args = parser.parse_args()
    source = args.source
    input_format = args.format
    output_dir = Path(args.output_dir)
    height = args.height
    return_json = args.return_json
    iri = args.iri
    _cache = args.cache

    digrdf_dir = Path.home() / "digrdf"
    if not digrdf_dir.exists():
        digrdf_dir.mkdir()

    get_graph(source, input_format, output_dir, height, return_json, iri, _cache=_cache)
