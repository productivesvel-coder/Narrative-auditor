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
    div[data-testid="stExpander"] { background-color: #0B0F19; border: 1px solid #1e293b; border-radius: 8px; }
    div[data-testid="stExpander"] summary p { font-weight: 600; color: #f8fafc; }
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
    st.write("🟢 **Render Engine:** WebGL Pulse Vortex")
    st.markdown("---")
    st.caption("Vortex Legend:")
    st.markdown("<span style='color: #ff003c; font-weight: bold;'>●</span> CONTRADICTION (Turbulence)", unsafe_allow_html=True)
    st.markdown("<span style='color: #00ff7f; font-weight: bold;'>●</span> CONSENSUS (Smooth Flow)", unsafe_allow_html=True)
    st.markdown("---")
    st.info("🖱️ **Vortex Control:** Click the map to freeze/unfreeze flow. Red particles will continue to vibrate.")

# --- 4. CORE LOGIC ENGINE ---
def fetch_news(query):
    tavily = TavilyClient(api_key=TAVILY_API_KEY)
    response = tavily.search(query=query, search_depth="advanced", max_results=6)
    if not response.get('results'):
        raise ValueError("No verified news sources found.")
    return response['results']

def repair_json(json_str):
    """Safety net to force-close broken JSON strings."""
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
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    context = "\n".join([f"[{r['title']} | {r['url']}] - {r['content']}" for r in news_results])
    
    # Bulletproof prompt with extremely strict JSON rules and shorter text limits
    prompt = f"""
    [SYSTEM PROTOCOL: DISONANCE ENGINE]
    Analyze the text for logical consensus and dissonance. 
    
    Return a RAW JSON object with EXACTLY this structure. Keep descriptions under 200 characters to prevent errors.
    {{
      "particles": [
        {{"id": "p1", "type": "consensus", "name": "Short Topic", "description": "Short detail...", "source": "Publisher Name"}},
        {{"id": "p2", "type": "contradiction", "name": "Short Topic", "description": "Short detail...", "source": "Publisher Name"}}
      ],
      "summary": {{
        "common_claims": [
          {{"title": "Claim 1", "detail": "Detailed explanation..."}}
        ],
        "contradictions": [
          {{"title": "Conflict 1", "detail": "Detailed explanation..."}}
        ]
      }}
    }}
    
    Rules:
    - Extract up to 10 'particles' total.
    - 'type' MUST be either "consensus" or "contradiction".
    - NO literal newlines inside strings.
    - OUTPUT RAW JSON ONLY. NO MARKDOWN.
    
    Context: {context}
    """
    
    response = model.generate_content(
        prompt, 
        generation_config={"response_mime_type": "application/json", "max_output_tokens": 8192, "temperature": 0.1}
    )
    
    raw_text = response.text.strip()
    json_match = re.search(r'(\{.*\})', raw_text, re.DOTALL)
    clean_text = json_match.group(1) if json_match else raw_text
    clean_text = "".join(char for char in clean_text if ord(char) >= 32 or char in "\n\r\t")
    clean_text = re.sub(r'(?<!\\)\n', ' ', clean_text)

    try:
        data = json.loads(clean_text, strict=False)
    except json.JSONDecodeError:
        try:
            data = json.loads(repair_json(clean_text), strict=False)
        except Exception:
            # Fallback placeholder to prevent app crash
            data = {"particles": [], "summary": {"common_claims": [], "contradictions": [{"title": "Data Parse Error", "detail": "AI output structure failed."}]}}
    
    return data

# --- 5. 3D VISUAL SYNTHESIS (PULSE VORTEX) ---
def render_3d_vortex(vortex_data):
    vortex_json = json.dumps(vortex_data.get("particles", []))
    
    html_code = f"""
    <div id="graph-wrapper" style="position: relative; border-radius: 12px; background: #05080F; overflow: hidden; height: 600px; border: 1px solid #1e293b;">
        <div id="info-panel" style="position: absolute; top: 15px; right: 15px; width: 320px; background: rgba(15, 23, 42, 0.95); backdrop-filter: blur(10px); color: white; padding: 20px; border-radius: 12px; display: none; border: 1px solid #334155; z-index: 100; font-family: 'Inter', sans-serif;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                <h3 id="info-title" style="margin: 0; color: #60a5fa; font-size: 18px; line-height: 1.2;"></h3>
                <span id="info-badge" style="font-size: 10px; padding: 2px 6px; border-radius: 4px; font-weight: bold; text-transform: uppercase;"></span>
            </div>
            <hr style="border: 0; border-top: 1px solid #334155; margin: 0 0 12px 0;">
            <div id="info-content"></div>
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
          
          // Scene Setup
          const scene = new THREE.Scene();
          scene.fog = new THREE.FogExp2(0x05080F, 0.015);
          
          const camera = new THREE.PerspectiveCamera(60, elem.clientWidth / elem.clientHeight, 0.1, 1000);
          camera.position.set(0, 30, 60);
          
          const renderer = new THREE.WebGLRenderer({{ antialias: true, alpha: true }});
          renderer.setSize(elem.clientWidth, elem.clientHeight);
          renderer.setPixelRatio(window.devicePixelRatio);
          elem.appendChild(renderer.domElement);
          
          const controls = new THREE.OrbitControls(camera, renderer.domElement);
          controls.enableDamping = true;
          controls.dampingFactor = 0.05;
          controls.autoRotate = true;
          controls.autoRotateSpeed = 1.0;
          
          // Core Vortex Pillar
          const coreGeo = new THREE.CylinderGeometry(0.5, 0.5, 100, 16);
          const coreMat = new THREE.MeshBasicMaterial({{ color: 0x1e293b, transparent: true, opacity: 0.3 }});
          const core = new THREE.Mesh(coreGeo, coreMat);
          scene.add(core);

          // Particle System
          const meshes = [];
          pData.forEach((p, i) => {{
              const isContra = p.type === 'contradiction';
              const color = isContra ? 0xff003c : 0x00ff7f;
              
              const geo = new THREE.SphereGeometry(isContra ? 1.5 : 1.0, 16, 16);
              const mat = new THREE.MeshBasicMaterial({{ color: color, wireframe: isContra }});
              const mesh = new THREE.Mesh(geo, mat);
              
              mesh.userData = {{
                  angle: Math.random() * Math.PI * 2,
                  radius: 10 + Math.random() * 25,
                  speed: (isContra ? 0.04 : 0.015) + Math.random() * 0.01,
                  yOffset: (Math.random() - 0.5) * 40,
                  isContra: isContra,
                  info: p
              }};
              
              const glowGeo = new THREE.SphereGeometry(isContra ? 2.5 : 1.8, 16, 16);
              const glowMat = new THREE.MeshBasicMaterial({{ color: color, transparent: true, opacity: 0.2 }});
              const glow = new THREE.Mesh(glowGeo, glowMat);
              mesh.add(glow);
              
              scene.add(mesh);
              meshes.push(mesh);
          }});

          // Interaction (Raycasting & Pause Toggle)
          const raycaster = new THREE.Raycaster();
          const mouse = new THREE.Vector2();
          
          elem.addEventListener('pointerdown', (event) => {{
              // Toggle Pause logic
              isPaused = !isPaused;
              controls.autoRotate = !isPaused;

              const rect = elem.getBoundingClientRect();
              mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
              mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
              
              raycaster.setFromCamera(mouse, camera);
              const intersects = raycaster.intersectObjects(meshes);
              
              if (intersects.length > 0) {{
                  const ud = intersects[0].object.userData;
                  const panel = document.getElementById('info-panel');
                  panel.style.display = 'block';
                  
                  document.getElementById('info-title').innerText = ud.info.name || 'Data Point';
                  const badge = document.getElementById('info-badge');
                  badge.innerText = ud.isContra ? 'Conflict' : 'Consensus';
                  badge.style.backgroundColor = ud.isContra ? 'rgba(255, 0, 60, 0.2)' : 'rgba(0, 255, 127, 0.2)';
                  badge.style.color = ud.isContra ? '#ff003c' : '#00ff7f';
                  
                  const infoText = ud.info.description || 'No detailed data available.';
                  const sourceText = ud.info.source || 'Unknown Publisher';
                  
                  document.getElementById('info-content').innerHTML = `
                      <p style="font-size: 14px; line-height: 1.5; color: #e2e8f0; margin-bottom: 15px;">${{infoText}}</p>
                      <p style="font-size: 12px; color: #94a3b8; border-top: 1px dashed #334155; padding-top: 10px;">
                          <strong>Source:</strong> ${{sourceText}}
                      </p>
                  `;
              }}
          }});

          // Animation Loop
          function animate() {{
              requestAnimationFrame(animate);
              
              meshes.forEach(m => {{
                  let ud = m.userData;
                  
                  // Only increment angle if not paused
                  if (!isPaused) {{
                      ud.angle += ud.speed;
                  }}
                  
                  // Base Circular Orbit (Calculated every frame to allow jitter offset)
                  let bx = Math.cos(ud.angle) * ud.radius;
                  let bz = Math.sin(ud.angle) * ud.radius;
                  let by = ud.yOffset;

                  // Apply Constant Jitter to Contradictions (even if paused)
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
          
          window.addEventListener('resize', () => {{
              camera.aspect = elem.clientWidth / elem.clientHeight;
              camera.updateProjectionMatrix();
              renderer.setSize(elem.clientWidth, elem.clientHeight);
          }});
          
          animate();
      }};
    </script>
    """
    components.html(html_code, height=620)

# --- 6. MAIN USER INTERFACE ---
st.title("Disonance Engine")
st.markdown("<p style='color: #94a3b8; font-size: 1.1rem;'>Real-time fluid dynamic audit of global narrative logical structures.</p>", unsafe_allow_html=True)

query = st.text_input("Target Subject / Event", placeholder="Enter geopolitical event or global narrative to audit...")

if st.button("Initialize Logic Audit"):
    if not query.strip():
        st.warning("Query required.")
    else:
        status_container = st.empty()
        
        try:
            with status_container.status("Deploying Disonance Engine...", expanded=True) as status:
                st.write("📡 Scanning global intelligence sources...")
                news = fetch_news(query)
                
                st.write("🧠 AI Engine synthesizing Pulse Vortex data...")
                payload = generate_audit_data(news)
                
                summary_data = payload.get("summary", {})
                
                status.update(label="Vortex Synthesis Complete", state="complete", expanded=False)
            
            # --- UI BREAKOUT ---
            st.subheader("Narrative Pulse Vortex")
            st.info("🖱️ **Interaction:** Click the map to **Freeze** orbital flow. Click particles to view intelligence metadata.")
            render_3d_vortex(payload)
            
            st.markdown("<br><hr>", unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("🟢 Consensus Data Stream")
                claims = summary_data.get("common_claims", [])
                if claims:
                    # Each claim is a clear overview header with its own detailed dropdown
                    for claim in claims:
                        with st.expander(f"✓ {claim.get('title', 'Verified Claim')}"):
                            st.write(claim.get('detail', 'No detailed text provided.'))
                else:
                    st.write("No major consensus detected in the data stream.")
                    
            with col2:
                st.subheader("🔴 Dissonance & Contradictions")
                contradictions = summary_data.get("contradictions", [])
                if contradictions:
                    # Each contradiction is a clear overview header with its own detailed dropdown
                    for contra in contradictions:
                        with st.expander(f"⚠️ {contra.get('title', 'Logical Conflict')}"):
                            st.write(contra.get('detail', 'No detailed text provided.'))
                else:
                    st.write("No major contradictions detected. The narrative is stable.")
            
            st.markdown("---")
            st.subheader("Verified Data Ledger")
            for item in news:
                with st.expander(f"Source: {item['title']}"):
                    st.caption(f"URL: {item['url']}")
                    st.write(item['content'])
                    
        except Exception as e:
            status_container.error(f"System Halt: {str(e)}")
