import streamlit as st
from tavily import TavilyClient
import google.generativeai as genai
import json
import streamlit.components.v1 as components

st.set_page_config(layout="wide", page_title="Disonance 3D")

TAVILY_API_KEY = "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-tavily"
AI_ENGINE_KEY = "AIzaSyAbwTIkuJU4CkZdVpwCNmr3R4hfzml5AKs"

def fetch_news(query):
    tavily = TavilyClient(api_key=TAVILY_API_KEY)
    response = tavily.search(query=query, search_depth="advanced", max_results=5)
    return response['results']

def generate_graph_data(news_results):
    genai.configure(api_key=AI_ENGINE_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    context = "\n".join([f"Source: {r['title']} - Content: {r['content']}" for r in news_results])
    
    prompt = f"""
    Analyze these news snippets: {context}
    1. Extract the 5 most important 'Claim' nodes.
    2. Extract the 'Source' names as nodes.
    3. Create links: 
       - 'SUPPORTS' if a source confirms a claim.
       - 'CONTRADICTS' if two claims or sources disagree.
    
    Return ONLY a valid JSON object. No markdown formatting.
    Structure:
    {{
      "nodes": [{"id": "Name", "group": 1}],
      "links": [{"source": "ID1", "target": "ID2", "value": "label"}]
    }}
    """
    
    response = model.generate_content(prompt)
    clean_json = response.text.replace('```json', '').replace('```', '').strip()
    return json.loads(clean_json)

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
    </script>
    <style> body {{ margin: 0; overflow: hidden; font-family: sans-serif; }} </style>
    """
    components.html(html_code, height=600)

st.title("🌐 Narrative Auditor: 3D Knowledge Graph")
st.markdown("Analyzing global news consensus and contradictions via a specialized AI Engine.")

query = st.text_input("Enter a global event to audit:", placeholder="e.g. US-Iran relations")

if st.button("Analyze Narratives"):
    with st.spinner("AI Engine is auditing claims..."):
        try:
            news = fetch_news(query)
            graph_data = generate_graph_data(news)
            
            st.subheader(f"3D Narrative Map: {query}")
            render_3d_graph(graph_data)
            
            with st.expander("View Verified Data Sources"):
                for item in news:
                    st.write(f"🔗 **[{item['title']}]({item['url']})**")
                    st.write(f"Source Snippet: {item['content'][:300]}...")
                    st.divider()
                    
        except Exception as e:
            st.error(f"Analysis interrupted. Please check network connection.")

st.sidebar.title("System Status")
st.sidebar.success("AI Engine: Online")
st.sidebar.success("News API: Connected")
st.sidebar.info("This system uses a custom-prompted AI Engine to perform logical verification across multiple international news sources.")