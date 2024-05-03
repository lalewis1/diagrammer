# Diagrammer

Generates Schema Diagrams from RDF

## Dependencies

- [ARQ - A Sparql Processor for Jena](https://jena.apache.org/documentation/query/index.html)

TODO: Fallback to rdflib if sparql is not available. Currently not used because of performance issues.

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

to see all the cmdline options run

```bash
python -m digrdf -h
```

