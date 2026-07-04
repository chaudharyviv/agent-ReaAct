import json
import asyncio
import os
import subprocess
import streamlit as st
import sys
from openai import OpenAI
from playwright.async_api import async_playwright

# ====================== PLAYWRIGHT INSTALLATION ======================
@st.cache_resource
def install_playwright_browsers():
    """Install Chromium for Playwright (Streamlit Cloud safe)."""
    result = subprocess.run(
        [sys.executable, "-m", "playwright", "install", "chromium"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        st.error(f"Playwright install failed:\n{result.stderr[-500:]}")
        st.stop()  # don't let the app continue to a guaranteed crash
    return True


# Run installation
install_playwright_browsers()

# ========================= CONFIG =========================
st.set_page_config(layout="wide", page_title="AI Agent Live Workspace", page_icon="🤖")

# ====================== VIBRANT & VISIBLE STYLES ======================
st.markdown("""
    <style>
    /* Global vibrant theme */
    .stApp {
      background: linear-gradient(135deg, #0f1620 0%, #1a2333 100%);
  }
    h1, h2, h3, .stMarkdown {
      color: #ffffff !important;
    }
    
    /* Enhanced browser window */
    .browser-window { 
      border: 3px solid #00ffcc; 
      border-radius: 12px; 
      background-color: #0a0f1a; 
      padding: 6px; 
      box-shadow: 0px 8px 30px rgba(0, 255, 200, 0.3), 
                  inset 0 0 40px rgba(0, 255, 200, 0.1);
      transition: box-shadow 0.3s ease;
    }
    .browser-window:hover {
      box-shadow: 0px 12px 40px rgba(0, 255, 200, 0.5);
    }
    
    .browser-bar { 
      background: linear-gradient(90deg, #1e2a44, #2a3a5a); 
      padding: 12px 16px; 
      border-radius: 8px 8px 0 0; 
      color: #fff; 
      font-family: monospace; 
      font-size: 14px; 
      display: flex; 
      align-items: center; 
      box-shadow: inset 0 2px 4px rgba(0,0,0,0.4);
    }
    .dot { 
      height: 14px; 
      width: 14px; 
      border-radius: 50%; 
      display: inline-block; 
      margin-right: 8px; 
      box-shadow: 0 0 6px currentColor;
    }
    .dot-red { background: #ff5f56; }
    .dot-yellow { background: #ffbd2e; }
    .dot-green { background: #27c93f; }
    
    .url-bar { 
      background: #0f1620; 
      padding: 6px 16px; 
      border-radius: 6px; 
      flex-grow: 1; 
      margin-left: 20px; 
      color: #00ffcc; 
      font-weight: 500;
      overflow: hidden; 
      text-overflow: ellipsis; 
      white-space: nowrap; 
      border: 1px solid #334455;
    }
    
    /* Vibrant thought boxes */
    .thought-box { 
      background: linear-gradient(145deg, #1e2a44, #16213a); 
      padding: 18px; 
      border-radius: 10px; 
      border-left: 6px solid #00ffcc; 
      margin-bottom: 16px; 
      box-shadow: 0 4px 15px rgba(0, 255, 204, 0.2);
      color: #e0f0ff;
      font-size: 15.5px;
      line-height: 1.55;
    }
    
    /* Sidebar enhancements */
    .css-1d391kg, .stSidebar {
      background: linear-gradient(180deg, #0f1620, #1a2333);
      border-right: 2px solid #00ffcc;
    }
    
    /* Buttons & inputs */
    .stButton > button {
      background: linear-gradient(90deg, #00cc99, #00ffcc);
      color: #0a0f1a;
      font-weight: bold;
      border: none;
      padding: 12px 28px;
      border-radius: 8px;
      box-shadow: 0 4px 15px rgba(0, 255, 204, 0.4);
      transition: all 0.3s ease;
    }
    .stButton > button:hover {
      transform: translateY(-2px);
      box-shadow: 0 8px 25px rgba(0, 255, 204, 0.6);
    }
    
    .stTextInput > div > div > input {
      background-color: #1e2a44;
      color: #ffffff;
      border: 2px solid #334455;
    }
    
    /* Log step highlights */
    .stMarkdown h3, .element-container div[data-testid="stMarkdownContainer"] h3 {
      color: #00ffcc !important;
      text-shadow: 0 0 8px rgba(0, 255, 204, 0.5);
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
      background-color: #16213a !important;
      border: 1px solid #334455;
    }
    </style>
""", unsafe_allow_html=True)

# ====================== UI ======================
st.title("🌐 **AUTONOMOUS WEB-AGENT CONTROL ROOM**")
st.markdown("<h3 style='color:#00ffcc; margin-top:-15px;'>ReAct Agent • Live Execution • Real-time Browser</h3>", unsafe_allow_html=True)

with st.sidebar:
    st.info("🔑 **OPENAI_API_KEY** must be set in Streamlit Secrets", icon="🔐")
    st.subheader("🛠️ Available Tools")
    st.markdown("""
    - **`interact_with_webpage`** → Navigate, click, scroll  
    - **`web_search`** → DuckDuckGo / Google News  
    - **`get_entity_info`** → Wikipedia lookups
    """)
    st.markdown("---")
    st.caption("Made more vibrant for better visibility 🔥")

user_prompt = st.text_input(
    "🎯 **Assign mission to the Web Agent:**",
    value="Give me latest news about India and recent activities of Elon Musk.",
    placeholder="E.g. Compare Tesla stock performance and latest SpaceX launches..."
)

col_agent, col_browser = st.columns([1.05, 1], gap="large")

with col_agent:
    st.subheader("🧠 Agent Thought Process & Logs")
    log_container = st.container()

with col_browser:
    st.subheader("🖥️ **Live Browser Viewport**")
    url_display = st.empty()
    viewport_display = st.empty()
    
    # Enhanced initial browser frame
    url_display.markdown(
        '''
        <div class="browser-window">
          <div class="browser-bar">
            <span class="dot dot-red"></span>
            <span class="dot dot-yellow"></span>
            <span class="dot dot-green"></span>
            <div class="url-bar">about:blank</div>
          </div>
        </div>
        ''',
        unsafe_allow_html=True
    )
    viewport_display.info("🚀 Ready. Click **Execute** to launch the agent...")

# ====================== CORE FUNCTIONS ======================
async def execute_browser_action(page, args: dict):
    target_url = args.get("url")
    click_selector = args.get("click_selector")
    scroll_down = args.get("scroll_down", False)

    try:
        if target_url:
            await page.goto(target_url, wait_until="domcontentloaded", timeout=30000)
        if click_selector:
            await asyncio.sleep(1.2)
            await page.click(click_selector)
            await page.wait_for_load_state("domcontentloaded")
        if scroll_down:
            await page.evaluate("window.scrollBy(0, 800)")

        screenshot = await page.screenshot(type="png")
        text = await page.evaluate("() => document.body.innerText")
        current_url = page.url

        return {
            "status": "SUCCESS",
            "current_url": current_url,
            "extracted_text": " ".join(text.split())[:6500],
            "screenshot": screenshot
        }
    except Exception as e:
        return {"status": "ERROR", "error": str(e)}

# ====================== AGENT ======================
async def run_agent(prompt: str):
    try:
        api_key = st.secrets["OPENAI_API_KEY"]
    except Exception:
        st.error("OpenAI API key not found in st.secrets.")
        return

    client = OpenAI(api_key=api_key)

    system_prompt = """You are a precise ReAct web agent."""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ]

    tools = [
        {"type": "function", "function": {"name": "interact_with_webpage", "description": "Navigate, click, scroll", "parameters": {"type": "object", "properties": {"url": {"type": "string"}, "click_selector": {"type": "string"}, "scroll_down": {"type": "boolean"}}, "required": ["url"]}}},
        {"type": "function", "function": {"name": "web_search", "description": "Search web or news", "parameters": {"type": "object", "properties": {"query": {"type": "string"}, "news_mode": {"type": "boolean"}}, "required": ["query"]}}},
        {"type": "function", "function": {"name": "get_entity_info", "description": "Info about entities", "parameters": {"type": "object", "properties": {"entity_name": {"type": "string"}}, "required": ["entity_name"]}}}
    ]

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage", "--disable-gpu"]
        )
        context = await browser.new_context(viewport={"width": 1280, "height": 900})
        page = await context.new_page()

        try:
            for turn in range(7):
                with log_container:
                    st.markdown(f"**Step {turn + 1}**")
                    
                    response = client.chat.completions.create(
                        model="gpt-4o-mini", messages=messages, tools=tools, tool_choice="auto"
                    )

                    msg = response.choices[0].message
                    messages.append(msg)

                    thought = msg.content or "Thinking..."
                    with st.expander(f"💭 Thought (Step {turn+1})", expanded=True):
                        st.markdown(f'<div class="thought-box">{thought}</div>', unsafe_allow_html=True)

                    if not msg.tool_calls:
                        st.success("✅ **Mission Complete**")
                        st.markdown(f"### Final Answer\n{thought}")
                        break

                    for tool_call in msg.tool_calls:
                        fn_name = tool_call.function.name
                        args = json.loads(tool_call.function.arguments)

                        st.markdown(f"🔧 **Tool:** `{fn_name}` → `{json.dumps(args)[:200]}`")

                        if fn_name == "interact_with_webpage":
                            result = await execute_browser_action(page, args)

                        elif fn_name == "web_search":
                            query = args.get("query", "")
                            search_url = f"https://duckduckgo.com/html/?q={query.replace(' ', '+')}"
                            if args.get("news_mode"):
                                search_url = f"https://news.google.com/search?q={query.replace(' ', '+')}"
                            result = await execute_browser_action(page, {"url": search_url})

                        elif fn_name == "get_entity_info":
                            entity = args.get("entity_name", "")
                            wiki_url = f"https://en.wikipedia.org/wiki/{entity.replace(' ', '_')}"
                            result = await execute_browser_action(page, {"url": wiki_url})

                        else:
                            result = {"status": "ERROR", "error": f"Unknown tool: {fn_name}"}

                        if result.get("status") == "SUCCESS":
                            url_display.markdown(
                                f'''
                                <div class="browser-window">
                                  <div class="browser-bar">
                                    <span class="dot dot-red"></span>
                                    <span class="dot dot-yellow"></span>
                                    <span class="dot dot-green"></span>
                                    <div class="url-bar">{result["current_url"]}</div>
                                  </div>
                                </div>
                                ''',
                                unsafe_allow_html=True
                            )
                            viewport_display.image(result["screenshot"], use_container_width=True)
                        else:
                            st.error(f"Tool error: {result.get('error', 'unknown')[:300]}")

                        tool_payload = {
                            "status": result.get("status"),
                            "current_url": result.get("current_url", ""),
                            "extracted_text": result.get("extracted_text", ""),
                            "error": result.get("error", ""),
                        }
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": json.dumps(tool_payload),
                        })
        finally:
            await context.close()
            await browser.close()


if st.button("🚀 **Execute Autonomous Run**", type="primary", use_container_width=True):
    asyncio.run(run_agent(user_prompt))