

def test_get_adjacency_matrix():

    #need to make this work!!
    
    #little test
    i = 0
    tmp_followies = []
    random_index = random.randint(0, len(adjacency_matrix) - 1)
    for x in adjacency_matrix[random_index]:
        if x: tmp_followies.append(unique_user_ids[i])
        i += 1
    assert not set(tmp_followies).difference(TwitterUser.get_by_id(unique_user_ids[random_index]).following_ids)
    print "Passed our little test: following %s users!" % len(tmp_followies) 
    
    
if __name__ == '__main__':
    test_get_adjacency_matrix()








