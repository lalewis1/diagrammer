import argparse
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


def create_graph(
    input_path: Path | str,
    input_format: str = "ttl",
    output_dir: Path = Path("./"),
    height: str = "800px",
    return_json: bool = False,
    iri: str | None = None,
):
    schema_query_path = Path(__file__).parent / "schema_query.sparql"
    instance_query_path = Path(__file__).parent / "instance_query.sparql"
    parsed_input_path = urlparse(input_path)
    # does it look like a url ?
    if not all([parsed_input_path.scheme, parsed_input_path.netloc]):
        # if not, assume its a local dir/file path
        input_path = Path(input_path)
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
            f"--query={schema_query_path}",
            "--results=csv",
        ] + datastrs
        query_results = check_output(cmd).decode().strip()
    else:
        # otherwise assume it is a sparql endpoint
        if not (parsed_input_path.path.endswith("sparql") or parsed_input_path.path.endswith("sparql/")):
            raise ValueError(f"{input_path} must be a sparql endpoint ending with 'sparql' or 'sparql/'")
        if iri:
            query_str = instance_query_path.read_text().replace("{}", iri)
        else:
            query_str = schema_query_path.read_text()
        response = requests.get(input_path, headers={"Accept": "text/csv"}, params={"query": query_str})
        query_results = response.content.decode()
    bool_map = {"true": True, "false": False}
    net = Network(
        height=height,
        width="100%",
        neighborhood_highlight=True,
        directed=True,
        select_menu=True,
        filter_menu=True,
    )
    for line in query_results.splitlines()[1:]:
        row = line.split(",")
        prop_label = get_label(row[0])
        is_literal = True if row[2] == "" else bool_map[row[3]]
        domain_label = get_label(row[1])
        range_label = get_label(row[2])
        net.add_node(domain_label, label=domain_label)
        shape = "box" if is_literal else "dot"
        net.add_node(range_label, label=range_label, shape=shape)
        net.add_edge(domain_label, range_label, title=prop_label)
    if return_json:
        print(net.to_json())
    else:
        net.show(str(output_dir / "diagram.html"), notebook=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-i",
        "--input-dir",
        action="store",
        type=str,
        required=True,
        dest="input_path",
        help="File or Directory containing files to be generate a diagram for",
    )
    parser.add_argument(
        "-f",
        "--format",
        action="store",
        type=str,
        required=False,
        dest="format",
        default="ttl",
        help="Format of input file(s). defaults to ttl, must be a valid rdf format.",
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
        "-s",
        "--subject",
        action="store",
        type=str,
        required=False,
        dest="iri",
        default=None,
        help="IRI of subject to generate a graph for."
    )
    args = parser.parse_args()
    input_path = args.input_path
    input_format = args.format
    output_dir = Path(args.output_dir)
    height = str(args.height) + "px"
    return_json = args.return_json
    iri = args.iri
    create_graph(input_path, input_format, output_dir, height, return_json, iri)
