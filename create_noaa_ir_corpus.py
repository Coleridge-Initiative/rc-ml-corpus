import requests
import pandas as pd
from pathlib import Path
from publications.scripts import publications_export_template

NOAA_COLUMNS = ['PID', 'mods.title', 'mods.abstract',
                  'mods.type_of_resource',
                  'mods.sm_digital_object_identifier',
                  'mods.ss_publishyear'  # ,  'mods.origin'
                 ,'mods.subject_topic']

NOAA_API_DOWNLOAD_URL = "https://repository.library.noaa.gov/fedora/export/download/collection/"
NOAA_API_VIEW_URL = "https://repository.library.noaa.gov/fedora/export/view/collection/"

NOAA_CORPUS_OUTPUT_FILENAME = "noaa_corpus.csv"

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


    # TODO: ***WARNING*** this is not true
    noaa_corpus_df['dataset'] = "dataset-610"  # TODO: placeholder

    # deduplicate results. According to NOAA documentation a document might be present in more than one endpoint
    print("Unique document PID values:", noaa_corpus_df.PID.nunique())
    noaa_corpus_df.drop_duplicates(inplace=True)
    print("Deduplicated corpus size:", len(noaa_corpus_df))

    # save corpus metadata as csv file
    noaa_corpus_df.to_csv(NOAA_CORPUS_OUTPUT_FILENAME, index=False)



def main():

    get_NOAA_corpus_metadata()

    # transform the csv file into a json file that can be processed by RCGraph code
    publications_export_template.export(Path("noaa_corpus.csv"), "datasets/datasets.json", "./",
                                        "20200831_noaa_corpus_publications.json")

if __name__ == '__main__':
    # This code is based on NOAA API documentation https://github.com/NOAA-Central-Library-NCL/NOAA_IR
    #
    # NOAA API has 17 endpoints. See documentation for details
    # - For each endpoint, get how many documents it has
    # - Download all the endpoint's documents metadata
    # - Extract useful columns that are present in all endpoints
    # - Deduplicate entries
    main()