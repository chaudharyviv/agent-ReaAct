import json
import asyncio
import os
import streamlit as st
from openai import OpenAI
from playwright.async_api import async_playwright

# Install browsers (cached)
@st.cache_resource
def install_playwright():
    os.system("playwright install chromium --with-deps")

install_playwright()

# ========================= CONFIG =========================
st.set_page_config(layout="wide", page_title="AI Agent Live Workspace", page_icon="🤖")

st.markdown("""
    <style>
    .browser-window { border: 2px solid #343a40; border-radius: 8px; background-color: #212529; padding: 4px; box-shadow: 0px 4px 15px rgba(0,0,0,0.3); }
    .browser-bar { background: #343a40; padding: 8px; border-radius: 4px 4px 0 0; color: #fff; font-family: monospace; font-size: 13px; display: flex; align-items: center; }
    .dot { height: 10px; width: 10px; border-radius: 50%; display: inline-block; margin-right: 5px; }
    .dot-red { background: #ff5f56; }
    .dot-yellow { background: #ffbd2e; }
    .dot-green { background: #27c93f; }
    .url-bar { background: #1c1f22; padding: 4px 12px; border-radius: 4px; flex-grow: 1; margin-left: 15px; color: #a9b2c3; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
    .thought-box { background-color: #1e2a38; padding: 12px; border-radius: 6px; border-left: 4px solid #4da6ff; margin-bottom: 10px; }
    </style>
""", unsafe_allow_html=True)

# ====================== SESSION STATE ======================
if "step_logs" not in st.session_state:
    st.session_state.step_logs = []

# ====================== UI ======================
st.title("🌐 Autonomous Web-Agent Control Room")
st.caption("ReAct Agent • Thought Process Visible • Multi-tool")

with st.sidebar:
    st.subheader("Tools")
    st.markdown("""
    - `interact_with_webpage`  
    - `web_search` (Google/News)  
    - `get_entity_info` (Countries, People, etc.)
    """)

user_prompt = st.text_input(
    "Assign mission to the Web Agent:",
    value="Give me latest news about India and recent activities of Elon Musk."
)

col_agent, col_browser = st.columns([1, 1], gap="large")

with col_agent:
    st.subheader("🧠 Agent Thought Process & Logs")
    log_container = st.container()

with col_browser:
    st.subheader("🖥️ Live Browser Viewport")
    url_display = st.empty()
    viewport_display = st.empty()
    
    url_display.markdown(
        '<div class="browser-bar"><span class="dot dot-red"></span><span class="dot dot-yellow"></span>'
        '<span class="dot dot-green"></span><div class="url-bar">about:blank</div></div>',
        unsafe_allow_html=True
    )
    viewport_display.info("Awaiting task...")

# ====================== TOOLS ======================
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

# ====================== AGENT RUN ======================
async def run_agent(prompt: str):
    try:
        api_key = st.secrets["OPENAI_API_KEY"]
    except Exception:
        st.error("OpenAI API key not found in st.secrets. Add it in app settings.")
        return

    client = OpenAI(api_key=api_key)

    system_prompt = """You are a precise ReAct web agent. Think step-by-step before every action.
    Use the best tool for the task. For news use web_search, for people/countries use get_entity_info."""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ]

    # Complete Tools Definition
    tools = [
        {
            "type": "function",
            "function": {
                "name": "interact_with_webpage",
                "description": "Navigate to any URL, click elements, scroll, and extract content.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {"type": "string"},
                        "click_selector": {"type": "string"},
                        "scroll_down": {"type": "boolean"}
                    },
                    "required": ["url"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "web_search",
                "description": "Search the web or news.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "news_mode": {"type": "boolean"}
                    },
                    "required": ["query"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_entity_info",
                "description": "Get information about countries, personalities, companies.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "entity_name": {"type": "string"},
                        "focus": {"type": "string"}
                    },
                    "required": ["entity_name"]
                }
            }
        }
    ]

    async with async_playwright() as p:
        # Improved launch settings for Streamlit Cloud / containers
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--disable-extensions"
            ]
        )
        context = await browser.new_context(viewport={"width": 1280, "height": 900})
        page = await context.new_page()

        try:
            for turn in range(7):
                with log_container:
                    st.markdown(f"**Step {turn + 1}**")
                    
                    response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=messages,
                        tools=tools,
                        tool_choice="auto"
                    )

                    msg = response.choices[0].message
                    messages.append(msg)

                    # Thought Visualization
                    thought = msg.content or "Deciding next action..."
                    with st.expander(f"💭 Thought (Step {turn+1})", expanded=True):
                        st.markdown(f'<div class="thought-box">{thought}</div>', unsafe_allow_html=True)

                    if not msg.tool_calls:
                        st.success("✅ Final Answer Ready")
                        st.markdown(f"### Summary\n{thought}")
                        break

                    for tool_call in msg.tool_calls:
                        args = json.loads(tool_call.function.arguments)
                        
                        with st.expander(f"⚡ Action", expanded=True):
                            st.write(f"**Tool**: {tool_call.function.name}")
                            st.write(f"**Args**: {args}")

                        result = None
                        if tool_call.function.name == "interact_with_webpage":
                            result = await execute_browser_action(page, args)
                        elif tool_call.function.name == "web_search":
                            q = args.get("query", "")
                            is_news = args.get("news_mode", False)
                            base = "https://news.google.com" if is_news else "https://www.google.com"
                            url = f"{base}/search?q={q.replace(' ', '+')}"
                            result = await execute_browser_action(page, {"url": url, "scroll_down": True})
                        elif tool_call.function.name == "get_entity_info":
                            entity = args.get("entity_name", "").replace(" ", "_")
                            url = f"https://en.wikipedia.org/wiki/{entity}"
                            result = await execute_browser_action(page, {"url": url, "scroll_down": True})

                        # Observation
                        obs_preview = result.get("extracted_text", "")[:500] if result else "Error"
                        with st.expander("👁️ Observation", expanded=True):
                            st.write(f"Status: {result.get('status', 'Failed')}")
                            st.write(f"URL: {result.get('current_url', 'N/A')}")
                            st.text_area("Content Preview", obs_preview, height=150)

                        # Live UI Update
                        if result and "current_url" in result:
                            url_display.markdown(
                                f'<div class="browser-bar"><span class="dot dot-red"></span>'
                                f'<span class="dot dot-yellow"></span><span class="dot dot-green"></span>'
                                f'<div class="url-bar">{result["current_url"]}</div></div>',
                                unsafe_allow_html=True
                            )
                        if result and "screenshot" in result:
                            viewport_display.image(result["screenshot"], use_container_width=True)

                        # Feed observation back
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": tool_call.function.name,
                            "content": json.dumps(result)
                        })

        finally:
            await context.close()
            await browser.close()


# ====================== TRIGGER ======================
if st.button("🚀 Execute Autonomous Run", type="primary"):
    asyncio.run(run_agent(user_prompt))
