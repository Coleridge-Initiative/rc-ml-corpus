import argparse
import sys
import os
import requests
import pandas as pd
from pathlib import Path

# the following imports are for reusing existing RC scripts
from publications.scripts import publications_export_template

# this avoids an exception when importing run_author,run_final,gen_ttl
sys.path.append(str(Path(__file__).parent / "rcgraph"))
from rcgraph import run_author , run_final, gen_ttl

from rclc.bin import download_resources

NOAA_COLUMNS = ['PID', 'mods.title', 'mods.abstract',
                  'mods.type_of_resource',
                  'mods.sm_digital_object_identifier',
                  'mods.ss_publishyear'  # ,  'mods.origin'
                 ,'mods.subject_topic']

NOAA_API_DOWNLOAD_URL = "https://repository.library.noaa.gov/fedora/export/download/collection/"
NOAA_API_VIEW_URL = "https://repository.library.noaa.gov/fedora/export/view/collection/"

NOAA_CORPUS_OUTPUT_FILENAME = "noaa_corpus.csv"

DEFAULT_SKIP_METADATA_PULL = False
DEFAULT_SKIP_GEN_CORPUS_FILE = False
DEFAULT_SKIP_DOWNLOAD = False
DEFAULT_FORCE_DOWNLOAD = False

def cleanup_PID(value):
    try:
        # remove noaa: prefix
        if str(value).startswith("noaa:"):
            return value[len("noaa:"):]
        print("unexpected PID",str(value))
    except TypeError:
        return value


def list_to_str(value):
    """
    Converts list objects to string objects.

    Exception used to handle NaN values.
    """

    try:
        aux = ';'.join(value)
        return aux
    except TypeError:
        return value

def get_endpoint_list():
    # See documentation in https://github.com/NOAA-Central-Library-NCL/NOAA_IR
    return [1, 23702, 3, 4, 5, 6, 7, 8, 9, 11, 12, 10031, 11879, 16402, 22022, 23649, 24914]

def count_endpoint_documents(endpoint_pid):

    url = NOAA_API_VIEW_URL +str(endpoint_pid)
    response = requests.get(url)
    json_d = response.json()
    rows = json_d['response']['numFound']
    print("endpoint {} has {} documents".format(endpoint_pid, rows))

    return rows

def get_NOAA_corpus_metadata():
    # create an empty DataFrame for NOAA metadata
    columns = NOAA_COLUMNS
    noaa_corpus_df = pd.DataFrame(columns=columns)

    # pull metadata from all the NOAA endpoints
    for endpoint in get_endpoint_list():
        # get how many documents the endpoint has, otherwise the API will return a subset by default
        rows = count_endpoint_documents(endpoint)

        print("processing endpoint {} contaning {} documents".format(endpoint, rows))

        # pull all the metadata associated with the endpoint
        url = NOAA_API_DOWNLOAD_URL + str(endpoint) + "?rows=" + str(rows)
        response = requests.get(url)
        json_d = response.json()
        docs = json_d['response']['docs']

        # convert the json document list into a DataFrame
        df = pd.DataFrame(docs)
        # keep only the useful columns
        df = df.reindex(columns=columns)

        # transforming list type to string to be able to deduplicate rows later on
        df['mods.abstract'] = df['mods.abstract'].apply(list_to_str)
        df['mods.type_of_resource'] = df['mods.type_of_resource'].apply(list_to_str)
        df['mods.subject_topic'] = df['mods.subject_topic'].apply(list_to_str)

        # no need to standarize the DOI field since this is better handled by RCGraph code later on
        df['mods.sm_digital_object_identifier'] = df['mods.sm_digital_object_identifier'].apply(list_to_str)

        noaa_corpus_df = noaa_corpus_df.append(df, ignore_index=True)

    # rename key columns to more convenient names
    noaa_corpus_df.rename(columns={'mods.title': 'title',
                                   'mods.sm_digital_object_identifier': 'doi'}, inplace=True)
    noaa_corpus_df.reset_index(drop=True, inplace=True)

    # get a clean PID
    noaa_corpus_df['noaa_pid'] = noaa_corpus_df['PID'].apply(cleanup_PID)

    # build the url pointing to NOAA repository PDF
    noaa_corpus_df['pdf'] = "https://repository.library.noaa.gov/view/noaa/" + noaa_corpus_df['noaa_pid'] + "/noaa_" + \
                            noaa_corpus_df['noaa_pid'] + "_DS1.pdf"


    print("**WARNING**")
    print("Using a placeholder for the dataset, needed for reusing existing code")
    noaa_corpus_df['dataset'] = "dataset-000"  # TODO: placeholder

    # deduplicate results. According to NOAA documentation a document might be present in more than one endpoint
    print("Unique document PID values:", noaa_corpus_df.PID.nunique())
    noaa_corpus_df.drop_duplicates(inplace=True)
    print("Deduplicated corpus size:", len(noaa_corpus_df))

    # save corpus metadata as csv file
    noaa_corpus_df.to_csv(NOAA_CORPUS_OUTPUT_FILENAME, index=False)


def prepare_context_for_rc_scripts():
    # this method prepares the arguments rcgraph scripts need and
    # overrides some constants to avoid creating files inside the submodules structure

    parser = argparse.ArgumentParser(
        # description="reconcile the journal and ISSN for each publication"
    )
    parser.add_argument(
        "--partition",
        type=str,
        default="20200831_noaa_corpus_publications.json",
        help="limit processing to a specified partition"
    )
    parser.add_argument(
        "--force",
        type=bool,
        default=False,
        help="force re-generating the author entities from scratch"
    )

    parser.add_argument(
        "--full_graph",
        type=bool,
        default=True,
        help="generate the full graph, not just the open source subset"
    )

    # change working directory so rcgraph scripts find some required files
    os.chdir("rcgraph")

    # overrides some constants to avoid creating files inside the submodules structure

    # run_step4.rc_graph.RCGraph.BUCKET_STAGE = (Path(__file__).parent / "bucket_stage" )
    run_author.rc_graph.RCGraph.BUCKET_STAGE = (Path(__file__).parent / "bucket_stage")
    run_final.rc_graph.RCGraph.BUCKET_STAGE = (Path(__file__).parent / "bucket_stage")
    run_final.rc_graph.RCGraph.BUCKET_FINAL = (Path(__file__).parent / "bucket_final")
    gen_ttl.rc_graph.RCGraph.BUCKET_FINAL = (Path(__file__).parent / "bucket_final")
    gen_ttl.rc_graph.RCGraph.PATH_DATASETS = (Path(__file__).parent / "corpus/unknown_dataset.json")
    gen_ttl.rc_graph.RCGraph.PATH_PROVIDERS = (Path(__file__).parent / "corpus/unknown_provider.json")
    gen_ttl.PATH_CORPUS_TTL = (Path(__file__).parent / "corpus/corpus.ttl")
    gen_ttl.PATH_SKOSIFY_CFG = (Path(__file__).parent / "adrf-onto/skosify.cfg")
    gen_ttl.PATH_ADRF_TTL = (Path(__file__).parent / "adrf-onto/adrf.ttl")

    return parser


def gen_corpus_jsonld():
    parser = prepare_context_for_rc_scripts()
    run_author.main(parser.parse_args())
    run_final.main(parser.parse_args())
    gen_ttl.main(parser.parse_args())
    os.replace("./corpus.jsonld","./../corpus/corpus.jsonld")

def download_pdf_files(force_download):

    parser = argparse.ArgumentParser(
        description="download publication PDFs and dataset foaf pages for the rclc corpus"
    )
    parser.add_argument(
        "--logger",
        type=str,
        default=download_resources.DEFAULT_LOGGER_FILE,
        help="logger file"
    )
    parser.add_argument(
        "--input",
        type=str,
        #default=download_resources.DEFAULT_CORPUS_FILE,
        default=(Path(__file__).parent / "corpus/corpus.jsonld"),
        help="rclc corpus file"
    )
    parser.add_argument(
        "--todo",
        type=str,
        default=download_resources.DEFAULT_TODO_LIST,
        help="download todo file"
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default=download_resources.DEFAULT_OUTPUT_RESOURCE,
        help="path to store downloaded resources"
    )

    parser.add_argument(
        "--force",
        type=bool,
        default=force_download,
        help="always download resources"
    )

    if force_download:
        print("Forcing download of files if they alredy have been dowloaded...")

    download_resources.DEFAULT_TODO_FILE = (Path(__file__).parent / "corpus/todo.tsv")
    download_resources.DEFAULT_OUTPUT_RESOURCE = (Path(__file__).parent / "corpus/resources/")

    # change working directory so the downloaed PDF files get stored in corpus/resources folder
    os.chdir((Path(__file__).parent / "corpus"))

    download_resources.main(parser.parse_args())


def main(args):

    if args.skip_metadata_pull:
        print("Skipping metadata pull using NOAA IR API")
    else:
        get_NOAA_corpus_metadata()

        # transform the csv file into a json file that can be processed by RCGraph code
        publications_export_template.export(Path("noaa_corpus.csv"), "corpus/unknown_dataset.json", "./",
                                            "bucket_stage/20200831_noaa_corpus_publications.json")

    if args.skip_gen_corpus_file:
        print("Skipping generating corpus.jsonld")
    else:
        gen_corpus_jsonld()

    if args.skip_download:
        print("Skipping PDF downloads")
    else:
        download_pdf_files(args.force_download)


if __name__ == '__main__':
    # This code is based on NOAA API documentation https://github.com/NOAA-Central-Library-NCL/NOAA_IR
    #
    # NOAA API has 17 endpoints. See documentation for details
    # - For each endpoint, get how many documents it has
    # - Download all the endpoint's documents metadata
    # - Extract useful columns that are present in all endpoints
    # - Deduplicate entries
    # - Saves as csv file
    # - Reuses RCGraph code to generate a corpus.jsonld file with the publications url to download the PDFs
    # - Reuses rclc code to download PDF files. Will store the files in subdirectory corpus/resources/pub/pdf

    # Example: python create_noaa_ir_corpus.py --skip_download

    # parse the command line arguments, if any
    parser = argparse.ArgumentParser(
        description="download NOAA corpus PDF files"
        )

    parser.add_argument(
        "--skip_metadata_pull",
        action="store_true",
        default=DEFAULT_SKIP_METADATA_PULL,
        help="Don't make API calls to institutional repository."
        )

    parser.add_argument(
        "--skip_gen_corpus_file",
        action="store_true",
        default=DEFAULT_SKIP_GEN_CORPUS_FILE,
        help="Don't create corpus.jsonld."
        )

    parser.add_argument(
        "--skip_download",
        action="store_true",
        default=DEFAULT_SKIP_DOWNLOAD,
        help="Don't download resources files"
        )

    parser.add_argument(
        "--force_download",
        action="store_true",
        default=DEFAULT_FORCE_DOWNLOAD,
        help="Always download resources, even if files already present."
        )


    main(parser.parse_args())