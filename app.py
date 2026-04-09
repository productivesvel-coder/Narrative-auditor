import streamlit as st
from tavily import TavilyClient
import google.generativeai as genai
import json
import streamlit.components.v1 as components

st.set_page_config(layout="wide", page_title="Disonance Engine 3D")

TAVILY_API_KEY = "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"
AI_ENGINE_KEY = "AIzaSyAbwTIkuJU4CkZdVpwCNmr3R4hfzml5AKs"

def fetch_news(query):
    tavily = TavilyClient(api_key=TAVILY_API_KEY)
    response = tavily.search(query=query, search_depth="advanced", max_results=5)
    return response['results']

def generate_graph_data(news_results):
    genai.configure(api_key=AI_ENGINE_KEY)
    # Targetting the specific 2.5 Flash stable model
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    context = "\n".join([f"Source: {r['title']} - Content: {r['content']}" for r in news_results])
    
    prompt = f"""
    Analyze this context: {context}
    
    You are the Disonance Engine. Create a 3D knowledge map JSON.
    1. Nodes: 5 'Claim' (group 2) and 'Source' names (group 1).
    2. Links: 'SUPPORTS' or 'CONTRADICTS'.
    
    Output ONLY raw JSON. No markdown.
    {{
      "nodes": [{{ "id": "Name", "group": 1 }}],
      "links": [{{ "source": "ID1", "target": "ID2", "value": "label" }}]
    }}
    """
    
    response = model.generate_content(
        prompt, 
        generation_config={{"response_mime_type": "application/json"}}
    )
    
    return json.loads(response.text)

def render_3d_graph(data):
    graph_json = json.dumps(data)
    html_code = f"""
    <div id="graph" style="background: #0e1117; width: 100vw; height: 600px;"></div>
    <script src="//cdn.jsdelivr.net/npm/3d-force-graph"></script>
    <script>
      const gData = {graph_json};
      const Graph = ForceGraph3D()
        (document.getElementById('graph'))
          .graphData(gData)
          .nodeAutoColorBy('group')
          .linkDirectionalParticles(3)
          .linkWidth(2)
          .linkLabel('value')
          .linkColor(link => link.value === 'CONTRADICTS' ? '#ff4b4b' : '#00ff7f')
          .backgroundColor('#0e1117');
    </script>
    <style> body {{ margin: 0; background: #0e1117; }} </style>
    """
    components.html(html_code, height=600)

st.title("🌐 Disonance Engine: 3D Narrative Auditor")
st.markdown("Auditing narratives with Gemini 2.5 Flash architecture.")

query = st.text_input("Enter a query for the Disonance Engine:", placeholder="e.g. AI ethics debate")

if st.button("Initialize Engine"):
    if not query:
        st.error("Please enter a query.")
    else:
        with st.spinner("Analyzing data with 2.5 Flash..."):
            try:
                news = fetch_news(query)
                graph_data = generate_graph_data(news)
                
                st.subheader(f"3D Logical Audit: {query}")
                render_3d_graph(graph_data)
                
                with st.expander("Data Sources"):
                    for item in news:
                        st.write(f"📂 **{item['title']}**")
                        st.caption(item['url'])
                        st.divider()
                        
            except Exception as e:
                st.error(f"Disonance Engine Error: {str(e)}")

st.sidebar.title("Engine Metrics")
st.sidebar.metric("Status", "Operational")
st.sidebar.write("Core: **Gemini 2.5 Flash**")
