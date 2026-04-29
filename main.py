from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
import random

# 六十四卦简表（先用8个做测试，后续补全）
HEXAGRAMS = {
    "乾为天": {"卦辞": "元亨利贞", "等级": "大吉"},
    "坤为地": {"卦辞": "元亨，利牝马之贞", "等级": "中吉"},
    "水雷屯": {"卦辞": "元亨利贞，勿用有攸往", "等级": "小凶"},
    "山水蒙": {"卦辞": "亨，匪我求童蒙，童蒙求我", "等级": "平"},
    "水天需": {"卦辞": "有孚，光亨，贞吉", "等级": "小吉"},
    "天水讼": {"卦辞": "有孚窒惕，中吉终凶", "等级": "中凶"},
    "地水师": {"卦辞": "贞，丈人吉，无咎", "等级": "小吉"},
    "水地比": {"卦辞": "吉，原筮元永贞，无咎", "等级": "大吉"},
}

@register("astrbot_plugin_iching_flag", "fengse7", "一个结合周易卦象与Flag打脸监督的插件", "1.0.0")
class IChingFlagPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        logger.info("周易Flag插件已加载")

    @filter.command("算卦")
    async def divination(self, event: AstrMessageEvent):
        '''随机抽取一卦'''
        name, data = random.choice(list(HEXAGRAMS.items()))
        user_name = event.get_sender_name()
        result = (
            f"🎋 {user_name} 摇了一卦...\n\n"
            f"卦象：【{name}】\n"
            f"等级：{data['等级']}\n"
            f"卦辞：{data['卦辞']}"
        )
        yield event.plain_result(result)