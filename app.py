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
    div[data-testid="stExpander"] { background-color: #0B0F19; border: 1px solid #1e293b; border-radius: 8px; margin-bottom: 8px; }
    div[data-testid="stExpander"] summary p { font-weight: 600; color: #f8fafc; }
    .claim-label { font-size: 0.9rem; font-weight: bold; margin-bottom: 5px; display: block; }
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
    st.write("🟢 **AI Engine:** Operational (Gemini 1.5 Flash)")
    st.write("🟢 **Render Engine:** WebGL Pulse Vortex")
    st.markdown("---")
    st.caption("Vortex Legend:")
    st.markdown("<span style='color: #ff003c; font-weight: bold;'>●</span> CONTRADICTION (Active Turbulence)", unsafe_allow_html=True)
    st.markdown("<span style='color: #00ff7f; font-weight: bold;'>●</span> CONSENSUS (Stable Orbit)", unsafe_allow_html=True)
    st.markdown("---")
    st.info("💡 **Tip:** Click the Vortex to freeze orbital flow. Red particles will continue to vibrate.")

# --- 4. CORE LOGIC ENGINE ---
def fetch_news(query):
    tavily = TavilyClient(api_key=TAVILY_API_KEY)
    response = tavily.search(query=query, search_depth="advanced", max_results=6)
    if not response.get('results'):
        raise ValueError("No verified news sources found.")
    return response['results']

def repair_json(json_str):
    json_str = json_str.strip()
    json_str = re.sub(r'[^}\]" \w]$', '', json_str)
    if json_str.count('"') % 2 != 0: json_str += '"'
    stack = []
    for char in json_str:
        if char == '{': stack.append('}')
        elif char == '[': stack.append(']')
        elif char in '}]':
            if stack and stack[-1] == char: stack.pop()
    return json_str + "".join(reversed(stack))

def generate_audit_data(news_results):
    genai.configure(api_key=AI_ENGINE_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    context = "\n".join([f"[{r['title']} | {r['url']}] - {r['content']}" for r in news_results])
    
    prompt = f"""
    [SYSTEM PROTOCOL: DISONANCE ENGINE]
    Analyze for logical consensus and dissonance. Return a RAW JSON object. 
    Keep descriptions under 200 characters.
    {{
      "particles": [
        {{"id": "p1", "type": "consensus", "name": "Claim Name", "description": "Short summary", "source": "Publisher"}}
      ],
      "summary": {{
        "common_claims": [
          {{"title": "Claim Overview", "detail": "Deep dive analysis of the consensus..."}}
        ],
        "contradictions": [
          {{"title": "Conflict Overview", "detail": "Deep dive analysis of the contradiction..."}}
        ]
      }}
    }}
    Rules: Max 10 particles. NO MARKDOWN. RAW JSON ONLY.
    Context: {context}
    """
    
    response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json", "temperature": 0.1})
    raw_text = response.text.strip()
    json_match = re.search(r'(\{.*\})', raw_text, re.DOTALL)
    clean_text = json_match.group(1) if json_match else raw_text

    try:
        return json.loads(clean_text, strict=False)
    except:
        return json.loads(repair_json(clean_text), strict=False)

# --- 5. 3D VISUAL SYNTHESIS (PULSE VORTEX V2) ---
def render_3d_vortex(vortex_data):
    vortex_json = json.dumps(vortex_data.get("particles", []))
    
    html_code = f"""
    <div id="graph-wrapper" style="position: relative; border-radius: 12px; background: #05080F; overflow: hidden; height: 600px; border: 1px solid #1e293b;">
        <div id="info-panel" style="position: absolute; top: 15px; right: 15px; width: 300px; background: rgba(15, 23, 42, 0.95); backdrop-filter: blur(10px); color: white; padding: 20px; border-radius: 12px; display: none; border: 1px solid #334155; z-index: 100; font-family: 'Inter', sans-serif;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                <h3 id="info-title" style="margin: 0; color: #60a5fa; font-size: 16px;"></h3>
                <span id="info-badge" style="font-size: 9px; padding: 2px 6px; border-radius: 4px; font-weight: bold; text-transform: uppercase;"></span>
            </div>
            <div id="info-content" style="font-size: 13px; color: #e2e8f0; line-height: 1.4;"></div>
        </div>
        <div id="vortex" style="width: 100%; height: 100%; cursor: crosshair;"></div>
    </div>
    
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
    
    <script>
      window.onload = function() {{
          const pData = {vortex_json};
          const elem = document.getElementById('vortex');
          let isPaused = false;
          
          const scene = new THREE.Scene();
          scene.fog = new THREE.FogExp2(0x05080F, 0.015);
          
          const camera = new THREE.PerspectiveCamera(60, elem.clientWidth / elem.clientHeight, 0.1, 1000);
          camera.position.set(0, 35, 65);
          
          const renderer = new THREE.WebGLRenderer({{ antialias: true, alpha: true }});
          renderer.setSize(elem.clientWidth, elem.clientHeight);
          elem.appendChild(renderer.domElement);
          
          const controls = new THREE.OrbitControls(camera, renderer.domElement);
          controls.enableDamping = true;
          controls.autoRotate = true;

          const meshes = [];
          pData.forEach(p => {{
              const isContra = p.type === 'contradiction';
              const color = isContra ? 0xff003c : 0x00ff7f;
              
              const mesh = new THREE.Mesh(
                  new THREE.SphereGeometry(isContra ? 1.5 : 1, 16, 16),
                  new THREE.MeshBasicMaterial({{ color: color, wireframe: isContra }})
              );
              
              mesh.userData = {{
                  angle: Math.random() * Math.PI * 2,
                  radius: 12 + Math.random() * 25,
                  speed: isContra ? 0.035 : 0.012,
                  y: (Math.random() - 0.5) * 40,
                  isContra: isContra,
                  info: p
              }};
              scene.add(mesh);
              meshes.push(mesh);
          }});

          // Interaction: Toggle Freeze
          elem.addEventListener('pointerdown', (event) => {{
              isPaused = !isPaused;
              controls.autoRotate = !isPaused;
              
              // Raycasting for info
              const rect = elem.getBoundingClientRect();
              const mouse = new THREE.Vector2(
                  ((event.clientX - rect.left) / rect.width) * 2 - 1,
                  -((event.clientY - rect.top) / rect.height) * 2 + 1
              );
              const raycaster = new THREE.Raycaster();
              raycaster.setFromCamera(mouse, camera);
              const intersects = raycaster.intersectObjects(meshes);
              
              if (intersects.length > 0) {{
                  const ud = intersects[0].object.userData;
                  const panel = document.getElementById('info-panel');
                  panel.style.display = 'block';
                  document.getElementById('info-title').innerText = ud.info.name;
                  document.getElementById('info-content').innerText = ud.info.description;
                  const badge = document.getElementById('info-badge');
                  badge.innerText = ud.isContra ? 'Conflict' : 'Consensus';
                  badge.style.backgroundColor = ud.isContra ? 'rgba(255,0,60,0.2)' : 'rgba(0,255,127,0.2)';
                  badge.style.color = ud.isContra ? '#ff003c' : '#00ff7f';
              }}
          }});

          function animate() {{
              requestAnimationFrame(animate);
              meshes.forEach(m => {{
                  let ud = m.userData;
                  
                  // Orbital movement stops if paused
                  if (!isPaused) {{ ud.angle += ud.speed; }}
                  
                  let bx = Math.cos(ud.angle) * ud.radius;
                  let bz = Math.sin(ud.angle) * ud.radius;
                  let by = ud.y;

                  // Red particles jitter regardless of pause
                  if(ud.isContra) {{
                      m.position.x = bx + (Math.random() - 0.5) * 1.5;
                      m.position.y = by + (Math.random() - 0.5) * 1.5;
                      m.position.z = bz + (Math.random() - 0.5) * 1.5;
                  }} else {{
                      m.position.set(bx, by, bz);
                  }}
              }});
              controls.update();
              renderer.render(scene, camera);
          }}
          animate();
      }};
    </script>
    """
    components.html(html_code, height=620)

# --- 6. MAIN USER INTERFACE ---
st.title("Disonance Engine")
st.markdown("<p style='color: #94a3b8;'>Narrative structural analysis & fluid dynamic visualization.</p>", unsafe_allow_html=True)

query = st.text_input("Target Subject", placeholder="Enter event or topic for narrative audit...")

if st.button("Initialize Logic Audit"):
    if not query.strip():
        st.warning("Input required.")
    else:
        status_container = st.empty()
        try:
            with status_container.status("Processing Intelligence...", expanded=True) as status:
                st.write("📡 Gathering source data...")
                news = fetch_news(query)
                st.write("🧠 Mapping logical variance...")
                payload = generate_audit_data(news)
                status.update(label="Audit Complete", state="complete", expanded=False)
            
            # --- IMMEDIATE OUTPUT ---
            st.subheader("Narrative Pulse Vortex")
            render_3d_vortex(payload)
            
            st.markdown("<br>", unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("🟢 Consensus Stream")
                for claim in payload.get('summary', {}).get('common_claims', []):
                    # Flat header with individual dropdown
                    st.markdown(f"<span class='claim-label'>✓ {claim['title']}</span>", unsafe_allow_html=True)
                    with st.expander("View Claim Analysis"):
                        st.write(claim['detail'])
            
            with col2:
                st.subheader("🔴 Dissonance Stream")
                for contra in payload.get('summary', {}).get('contradictions', []):
                    # Flat header with individual dropdown
                    st.markdown(f"<span class='claim-label' style='color:#ff003c;'>⚠️ {contra['title']}</span>", unsafe_allow_html=True)
                    with st.expander("View Conflict Analysis"):
                        st.write(contra['detail'])
            
            st.markdown("---")
            st.subheader("Verified Data Ledger")
            for item in news:
                with st.expander(f"Source: {item['title']}"):
                    st.caption(item['url'])
                    st.write(item['content'])
                    
        except Exception as e:
            status_container.error(f"Audit Halted: {str(e)}")
