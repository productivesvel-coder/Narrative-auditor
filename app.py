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
    .stButton>button:hover {
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
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
        raise ValueError("The AI Engine response was not in a valid JSON format.")

def generate_graph_data(news_results):
    genai.configure(api_key=AI_ENGINE_KEY)
    model = genai.GenerativeModel('gemini-2.5-flash-lite')
    
    context = "\n".join([f"[{r['title']}] - {r['content']}" for r in news_results])
    
    prompt = f"""
    [SYSTEM PROTOCOL: DISONANCE ENGINE]
    Analyze the provided global news context for logical consensus and dissonance.
    
    TASK:
    1. Extract exactly 5 'Claim' nodes (group: 2).
    2. Extract 'Source' names as nodes (group: 1).
    3. Link sources to claims using 'REPORTS'.
    4. Link claims to each other using 'CONTRADICTS' or 'SUPPORTS'.
    
    CRITICAL: For every node, provide a concise 'name' (visible title) and a detailed 'description' (contextual summary).
    
    OUTPUT FORMAT: RAW JSON ONLY.
    {{
      "nodes": [{{ "id": "String", "name": "String", "description": "String", "group": 1 }}],
      "links": [{{ "source": "String", "target": "String", "value": "String" }}]
    }}
    
    [CONTEXT]
    {context}
    """
    
    response = model.generate_content(
        prompt, 
        generation_config={"response_mime_type": "application/json"}
    )
    
    raw_data = extract_json_safely(response.text)
    node_ids = {node['id'] for node in raw_data.get('nodes', [])}
    if 'links' in raw_data:
        raw_data['links'] = [
            link for link in raw_data['links'] 
            if link.get('source') in node_ids and link.get('target') in node_ids
        ]
    else:
        raw_data['links'] = []
        
    return raw_data

# --- 4. 3D VISUAL SYNTHESIS ---
def render_3d_graph(data):
    graph_json = json.dumps(data)
    html_code = f"""
    <div id="graph-container" style="position: relative; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.5);">
        
        <div id="info-panel" style="position: absolute; top: 15px; right: 15px; width: 320px; background: rgba(15, 23, 42, 0.9); backdrop-filter: blur(12px); color: white; padding: 20px; border-radius: 12px; display: none; border: 1px solid #334155; z-index: 100; box-shadow: 0 10px 25px rgba(0,0,0,0.5);">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px;">
                <h3 id="info-title" style="margin: 0; color: #60a5fa; font-size: 18px; font-family: 'Inter', sans-serif;"></h3>
                <button onclick="document.getElementById('info-panel').style.display='none'" style="background: none; border: none; color: #94a3b8; cursor: pointer; font-size: 18px;">✖</button>
            </div>
            <p id="info-desc" style="font-size: 14px; line-height: 1.6; color: #e2e8f0; font-family: 'Inter', sans-serif; margin-bottom: 15px;"></p>
            <div style="font-size: 11px; color: #94a3b8; font-family: 'Inter', sans-serif; text-transform: uppercase; letter-spacing: 1px; border-top: 1px solid #334155; padding-top: 10px;">
                Classification: <strong id="info-group" style="color: #cbd5e1;"></strong>
            </div>
        </div>

        <div id="graph" style="width: 100%; height: 70vh; background: #0B0F19;"></div>
    </div>
    
    <script src="//unpkg.com/three"></script>
    <script src="//unpkg.com/three-spritetext"></script>
    <script src="//unpkg.com/3d-force-graph"></script>
    
    <script>
      const gData = {graph_json};
      const elem = document.getElementById('graph');
      
      const Graph = ForceGraph3D()(elem)
          .graphData(gData)
          .nodeAutoColorBy('group')
          .nodeRelSize(8)
          
          .nodeThreeObjectExtend(true)
          .nodeThreeObject(node => {{
              const sprite = new SpriteText(node.name || node.id);
              sprite.color = '#f8fafc';
              sprite.textHeight = 4.5;
              sprite.center = new THREE.Vector2(0.5, -1.5);
              return sprite;
          }})
          
          .onNodeClick(node => {{
              document.getElementById('info-panel').style.display = 'block';
              document.getElementById('info-title').innerText = node.name || node.id;
              document.getElementById('info-desc').innerText = node.description || 'No additional data compiled for this entity.';
              document.getElementById('info-group').innerText = node.group === 1 ? 'NEWS SOURCE' : 'EXTRACTED CLAIM';
              
              const distance = 100;
              const distRatio = 1 + distance/Math.hypot(node.x, node.y, node.z);
              Graph.cameraPosition(
                  {{ x: node.x * distRatio, y: node.y * distRatio, z: node.z * distRatio }},
                  node, 
                  1500
              );
          }})
          
          .linkDirectionalParticles(link => link.value === 'CONTRADICTS' ? 8 : 3)
          .linkDirectionalParticleSpeed(link => link.value === 'CONTRADICTS' ? 0.02 : 0.008)
          .linkWidth(link => link.value === 'CONTRADICTS' ? 5 : (link.value === 'SUPPORTS' ? 3 : 1))
          .linkColor(link => {{
              if (link.value === 'CONTRADICTS') return '#ff3333';
              if (link.value === 'SUPPORTS') return '#00ff66';
              return '#64748b';
          }})
          .backgroundColor('#0B0F19');
          
      window.addEventListener('resize', () => {{
          Graph.width(elem.clientWidth).height(elem.clientHeight);
      }});
    </script>
    <style> body {{ margin: 0; background: transparent; overflow: hidden; }} </style>
    """
    components.html(html_code, height=650)

# --- 5. USER INTERFACE ---
col1, col2 = st.columns([3, 1])

with col1:
    st.title("Disonance Engine")
    st.markdown("<p style='color: #94a3b8; font-size: 1.1rem;'>Audit global narrative topology and logic contradictions in real-time.</p>", unsafe_allow_html=True)

query = st.text_input("Target Subject / Event", placeholder="Enter geopolitical event or global narrative to audit...")

if st.button("Initialize Logic Audit"):
    if not query.strip():
        st.warning("Target subject required.")
    else:
        # Define placeholders so the results appear immediately after analysis
        status_container = st.empty()
        results_container = st.container()
        
        with status_container:
            with st.status("Deploying Disonance Engine...", expanded=True) as status:
                try:
                    st.write("📡 Scanning global intelligence sources...")
                    news = fetch_news(query)
                    
                    st.write("🧠 AI Engine mapping logical dissonance...")
                    graph_data = generate_graph_data(news)
                    
                    status.update(label="Audit Finalized", state="complete", expanded=False)
                except Exception as e:
                    status.update(label="Audit Failure", state="error")
                    st.error(f"Critical System Error: {str(e)}")
                    st.stop()
        
        # Results inject directly below the collapsed status
        with results_container:
            st.markdown("### Topology Map")
            st.info("🖱️ **Interaction Logic:** Click spheres to expand context. Contradictions (Red) indicate narrative dissonance.")
            render_3d_graph(graph_data)
            
            st.markdown("---")
            st.markdown("### Verified Data Ledger")
            for i, item in enumerate(news):
                with st.expander(f"INTEL SOURCE {i+1}: {item['title']}"):
                    st.caption(f"**Origin:** {item['url']}")
                    st.write(item['content'])

# --- 6. SIDEBAR METRICS ---
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
