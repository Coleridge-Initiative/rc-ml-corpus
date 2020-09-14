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



