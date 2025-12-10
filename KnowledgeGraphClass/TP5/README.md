# TP5: Knowledge Graph RAG with Ollama & LangChain

Building intelligent knowledge graphs from unstructured text using LLMs, Neo4j, and LangChain.

## 📋 Overview

This project demonstrates how to:
- Extract structured data (entities and relationships) from unstructured Wikipedia articles
- Build a knowledge graph automatically using AI
- Query the graph using natural language instead of Cypher
- Create a Retrieval-Augmented Generation (RAG) system combining structured and unstructured data

## 🛠 Technologies

- **Neo4j 5.20 Enterprise** - Graph database with APOC, GDS, and Bloom plugins
- **Ollama** - Local LLM runtime (llama3:8b)
- **LangChain** - LLM application framework
- **Diffbot API** - Entity and relationship extraction
- **Wikipedia API** - Source of unstructured text data
- **Docker** - Container orchestration
- **Jupyter Lab** - Interactive analysis environment
- **Python 3.13** - Implementation language

## 🚀 Quick Start

### Prerequisites

1. **Docker Desktop** - Install from [docker.com](https://www.docker.com/products/docker-desktop)
2. **Ollama** - Install from [ollama.ai](https://ollama.ai/)
3. **Diffbot API Key** (optional) - Get free key from [diffbot.com](https://www.diffbot.com/)

### Step 1: Setup Ollama

```bash
# Install Ollama (if not already installed)
# Visit: https://ollama.ai/

# Pull the recommended model
ollama pull llama3:8b

# Verify it's running
ollama list
```

### Step 2: Configure Environment

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your Diffbot API key (optional)
# If you don't have a Diffbot key, the system will use mock data
nano .env
```

### Step 3: Start Services

```bash
# Start all containers
docker-compose up -d

# Wait for services to be ready (about 30 seconds)
./scripts/check_containers.sh
```

### Step 4: Load Data

```bash
# Load Wikipedia articles and extract entities
docker exec tp5-jupyter python /workspace/load_data.py
```

Expected output:
```
✓ Connected to Neo4j at bolt://neo4j:7687
📐 Creating Neo4j schema...
✓ Schema created successfully

📚 Fetching Wikipedia article: Albert Einstein
✓ Fetched article: Albert Einstein
📊 Database Statistics:
  • Articles: 3
  • Entities: 45
  • Relationships: 48
```

### Step 5: Access Services

- **Jupyter Lab**: http://localhost:8888
- **Neo4j Browser**: http://localhost:7474 (neo4j / password123)

Open the notebook: [knowledge_graph_rag.ipynb](http://localhost:8888/lab/tree/knowledge_graph_rag.ipynb)

## 📊 Data Model

### Node Types

- **Article** - Wikipedia articles
  - Properties: `title`, `url`, `summary`, `loaded_at`

- **Entity** - Extracted entities (with dynamic labels)
  - Properties: `name`, `type`, `salience`
  - Labels: `Person`, `Organization`, `Location`, `Entity`

### Relationship Types

- **MENTIONS** - Article → Entity
  - Properties: `salience` (importance score)

### Example Graph Structure

```
(Article:Albert Einstein)-[:MENTIONS {salience: 0.95}]->(Entity:Person:Einstein)
(Article:Albert Einstein)-[:MENTIONS {salience: 0.87}]->(Entity:Organization:Princeton)
(Article:Albert Einstein)-[:MENTIONS {salience: 0.76}]->(Entity:Location:Germany)
```

## 💻 Usage

### Option 1: Interactive Notebook (Recommended)

Open Jupyter Lab at http://localhost:8888 and run through the notebook sections:

1. **Setup** - Configure connections and test services
2. **Explore** - Examine the loaded knowledge graph
3. **Visualize** - Create interactive graph visualizations
4. **Query** - Run Cypher queries for analysis
5. **Natural Language** - Ask questions in plain English
6. **RAG** - Combine graph queries with article context

### Option 2: Python Script

```bash
# Load data programmatically
docker exec tp5-jupyter python /workspace/load_data.py

# Run custom queries
docker exec tp5-jupyter python -c "
from neo4j import GraphDatabase
driver = GraphDatabase.driver('bolt://neo4j:7687', auth=('neo4j', 'password123'))
with driver.session() as session:
    result = session.run('MATCH (e:Entity) RETURN e.name LIMIT 5')
    for record in result:
        print(record['e.name'])
driver.close()
"
```

### Option 3: Neo4j Browser

Access http://localhost:7474 and run Cypher queries directly:

```cypher
// Get all articles
MATCH (a:Article)
RETURN a.title, a.url

// Find most mentioned entities
MATCH (a:Article)-[m:MENTIONS]->(e:Entity)
WITH e, count(a) as mentions, avg(m.salience) as avg_salience
ORDER BY mentions DESC, avg_salience DESC
RETURN e.name, e.type, mentions, round(avg_salience, 3) as salience
LIMIT 10

// Find entities mentioned in multiple articles
MATCH (a:Article)-[:MENTIONS]->(e:Entity)
WITH e, collect(DISTINCT a.title) as articles
WHERE size(articles) > 1
RETURN e.name, e.type, articles
```

## 📈 Analysis Features

### 1. Entity Extraction

The system automatically extracts:
- **People** - Names of individuals
- **Organizations** - Companies, institutions, groups
- **Locations** - Countries, cities, places
- **Other entities** - Concepts, events, etc.

### 2. Natural Language Querying

Ask questions in plain English:

```python
# In the notebook
ask_graph("How many articles are in the knowledge graph?")
ask_graph("What are the names of all the people mentioned?")
ask_graph("Which articles mention organizations?")
ask_graph("What are the most frequently mentioned entities?")
```

### 3. RAG (Retrieval-Augmented Generation)

Combine structured graph data with unstructured article content:

```python
# In the notebook
rag_query("What are the main topics covered and how are they related?")
```

### 4. Entity Summarization

Get comprehensive information about any entity:

```python
# In the notebook
summarize_entity("Albert Einstein")
```

Output:
```
📌 Entity: Albert Einstein
   Type: Person
   Mentioned in 1 article(s)
   Average salience: 0.950
   Articles: Albert Einstein
```

## 📁 Project Structure

```
TP5/
├── app/
│   ├── Dockerfile                    # Jupyter environment setup
│   ├── pyproject.toml               # Python dependencies
│   ├── load_data.py                 # Data loading script
│   └── knowledge_graph_rag.ipynb   # Main analysis notebook
├── neo4j/
│   ├── data/                        # Neo4j database files (gitignored)
│   ├── logs/                        # Neo4j logs
│   └── import/                      # Import directory for CSV files
├── scripts/
│   └── check_containers.sh          # Health check script
├── media/                           # Screenshots and visualizations
├── docker-compose.yml               # Container orchestration
├── .env.example                     # Environment variables template
├── .gitignore                       # Git ignore rules
└── README.md                        # This file
```

## 🔍 Example Queries

### Cypher Queries

```cypher
-- 1. Entity type distribution
MATCH (e:Entity)
RETURN e.type as entity_type, count(e) as count
ORDER BY count DESC

-- 2. Most salient entities per article
MATCH (a:Article)-[m:MENTIONS]->(e:Entity)
WITH a, e, m.salience as salience
ORDER BY a.title, salience DESC
WITH a.title as article, collect({entity: e.name, type: e.type})[0..5] as top_entities
RETURN article, top_entities

-- 3. Entity co-occurrence (entities in same articles)
MATCH (e1:Entity)<-[:MENTIONS]-(a:Article)-[:MENTIONS]->(e2:Entity)
WHERE id(e1) < id(e2)
WITH e1.name as entity1, e2.name as entity2, count(DISTINCT a) as shared_articles
WHERE shared_articles > 1
RETURN entity1, entity2, shared_articles
ORDER BY shared_articles DESC
LIMIT 10
```

### Natural Language Questions

- "How many people are mentioned in the knowledge graph?"
- "List all organizations mentioned in the articles"
- "What entities are mentioned in multiple articles?"
- "Which article mentions the most entities?"
- "What are the most salient entities across all articles?"

## 🎨 Visualizations

The notebook generates several visualizations:

1. **Graph Statistics Chart** ([media/graph_statistics.png](media/graph_statistics.png))
   - Bar chart showing counts of nodes and relationships

2. **Entity Type Distribution** ([media/entity_type_distribution.png](media/entity_type_distribution.png))
   - Pie chart showing distribution of entity types

3. **Interactive Knowledge Graph** ([media/knowledge_graph.html](media/knowledge_graph.html))
   - Interactive network visualization (open in browser)

## 🐛 Troubleshooting

### Issue: Ollama connection fails

```bash
# Check Ollama is running
ollama list

# On macOS/Linux, Ollama runs on localhost:11434
curl http://localhost:11434/api/tags

# If using Docker Desktop, ensure host.docker.internal is accessible
docker exec tp5-jupyter curl http://host.docker.internal:11434/api/tags
```

### Issue: Neo4j connection fails

```bash
# Check Neo4j logs
docker logs tp5-neo4j --tail 50

# Restart Neo4j
docker-compose restart neo4j

# Wait for health check
./scripts/check_containers.sh
```

### Issue: Diffbot API errors

The system will automatically fall back to mock data if Diffbot is unavailable:

```bash
# Check your API key in .env
cat .env | grep DIFFBOT_API_KEY

# Test Diffbot API
curl "https://nl.diffbot.com/v1/?token=YOUR_API_KEY&content=test"
```

### Issue: Python dependencies missing

```bash
# Rebuild the Jupyter container
docker-compose build --no-cache jupyter
docker-compose up -d jupyter
```

### Issue: No data in Neo4j

```bash
# Re-run the data loading script
docker exec tp5-jupyter python /workspace/load_data.py

# Check data was loaded
docker exec tp5-neo4j cypher-shell -u neo4j -p password123 \
  "MATCH (a:Article) RETURN count(a) AS articles;"
```

## 🔧 Configuration

### Environment Variables (.env)

```bash
# Neo4j Configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password123

# Ollama Configuration
OLLAMA_BASE_URL=http://host.docker.internal:11434
OLLAMA_MODEL=llama3:8b

# Diffbot API (optional)
DIFFBOT_API_KEY=your_api_key_here

# Wikipedia Topics (comma-separated)
WIKIPEDIA_TOPICS=Albert Einstein,Marie Curie,Isaac Newton
```

### Customizing Topics

Edit `.env` to change which Wikipedia articles are processed:

```bash
# Single topic
WIKIPEDIA_TOPICS=Artificial Intelligence

# Multiple topics
WIKIPEDIA_TOPICS=Machine Learning,Neural Networks,Deep Learning

# People
WIKIPEDIA_TOPICS=Alan Turing,Ada Lovelace,Grace Hopper
```

Then reload the data:

```bash
# Clear existing data (optional)
docker exec tp5-neo4j cypher-shell -u neo4j -p password123 "MATCH (n) DETACH DELETE n;"

# Load new topics
docker exec tp5-jupyter python /workspace/load_data.py
```

## 🧪 Testing

```bash
# Run health checks
./scripts/check_containers.sh

# Test Neo4j connection
docker exec tp5-jupyter python -c "
from neo4j import GraphDatabase
driver = GraphDatabase.driver('bolt://neo4j:7687', auth=('neo4j', 'password123'))
with driver.session() as session:
    result = session.run('RETURN 1 AS test')
    print(f'✓ Neo4j connection successful: {result.single()[\"test\"]}')
driver.close()
"

# Test Ollama connection
curl http://localhost:11434/api/tags
```

## 📚 Resources

- [Neo4j Documentation](https://neo4j.com/docs/)
- [LangChain Documentation](https://python.langchain.com/docs/get_started/introduction)
- [Ollama Documentation](https://github.com/ollama/ollama/blob/main/docs/api.md)
- [Diffbot API Documentation](https://docs.diffbot.com/)
- [Wikipedia API Documentation](https://wikipedia-api.readthedocs.io/)

## 🎓 Learning Objectives

By completing this TP, you will learn:

1. **Unstructured Data Processing**
   - Extract structured information from natural language text
   - Use LLMs for entity and relationship extraction

2. **Knowledge Graph Construction**
   - Build graphs automatically from unstructured sources
   - Design flexible schemas for dynamic entity types

3. **LLM Integration**
   - Use LangChain to orchestrate LLM workflows
   - Run local LLMs with Ollama

4. **Natural Language Querying**
   - Convert natural language questions to Cypher queries
   - Build question-answering systems over graphs

5. **RAG Systems**
   - Combine structured (graph) and unstructured (text) data
   - Implement retrieval-augmented generation pipelines

## 📝 Assignment Questions

### Question 1: Data Extraction
How many entities were extracted from your Wikipedia articles? What is the distribution by entity type?

**Answer**: See [media/graph_statistics.png](media/graph_statistics.png) and [media/entity_type_distribution.png](media/entity_type_distribution.png)

### Question 2: Entity Analysis
What are the top 5 most mentioned entities across all articles? Why do you think they have high salience?

**Answer**: Run the "Top 10 Entities Overall" cell in the notebook.

### Question 3: Natural Language Querying
Provide 3 examples of natural language questions you asked the knowledge graph and the Cypher queries that were generated.

**Answer**: See Section 7 in the notebook.

### Question 4: RAG Implementation
Explain how the RAG system combines structured graph data with unstructured article content. What are the advantages of this approach?

**Answer**: See Section 9 in the notebook and the `rag_query()` function.

### Question 5: Graph Insights
What interesting relationships or patterns did you discover in your knowledge graph? Provide specific examples.

**Answer**: See Section 4 (Cypher Query Exploration) in the notebook.

## 🤝 Contributing

This is an educational project for a knowledge graph class. Improvements and extensions are welcome!

## 📄 License

Educational use only.

## ✨ Acknowledgments

- Course: Knowledge Graphs (NoSQL)
- Instructor: [Course Instructor Name]
- Institution: [University Name]
- Resources: [Neo4j Blog Post on Unstructured Knowledge Graphs](https://neo4j.com/blog/developer/unstructured-knowledge-graph-neo4j-langchain/)
