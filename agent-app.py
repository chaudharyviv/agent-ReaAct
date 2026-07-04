import json
import asyncio
import subprocess
import streamlit as st
import sys
from openai import OpenAI
from playwright.async_api import async_playwright

# ====================== PLAYWRIGHT ======================
@st.cache_resource
def install_playwright_browsers():
    result = subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], capture_output=True, text=True)
    if result.returncode != 0:
        st.error(f"Playwright install failed")
        st.stop()
    return True

install_playwright_browsers()

# ========================= CONFIG & STYLES =========================
st.set_page_config(layout="wide", page_title="AI Agent Live Workspace", page_icon="🤖")

st.markdown("""
<style>
    .stApp { background: linear-gradient(135deg, #0f1620 0%, #1a2333 100%); }
    .thought-box { 
        background: linear-gradient(145deg, #1e2a44, #16213a); padding: 18px; 
        border-radius: 10px; border-left: 6px solid #00ffcc; margin: 12px 0;
        box-shadow: 0 4px 15px rgba(0, 255, 204, 0.25);
    }
    .tool-call { 
        background: #1e2a44; padding: 14px; border-radius: 8px; 
        border-left: 5px solid #ffaa00; margin: 10px 0;
    }
    .tool-result { 
        background: #16213a; padding: 12px; border-radius: 8px; 
        border-left: 5px solid #00cc99; font-size: 14px;
    }
    .summary-box { background: #0f1c2e; padding: 20px; border-radius: 12px; border: 2px solid #00ffcc; }
</style>
""", unsafe_allow_html=True)

st.title("🌐 **AUTONOMOUS WEB-AGENT CONTROL ROOM**")
st.markdown("### ReAct Agent • Live Execution • **Demo Mode**")

with st.sidebar:
    st.info("🔑 Tools lookup", icon="🔐")
    st.subheader("🛠️ Tools")
    st.markdown("""
    - `interact_with_webpage` → Navigate & Interact  
    - `web_search` → Search Web/News  
    - `get_entity_info` → Wikipedia Info
    """)

user_prompt = st.text_input("🎯 **Assign mission to the Web Agent:**", 
                           value="Tell me about the recent news on Deutsche Bank and activities on Elon Musk.")

col_agent, col_browser = st.columns([1.1, 1], gap="large")

with col_agent:
    st.subheader("🧠 Agent Thought Process & Logs")
    log_container = st.container()

with col_browser:
    st.subheader("🖥️ Live Browser Viewport")
    url_display = st.empty()
    viewport_display = st.empty()

# ====================== CORE FUNCTIONS ======================
async def execute_browser_action(page, args: dict):
    # ... (same as before) ...
    try:
        if args.get("url"):
            await page.goto(args.get("url"), wait_until="domcontentloaded", timeout=30000)
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

# ====================== IMPROVED AGENT ======================
async def run_agent(prompt: str):
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

    system_prompt = """You are an expert ReAct web agent. Always think step-by-step and explain your reasoning before calling tools."""

    messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}]

    tools = [
        {"type": "function", "function": {"name": "interact_with_webpage", "description": "Navigate, click, scroll", "parameters": {"type": "object", "properties": {"url": {"type": "string"}, "click_selector": {"type": "string"}, "scroll_down": {"type": "boolean"}}, "required": ["url"]}}},
        {"type": "function", "function": {"name": "web_search", "description": "Search web or news", "parameters": {"type": "object", "properties": {"query": {"type": "string"}, "news_mode": {"type": "boolean"}}, "required": ["query"]}}},
        {"type": "function", "function": {"name": "get_entity_info", "description": "Info about entities", "parameters": {"type": "object", "properties": {"entity_name": {"type": "string"}}, "required": ["entity_name"]}}}
    ]

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        context = await browser.new_context(viewport={"width": 1280, "height": 900})
        page = await context.new_page()

        try:
            for turn in range(8):
                with log_container:
                    st.markdown(f"### **Step {turn + 1}**")

                    response = client.chat.completions.create(
                        model="gpt-4o-mini", messages=messages, tools=tools, tool_choice="auto"
                    )
                    msg = response.choices[0].message
                    messages.append(msg)

                    thought = msg.content.strip() if msg.content else "Planning tool usage..."
                    with st.expander(f"💭 Thought (Step {turn+1})", expanded=True):
                        st.markdown(f'<div class="thought-box">{thought}</div>', unsafe_allow_html=True)

                    if not msg.tool_calls:
                        st.success("✅ **Mission Complete**")
                        st.markdown(f"### Final Answer\n{thought}")
                        break

                    for tool_call in msg.tool_calls:
                        fn_name = tool_call.function.name
                        args = json.loads(tool_call.function.arguments)

                        # Enhanced Tool Display for Demo
                        st.markdown(f"""
                        <div class="tool-call">
                            <strong>🔧 Tool Used:</strong> <span style="color:#ffaa00">{fn_name}</span><br>
                            <strong>Arguments:</strong> {json.dumps(args, indent=2)}
                        </div>
                        """, unsafe_allow_html=True)

                        # Execute tool
                        if fn_name == "web_search":
                            query = args.get("query", "")
                            search_url = f"https://news.google.com/search?q={query.replace(' ', '+')}" if args.get("news_mode") else f"https://duckduckgo.com/html/?q={query.replace(' ', '+')}"
                            result = await execute_browser_action(page, {"url": search_url})
                        elif fn_name == "get_entity_info":
                            result = await execute_browser_action(page, {"url": f"https://en.wikipedia.org/wiki/{args.get('entity_name','').replace(' ','_')}"})
                        else:
                            result = await execute_browser_action(page, args)

                        # Show Result Preview
                        if result.get("status") == "SUCCESS":
                            preview = result["extracted_text"][:800] + "..." if len(result["extracted_text"]) > 800 else result["extracted_text"]
                            st.markdown(f"""
                            <div class="tool-result">
                                <strong>📥 Tool Result:</strong><br>
                                {preview}
                            </div>
                            """, unsafe_allow_html=True)

                            url_display.markdown(f'<div class="browser-bar"><span class="dot dot-red"></span><span class="dot dot-yellow"></span><span class="dot dot-green"></span><div class="url-bar">{result["current_url"]}</div></div>', unsafe_allow_html=True)
                            viewport_display.image(result["screenshot"], use_container_width=True)

                        # Add tool response to history
                        messages.append({"role": "tool", "tool_call_id": tool_call.id, "content": json.dumps({"status": result.get("status"), "extracted_text": result.get("extracted_text","")})})

            # Final Demo Summary
            st.markdown("""
            <div class="summary-box">
                <h3>🔍 Tools Usage Summary</h3>
                <strong>Tools Used:</strong> web_search (x2)<br>
                <strong>Purpose:</strong> Gather latest news on Deutsche Bank and Elon Musk
            </div>
            """, unsafe_allow_html=True)

        finally:
            await context.close()
            await browser.close()


if st.button("🚀 **Launch Agent Demo**", type="primary", use_container_width=True):
    asyncio.run(run_agent(user_prompt))