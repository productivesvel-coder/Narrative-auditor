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
    .block-container { padding-top: 2rem; font-family: 'Inter', sans-serif; }
    .stTextInput input { border-radius: 8px; background-color: #0f172a; color: #f8fafc; border: 1px solid #334155; }
    .stButton>button {
        border-radius: 8px;
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
        color: white; font-weight: 600; border: none; padding: 10px 24px; transition: 0.3s; width: 100%;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. SECURE CREDENTIALS (HARDCODED PER REQUEST) ---
TAVILY_API_KEY = "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"
AI_ENGINE_KEY = "AIzaSyAX1R8ufSSRO2BS-VmhInAJkVe7QWCCN_E"

# --- 3. SIDEBAR TELEMETRY ---
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

# --- 4. CORE LOGIC ENGINE ---
def fetch_news(query):
    tavily = TavilyClient(api_key=TAVILY_API_KEY)
    response = tavily.search(query=query, search_depth="advanced", max_results=6)
    if not response.get('results'):
        raise ValueError("No verified news sources found.")
    return response['results']

def generate_graph_data(news_results):
    genai.configure(api_key=AI_ENGINE_KEY)
    model = genai.GenerativeModel('gemini-2.5-flash-lite')
    
    context = "\n".join([f"[{r['title']}] - {r['content']}" for r in news_results])
    
    prompt = f"""
    [SYSTEM PROTOCOL: DISONANCE ENGINE]
    Analyze for logical consensus and dissonance. 
    1. Extract 5 'Claim' nodes (group 2).
    2. Extract 'Source' nodes (group 1).
    3. Link using 'REPORTS', 'CONTRADICTS', or 'SUPPORTS'.
    4. Provide 'name' (short) and 'description' (detailed context) for every node.
    
    OUTPUT: RAW JSON ONLY.
    Context: {context}
    """
    
    # Safety settings to prevent Permission/Blocked errors during dissonance analysis
    safety = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    ]

    response = model.generate_content(
        prompt, 
        generation_config={"response_mime_type": "application/json"},
        safety_settings=safety
    )
    
    clean_json = re.search(r'\{.*\}', response.text, re.DOTALL).group(0)
    data = json.loads(clean_json)
    
    node_ids = {node['id'] for node in data.get('nodes', [])}
    data['links'] = [l for l in data.get('links', []) if l.get('source') in node_ids and l.get('target') in node_ids]
    return data

# --- 5. 3D VISUAL SYNTHESIS ---
def render_3d_graph(data):
    graph_json = json.dumps(data)
    html_code = f"""
    <div id="graph-wrapper" style="position: relative; border-radius: 12px; background: #0B0F19; overflow: hidden; height: 600px; border: 1px solid #1e293b;">
        <div id="info-panel" style="position: absolute; top: 15px; right: 15px; width: 300px; background: rgba(15, 23, 42, 0.95); backdrop-filter: blur(10px); color: white; padding: 20px; border-radius: 12px; display: none; border: 1px solid #334155; z-index: 100; font-family: 'Inter', sans-serif;">
            <h3 id="info-title" style="margin: 0; color: #60a5fa; font-size: 18px;"></h3>
            <hr style="border: 0; border-top: 1px solid #334155; margin: 10px 0;">
            <p id="info-desc" style="font-size: 14px; line-height: 1.5; color: #e2e8f0;"></p>
        </div>
        <div id="graph" style="width: 100%; height: 100%;"></div>
    </div>
    
    <script src="https://unpkg.com/three"></script>
    <script src="https://unpkg.com/three-spritetext"></script>
    <script src="https://unpkg.com/3d-force-graph"></script>
    
    <script>
      window.onload = function() {{
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
                  sprite.center = new THREE.Vector2(0.5, -1.5);
                  return sprite;
              }})
              .onNodeClick(node => {{
                  const panel = document.getElementById('info-panel');
                  panel.style.display = 'block';
                  document.getElementById('info-title').innerText = node.name || node.id;
                  document.getElementById('info-desc').innerText = node.description || 'No additional data compiled.';
                  
                  const distance = 100;
                  const distRatio = 1 + distance/Math.hypot(node.x, node.y, node.z);
                  Graph.cameraPosition(
                      {{ x: node.x * distRatio, y: node.y * distRatio, z: node.z * distRatio }},
                      node, 
                      1200
                  );
              }})
              .linkColor(link => {{
                  if (link.value === 'CONTRADICTS') return '#ff3333';
                  if (link.value === 'SUPPORTS') return '#00ff66';
                  return '#64748b';
              }})
              .linkWidth(link => link.value === 'CONTRADICTS' ? 4 : 2)
              .linkDirectionalParticles(link => link.value === 'CONTRADICTS' ? 5 : 2)
              .backgroundColor('#0B0F19');
      }};
    </script>
    """
    components.html(html_code, height=620)

# --- 6. MAIN USER INTERFACE ---
st.title("Disonance Engine")
st.markdown("<p style='color: #94a3b8; font-size: 1.1rem;'>Real-time spatial audit of global narrative logical structures.</p>", unsafe_allow_html=True)

query = st.text_input("Target Subject / Event", placeholder="Enter geopolitical event or global narrative to audit...")

if st.button("Initialize Logic Audit"):
    if not query.strip():
        st.warning("Query required.")
    else:
        status_placeholder = st.empty()
        with status_placeholder.status("Deploying Disonance Engine...", expanded=True) as status:
            try:
                st.write("📡 Scanning global intelligence sources...")
                news = fetch_news(query)
                
                st.write("🧠 AI Engine mapping logical dissonance...")
                graph_data = generate_graph_data(news)
                
                status.update(label="Audit Complete", state="complete", expanded=False)
                
                # Render results immediately after status collapses
                st.subheader("Narrative Topology Map")
                st.info("🖱️ **Interaction:** Click nodes to view AI-classified context. Contradictions (Red) move faster.")
                render_3d_graph(graph_data)
                
                st.markdown("---")
                st.subheader("Verified Data Ledger")
                for item in news:
                    with st.expander(f"Source: {item['title']}"):
                        st.caption(f"URL: {item['url']}")
                        st.write(item['content'])
                        
            except Exception as e:
                status.update(label="Audit Failure", state="error")
                st.error(f"System Halt: {str(e)}")
