# rc-ml-corpus
##### Repository to generate agency/organization specific corpus to build ML models


This repository initially contains code to download PDF files of the documents hosted at the NOAA Institutional Repository. It reuses scripts from other RC repositories that are added as Git submodules.


After cloning this repo, initialize the local Git configuration for the required submodules:

```
git submodule init
```

For more info about how to use Git submodules, see:

  - <https://git-scm.com/book/en/v2/Git-Tools-Submodules>
  - <https://github.blog/2016-02-01-working-with-submodules/> 

Once you confirm the submodules are initialized correctly, you can run the script by:
```
python create_noaa_ir_corpus.py 
```

The current script workflow is:
1. Pull all documents metadata from NOAA Institutional Repository
2. Reuse scripts form several Rich Context repositories to crete a corpus.jsonld (same structure as <https://github.com/Coleridge-Initiative/rclc>) 
3. Download all PDFs files

You can skip any of those steps. To see the how to do it you can run:

```
python create_noaa_ir_corpus.py -h
```

###### Example: python create_noaa_ir_corpus.py --skip_download

 NOAA API has 17 collections, each one with its own endpoint. See [NOAA API documentation](https://github.com/NOAA-Central-Library-NCL/NOAA_IR) for details.
 
 In step 1, the script will pull the documents metadata from all the collections and then deduplicate them, since one document could be present in more than one collection/endpoint. It will generate a csv file with the documents metadata (eg NOAA id, title, doi, etc) and a programmatically generated URL pointing to the PDF files in the NOAA IR.
 
 In step 2, the script will reuse code from RCGraph to generate a `corpus.jsonld` file. The file might have additional entities when compared with the one published originally in 
[RCLC](https://github.com/Coleridge-Initiative/rclc). It will initially contain a placeholder for the dataset links.

In step 3, the script will try to download all the PDF files present in corpus.jsonld file. It will save them into the subdirectory corpus/pub/pdf. The download script will make 3 attemps by default. A few NOAA documents will fail to be downloaded. If the download is interrupted, the script will pick up where it left, preventing downloading again files already present in corpus/pub/pdf.

### Corpus available in S3 bucket

Since the download and pdf-to-text conversion will take a significant time for bigger corpora we are making both PDF and TXT files available in a S3 bucket named `richcontext`.

Please, note that the S3 bucket will contain more files than just the current corpus. You need to use `corpus.jsonld` file as an index. You will see that the entries in that file of type ResearchPublication has an id that matches those files in the S3 bucket.

###### Example: for this entry in corpus.jsonld file, `"@id": "https://github.com/Coleridge-Initiative/adrf-onto/wiki/Vocabulary#publication-f23cafe87a6977199527"`, the corresponding filenames will be `f23cafe87a6977199527.pdf` and `f23cafe87a6977199527.pdf.txt` 

First, you need to have your .aws directory configured with valid keys, etc., for S3 access before the following script will work. The bucket is readable by the public, even so the boto3 library for requires keys for a valid AWS user account.

Then adapt the rclc/bin/download_s3.py script as example code to download the PDF files (open access publications), and TXT files (raw extracted text) from the public S3 bucket. You will need to modify or adapt that code. For now we are not providing structured JSON files for these corpora.

You will find missing files in the S3 bucket. There are two reasons why a publication present in `corpus.jsonld` file might not have the corresponding .txt file uploaded in the S3 bucket:
1. The PDF file of that publication failed to be retrieved from the NOAA Institutional Repository -a few files are missing there
2. The pdf-to-text tool could not process the PDF file.
