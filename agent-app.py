import json
import asyncio
import subprocess
import streamlit as st
import sys
from openai import OpenAI
from playwright.async_api import async_playwright

# ====================== PLAYWRIGHT BROWSER INSTALLATION ======================
@st.cache_resource
def install_playwright_browsers():
    result = subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], capture_output=True, text=True)
    if result.returncode != 0:
        st.error("Playwright install failed")
        st.stop()
    return True

install_playwright_browsers()

# ========================= STYLING & ULTIMATE UI =========================
st.set_page_config(layout="wide", page_title="AI Agent Intelligence Hub", page_icon="🧬")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
    
    /* Core Layout adjustments */
    .stApp { 
        background: radial-gradient(circle at 50% 0%, #121824 0%, #0a0d14 100%);
        font-family: 'Inter', sans-serif;
        color: #e2e8f0;
    }
    
    /* Elegant Thought Box */
    .thought-box { 
        background: rgba(30, 41, 59, 0.5);
        padding: 20px; 
        border-radius: 12px; 
        border: 1px solid rgba(0, 255, 204, 0.2);
        border-left: 6px solid #00ffcc; 
        margin: 15px 0;
        box-shadow: 0 8px 32px 0 rgba(0, 255, 204, 0.05);
        backdrop-filter: blur(4px);
    }
    
    /* Action / Tool Execution Card */
    .tool-call { 
        background: rgba(30, 41, 59, 0.7); 
        padding: 16px; 
        border-radius: 12px; 
        border: 1px solid rgba(255, 170, 0, 0.2);
        border-left: 6px solid #ffaa00; 
        margin: 12px 0;
        font-family: 'JetBrains Mono', monospace;
    }
    
    /* Output Result Box */
    .tool-result { 
        background: rgba(15, 23, 42, 0.8); 
        padding: 16px; 
        border-radius: 12px; 
        border: 1px solid rgba(0, 204, 153, 0.2);
        border-left: 6px solid #00cc99; 
        font-size: 14px;
        line-height: 1.6;
    }
    
    /* Summary Panel */
    .summary-box { 
        background: linear-gradient(135deg, rgba(15, 28, 46, 0.9) 0%, rgba(10, 15, 30, 0.9) 100%); 
        padding: 25px; 
        border-radius: 16px; 
        border: 1px solid #00ffcc;
        box-shadow: 0 0 20px rgba(0, 255, 204, 0.1);
        margin-top: 30px;
    }

    /* Custom Browser Mockup Bar */
    .browser-bar {
        background: #1e293b;
        padding: 10px;
        border-top-left-radius: 12px;
        border-top-right-radius: 12px;
        display: flex;
        align-items: center;
        border: 1px solid rgba(255,255,255,0.1);
    }
    .url-bar {
        background: #0f172a;
        color: #94a3b8;
        padding: 4px 16px;
        border-radius: 6px;
        width: 85%;
        margin-left: 15px;
        font-size: 13px;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }
    .dot { height: 10px; width: 10px; border-radius: 50%; display: inline-block; margin-right: 6px; }
    .dot-red { background: #ef4444; }
    .dot-yellow { background: #f59e0b; }
    .dot-green { background: #10b981; }
</style>
""", unsafe_allow_html=True)

# Title & Layout Header
st.title("⚡ AI AGENT INTELLIGENCE CENTER")
st.markdown("### Powered by ReAct Framework • Dual-Tool Architecture")
st.markdown("---")

# ========================= SIDEBAR PANEL =========================
with st.sidebar:
    st.image("https://img.icons8.com/wired/128/00ffcc/ai.png", width=80)
    st.header("⚙️ Agent Profile")
    st.caption("Active Core Status: Online")
    st.markdown("---")
    st.subheader("🛠️ Equipped Core Tools")
    st.markdown("""
    🌐 **`web_search`**  
    Scours search engines & live news networks.
    
    📖 **`wiki_search`**  
    Queries deep encyclopedia intelligence data.
    """)
    st.markdown("---")
    st.info("Agent is configured to auto-terminate once standard parameters or constraints are fully met.")

# Input Field Configuration
user_prompt = st.text_input("🎯 **Assign Mission Objective:**", 
                           value="Find the latest news regarding Deutsche Bank, then look up the corporate Wikipedia definition of Elon Musk.")

# Workspace Columns split
col_agent, col_browser = st.columns([1.1, 1], gap="large")

with col_agent:
    st.subheader("🧠 Cognitive Execution Stream")
    log_container = st.container()

with col_browser:
    st.subheader("🖥️ Live Viewport Stream")
    url_display = st.empty()
    viewport_display = st.empty()

# ====================== CORE EXECUTION LOGIC ======================
async def execute_browser_action(page, url: str):
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        screenshot = await page.screenshot(type="png")
        text = await page.evaluate("() => document.body.innerText")
        return {
            "status": "SUCCESS",
            "current_url": page.url,
            "extracted_text": " ".join(text.split())[:6000],
            "screenshot": screenshot
        }
    except Exception as e:
        return {"status": "ERROR", "error": str(e)}

async def run_agent(prompt: str):
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

    system_prompt = "You are an advanced, hyper-focused ReAct web agent. Always think step-by-step and explicitly log your thoughts before triggering tools."

    messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}]

    # Simplified Tool definitions down to exactly two explicit functions
    tools = [
        {
            "type": "function", 
            "function": {
                "name": "web_search", 
                "description": "Search the live web or current news for topical event coverage.", 
                "parameters": {
                    "type": "object", 
                    "properties": {
                        "query": {"type": "string", "description": "The target search terms."}, 
                        "news_mode": {"type": "boolean", "description": "Enable to pull specifically from Google News."}
                    }, 
                    "required": ["query"]
                }
            }
        },
        {
            "type": "function", 
            "function": {
                "name": "wiki_search", 
                "description": "Fetch deep encyclopedia backgrounds and structural reference definitions.", 
                "parameters": {
                    "type": "object", 
                    "properties": {
                        "entity_name": {"type": "string", "description": "The exact subject or entity name to pull from Wikipedia."}
                    }, 
                    "required": ["entity_name"]
                }
            }
        }
    ]

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        context = await browser.new_context(viewport={"width": 1280, "height": 900})
        page = await context.new_page()

        try:
            for turn in range(6): # Fast, concise sequence loops
                with log_container:
                    st.markdown(f"#### 🧭 **Execution Cycle {turn + 1}**")

                    response = client.chat.completions.create(
                        model="gpt-4o-mini", messages=messages, tools=tools, tool_choice="auto"
                    )
                    msg = response.choices[0].message
                    messages.append(msg)

                    thought = msg.content.strip() if msg.content else "Formulating next operative movement..."
                    with st.expander(f"💭 Internal Monologue (Cycle {turn+1})", expanded=True):
                        st.markdown(f'<div class="thought-box">{thought}</div>', unsafe_allow_html=True)

                    if not msg.tool_calls:
                        st.success("🏁 **Mission Parameters Reached Successfully**")
                        st.markdown(f"### 📥 Final Aggregated Synthesis\n{thought}")
                        break

                    for tool_call in msg.tool_calls:
                        fn_name = tool_call.function.name
                        args = json.loads(tool_call.function.arguments)

                        # Clean Tool Card Visuals
                        st.markdown(f"""
                        <div class="tool-call">
                            <strong>🔧 Triggered System Interface:</strong> <span style="color:#ffaa00; font-weight:600;">{fn_name}()</span><br>
                            <span style="color:#94a3b8;">Payload parameters:</span> {json.dumps(args)}
                        </div>
                        """, unsafe_allow_html=True)

                        # Dual-branch Tool routing
                        if fn_name == "web_search":
                            query = args.get("query", "")
                            search_url = f"https://news.google.com/search?q={query.replace(' ', '+')}" if args.get("news_mode") else f"https://duckduckgo.com/html/?q={query.replace(' ', '+')}"
                            result = await execute_browser_action(page, search_url)
                        elif fn_name == "wiki_search":
                            entity = args.get("entity_name", "").replace(' ', '_')
                            result = await execute_browser_action(page, f"https://en.wikipedia.org/wiki/{entity}")
                        else:
                            result = {"status": "ERROR", "error": f"Tool '{fn_name}' is deprecated or missing."}

                        # Show dynamic output telemetry data
                        if result.get("status") == "SUCCESS":
                            preview = result["extracted_text"][:600] + "..." if len(result["extracted_text"]) > 600 else result["extracted_text"]
                            st.markdown(f"""
                            <div class="tool-result">
                                <strong style="color:#00cc99;">📥 Parsed Network Telemetry:</strong><br>
                                {preview}
                            </div>
                            """, unsafe_allow_html=True)

                            # Upgraded Mock Browser Bar & Viewport Capture
                            url_display.markdown(f"""
                            <div class="browser-bar">
                                <span class="dot dot-red"></span><span class="dot dot-yellow"></span><span class="dot dot-green"></span>
                                <div class="url-bar">{result["current_url"]}</div>
                            </div>
                            """, unsafe_allow_html=True)
                            viewport_display.image(result["screenshot"], use_container_width=True)

                        messages.append({
                            "role": "tool", 
                            "tool_call_id": tool_call.id, 
                            "content": json.dumps({"status": result.get("status"), "extracted_text": result.get("extracted_text","")})
                        })

            # Clean Analytics Summary Board
            st.markdown("""
            <div class="summary-box">
                <h3 style="margin-top:0; color:#00ffcc;">📊 Session Audit Log</h3>
                <strong>Optimized Routing Configuration:</strong> Dual Core Framework Active<br>
                <strong>Operational Status:</strong> Run completed without exceptions.
            </div>
            """, unsafe_allow_html=True)

        finally:
            await context.close()
            await browser.close()

# Primary Action Activation Area
if st.button("🚀 INITIATE AUTONOMOUS AGENT RUN", type="primary", use_container_width=True):
    asyncio.run(run_agent(user_prompt))