# YFinance Chatbot 📈

An advanced AI-powered financial assistant for stock market analysis, news aggregation, and intelligent insights. Built with FastAPI, Streamlit, Plotly, OpenSearch, and Google Gemini 2.0 Flash.

## Features

### Core Capabilities
- 🤖 **AI-Powered Conversations** - Natural language queries powered by Google Gemini 2.0 Flash
- � ***Interactive Chatbot** - Ask any question about stocks, investing, or market analysis
- 📊 **Dynamic Charts** - Multiple chart types: candlestick, line, volume, dividends, scatter plots, heatmaps, and comparison charts
- 🎯 **Smart Suggestions** - Persistent follow-up question recommendations after each query
- ⚡ **Quick Actions** - One-click buttons for common queries
- � **CReal-time Data** - Live stock data from Yahoo Finance

### Advanced Features
- � **Naews Aggregation** - Real-time financial news from SerpAPI with AI-powered summaries
- 🔍 **RAG System** - Semantic search using OpenSearch vector database with sentence transformers
- 📈 **Market Overview** - Live market indices (S&P 500, Dow Jones, NASDAQ) with performance tracking
- 💹 **Stock Comparison** - Compare multiple stocks side-by-side with interactive charts
- 🎨 **Modular UI** - Clean component-based architecture with sidebar, news feed, and market overview
- ⚡ **Performance Optimized** - 5-minute caching system reducing response times by 98% (from 15-25s to 276ms)
- 🚀 **Batch Processing** - Smart AI usage with batch operations for efficiency
- 💾 **History Tracking** - Save all queries to NocoDB

## Project Structure

```
yfinance-chatbot/
├── backend/
│   ├── main.py                    # FastAPI server with caching & optimization
│   ├── opensearch_client.py       # Vector database integration
│   ├── requirements.txt           # Backend dependencies
│   └── .env                       # Environment variables (not in git)
├── frontend/
│   ├── app.py                     # Main Streamlit app
│   ├── components/
│   │   ├── chat_interface.py     # Chat UI component
│   │   ├── sidebar.py            # Sidebar with stock selector
│   │   ├── news_feed.py          # News aggregation component
│   │   ├── market_overview.py   # Market indices display
│   │   └── charts.py             # Dynamic chart generation
│   └── requirements.txt          # Frontend dependencies
└── README.md
```

## Setup

### 1. Install Dependencies

**Backend:**
```bash
cd backend
pip install -r requirements.txt
```

**Frontend:**
```bash
cd frontend
pip install -r requirements.txt
```

### 2. Configure API Keys

Create a `backend/.env` file with the following:

```env
# Required
GEMINI_API_KEY=your_gemini_api_key_here

# Optional - for news features
SERPAPI_API_KEY=your_serpapi_key_here

# Optional - for OpenSearch RAG
OPENSEARCH_HOST=localhost
OPENSEARCH_PORT=9200
OPENSEARCH_USER=admin
OPENSEARCH_PASSWORD=admin

# Optional - for NocoDB history
NOCODB_API_TOKEN=your_nocodb_token
NOCODB_TABLE_ID=your_table_id
NOCODB_BASE_URL=http://localhost:8080
```

**Get API Keys:**
- Gemini API: [Google AI Studio](https://makersuite.google.com/app/apikey)
- SerpAPI: [SerpAPI Dashboard](https://serpapi.com/manage-api-key)

### 3. Configure OpenSearch (Optional - for RAG)

Run OpenSearch with Docker:
```bash
docker run -d -p 9200:9200 -p 9600:9600 -e "discovery.type=single-node" -e "OPENSEARCH_INITIAL_ADMIN_PASSWORD=Admin@123" opensearchproject/opensearch:latest
```

The RAG system will automatically create the necessary index on first use.

### 4. Configure NocoDB (Optional - for history)

1. Install and run NocoDB:
```bash
docker run -d --name nocodb -p 8080:8080 nocodb/nocodb:latest
```

2. Create a new table with these fields:
   - `question` (SingleLineText)
   - `ticker` (SingleLineText)
   - `timestamp` (DateTime)
   - `response` (LongText)

3. Get your API token and table ID from NocoDB

4. Update `backend/.env` with your NocoDB credentials

### 5. Run the Application

**Start Backend (Terminal 1):**
```bash
cd backend
python main.py
```
The API will be available at `http://localhost:8000`

**Start Frontend (Terminal 2):**
```bash
cd frontend
streamlit run app.py
```
The app will open in your browser at `http://localhost:8501`

## Usage

### Basic Usage
1. Enter a stock ticker in the sidebar (e.g., AAPL, GOOGL, MSFT)
2. Select a time period
3. View real-time market overview and latest news
4. Ask questions in natural language

### Advanced Features
- **News Feed**: Get AI-summarized financial news for any stock
- **Stock Comparison**: Compare multiple stocks with "compare AAPL vs GOOGL"
- **Custom Charts**: Request scatter plots, heatmaps, or performance analysis
- **RAG Search**: Ask questions and get context from historical conversations
- **Market Overview**: Track S&P 500, Dow Jones, and NASDAQ in real-time

## Example Questions

The chatbot can handle a wide variety of questions:

**Basic Queries:**
- "Show me the price chart"
- "What's the current price?"
- "Tell me about this company"
- "Show me the latest news"

**Analysis & Insights:**
- "How has this stock performed this year?"
- "Is this stock overvalued?"
- "Give me a detailed analysis"
- "What's the P/E ratio?"
- "Compare to the 52-week high"

**Comparison & Advanced Charts:**
- "Compare AAPL vs GOOGL"
- "Show me a scatter plot of price vs volume"
- "Create a heatmap of returns"
- "Show performance comparison with MSFT and TSLA"

**Market Data:**
- "Show me the trading volume"
- "What are the dividends?"
- "What sector is this in?"
- "Show me the price trend"

**News & Sentiment:**
- "What's the latest news about this stock?"
- "Summarize recent developments"
- "What are analysts saying?"

**Investment Questions:**
- "Should I invest in this stock?"
- "What are the risks?"
- "Explain the recent trend"
- "How volatile is this stock?"

## API Endpoints

- `GET /` - Health check
- `POST /query` - Process natural language query with caching
- `GET /history` - Get query history from NocoDB
- `GET /news/{ticker}` - Get latest news for a stock with AI summaries
- `POST /rag/store` - Store conversation in vector database
- `POST /rag/search` - Semantic search through conversation history
- `GET /market-overview` - Get current market indices data

## Technologies

- **AI**: Google Gemini 2.0 Flash
- **Backend**: FastAPI, YFinance, Pandas, SerpAPI
- **Frontend**: Streamlit, Plotly (multiple chart types)
- **Vector Database**: OpenSearch with sentence-transformers
- **Database**: NocoDB (optional)
- **Data Sources**: Yahoo Finance, SerpAPI News
- **Caching**: In-memory with 5-minute TTL
- **Performance**: Batch processing, smart AI usage optimization

## Performance

The application includes several optimizations:
- **5-minute caching**: Reduces repeated API calls
- **98% faster responses**: From 15-25s to 276ms for cached queries
- **Batch processing**: Efficient data handling
- **Smart AI usage**: Minimizes unnecessary Gemini API calls

## Notes

- **Optional Services**: SerpAPI, OpenSearch, and NocoDB are optional - the core app works without them
- **API Keys**: Only Gemini API key is required for basic functionality
- **Ports**: Backend runs on 8000, Frontend on 8501
- **Caching**: First query may be slow, subsequent queries are much faster
- **News**: Requires SerpAPI key for news aggregation feature
- **RAG**: Requires OpenSearch for semantic search capabilities

## License

MIT
