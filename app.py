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
AI_ENGINE_KEY = "AIzaSyAyTNUZ7ZkaRNGdL-QD5om4_iGzbdEMmp4"

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
        raise ValueError("AI Engine failed to structure data correctly.")

def generate_graph_data(news_results):
    genai.configure(api_key=AI_ENGINE_KEY)
    
    # Targetting the Gemini 2.5 Flash architecture
    model = genai.GenerativeModel('gemini-2.5-flash') 
    
    context = "\n".join([f"[{r['title']}] - {r['content']}" for r in news_results])
    
    prompt = f"""
    [SYSTEM PROTOCOL: DISONANCE ENGINE]
    Analyze the provided global news context.
    
    Extract exactly 5 'Claim' nodes (group: 2).
    Extract involved 'Source' nodes (group: 1).
    Link claims to sources (value: 'REPORTS').
    Link claims to other claims ONLY if they directly conflict (value: 'CONTRADICTS') or align (value: 'SUPPORTS').
    
    OUTPUT FORMAT MUST BE RAW JSON.
    {{
      "nodes": [{{"id": "String", "group": 1}}],
      "links": [{{"source": "String", "target": "String", "value": "String"}}]
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
    clean_links = [
        link for link in raw_data.get('links', []) 
        if link['source'] in node_ids and link['target'] in node_ids
    ]
    raw_data['links'] = clean_links
    
    return raw_data

# --- 4. 3D VISUAL SYNTHESIS ---
def render_3d_graph(data):
    graph_json = json.dumps(data)
    html_code = f"""
    <div id="graph-container" style="border-radius: 12px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.5);">
        <div id="graph" style="width: 100%; height: 65vh; background: #0B0F19;"></div>
    </div>
    <script src="//cdn.jsdelivr.net/npm/3d-force-graph"></script>
    <script>
      const gData = {graph_json};
      const elem = document.getElementById('graph');
      
      const Graph = ForceGraph3D()(elem)
          .graphData(gData)
          .nodeAutoColorBy('group')
          .nodeRelSize(6)
          .linkDirectionalParticles(link => link.value === 'CONTRADICTS' ? 4 : 2)
          .linkDirectionalParticleSpeed(link => link.value === 'CONTRADICTS' ? 0.01 : 0.005)
          .linkWidth(link => link.value === 'CONTRADICTS' ? 3 : 1)
          .linkLabel('value')
          .linkColor(link => {{
              if (link.value === 'CONTRADICTS') return '#ef4444';
              if (link.value === 'SUPPORTS') return '#10b981';
              return '#64748b';
          }})
          .backgroundColor('#0B0F19');
          
      window.addEventListener('resize', () => {{
          Graph.width(elem.clientWidth).height(elem.clientHeight);
      }});
    </script>
    <style> body {{ margin: 0; background: transparent; }} </style>
    """
    components.html(html_code, height=600)

# --- 5. USER INTERFACE ---
col1, col2 = st.columns([3, 1])

with col1:
    st.title("Disonance Engine")
    st.markdown("<p style='color: #94a3b8; font-size: 1.1rem;'>Real-time spatial mapping of global narrative consensus and contradiction.</p>", unsafe_allow_html=True)

query = st.text_input("Target Subject / Event", placeholder="Enter subject to begin audit...")

if st.button("Initialize Logic Audit"):
    if not query.strip():
        st.warning("Please define a target subject.")
    else:
        with st.status("Deploying Disonance Engine...", expanded=True) as status:
            try:
                st.write("📡 Accessing global news APIs...")
                news = fetch_news(query)
                
                st.write("🧠 AI Engine compiling logical topology...")
                graph_data = generate_graph_data(news)
                
                status.update(label="Audit Complete", state="complete", expanded=False)
                
                st.markdown("### Topology Map")
                render_3d_graph(graph_data)
                
                st.markdown("### Verified Data Ledger")
                for i, item in enumerate(news):
                    with st.expander(f"Source {i+1}: {item['title']}"):
                        st.caption(f"**URL:** {item['url']}")
                        st.write(item['content'])
                        
            except Exception as e:
                status.update(label="Audit Failed", state="error", expanded=False)
                st.error(f"SYSTEM HALT: {str(e)}")

# --- 6. SIDEBAR METRICS ---
with st.sidebar:
    st.markdown("### System Telemetry")
    st.markdown("---")
    st.write("🟢 **Data Fetcher:** Active")
    st.write("🟢 **AI Engine:** Linked")
    st.write("🟢 **Render Engine:** 3D Force")
    st.markdown("---")
    st.caption("Visual Legend:")
    st.markdown("<span style='color: #ef4444;'>█</span> Contradiction", unsafe_allow_html=True)
    st.markdown("<span style='color: #10b981;'>█</span> Support", unsafe_allow_html=True)
    st.markdown("<span style='color: #64748b;'>█</span> Report / Mention", unsafe_allow_html=True)
