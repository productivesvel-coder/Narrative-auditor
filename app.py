import streamlit as st
from tavily import TavilyClient
import google.generativeai as genai
import json
import streamlit.components.v1 as components

st.set_page_config(layout="wide", page_title="Disonance Engine 3D")

# API Keys
TAVILY_API_KEY = "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"
AI_ENGINE_KEY = "AIzaSyAbwTIkuJU4CkZdVpwCNmr3R4hfzml5AKs"

def fetch_news(query):
    # This layer bypasses the 'Scraping Wall' of major news outlets
    tavily = TavilyClient(api_key=TAVILY_API_KEY)
    response = tavily.search(query=query, search_depth="advanced", max_results=5)
    return response['results']

def generate_graph_data(news_results):
    genai.configure(api_key=AI_ENGINE_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    context = "\n".join([f"Source: {r['title']} - Content: {r['content']}" for r in news_results])
    
    # Strict JSON instruction for the Disonance Engine
    prompt = f"""
    [CONTEXT]
    {context}

    [TASK]
    As the Disonance Engine, perform a logical audit of the context.
    1. Extract 5 most critical 'Claim' nodes (group: 2).
    2. Extract 'Source' names as nodes (group: 1).
    3. Create links between Sources and Claims.
    4. Link Claims to each other ONLY if they logically 'CONTRADICTS' or 'SUPPORTS'.
    
    [OUTPUT]
    Return ONLY a valid JSON object. No conversational text. No markdown.
    Structure:
    {{
      "nodes": [{"id": "Node Name", "group": 1}],
      "links": [{"source": "Node A", "target": "Node B", "value": "CONTRADICTS"}]
    }}
    """
    
    # Using GenerationConfig to force JSON output and minimize errors
    response = model.generate_content(
        prompt, 
        generation_config={"response_mime_type": "application/json"}
    )
    
    return json.loads(response.text)

def render_3d_graph(data):
    graph_json = json.dumps(data)
    html_code = f"""
    <div id="graph" style="background: #0e1117;"></div>
    <script src="//cdn.jsdelivr.net/npm/3d-force-graph"></script>
    <script>
      const gData = {graph_json};
      const Graph = ForceGraph3D()
        (document.getElementById('graph'))
          .graphData(gData)
          .nodeAutoColorBy('group')
          .linkDirectionalParticles(2)
          .linkWidth(2)
          .linkLabel('value')
          .linkColor(link => link.value === 'CONTRADICTS' ? '#ff4b4b' : '#00ff7f');
          
      // Ensure the graph fits the window
      window.addEventListener('resize', () => Graph.width(window.innerWidth).height(600));
    </script>
    <style> body {{ margin: 0; overflow: hidden; }} </style>
    """
    components.html(html_code, height=600)

# UI Layout
st.title("🌐 Disonance Engine: 3D Narrative Auditor")
st.markdown("Mapping the logical landscape of global news consensus and contradiction.")

query = st.text_input("Enter a news event to analyze:", placeholder="e.g. Geopolitical tensions in 2026")

if st.button("Run Disonance Audit"):
    if not query:
        st.warning("Please enter a query first.")
    else:
        with st.spinner("Disonance Engine is auditing global narratives..."):
            try:
                # Stage 1: Search
                news = fetch_news(query)
                
                # Stage 2: Logical Audit
                graph_data = generate_graph_data(news)
                
                # Stage 3: Visual Synthesis
                st.subheader(f"Logical Map for: {query}")
                render_3d_graph(graph_data)
                
                # Stage 4: Documentation
                with st.expander("Audit Trail (Raw Data)"):
                    for item in news:
                        st.write(f"🔗 **[{item['title']}]({item['url']})**")
                        st.write(f"Snippet: {item['content'][:300]}...")
                        st.divider()
                        
            except Exception as e:
                # Detailed error logging for debugging
                st.error(f"Disonance Engine Error: {str(e)}")
                st.info("Check if your API keys are still active or if the query was too broad.")

st.sidebar.title("Disonance Engine Status")
st.sidebar.write("● Node Processing: **Active**")
st.sidebar.write("● Verification Layer: **Strict**")
st.sidebar.write("● Visualization: **3D Force-Directed**")
