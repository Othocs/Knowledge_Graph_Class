// SCHEMA: CONSTRAINTS AND INDEXES

// Create unique constraint for User nodes
CREATE CONSTRAINT user_id_unique IF NOT EXISTS
FOR (u:User) REQUIRE u.id IS UNIQUE;

// Create unique constraint for Tweet nodes
CREATE CONSTRAINT tweet_id_unique IF NOT EXISTS
FOR (t:Tweet) REQUIRE t.id IS UNIQUE;

CREATE INDEX user_username_idx IF NOT EXISTS FOR (u:User) ON (u.username);
CREATE INDEX tweet_created_at_idx IF NOT EXISTS FOR (t:Tweet) ON (t.createdAt);


// DATA LOADING QUERIES

LOAD CSV WITH HEADERS FROM 'file:///users.csv' AS row
CREATE (u:User {
    id: toInteger(row.id),
    name: row.name,
    username: row.username,
    registeredAt: date(row.registeredAt)
});

// Load Follower relationships
LOAD CSV WITH HEADERS FROM 'file:///followers.csv' AS row
MATCH (source:User {id: toInteger(row.sourceId)})
MATCH (target:User {id: toInteger(row.targetId)})
CREATE (source)-[:FOLLOWS]->(target);

// Load Tweets
LOAD CSV WITH HEADERS FROM 'file:///tweets.csv' AS row
CREATE (t:Tweet {
    id: toInteger(row.id),
    text: row.text,
    createdAt: datetime(row.createdAt)
});

// Connect Tweets to Authors (PUBLISH relationship)
LOAD CSV WITH HEADERS FROM 'file:///tweets.csv' AS row
MATCH (u:User {id: toInteger(row.authorId)})
MATCH (t:Tweet {id: toInteger(row.id)})
CREATE (u)-[:PUBLISH]->(t);

// Load Tweet Relationships (RETWEET, REPLY, MENTION)
LOAD CSV WITH HEADERS FROM 'file:///tweet_relationships.csv' AS row
WITH row
WHERE row.type = 'RETWEET' AND row.sourceId IS NOT NULL AND row.targetId IS NOT NULL
MATCH (source:Tweet {id: toInteger(row.sourceId)})
MATCH (target:Tweet {id: toInteger(row.targetId)})
CREATE (source)-[:RETWEETS]->(target);

LOAD CSV WITH HEADERS FROM 'file:///tweet_relationships.csv' AS row
WITH row
WHERE row.type = 'REPLY' AND row.sourceId IS NOT NULL AND row.targetId IS NOT NULL
MATCH (source:Tweet {id: toInteger(row.sourceId)})
MATCH (target:Tweet {id: toInteger(row.targetId)})
CREATE (source)-[:IN_REPLY_TO]->(target);

LOAD CSV WITH HEADERS FROM 'file:///tweet_relationships.csv' AS row
WITH row
WHERE row.type = 'MENTION' AND row.sourceId IS NOT NULL AND row.mentionedUserId IS NOT NULL
MATCH (tweet:Tweet {id: toInteger(row.sourceId)})
MATCH (user:User {id: toInteger(row.mentionedUserId)})
CREATE (tweet)-[:MENTIONS]->(user);


// PRACTICE QUERIES (16 Questions)

// Q1: Return 5 random User nodes
MATCH (u:User)
RETURN u
ORDER BY rand()
LIMIT 5;

// Q2: Return 5 random relationships of any type
MATCH ()-[r]->()
RETURN r
ORDER BY rand()
LIMIT 5;

// Q3: Extract text property from three random Tweet nodes
MATCH (t:Tweet)
RETURN t.text AS tweetText
ORDER BY rand()
LIMIT 3;

// Q4: Create visualization query for RETWEETS relationships
MATCH (original:Tweet)<-[:RETWEETS]-(retweet:Tweet)
MATCH (original)<-[:PUBLISH]-(originalAuthor:User)
MATCH (retweet)<-[:PUBLISH]-(retweetAuthor:User)
RETURN original, retweet, originalAuthor, retweetAuthor
LIMIT 25;

// Q5: MERGE vs CREATE - Explanation and Examples
// MERGE is used when you want to match existing nodes or create them if they don't exist (idempotent)
// CREATE always creates new nodes, even if they already exist (not idempotent)
//
// Use MERGE when:
// - Loading data that might have duplicates
// - Ensuring uniqueness (e.g., users, tweets with unique IDs)
// - Creating relationships between existing nodes
//
// Use CREATE when:
// - You're certain the node doesn't exist
// - Initial data load with guaranteed unique data
// - Performance is critical and you've validated uniqueness
//
// Example MERGE:
// MERGE (u:User {id: 1})
// ON CREATE SET u.name = 'Alice', u.created = timestamp()
// ON MATCH SET u.lastSeen = timestamp()
//
// Example CREATE:
// CREATE (t:Tweet {id: 101, text: 'Hello World', createdAt: datetime()})

// Q6: Calculate the ratio of missing createdAt values in Tweet nodes
MATCH (t:Tweet)
WITH count(t) AS total
MATCH (t2:Tweet)
WHERE t2.createdAt IS NULL
WITH total, count(t2) AS missing
RETURN toFloat(missing) / total AS missingCreatedAtRatio;

// Q7: Count the number of relationship types in the graph
MATCH ()-[r]->()
RETURN type(r) AS relationshipType, count(r) AS count
ORDER BY count DESC;

// Q8: Compare original tweet text with its retweet
MATCH (original:Tweet)<-[:RETWEETS]-(retweet:Tweet)
RETURN original.text AS originalText,
       retweet.text AS retweetText
LIMIT 5;

// Q9: Show the distribution of tweet creation by year
MATCH (t:Tweet)
RETURN date.truncate('year', t.createdAt) AS year, count(t) AS tweetCount
ORDER BY year;

// Q10: Select all tweets created in 2021 using MATCH and WHERE
MATCH (t:Tweet)
WHERE date.truncate('year', t.createdAt) = date('2021-01-01')
RETURN t.id, t.text, t.createdAt
ORDER BY t.createdAt
LIMIT 10;

// Q11: Identify top four days by tweet creation count
MATCH (t:Tweet)
WITH date.truncate('day', t.createdAt) AS day, count(t) AS tweetCount
RETURN day, tweetCount
ORDER BY tweetCount DESC, day DESC
LIMIT 4;

// Q12: Count mentioned users with zero published tweets
MATCH (u:User)
WHERE (u)<-[:MENTIONS]-() AND NOT (u)-[:PUBLISH]->()
RETURN count(u) AS mentionedButNeverPublished;

// Q13: Find top five users with most retweeted distinct tweets
MATCH (u:User)-[:PUBLISH]->(t:Tweet)<-[:RETWEETS]-()
WITH u, count(DISTINCT t) AS distinctRetweetedTweets
RETURN u.id, u.name, u.username, distinctRetweetedTweets
ORDER BY distinctRetweetedTweets DESC
LIMIT 5;

// Q14: Identify top five most-mentioned users
MATCH (u:User)<-[:MENTIONS]-(t:Tweet)
WITH u, count(t) AS mentionCount
RETURN u.id, u.name, u.username, mentionCount
ORDER BY mentionCount DESC
LIMIT 5;

// Q15: List ten most-followed users
MATCH (u:User)<-[:FOLLOWS]-(follower:User)
WITH u, count(follower) AS followerCount
RETURN u.id, u.name, u.username, followerCount
ORDER BY followerCount DESC
LIMIT 10;

// Q16: List ten users following the most people
MATCH (u:User)-[:FOLLOWS]->(following:User)
WITH u, count(following) AS followingCount
RETURN u.id, u.name, u.username, followingCount
ORDER BY followingCount DESC
LIMIT 10;


// GRAPH DATA SCIENCE (GDS) QUERIES

// Create graph projection for user network analysis
CALL gds.graph.project(
    'userNetwork',
    'User',
    'FOLLOWS',
    {}
);

// PageRank - Identify influential users
CALL gds.pageRank.stream('userNetwork')
YIELD nodeId, score
RETURN gds.util.asNode(nodeId).username AS username,
       gds.util.asNode(nodeId).name AS name,
       score
ORDER BY score DESC
LIMIT 10;

// Betweenness Centrality - Find bridge users
CALL gds.betweenness.stream('userNetwork')
YIELD nodeId, score
RETURN gds.util.asNode(nodeId).username AS username,
       gds.util.asNode(nodeId).name AS name,
       score
ORDER BY score DESC
LIMIT 10;

// Louvain Algorithm - Community detection
CALL gds.louvain.stream('userNetwork')
YIELD nodeId, communityId
RETURN communityId,
       collect(gds.util.asNode(nodeId).username) AS members,
       count(*) AS memberCount
ORDER BY memberCount DESC;

// Triangle Count - Network cohesion measurement
CALL gds.triangleCount.stream('userNetwork')
YIELD nodeId, triangleCount
RETURN gds.util.asNode(nodeId).username AS username,
       triangleCount
ORDER BY triangleCount DESC
LIMIT 10;

// Shortest Path - Find connection between two users
MATCH (source:User {username: 'alice_j'})
MATCH (target:User {username: 'noah_g'})
MATCH path = shortestPath((source)-[:FOLLOWS*]-(target))
RETURN [node IN nodes(path) | node.username] AS pathNodes,
       length(path) AS pathLength;

// Degree Centrality - Count direct connections
MATCH (u:User)
WITH u,
     count{(u)-[:FOLLOWS]->()} AS following,
     count{(u)<-[:FOLLOWS]-()} AS followers
RETURN u.username, following, followers, following + followers AS totalConnections
ORDER BY totalConnections DESC
LIMIT 10;

// Create undirected graph projection for path-finding algorithms
CALL gds.graph.project(
    'twitter_undirected',
    'User',
    {FOLLOWS: {orientation: 'UNDIRECTED'}}
);

// GDS Dijkstra Shortest Path - Find shortest path using GDS
MATCH (source:User {username: 'alice_j'})
MATCH (target:User {username: 'noah_g'})
CALL gds.shortestPath.dijkstra.stream('twitter_undirected', {
    sourceNode: source,
    targetNode: target
})
YIELD nodeIds, costs
RETURN [nodeId IN nodeIds | gds.util.asNode(nodeId).username] AS path,
       costs;

// Hop Distance Analysis - Find users within X degrees of separation
MATCH (u:User {username: 'alice_j'})
MATCH (other:User)
WHERE u <> other
WITH u, other,
     shortestPath((u)-[:FOLLOWS*..3]-(other)) AS path
WHERE path IS NOT NULL
RETURN other.username, length(path) AS hops
ORDER BY hops, other.username
LIMIT 20;

// GDS Write Operations - Store algorithm results as node properties

// Write PageRank scores to nodes
CALL gds.pageRank.write('userNetwork', {
    writeProperty: 'pagerank',
    maxIterations: 20,
    dampingFactor: 0.85
})
YIELD nodePropertiesWritten, ranIterations;

// Write Betweenness Centrality to nodes
CALL gds.betweenness.write('userNetwork', {
    writeProperty: 'betweenness'
})
YIELD nodePropertiesWritten, centralityDistribution;

// Write Louvain Community IDs to nodes
CALL gds.louvain.write('userNetwork', {
    writeProperty: 'community'
})
YIELD nodePropertiesWritten, communityCount;

// Write Triangle Counts to nodes
CALL gds.triangleCount.write('userNetwork', {
    writeProperty: 'triangles'
})
YIELD nodePropertiesWritten, globalTriangleCount;

// Query nodes with written properties
MATCH (u:User)
WHERE u.pagerank IS NOT NULL
RETURN u.username, u.pagerank, u.betweenness, u.community, u.triangles
ORDER BY u.pagerank DESC
LIMIT 10;

// Clean up graph projections
CALL gds.graph.drop('userNetwork');
CALL gds.graph.drop('twitter_undirected');
