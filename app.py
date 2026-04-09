import streamlit as st
from tavily import TavilyClient
import google.generativeai as genai
import json
import re
import streamlit.components.v1 as components

# --- 1. PAGE CONFIGURATION & CUSTOM CSS ---
st.set_page_config(layout="wide", page_title="Disonance Engine | Audit", initial_sidebar_state="expanded")

st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    .stTextInput input {
        border-radius: 8px;
        border: 1px solid #334155;
        padding: 12px;
        background-color: #0f172a;
        color: #f8fafc;
    }
    .stButton>button {
        border-radius: 8px;
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
        color: white;
        font-weight: 600;
        border: none;
        padding: 10px 24px;
        transition: all 0.3s ease;
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. SECURE CREDENTIALS ---
TAVILY_API_KEY = "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"
AI_ENGINE_KEY = "AIzaSyAJioZHv3AXVij5P5b3rHBEVlCDet3chGo"

# --- 3. CORE LOGIC ENGINE ---
def fetch_news(query):
    tavily = TavilyClient(api_key=TAVILY_API_KEY)
    response = tavily.search(query=query, search_depth="advanced", max_results=6)
    if not response.get('results'):
        raise ValueError("No verified news sources found for this query.")
    return response['results']

def extract_json_safely(text):
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        raise ValueError("AI Engine response format invalid.")

def generate_graph_data(news_results):
    genai.configure(api_key=AI_ENGINE_KEY)
    model = genai.GenerativeModel('gemini-2.5-flash-lite')
    
    context = "\n".join([f"[{r['title']}] - {r['content']}" for r in news_results])
    
    prompt = f"""
    [SYSTEM PROTOCOL: DISONANCE ENGINE]
    Analyze for logical consensus and dissonance.
    TASK:
    1. Extract 5 'Claim' nodes (group: 2).
    2. Extract 'Source' nodes (group: 1).
    3. Link using 'REPORTS', 'CONTRADICTS', or 'SUPPORTS'.
    4. Provide 'name' and 'description' for every node.
    OUTPUT RAW JSON ONLY.
    Context: {context}
    """
    
    response = model.generate_content(
        prompt, 
        generation_config={"response_mime_type": "application/json"}
    )
    
    raw_data = extract_json_safely(response.text)
    # Sanitize links
    node_ids = {node['id'] for node in raw_data.get('nodes', [])}
    raw_data['links'] = [l for l in raw_data.get('links', []) if l.get('source') in node_ids and l.get('target') in node_ids]
    return raw_data

# --- 4. 3D VISUAL SYNTHESIS ---
def render_3d_graph(data):
    graph_json = json.dumps(data)
    html_code = f"""
    <div id="graph-wrapper" style="position: relative; border-radius: 12px; background: #0B0F19; overflow: hidden; height: 650px;">
        <div id="loading-overlay" style="position: absolute; top:50%; left:50%; transform:translate(-50%, -50%); color: #3b82f6; font-family: sans-serif; z-index: 5;">
            Initializing Neural Topology...
        </div>
        
        <div id="info-panel" style="position: absolute; top: 15px; right: 15px; width: 300px; background: rgba(15, 23, 42, 0.95); backdrop-filter: blur(10px); color: white; padding: 20px; border-radius: 12px; display: none; border: 1px solid #334155; z-index: 100;">
            <h3 id="info-title" style="margin: 0; color: #60a5fa; font-size: 18px;"></h3>
            <p id="info-desc" style="font-size: 14px; color: #e2e8f0;"></p>
            <button onclick="this.parentElement.style.display='none'" style="margin-top:10px; background:#334155; color:white; border:none; padding:5px 10px; border-radius:4px; cursor:pointer;">Close</button>
        </div>

        <div id="graph" style="width: 100%; height: 100%;"></div>
    </div>
    
    <script src="https://unpkg.com/three"></script>
    <script src="https://unpkg.com/three-spritetext"></script>
    <script src="https://unpkg.com/3d-force-graph"></script>
    
    <script>
      window.onload = function() {{
        try {{
          const gData = {graph_json};
          const elem = document.getElementById('graph');
          
          const Graph = ForceGraph3D()(elem)
              .graphData(gData)
              .nodeAutoColorBy('group')
              .nodeThreeObjectExtend(true)
              .nodeThreeObject(node => {{
                  const sprite = new SpriteText(node.name || node.id);
                  sprite.color = '#f8fafc';
                  sprite.textHeight = 4;
                  return sprite;
              }})
              .onNodeClick(node => {{
                  document.getElementById('info-panel').style.display = 'block';
                  document.getElementById('info-title').innerText = node.name || node.id;
                  document.getElementById('info-desc').innerText = node.description || 'No data.';
              }})
              .linkColor(link => {{
                  if (link.value === 'CONTRADICTS') return '#ff3333';
                  if (link.value === 'SUPPORTS') return '#00ff66';
                  return '#64748b';
              }})
              .linkWidth(link => link.value === 'CONTRADICTS' ? 4 : 1)
              .backgroundColor('#0B0F19');

          document.getElementById('loading-overlay').style.display = 'none';
        }} catch (err) {{
          document.getElementById('loading-overlay').innerHTML = "WebGL Error: " + err.message;
        }}
      }};
    </script>
    """
    components.html(html_code, height=660)

# --- 5. USER INTERFACE ---
st.title("Disonance Engine")
query = st.text_input("Target Subject / Event", placeholder="Enter geopolitical event to audit...")

if st.button("Initialize Logic Audit"):
    if not query.strip():
        st.warning("Query required.")
    else:
        status_placeholder = st.empty()
        with status_placeholder.status("Processing Audit...", expanded=True) as status:
            news = fetch_news(query)
            graph_data = generate_graph_data(news)
            status.update(label="Audit Complete", state="complete", expanded=False)
        
        st.markdown("### Topology Map")
        render_3d_graph(graph_data)
        
        st.markdown("### Data Ledger")
        for item in news:
            with st.expander(item['title']):
                st.caption(item['url'])
                st.write(item['content'])
with st.sidebar:
    st.markdown("### System Telemetry")
    st.markdown("---")
    st.write("🟢 **Data Fetcher:** Active")
    st.write("🟢 **AI Engine:** Operational")
    st.write("🟢 **Render Engine:** WebGL 3D")
    st.markdown("---")
    st.caption("Dissonance Metrics:")
    st.markdown("<span style='color: #ff3333; font-weight: bold;'>█</span> CONTRADICTION (Conflict)", unsafe_allow_html=True)
    st.markdown("<span style='color: #00ff66; font-weight: bold;'>█</span> SUPPORT (Consensus)", unsafe_allow_html=True)
    st.markdown("<span style='color: #64748b; font-weight: bold;'>█</span> REPORT (Neutral Link)", unsafe_allow_html=True)
