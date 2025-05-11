import logging
import os
from logging.handlers import RotatingFileHandler

# ========== 🎨 Formatter ==========
formatter = logging.Formatter(
    "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
)

# ========== 🗃️ Log File Path and Directory ==========
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)  # Create log directory if it doesn't exist
log_file = os.path.join(log_dir, "user_manager.log")

# ========== 🔧 Logger Factory Function ==========
def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Prevent duplicate handlers (very important!)
    if not logger.handlers:
        # ========== 🗃️ Rotating File Handler ==========
        log_size = 5 * 1024 * 1024  # 5 MB
        fh = RotatingFileHandler(log_file, maxBytes=log_size, backupCount=3)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

        # ========== 🖥️ Optional: Terminal Output ==========
        # ch = logging.StreamHandler()
        # ch.setFormatter(formatter)
        # logger.addHandler(ch)

    return logger

"""
📚 === EMOJI LOGGER CHEAT SHEET ===

🔥 Basic Logging Levels with Emojis

| Level         | Emoji(s)                              | Vibe / Usage                                      |
|---------------|----------------------------------------|---------------------------------------------------|
| DEBUG         | 🐛 🔍 🧠 🛠️                          | Dev insights, bug hunting, internal values        |
| INFO          | ℹ️ ✅ 📘 🧾 🪄                         | Normal ops, tracking flow                         |
| SUCCESS       | ✅ 🎉 🟢 🚀 💯                         | Task done, ops success                            |
| WARNING       | ⚠️ 🟡 👀 🚧 🫣                         | Something fishy, not broken yet                   |
| ERROR         | ❌ 🔴 🛑 💥 🤬                         | Something failed, needs fix                       |
| CRITICAL      | 💣 🚨 🔥 😱 💀                        | System down, emergency!                         

🔮 Context-Specific Emojis

| Context             | Emoji(s)                        |
|---------------------|---------------------------------|
| API Call            | 🌐 📡 📲                        |
| Database            | 🗄️ 💾 📦                        |
| Authentication      | 🔐 🧑‍💻 🪪                      |
| File System         | 📁 📝 📂                        |
| Time/Delay          | ⏳ ⏰ 🕒                        |
| Start/Init          | 🟢 🚀 🛫                        |
| Shutdown/Exit       | 🔚 🛑 👋                        |
| Network/Proxy       | 🌍 🕸️ 🧱                       |
| Retry/Loop          | 🔁 ♻️ 🔄                       |

🧪 Example Usage

    logger.debug("🐛 Debugging the user flow")
    logger.info("ℹ️ App initialized")
    logger.warning("⚠️ Disk space low")
    logger.error("❌ Couldn't connect to DB")
    logger.critical("💀 Kernel panic. Goodbye.")
"""




