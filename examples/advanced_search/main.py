from pymed import PubMed

# Create a PubMed object for querying
# Note that the parameters are not required but kindly requested by PubMed Central
# https://www.ncbi.nlm.nih.gov/pmc/tools/developers/
pubmed = PubMed(tool="MyTool", email="my@email.address")

# Create a query in plain text
query = (
    '(("2018/05/01"[Date - Create] : "3000"[Date - Create])) '
    "AND (Xiaoying Xian[Author] OR diabetes)"
)

# Execute the query against the API
results = pubmed.query(query, max_results=500)

# Loop over the retrieved articles
for article in results:
    # Extract and format information from the article
    article_id = article.pubmed_id
    title = article.title
    keywords_list = [keyword for keyword in getattr(article, "keywords", []) if keyword]
    keywords = '", "'.join(keywords_list)
    publication_date = article.publication_date
    abstract = article.abstract

    # Show information about the article
    print(
        f"{article_id} - {publication_date} - {title}\n"
        f'Keywords: "{keywords}"\n{abstract}\n'
    )
