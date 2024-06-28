import argparse
from pathlib import Path

from .core import get_graph


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

    digrdf_dir = Path.home() / ".digrdf"
    if not digrdf_dir.exists():
        digrdf_dir.mkdir()

    json = get_graph(source, input_format, output_dir, height, return_json, iri, _cache=_cache)
    if json:
        print(json)
