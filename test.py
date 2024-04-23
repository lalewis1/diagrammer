from pathlib import Path

from rdflib import Graph, URIRef
from itertools import product
import re

g = Graph()
turtles = Path().glob("*.ttl")
for turt in turtles:
    g.parse(turt)
# g.parse("flags.ttl")
results = g.query(
    "prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> select distinct ?class where { ?s rdf:type ?class }"
)
classes = {result["class"] for result in results.bindings}
results = g.query("select distinct ?p where {?s ?p ?o}")
properties = {result["p"] for result in results.bindings}
ids = product("ABCDEFGHIJKLMNOPQSTUVWXYZ", range(1, 10))
statements = []
dmap = dict()
for property in properties:
    results = g.query(
        """
        prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        select distinct ?c
        where {
            ?s {} ?o .
            ?o rdf:type ?c
        }
    """.replace("{}", "<" + str(property) + ">")
    )
    prop_range = {result["c"] for result in results.bindings}
    results = g.query(
        """
        prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        select distinct ?c
        where {
            ?s {} ?o .
            ?s rdf:type ?c
        }
    """.replace("{}", "<" + str(property) + ">")
    )
    prop_domain = {result["c"] for result in results.bindings}
    results = g.query(
        """
        prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        select distinct ?o
        where {
            ?s {} ?o .
            filter(isliteral(?o))
        }
    """.replace("{}", "<" + str(property) + ">")
    )
    literals = {result["o"].datatype for result in results.bindings}
    if literals:
        if None in literals:
            literals = literals.difference({None}).union({URIRef("http://www.w3.org/2001/XMLSchema#text")})
        prop_range = prop_range.union(literals)
    for x in prop_range.union(prop_domain):
        if not dmap.get(x):
            dmap[x] = re.sub(r"[^A-z0-9]", "", str(next(ids)))
    sub_obs = list(product(prop_domain, prop_range))
    for sub, ob in sub_obs:
        statements.append(f"\t\t{dmap[sub]} -->|{str(property)}| {dmap[ob]}\n")

with open("diagram.md", "w") as file:
    file.write("```mermaid\nflowchart LR\n")
    for k, v in dmap.items():
        klass_name = k.split("/")[-1]
        file.write(f"\t\t{v}[{klass_name}] -->|rdf:type| {k}\n")
    file.writelines([statement for statement in statements])
    file.write("```")
