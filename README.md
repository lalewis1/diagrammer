# Diagrammer

Generates Schema Diagrams from RDF

## Dependencies

- [ARQ - A Sparql Processor for Jena](https://jena.apache.org/documentation/query/index.html)

> Only required to query local files

TODO: Fallback to rdflib if sparql is not available. Currently not implemented because of performance issues.

## Installation

```bash
pip install digrdf
```

## Usage

from the command line

```bash
python -m digrdf -i myfiles/
```

This will create a file called diagram.html in the working directory and open it for viewing.

You can query any sparql endpoint as well.

```bash
python -m digrdf -i "http://myserver.com/sparql"
```

This will generate a schema diagram for all triples at that endpoint.

> **warning** The query is intensive and may crash / timeout if the triple store has a lot of triples (like 1.0GB plus)

You can also generate an instance level diagram for a particular iri

```bash
python -m rdflib -i "http://myserver.com/sparql" -s "http://myserver.com/objects/1234"
```

where `-s` or `--subject` is a valid iri for an object in the triple store


To see all the cmdline options run

```bash
python -m digrdf -h
```
