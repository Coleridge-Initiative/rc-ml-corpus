#!/usr/bin/env python
# coding: utf-8

# In[1]:

from rc_util import *

from richcontext import scholapi as rc_scholapi

# import matplotlib.pyplot as plt
# get_ipython().run_line_magic('matplotlib', 'inline')


# In[2]:


# build a graph from the JSON-LD corpus
net = RCNetwork()

# parses, builds NetworkX graph, and creates default "rank" for each entity
net.load_network("full.jsonld") # net.load_network("../../rclc/corpus.jsonld")


# In[3]:


# profile corpus
num_datasets = len(set(net.data.keys()))

num_publications = len(set(net.publ.keys()))

num_providers = len(set(net.prov.keys()))

num_authors = len(set(net.auth.keys()))

print("this corpus has: \n--{:,.0f} datasets \n--{:,.0f} publications \n--{:,.0f} providers \n--{:,.0f} authors".format(
num_datasets, num_publications, num_providers, num_authors))


# In[4]:


## dataset RC-IDs for 4 target datasets: FoodAPS, ARMS, IRI InfoScan & Consumer Network
data_list = ['dataset-955eb4bf66b73016354c', # ARMS
             'dataset-fc71e81f1f2c4130d897', # FoodAPS
            'dataset-ae01c2bf3451493f3620',  # IRI Consumer Network
             'dataset-cb23c2370049f4960a3a'] # IRI InfoScan


# In[5]:


# simple count of publications for each dataset:
for rc_id in data_list:
    # gather  info from 'recommender'; it sorts the publications based on Eigenvector calc of 'rank'
    uuid, title, rank, url, provider, publ_list = net.reco_data(net.data[rc_id])
    print('{} | {} |  has {} publications'.format(rc_id, title,len(publ_list)))


# 1. dataset name
# 2. number of publications
# 3. number of combined datasets
# 4. top 5 datasets and their providers
# 5. number of authors
# 6. top 5 authors

# ### test steps for one dataset

# In[ ]:


# build on existing function to generate metrics
uuid, title, rank, url, provider, publ_list = net.reco_data(net.data['dataset-ae01c2bf3451493f3620'])


# In[ ]:

def extract_institution(orcid,institutions_dict, institutions_count):
    # get orcid institution
    if len(net.auth[a].view["orcid"]) > 19:
        orcid = net.auth[a].view["orcid"][-19:]

    result = schol.orcid.affiliations(orcid)
    result2 = schol.orcid.funding(orcid)
    if result.meta:
        if isinstance(result.meta, list):
            institution = result.meta[0]['employment:organization']
        else:
            institution = result.meta['employment:organization']
        #print(orcid, institution['common:name'])

        if institution['common:name'] in institutions_dict.keys():
            institutions_count[institution['common:name']] += 1
        else:
            institutions_dict[institution['common:name']] = institution  # TODO potentially show countries?
            institutions_count[institution['common:name']] = 1
    if result2.meta:
        print("WARNING, look at this", result2.meta)


print(net.data['dataset-ae01c2bf3451493f3620'].view['title'])
print(len(publ_list))
joined_datasets = {}
joined_data_counts = {}
authors_dict = {}
authors_count = {}
institutions_dict = {}
institutions_count = {}
schol = rc_scholapi.ScholInfraAPI(config_file="rc.cfg", logger=None)




for pubid, pub, pubrank in publ_list:
    d_list = net.publ[net.id_list[pubid]].view['datasets'].copy()
    d_list.remove(uuid) # don't include current dataset
    for d in d_list:
        if d in joined_datasets.keys():
            joined_data_counts[d] += 1
        else:
            joined_datasets[d] = net.data[d].view
            joined_data_counts[d] = 1
            joined_datasets[d]['ProvName'] = net.prov[joined_datasets[d]['provider']].view['title']
    a_list = net.publ[net.id_list[pubid]].view['authors'].copy()
    for a in a_list:
        if a in authors_dict.keys():
            authors_count[a] += 1
        else:
            ## todo add institution to author
            authors_dict[a] = net.auth[a].view
            authors_count[a] = 1

            if net.auth[a].view["orcid"]:
                extract_institution(net.auth[a].view["orcid"], institutions_dict, institutions_count)




# In[ ]:


print(joined_datasets.keys())


# In[ ]:


joined_datasets['dataset-17fbd0c3d561e8260ab3']


# In[ ]:


# to get top 5 authors
sorted(authors_count.items(), key=lambda t: t[1], reverse=-True)[:5]


# In[ ]:


sorted(joined_data_counts.items(), key=lambda t: t[1], reverse=-True)[:5]


# In[ ]:


for data_id, data_count in sorted(joined_data_counts.items(), key=lambda t: t[1], reverse=-True)[:5]:
    DataName = joined_datasets[data_id]['title']
    DataProv = net.prov[joined_datasets[data_id]['provider']].view['title']
    print('Dataset {} by {} joined {} times'.format(DataName,DataProv,data_count))


# In[ ]:


for auth_id, auth_count in sorted(authors_count.items(), key=lambda t: t[1], reverse=-True)[:5]:
    AuthName = authors_dict[auth_id]['title']
    AuthORCID = authors_dict[auth_id]['orcid']
    print('{} | {} | used dataset {} times'.format(AuthName, AuthORCID, auth_count))


# ### work through specified list of datasets
# metrics to generate for each:
# - number of publications
# - number of combined datasets
# - top 5 datasets and their providers
# - number of authors
# - top 5 authors

# In[9]:

schol = rc_scholapi.ScholInfraAPI(config_file="rc.cfg", logger=None) # to access ORCID

dataset_metrics = {} # object to hold resulting metrics calculated below

for this_data in data_list:
    # build on existing function to generate metrics
    uuid, title, rank, url, provider, publ_list = net.reco_data(net.data[this_data])
    print('collecting measures for {}'.format(title))
    num_pubs = len(publ_list)
    print('-- used in {} publications'.format(num_pubs))
    joined_datasets = {}
    joined_data_counts = {}
    authors_dict = {}
    authors_count = {}
    institutions_dict = {}
    institutions_count = {}

    for pubid, pub, pubrank in publ_list:
        # get datasets used in publication
        d_list = net.publ[net.id_list[pubid]].view['datasets'].copy()
        d_list.remove(uuid) # don't include current dataset
        for d in d_list:
            if d in joined_datasets.keys():
                joined_data_counts[d] += 1
            else:
                joined_datasets[d] = net.data[d].view
                joined_data_counts[d] = 1
                joined_datasets[d]['ProvName'] = net.prov[joined_datasets[d]['provider']].view['title']
        a_list = net.publ[net.id_list[pubid]].view['authors'].copy()
        for a in a_list:
            if a in authors_dict.keys():
                authors_count[a] += 1
            else:
                authors_dict[a] = net.auth[a].view
                authors_count[a] = 1

                if net.auth[a].view["orcid"]:
                    extract_institution(net.auth[a].view["orcid"], institutions_dict, institutions_count)

    # add results to dataset_metrics dict:
    dataset_metrics[uuid] = {'combinedDatasets': joined_datasets, 'combinedDataCounts': joined_data_counts,
                            'PubAuthors': authors_dict, 'AuthorCounts': authors_count,
                            'TotalPublications': num_pubs, 'PubIDs': publ_list,
                             'AuthorInstitutions':institutions_dict, 'InstitutionCounts':institutions_count}
    
    ## print selected gathered info:
    # total datasets
    print('-- {} datasets were combined with this dataset. The top 5 are:'.format(len(joined_datasets.keys())))
    # top 5 datasets
    for data_id, data_count in sorted(joined_data_counts.items(), key=lambda t: t[1], reverse=-True)[:5]:
        DataName = joined_datasets[data_id]['title']
        DataProv = joined_datasets[data_id]['ProvName']
        print('---- {} by {} joined {} times'.format(DataName,DataProv,data_count))
    # total authors:
    print('-- {} authors used this dataset. The top 5 are:'.format(len(authors_dict.keys())))
    # top 5 authors:
    for auth_id, auth_count in sorted(authors_count.items(), key=lambda t: t[1], reverse=-True)[:5]:
        AuthName = authors_dict[auth_id]['title']
        AuthORCID = authors_dict[auth_id]['orcid']
        if AuthORCID=='':
            AuthORCID = 'unknown'
        print('---- {} | ORCID = {} | used dataset {} times'.format(AuthName, AuthORCID, auth_count))
    # total institutions:
    print('-- {} institutions used this dataset. The top 5 are:'.format(len(institutions_dict.keys())))
    # top 5 institutions:
    for institution_name , institution_count in sorted(institutions_count.items(), key=lambda t: t[1], reverse=-True)[:5]:
        InstitutionName = institution_name

        print('---- {} | used dataset {} times'.format(InstitutionName, institution_count))

    print('') # add line between each datast summary


# In[10]:


dataset_metrics.keys()


# In[12]:


# can access all results if need to report out differently, eg number of datasets:
len(dataset_metrics['dataset-955eb4bf66b73016354c']['combinedDatasets'].keys())


# In[ ]:




