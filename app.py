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

# --- 2. SECURE CREDENTIALS (VIA STREAMLIT SECRETS) ---
# Ensure your .streamlit/secrets.toml contains TAVILY_API_KEY and AI_ENGINE_KEY
TAVILY_API_KEY = st.secrets["TAVILY_API_KEY"]
AI_ENGINE_KEY = st.secrets["AI_ENGINE_KEY"]

# --- 3. SIDEBAR TELEMETRY ---
with st.sidebar:
    st.markdown("### System Telemetry")
    st.markdown("---")
    st.write("🟢 **Data Fetcher:** Active")
    st.write("🟢 **AI Engine:** Operational (Gemini 2.5 Flash)")
    st.write("🟢 **Render Engine:** WebGL 3D")
    st.markdown("---")
    st.caption("Dissonance Metrics:")
    st.markdown("<span style='color: #ff003c; font-weight: bold;'>█</span> CONTRADICTION (Conflict)", unsafe_allow_html=True)
    st.markdown("<span style='color: #00ff7f; font-weight: bold;'>█</span> SUPPORT (Consensus)", unsafe_allow_html=True)
    st.markdown("<span style='color: #475569; font-weight: bold;'>█</span> REPORT (Neutral Link)", unsafe_allow_html=True)

# --- 4. CORE LOGIC ENGINE ---
def fetch_news(query):
    tavily = TavilyClient(api_key=TAVILY_API_KEY)
    response = tavily.search(query=query, search_depth="advanced", max_results=6)
    if not response.get('results'):
        raise ValueError("No verified news sources found.")
    return response['results']

def generate_audit_data(news_results):
    genai.configure(api_key=AI_ENGINE_KEY)
    # 1. Updated Model to 2.5 Flash
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    context = "\n".join([f"[{r['title']} | {r['url']}] - {r['content']}" for r in news_results])
    
    # 3 & 4. Ask for summary data alongside the graph data, enforce naming schemas
    prompt = f"""
    [SYSTEM PROTOCOL: DISONANCE ENGINE]
    Analyze for logical consensus and dissonance. 
    
    Return a RAW JSON object with exactly this structure:
    {{
      "graph": {{
        "nodes": [
          {{"id": "unique_id", "group": 1_or_2, "name": "Short Topic Title", "description": "Detailed claim/info...", "source": "Publisher or URL"}}
        ],
        "links": [
          {{"source": "source_node_id", "target": "target_node_id", "value": "CONTRADICTS" | "SUPPORTS" | "REPORTS"}}
        ]
      }},
      "summary": {{
        "common_claims": ["claim 1", "claim 2"],
        "contradictions": ["contradiction 1", "contradiction 2"]
      }}
    }}
    
    Rules for Graph:
    - Group 1: Source Nodes. Group 2: Claim Nodes.
    - Extract up to 6 'Claim' nodes and link them to their 'Source' nodes.
    - EVERY node must have a short, punchy 'name' and a detailed 'description'.
    
    OUTPUT RAW JSON ONLY.
    Context: {context}
    """
    
    safety = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    ]

    # FIX 3: Optimized generation config for speed and precision
    response = model.generate_content(
        prompt, 
        generation_config={
            "response_mime_type": "application/json",
            "temperature": 0.1,
            "max_output_tokens": 1024
        },
        safety_settings=safety
    )
    
    # 5. Robust JSON Cleaning
    raw_text = response.text.strip()
    if raw_text.startswith("```json"):
        raw_text = raw_text[7:]
    if raw_text.endswith("```"):
        raw_text = raw_text[:-3]
    raw_text = raw_text.strip()
    
    data = json.loads(raw_text)
    
    # Ghost node sanitizer on the graph object
    node_ids = {node['id'] for node in data['graph'].get('nodes', [])}
    data['graph']['links'] = [l for l in data['graph'].get('links', []) if l.get('source') in node_ids and l.get('target') in node_ids]
    
    return data

# --- 5. 3D VISUAL SYNTHESIS ---
def render_3d_graph(graph_data):
    graph_json = json.dumps(graph_data)
    
    # FIX 1: Cleaned the script tags so the browser can load the JS libraries properly
    html_code = f"""
    <div id="graph-wrapper" style="position: relative; border-radius: 12px; background: #0B0F19; overflow: hidden; height: 600px; border: 1px solid #1e293b;">
        <div id="info-panel" style="position: absolute; top: 15px; right: 15px; width: 320px; background: rgba(15, 23, 42, 0.95); backdrop-filter: blur(10px); color: white; padding: 20px; border-radius: 12px; display: none; border: 1px solid #334155; z-index: 100; font-family: 'Inter', sans-serif;">
            <h3 id="info-title" style="margin: 0; color: #60a5fa; font-size: 18px; line-height: 1.2;"></h3>
            <hr style="border: 0; border-top: 1px solid #334155; margin: 12px 0;">
            <div id="info-content"></div>
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
                  sprite.textHeight = 5;
                  sprite.center = new THREE.Vector2(0.5, -1.2);
                  return sprite;
              }})
              .onNodeClick(node => {{
                  const panel = document.getElementById('info-panel');
                  panel.style.display = 'block';
                  
                  // Setting Title
                  document.getElementById('info-title').innerText = node.name || node.id;
                  
                  // Setting Content (Info heavily emphasized, Source muted below)
                  const infoText = node.description || 'No detailed data available.';
                  const sourceText = node.source || 'Unknown Publisher';
                  
                  document.getElementById('info-content').innerHTML = `
                      <p style="font-size: 15px; line-height: 1.5; color: #e2e8f0; margin-bottom: 15px;">
                          ${{infoText}}
                      </p>
                      <p style="font-size: 12px; color: #94a3b8; border-top: 1px dashed #334155; padding-top: 10px;">
                          <strong>Source:</strong> ${{sourceText}}
                      </p>
                  `;
                  
                  // Camera Zoom
                  const distance = 100;
                  const distRatio = 1 + distance/Math.hypot(node.x, node.y, node.z);
                  Graph.cameraPosition(
                      {{ x: node.x * distRatio, y: node.y * distRatio, z: node.z * distRatio }},
                      node, 
                      1200
                  );
              }})
              .linkColor(link => {{
                  if (link.value === 'CONTRADICTS') return '#ff003c'; // Neon Red
                  if (link.value === 'SUPPORTS') return '#00ff7f';    // Spring Green
                  return '#475569';                                   // Muted Slate
              }})
              .linkWidth(link => link.value === 'CONTRADICTS' ? 5 : (link.value === 'SUPPORTS' ? 3 : 1))
              .linkDirectionalParticles(link => link.value === 'CONTRADICTS' ? 5 : (link.value === 'SUPPORTS' ? 3 : 1))
              .linkDirectionalParticleWidth(link => link.value === 'CONTRADICTS' ? 4 : 2)
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
        
        try:
            # FIX 2: This block only handles the loading state. Rendering happens after.
            with status_placeholder.status("Deploying Disonance Engine...", expanded=True) as status:
                st.write("📡 Scanning global intelligence sources...")
                news = fetch_news(query)
                
                st.write("🧠 AI Engine (Gemini 2.5 Flash) mapping logical dissonance...")
                payload = generate_audit_data(news)
                
                status.update(label="Audit Complete", state="complete", expanded=False)

            # --- RENDERING OUTSIDE THE STATUS DROPDOWN ---
            graph_data = payload.get("graph", {})
            summary_data = payload.get("summary", {})
            
            # Top: 3D Visualization
            st.subheader("Narrative Topology Map")
            st.info("🖱️ **Interaction:** Click nodes to view detailed claims and sources. Contradictions (Red) move faster.")
            render_3d_graph(graph_data)
            
            # Bottom: AI Summary & Ledgers
            st.markdown("---")
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Consensus & Claims")
                claims = summary_data.get("common_claims", [])
                if claims:
                    for claim in claims:
                        st.success(f"✓ {claim}")
                else:
                    st.write("No major consensus detected.")
                    
            with col2:
                st.subheader("Key Contradictions")
                contradictions = summary_data.get("contradictions", [])
                if contradictions:
                    for contra in contradictions:
                        st.error(f"⚠️ {contra}")
                else:
                    st.write("No major contradictions detected.")
            
            st.markdown("---")
            st.subheader("Verified Data Ledger")
            for item in news:
                with st.expander(f"Source: {item['title']}"):
                    st.caption(f"URL: {item['url']}")
                    st.write(item['content'])
                    
        except Exception as e:
            # Revert the status UI to show the error
            status_placeholder.error(f"System Halt: {str(e)}")
