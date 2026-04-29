from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
import random
import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join("data", "iching_flag.db")

# 八卦符号映射
TRIGRAM_SYMBOLS = {
    "乾": "☰", "坤": "☷", "震": "☳", "巽": "☴",
    "坎": "☵", "离": "☲", "艮": "☶", "兑": "☱",
}

# 64卦数据（目前8卦，后续补全）
HEXAGRAMS = {
    "乾为天": {
        "上卦": "乾", "下卦": "乾",
        "等级": "上吉",
        "卦辞": "元亨利贞。",
        "解读": "大吉大利，万事亨通。",
        "时运": "位极人臣，名利双收。",
        "财运": "大有可为，一本万利。",
        "感情": "两情相悦，天作之合。",
    },
    "坤为地": {
        "上卦": "坤", "下卦": "坤",
        "等级": "中吉",
        "卦辞": "元亨，利牝马之贞。",
        "解读": "柔顺包容，厚德载物。",
        "时运": "脚踏实地，稳步上升。",
        "财运": "稳定增长，不宜投机。",
        "感情": "相敬如宾，细水长流。",
    },
    "水雷屯": {
        "上卦": "坎", "下卦": "震",
        "等级": "下凶",
        "卦辞": "元亨利贞，勿用有攸往。",
        "解读": "万事开头难，宜守不宜攻。",
        "时运": "初创艰难，需忍耐。",
        "财运": "投入较大，回报未显。",
        "感情": "好事多磨，勿急于求成。",
    },
    "山水蒙": {
        "上卦": "艮", "下卦": "坎",
        "等级": "平",
        "卦辞": "亨，匪我求童蒙，童蒙求我。",
        "解读": "蒙昧初开，需要耐心引导。",
        "时运": "尚未明朗，等待时机。",
        "财运": "勿轻信他人，防被骗。",
        "感情": "对方心意未明，再观察。",
    },
    "水天需": {
        "上卦": "坎", "下卦": "乾",
        "等级": "中吉",
        "卦辞": "有孚，光亨，贞吉。",
        "解读": "耐心等待，光明在前。",
        "时运": "时机将至，稍安勿躁。",
        "财运": "守成即可，不宜冒进。",
        "感情": "水到渠成，不必强求。",
    },
    "天水讼": {
        "上卦": "乾", "下卦": "坎",
        "等级": "中凶",
        "卦辞": "有孚窒惕，中吉终凶。",
        "解读": "争执不利，退一步海阔天空。",
        "时运": "易生口舌，谨言慎行。",
        "财运": "恐有纠纷，合同需谨慎。",
        "感情": "意见不合，需多沟通。",
    },
    "地水师": {
        "上卦": "坤", "下卦": "坎",
        "等级": "中吉",
        "卦辞": "贞，丈人吉，无咎。",
        "解读": "有组织有纪律则吉，得遇良师。",
        "时运": "得贵人提携，前途光明。",
        "财运": "与人合伙，共享收益。",
        "感情": "长辈介绍，可考虑。",
    },
    "水地比": {
        "上卦": "坎", "下卦": "坤",
        "等级": "上吉",
        "卦辞": "吉，原筮元永贞，无咎。",
        "解读": "比卦：吉利。同时再卜筮，仍然大吉大利。",
        "时运": "众人相贺，荣显之极。",
        "财运": "善人相扶，大发利市。",
        "感情": "异性缘多，但烦恼也多。",
    },
}

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS flags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            group_id TEXT NOT NULL,
            user_name TEXT,
            flag_content TEXT NOT NULL,
            hexagram_name TEXT,
            hexagram_level TEXT,
            status TEXT DEFAULT '进行中',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            judged_at TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

@register("astrbot_plugin_iching_flag", "fengse7", "一个结合周易卦象与Flag打脸监督的插件", "1.0.0")
class IChingFlagPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        init_db()
        logger.info("周易Flag插件已加载")

    @filter.command("算卦")
    async def divination(self, event: AstrMessageEvent):
        name, data = random.choice(list(HEXAGRAMS.items()))
        user_name = event.get_sender_name()
        upper = TRIGRAM_SYMBOLS.get(data["上卦"], "?")
        lower = TRIGRAM_SYMBOLS.get(data["下卦"], "?")

        result = (
            f"🎋 {user_name} 摇了一卦...\n\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"{upper} {lower} 【{name}】\n"
            f"等级：{data['等级']} ⭐\n"
            f"━━━━━━━━━━━━━━━━\n\n"
            f"📜 卦辞：{data['卦辞']}\n\n"
            f"💬 解读：{data['解读']}\n\n"
            f"时运：{data['时运']}\n"
            f"财运：{data['财运']}\n"
            f"感情：{data['感情']}"
        )
        yield event.plain_result(result)