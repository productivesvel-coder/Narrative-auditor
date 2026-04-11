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

# --- 2. SECURE CREDENTIALS ---
TAVILY_API_KEY = st.secrets["TAVILY_API_KEY"]
AI_ENGINE_KEY = st.secrets["AI_ENGINE_KEY"]

# --- 3. SIDEBAR TELEMETRY ---
with st.sidebar:
    st.markdown("### System Telemetry")
    st.markdown("---")
    st.write("🟢 **Data Fetcher:** Active")
    st.write("🟢 **AI Engine:** Operational")
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
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    context = "\n".join([f"[{r['title']} | {r['url']}] - {r['content']}" for r in news_results])
    
    prompt = f"""
    [SYSTEM PROTOCOL: DISONANCE ENGINE]
    Analyze for logical consensus and dissonance. 
    
    Return a RAW JSON object with exactly this structure:
    {{
      "graph": {{
        "nodes": [
          {{"id": "unique_id", "group": 1, "name": "Short Topic Title", "description": "Detailed claim/info...", "source": "Publisher or URL"}}
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
    
    CRITICAL FORMATTING RULES:
    1. Do NOT use literal newlines inside descriptions. Use " " or "\\n".
    2. Escape all double quotes inside strings (e.g., \\").
    3. Ensure all JSON keys and values are properly closed.
    
    Context: {context}
    """
    
    safety = [{"category": c, "threshold": "BLOCK_NONE"} for c in [
        "HARM_CATEGORY_HARASSMENT", "HARM_CATEGORY_HATE_SPEECH", 
        "HARM_CATEGORY_DANGEROUS_CONTENT", "HARM_CATEGORY_SEXUALLY_EXPLICIT"
    ]]

    # Optimized for Speed and Precision
    response = model.generate_content(
        prompt, 
        generation_config={
            "response_mime_type": "application/json",
            "temperature": 0.1,
            "max_output_tokens": 2048
        },
        safety_settings=safety
    )
    
    raw_text = response.text.strip()
    # Clean markdown formatting if model ignores mime_type instruction
    raw_text = re.sub(r'^```json\s*|\s*```$', '', raw_text, flags=re.MULTILINE)
    
    try:
        # strict=False handles many "unterminated string" issues caused by control chars
        data = json.loads(raw_text, strict=False)
    except json.JSONDecodeError:
        # Emergency Regex: Replaces literal newlines inside quotes that break JSON
        fixed_text = re.sub(r'\n(?=[^"]*"(?:[^"]*"[^"]*")*[^"]*$)', ' ', raw_text)
        data = json.loads(fixed_text, strict=False)
    
    # Ghost node sanitizer
    node_ids = {node['id'] for node in data['graph'].get('nodes', [])}
    data['graph']['links'] = [l for l in data['graph'].get('links', []) if l.get('source') in node_ids and l.get('target') in node_ids]
    
    return data

# --- 5. 3D VISUAL SYNTHESIS ---
def render_3d_graph(graph_data):
    graph_json = json.dumps(graph_data)
    
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
                  document.getElementById('info-title').innerText = node.name || node.id;
                  
                  const infoText = node.description || 'No detailed data available.';
                  const sourceText = node.source || 'Unknown Publisher';
                  
                  document.getElementById('info-content').innerHTML = `
                      <p style="font-size: 15px; line-height: 1.5; color: #e2e8f0; margin-bottom: 15px;">${{infoText}}</p>
                      <p style="font-size: 12px; color: #94a3b8; border-top: 1px dashed #334155; padding-top: 10px;">
                          <strong>Source:</strong> ${{sourceText}}
                      </p>`;
                  
                  const distance = 100;
                  const distRatio = 1 + distance/Math.hypot(node.x, node.y, node.z);
                  Graph.cameraPosition({{ x: node.x * distRatio, y: node.y * distRatio, z: node.z * distRatio }}, node, 1200);
              }})
              .linkColor(link => {{
                  if (link.value === 'CONTRADICTS') return '#ff003c';
                  if (link.value === 'SUPPORTS') return '#00ff7f';
                  return '#475569';
              }})
              .linkWidth(link => link.value === 'CONTRADICTS' ? 5 : 2)
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
        
        try:
            # Loading UI
            with status_placeholder.status("Deploying Disonance Engine...", expanded=True) as status:
                st.write("📡 Scanning global intelligence sources...")
                news = fetch_news(query)
                st.write("🧠 AI Engine mapping logical dissonance...")
                payload = generate_audit_data(news)
                status.update(label="Audit Complete", state="complete", expanded=False)

            # Results Display (Outside the status block for immediate visibility)
            graph_data = payload.get("graph", {})
            summary_data = payload.get("summary", {})
            
            st.subheader("Narrative Topology Map")
            st.info("🖱️ **Interaction:** Click nodes to view detailed claims and sources.")
            render_3d_graph(graph_data)
            
            st.markdown("---")
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Consensus & Claims")
                claims = summary_data.get("common_claims", [])
                for claim in claims: st.success(f"✓ {claim}")
                if not claims: st.write("No major consensus detected.")
                    
            with col2:
                st.subheader("Key Contradictions")
                contradictions = summary_data.get("contradictions", [])
                for contra in contradictions: st.error(f"⚠️ {contra}")
                if not contradictions: st.write("No major contradictions detected.")
            
            st.markdown("---")
            st.subheader("Verified Data Ledger")
            for item in news:
                with st.expander(f"Source: {item['title']}"):
                    st.caption(f"URL: {item['url']}")
                    st.write(item['content'])
                    
        except Exception as e:
            status_placeholder.error(f"System Halt: {str(e)}")
