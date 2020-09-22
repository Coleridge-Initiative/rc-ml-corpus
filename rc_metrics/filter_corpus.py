import csv
import json
from urllib.parse import urlparse

from rc_util import *
from pathlib import Path
from typing import Any, Dict, List, Tuple

KEY_USDA_DATASETS_RC_UUID = ['dataset-955eb4bf66b73016354c', # ARMS
             'dataset-fc71e81f1f2c4130d897', # FoodAPS
            'dataset-ae01c2bf3451493f3620',  # IRI Consumer Network
             'dataset-cb23c2370049f4960a3a'] # IRI InfoScan

# TODO, copied from download_resources.py
def enum_pub_resources (corpus: dict, output_path: Path, usda_corpus) -> Tuple[Path, List[List[Any]]]:
    """ Enumerate all publications PDF files from the corpus data to be
        downloaded, if not downloaded yet.  We use the entity id as filename.
        All downloaded files are stored under `output_path` folder.
        Input:
            - corpus: corpus file containing a list of publications.
            - output_path: path to store downloaded resources.
            - force_download: always download resources.
    """
    pub_path = Path( output_path) / "pub/pdf/"

    if not pub_path.exists():
        pub_path.mkdir(parents=True)

    pubs = [e for e in corpus if e["@type"] == "ResearchPublication"]

    todo = []
    skipped = 0
    added = 0

    for entity in pubs:
        e_id = urlparse(entity["@id"]).fragment

        if e_id not in usda_corpus:
            skipped +=1
            continue

        added += 1

        if "openAccess" in entity:
            if isinstance(entity["openAccess"], list):
                ## this only happens in the error case where
                ## publications are duplicated in the corpus
                res_url = entity["openAccess"][0]["@value"]
                print("WARNING duplicate: {} {}".format(e_id, entity["openAccess"]))
            else:
                res_url = entity["openAccess"]["@value"]

            todo.append(["pdf", e_id, res_url, pub_path])
        else:
            print("Warning -  missing openAccess url in pub",e_id)

    print("skipped", skipped, "added",added)
    return pub_path, todo

def main():
    # build a graph from the JSON-LD corpus
    net = RCNetwork()

    # parses, builds NetworkX graph, and creates default "rank" for each entity
    net.load_network("full.jsonld")  # net.load_network("../../rclc/corpus.jsonld")

    # view an element of the graph
    print(net.data['dataset-b1b062c8a276fe2800fd'].view)

    # view an element of the graph
    print(net.prov['provider-99fda6d9f6fbf67c3f72'].view['title'])

    # for p in net.prov.keys():
    #     if net.prov[p].view['title'] in ['US Department of Agriculture']:
    #         print(net.prov[p].view)

    usda_corpus = set()
    usda_count = 0
    for pub in net.publ.keys():
        for dataset in net.publ[pub].view['datasets']:
            if dataset in KEY_USDA_DATASETS_RC_UUID:
                print(net.publ[pub].view)
                usda_corpus.add(pub)
                usda_count +=1

    print("usda key pubs",usda_count)

    # not efficient, but reading the corpus directly
    with open("full.jsonld", "r") as f:
        jld_corpus = json.load(f)
        corpus = jld_corpus["@graph"]
    print(len(corpus))

    output_path = "usda/resources/"
    pub_path, todo = enum_pub_resources(corpus, output_path, usda_corpus)

    with open("../corpus/todo_usda.tsv", "wt") as f:
        writer = csv.writer(f, delimiter="\t")

        for t in todo:
            writer.writerow(t)



if __name__ == '__main__':
    # todo: clean up this script, for now just used to generate a download task for publications linked to key USDA datasets

    main()