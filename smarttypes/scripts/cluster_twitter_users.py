
import smarttypes, sys, gensim

from smarttypes.utils.postgres_handle import PostgresHandle
from smarttypes.model.postgres_base_model import PostgresBaseModel
postgres_handle = PostgresHandle(smarttypes.connection_string)
PostgresBaseModel.postgres_handle = postgres_handle

from smarttypes.model.twitter_user import TwitterUser
from smarttypes.model.twitter_group import TwitterGroup

def cluster_users_twitter_net(twitter_id):
    twitter_user = TwitterUser.get_by_id(twitter_id)
    
    #each doc is a list of (following_id, weight) tuples
    all_docs = [[(x,1) for x in twitter_user.following_ids_default]]
    for following in twitter_user.following:
        new_doc = []
        for following_following_id in following.following_ids_default:
            new_doc.append((following_following_id, 1))
        all_docs.append(new_doc)

    all_docs_dictionary = gensim.corpora.Dictionary(all_docs)
    all_docs_corpus = [all_docs_dictionary.doc2bow(doc) for doc in all_docs]        
        
    print "# of docs %s" % len(all_docs)
    num_communities = 50
    community_lda = gensim.models.ldamodel.LdaModel(all_docs_corpus, num_communities, all_docs_dictionary, update_every=10, passes=5)
    #communities = community_lda.show_topics(topics=-1, formatted=False)
    return community_lda

            
    
#if __name__ == "__main__":

twitter_user = TwitterUser.by_screen_name('SmartTypes')
community_lda = cluster_users_twitter_net(twitter_user.id)







