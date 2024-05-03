import argparse
from pathlib import Path
from subprocess import check_output

from pyvis.network import Network

from .prefixes import prefix_map


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


def create_graph(input_path: Path, input_format: str, output_dir: Path, height: str):
    query_path = Path(__file__).parent / "query.sparql"
    if input_path.is_dir():
        datastrs = [f"--data={path}" for path in input_path.glob(f"*.{input_format}")]
    else:
        datastrs = [f"--data={input_path}"]
    cmd = [
        "sparql",
        f"--query={query_path}",
        "--results=csv",
    ] + datastrs
    query_results = check_output(cmd).decode().strip()
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
    net.show(str(output_dir / "diagram.html"), notebook=False)


if __name__ == "__main__":
    # parse cmdline args
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
    args = parser.parse_args()
    input_path = Path(args.input_path)
    input_format = args.format
    output_dir = Path(args.output_dir)
    height = str(args.height) + "px"
    if not (input_path.exists() and output_dir.exists()):
        print("could not resolve the given input and output paths")
        exit(2)
    create_graph(input_path, input_format, output_dir, height)
