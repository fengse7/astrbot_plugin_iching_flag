from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
from astrbot.api.event.filter import event_message_type, EventMessageType
import random, sqlite3, os, re
from datetime import datetime, date, timedelta

DB_PATH = os.path.join("data", "iching_flag.db")
pending_judge = {}
pending_punish = {}
daily_counter = {}
DAILY_DIV_LIMIT = 1
DAILY_SLAP_LIMIT = 3
CALLBACK_CHANCE = 0.6

TRIGRAM_SYMBOLS = {"乾":"☰","坤":"☷","震":"☳","巽":"☴","坎":"☵","离":"☲","艮":"☶","兑":"☱"}

HEXAGRAMS = {
    "乾为天":{"上卦":"乾","下卦":"乾","等级":"上吉","卦辞":"元亨利贞。","解读":"大吉大利，万事亨通。","吐槽":"哼～今天运气好得让人嫉妒呢✨ 事业财运桃花全开花，今天你说啥都对，但别太得意哦，人家盯着你呢～"},
    "坤为地":{"上卦":"坤","下卦":"坤","等级":"中吉","卦辞":"元亨，利牝马之贞。","解读":"柔顺包容，厚德载物。","吐槽":"喔～稳得一批呢🌱 财运平平但不会亏，感情也温温的，今天就是个老实人，挺好挺好，继续保持～"},
    "水雷屯":{"上卦":"坎","下卦":"震","等级":"下凶","卦辞":"元亨利贞，勿用有攸往。","解读":"万事开头难，宜守不宜攻。","吐槽":"噗～这卦一看就不妙😮 财没影，情路堵，干啥都卡关，今天乖乖躺平别折腾啦，不然人家要笑话你了～"},
    "山水蒙":{"上卦":"艮","下卦":"坎","等级":"平","卦辞":"亨，匪我求童蒙，童蒙求我。","解读":"蒙昧初开，需要耐心引导。","吐槽":"诶～一脸懵逼的状态呢😐 财运看不清，感情也猜不透，今天多说多错，闭上嘴装高手最安全～"},
    "水天需":{"上卦":"坎","下卦":"乾","等级":"中吉","卦辞":"有孚，光亨，贞吉。","解读":"耐心等待，光明在前。","吐槽":"哎呀～好事快来了但还没到呢⏳ 财运感情都在路上，今天耐心点别急，急也没用略略略～"},
    "天水讼":{"上卦":"乾","下卦":"坎","等级":"中凶","卦辞":"有孚窒惕，中吉终凶。","解读":"争执不利，退一步海阔天空。","吐槽":"哎呦～火药味有点重哦⚠️ 今天容易跟人吵起来，钱包和感情都危险，管好嘴巴别来找我哭～"},
    "地水师":{"上卦":"坤","下卦":"坎","等级":"小凶","卦辞":"贞，丈人吉，无咎。","解读":"有组织有纪律则吉，得遇良师。","吐槽":"哼～今天装得还挺像领导的嘛⚔️ 财运合伙还行，感情长辈介绍的可考虑，但别是纸上谈兵哦～"},
    "水地比":{"上卦":"坎","下卦":"坤","等级":"上吉","卦辞":"吉，原筮元永贞，无咎。","解读":"比卦：吉利。同时再卜筮，仍然大吉大利。","吐槽":"呀～人缘好得不像话呢🤝 财运跟着沾光，追求者又多了一个...啧，太受欢迎也是一种烦恼呢，真替你累～"},
    "风天小畜":{"上卦":"巽","下卦":"乾","等级":"小吉","卦辞":"亨，密云不雨，自我西郊。","解读":"小有积蓄，时机未到。","吐槽":"嗯～小小的好运在酝酿呢🌬️ 财不多但够花，感情慢慢来，今天别膨胀，攒着点人品～"},
    "天泽履":{"上卦":"乾","下卦":"兑","等级":"平","卦辞":"履虎尾，不咥人，亨。","解读":"如履薄冰，小心行事。","吐槽":"呀～今天踩在老虎尾巴上了⚠️ 财运风险大，感情小心翼翼，走稳每一步，摔了人家可不扶你～"},
    "地天泰":{"上卦":"坤","下卦":"乾","等级":"上吉","卦辞":"小往大来，吉亨。","解读":"否极泰来，万事顺遂。","吐槽":"哇～时来运转了呢✨ 财运感情全面开花，今天你就是锦鲤本鲤，羡慕死人家了～"},
    "天地否":{"上卦":"乾","下卦":"坤","等级":"中凶","卦辞":"否之匪人，不利君子贞。","解读":"闭塞不通，小人当道。","吐槽":"啧～今天运气堵得慌😈 财运破财感情冷战，干啥啥不顺，建议关机睡觉保平安～"},
    "天火同人":{"上卦":"乾","下卦":"离","等级":"中吉","卦辞":"同人于野，亨。","解读":"志同道合，团结一致。","吐槽":"哼～今天人缘不错嘛🔥 朋友带财，感情心有灵犀，抱团取暖比单打独斗强多啦～"},
    "火天大有":{"上卦":"离","下卦":"乾","等级":"上吉","卦辞":"元亨。","解读":"大有收获，丰收之年。","吐槽":"哇塞～大丰收呢🌟 财运旺到冒烟，感情热情似火，今天你是行走的锦鲤，别忘了请客！"},
    "地山谦":{"上卦":"坤","下卦":"艮","等级":"上吉","卦辞":"亨，君子有终。","解读":"谦虚谨慎，终得善果。","吐槽":"哼～低调反而运气好呢🏔️ 财运稳感情顺，今天不显摆反而有好报，继续保持乖宝宝人设～"},
    "雷地豫":{"上卦":"震","下卦":"坤","等级":"中吉","卦辞":"利建侯行师。","解读":"欢愉快乐，顺势而为。","吐槽":"诶嘿～心情好得不行呢😊 财运见好就收，感情甜甜的，今天适合享受，别想太多烦心事～"},
    "泽雷随":{"上卦":"兑","下卦":"震","等级":"小吉","卦辞":"元亨利贞，无咎。","解读":"随和顺从，随机应变。","吐槽":"嘛～跟着感觉走就对了💧 财运随行就市，感情顺其自然，今天别倔，顺着来反而有惊喜～"},
    "山风蛊":{"上卦":"艮","下卦":"巽","等级":"小凶","卦辞":"元亨，利涉大川。","解读":"蛊惑腐败，需整治。","吐槽":"咦～今天是不是有人在挖坑🐛 财运混乱感情要修复，睁大眼睛别被忽悠啦，人家可不替你背锅～"},
    "地泽临":{"上卦":"坤","下卦":"兑","等级":"中吉","卦辞":"元亨利贞。","解读":"居高临下，监督视察。","吐槽":"哦～好运在靠近了呢👑 财运感情都主动点，今天适合出击，别等着天上掉馅饼～"},
    "风地观":{"上卦":"巽","下卦":"坤","等级":"平","卦辞":"盥而不荐，有孚颙若。","解读":"观察等待，不宜行动。","吐槽":"嘘～今天适合暗中观察👀 财运多看少动，感情也是观望期，别急着表态，先看清楚再说～"},
    "火雷噬嗑":{"上卦":"离","下卦":"震","等级":"小凶","卦辞":"亨，利用狱。","解读":"咬合咀嚼，排除障碍。","吐槽":"嘶～今天有点咬手呢🔥 财运纠纷感情吵架，有坎得硬啃，不过啃完就好啦，加油哦～"},
    "山火贲":{"上卦":"艮","下卦":"离","等级":"小吉","卦辞":"亨，小利有攸往。","解读":"装饰美化，注重外表。","吐槽":"哎哟～今天挺会打扮的嘛💅 表面风光有小财，感情仪式感拉满，但别光顾着好看忘了里子～"},
    "山地剥":{"上卦":"艮","下卦":"坤","等级":"中凶","卦辞":"不利有攸往。","解读":"剥落衰败，小人得势。","吐槽":"啊啦～今天运气往下掉呢😬 财运亏感情崩，小人猖狂你躺平，今天别挣扎，苟住就是赢～"},
    "地雷复":{"上卦":"坤","下卦":"震","等级":"中吉","卦辞":"亨，出入无疾。","解读":"一阳来复，万象更新。","吐槽":"嘿～转运了呢🔄 财运回升感情破镜重圆，今天否极泰来，趁热打铁别墨迹～"},
    "天雷无妄":{"上卦":"乾","下卦":"震","等级":"小吉","卦辞":"元亨利贞。","解读":"不妄为，顺其自然。","吐槽":"嗯～今天别瞎折腾就行🤨 财运平平感情真诚就好，做多了反而坏事，佛系一天吧～"},
    "山天大畜":{"上卦":"艮","下卦":"乾","等级":"中吉","卦辞":"利贞，不家食吉。","解读":"大积蓄，厚积薄发。","吐槽":"哼～攒人品呢💪 财运厚积感情稳，今天不显山露水但底气十足，迟早亮瞎他们～"},
    "山雷颐":{"上卦":"艮","下卦":"震","等级":"平","卦辞":"贞吉，观颐，自求口实。","解读":"颐养天年，自食其力。","吐槽":"呼～今天养生局🍵 财运自给自足，感情细水长流，别激动别亢奋，喝口茶稳稳过～"},
    "泽风大过":{"上卦":"兑","下卦":"巽","等级":"中凶","卦辞":"栋桡，利有攸往，亨。","解读":"太过分了，物极必反。","吐槽":"哇啊～今天是不是用力过猛了😅 财运负担重感情过度依赖，悠着点，过犹不及懂不懂～"},
    "坎为水":{"上卦":"坎","下卦":"坎","等级":"下凶","卦辞":"习坎，有孚，维心亨。","解读":"重重险阻，保持信心。","吐槽":"嘶～双重水逆呢🌊👻 财运亏感情丧，一波未平一波又起，今天苟住别浪，人家心疼你一秒钟～"},
    "离为火":{"上卦":"离","下卦":"离","等级":"中吉","卦辞":"利贞，亨，畜牝牛吉。","解读":"光明依附，柔顺为吉。","吐槽":"哇～今天闪闪发光呢🔆 财运稳感情暖，温柔一点反而运气更好，今天当个软妹～"},
    "泽山咸":{"上卦":"兑","下卦":"艮","等级":"小吉","卦辞":"亨，利贞，取女吉。","解读":"感应相通，心有灵犀。","吐槽":"诶嘿～今天心有灵犀呢💕 人际和谐合作愉快，感情说不定有惊喜，保持感应哦～"},
    "雷风恒":{"上卦":"震","下卦":"巽","等级":"中吉","卦辞":"亨，无咎，利贞。","解读":"持之以恒，长久之道。","吐槽":"哼～坚持就是胜利呢⏳ 财运长期投资，感情长长久久，今天不冒进，稳一手～"},
    "天山遁":{"上卦":"乾","下卦":"艮","等级":"小凶","卦辞":"亨，小利贞。","解读":"退避三舍，明哲保身。","吐槽":"诶～今天适合跑路呢🏃 财运止损感情冷静，遇到麻烦先撤退，不丢人，这叫战略转移～"},
    "雷天大壮":{"上卦":"震","下卦":"乾","等级":"中吉","卦辞":"利贞。","解读":"强盛壮大，勿用非礼。","吐槽":"哇哦～今天气势十足呢💥 财运大涨感情奔放，别太猛了吓到别人，收敛点更好～"},
    "火地晋":{"上卦":"离","下卦":"坤","等级":"小吉","卦辞":"康侯用锡马蕃庶。","解读":"晋升进步，蒸蒸日上。","吐槽":"嘿～今天在往上走呢🌅 财运增感情升温，一步一步爬，别急，爬到顶了记得拉人家一把～"},
    "地火明夷":{"上卦":"坤","下卦":"离","等级":"中凶","卦辞":"利艰贞。","解读":"光明受伤，韬光养晦。","吐槽":"诶...今天有点灰暗呢😔 财运暗亏感情受伤，别硬撑，该哭就哭，人家勉强借你个肩膀～"},
    "风火家人":{"上卦":"巽","下卦":"离","等级":"小吉","卦辞":"利女贞。","解读":"家庭和睦，各司其职。","吐槽":"唔～今天家宅气满满呢🏠 财运家庭开支，感情温馨和睦，适合宅着，出门反而破运～"},
    "火泽睽":{"上卦":"离","下卦":"兑","等级":"小凶","卦辞":"小事吉。","解读":"分歧不合，求同存异。","吐槽":"啧～今天跟人对不上频呢🤷 合伙不利感情吵架，小事能成大事别想，忍忍就过去了～"},
    "水山蹇":{"上卦":"坎","下卦":"艮","等级":"下凶","卦辞":"利西南，不利东北。","解读":"艰难险阻，寸步难行。","吐槽":"呜哇～今天卡成狗了🚧 财运陷坑感情坎坷，几乎寸步难行，今天躺平不丢人，苟着等风来～"},
    "雷水解":{"上卦":"震","下卦":"坎","等级":"中吉","卦辞":"利西南，无所往。","解读":"困难解除，雨过天晴。","吐槽":"呀～雨过天晴了呢🌈 财运止损回升，感情误会解除，今天啥都顺了，开香槟～"},
    "山泽损":{"上卦":"艮","下卦":"兑","等级":"小凶","卦辞":"有孚，元吉，无咎。","解读":"损下益上，有失有得。","吐槽":"唔...今天要交点保护费呢⚖️ 财运有损感情付出多，有失才有得，就当攒人品了～"},
    "风雷益":{"上卦":"巽","下卦":"震","等级":"上吉","卦辞":"利有攸往，利涉大川。","解读":"增益有利，大有可为。","吐槽":"呀哈～今天旺到飞起呢🍀 财运收益感情互相成就，干啥啥顺，多说几句好话吸好运～"},
    "泽天夬":{"上卦":"兑","下卦":"乾","等级":"小吉","卦辞":"扬于王庭，孚号有厉。","解读":"决断果敢，当断则断。","吐槽":"哼～该出手时就出手呢⚡ 财运果断出手，感情该断则断，今天不犹豫，犹豫就败北～"},
    "天风姤":{"上卦":"乾","下卦":"巽","等级":"平","卦辞":"女壮，勿用取女。","解读":"不期而遇，邂逅相逢。","吐槽":"诶～今天有偶遇呢💫 意外之财或桃花，但不一定是好事哦，看清楚再上，人家怕你被坑～"},
    "泽地萃":{"上卦":"兑","下卦":"坤","等级":"小吉","卦辞":"亨，王假有庙。","解读":"群英荟萃，聚集一堂。","吐槽":"哇～今天人气爆棚呢🎯 众人拾柴财运旺，聚会可能遇桃花，好好表现别丢人～"},
    "地风升":{"上卦":"坤","下卦":"巽","等级":"中吉","卦辞":"元亨，用见大人。","解读":"步步高升，前程似锦。","吐槽":"耶～今天在升级呢📈 财运增长感情升温，一步一个台阶，加油登顶人家看好你哦～"},
    "泽水困":{"上卦":"兑","下卦":"坎","等级":"下凶","卦辞":"亨，贞，大人吉。","解读":"困厄窘迫，坚守待援。","吐槽":"啊...今天困住了呢🕳️ 资金紧张感情被困，四面楚歌但别放弃，撑着撑着就出头了～"},
    "水风井":{"上卦":"坎","下卦":"巽","等级":"平","卦辞":"改邑不改井，无丧无得。","解读":"井养不穷，稳定不变。","吐槽":"嘛～今天跟昨天一样呢💧 财运平平感情不变，无聊但安全，稳定也是一种福气啦～"},
    "泽火革":{"上卦":"兑","下卦":"离","等级":"小吉","卦辞":"己日乃孚，元亨利贞。","解读":"变革革新，除旧布新。","吐槽":"哦呀～今天要搞事情呢🔥 财运转换赛道感情要变革，旧的不去新的不来，冲鸭～"},
    "火风鼎":{"上卦":"离","下卦":"巽","等级":"上吉","卦辞":"元吉，亨。","解读":"鼎立天下，稳固权威。","吐槽":"哇哦～今天稳如泰山呢🍳 财源广进感情稳定，地位稳固说话管用，今天你就是大佬！"},
    "震为雷":{"上卦":"震","下卦":"震","等级":"小凶","卦辞":"亨，震来虩虩，笑言哑哑。","解读":"惊雷震动，临危不乱。","吐槽":"哎哟～今天一惊一乍的⚡ 财运大起大落感情也刺激，别被吓到，人家等着看你笑话呢～"},
    "艮为山":{"上卦":"艮","下卦":"艮","等级":"平","卦辞":"艮其背，不获其身。","解读":"停止不前，适可而止。","吐槽":"唔...今天卡住了呢🏔️ 财运不动感情止步，不是坏事，停一停看看风景再走～"},
    "风山渐":{"上卦":"巽","下卦":"艮","等级":"小吉","卦辞":"女归吉，利贞。","解读":"循序渐进，水到渠成。","吐槽":"嗯～一步一个脚印呢👣 财运渐涨感情慢慢培养，不急不急，好事多磨，磨出来才香～"},
    "雷泽归妹":{"上卦":"震","下卦":"兑","等级":"小凶","卦辞":"征凶，无攸利。","解读":"少女出嫁，名不正言不顺。","吐槽":"呀...这名分有点问题呢💍 投资不当感情不对等，别急着上船，看清楚是不是贼船～"},
    "雷火丰":{"上卦":"震","下卦":"离","等级":"中吉","卦辞":"亨，王假之，勿忧。","解读":"丰盛盈满，盛极一时。","吐槽":"哇哈～大丰收呢💪🔥 财运爆棚感情热烈，巅峰时刻别掉链子，趁热打铁！"},
    "火山旅":{"上卦":"离","下卦":"艮","等级":"小凶","卦辞":"小亨，旅贞吉。","解读":"旅途漂泊，居无定所。","吐槽":"诶～今天奔波劳碌呢🧳 开销大感情异地，漂泊不定的日子，就当旅行了～"},
    "巽为风":{"上卦":"巽","下卦":"巽","等级":"小吉","卦辞":"小亨，利有攸往。","解读":"顺风而行，柔顺谦逊。","吐槽":"呼呼～今天顺风呢🌬️ 小财入账感情温柔，顺着来别逆风，今天当个软软的小可爱～"},
    "兑为泽":{"上卦":"兑","下卦":"兑","等级":"小吉","卦辞":"亨，利贞。","解读":"喜悦和悦，朋友讲习。","吐槽":"嘻嘻～今天心情好好呢😊 小利入袋感情甜蜜，开心就笑出来，今天不喷你了，享福吧～"},
    "风水涣":{"上卦":"巽","下卦":"坎","等级":"平","卦辞":"亨，王假有庙。","解读":"涣散分离，聚散无常。","吐槽":"唔...今天有点散呢💨 财分散感情聚少离多，别强求，该散的散该来的来～"},
    "水泽节":{"上卦":"坎","下卦":"兑","等级":"小吉","卦辞":"亨，苦节不可贞。","解读":"节制适度，过犹不及。","吐槽":"嗯哼～今天有节制呢✅ 不铺张不抠门刚刚好，感情也适度，多了少了都不好～"},
    "风泽中孚":{"上卦":"巽","下卦":"兑","等级":"中吉","卦辞":"豚鱼吉，利涉大川。","解读":"诚信忠信，感化他人。","吐槽":"哼～以诚待人有好报呢🤞 诚信得财真心换真心，今天做个诚实的好孩子，运气自己来～"},
    "雷山小过":{"上卦":"震","下卦":"艮","等级":"小凶","卦辞":"亨，利贞，可小事。","解读":"小有过失，宜下不宜上。","吐槽":"哎呀～一点点小翻车呢🤏 小亏损小摩擦，问题不大但有点烦，忍忍就过了～"},
    "水火既济":{"上卦":"坎","下卦":"离","等级":"中吉","卦辞":"亨小，利贞，初吉终乱。","解读":"大功告成，盛极将衰。","吐槽":"哈～大功告成呢🎉 财到手情稳定，但别得意太早，巅峰之后容易下坡，见好就收哦～"},
    "火水未济":{"上卦":"离","下卦":"坎","等级":"小凶","卦辞":"亨，小狐汔济，濡其尾。","解读":"未完成，功败垂成。","吐槽":"啧～差一点就成呢🤡 财差一步感情临门一脚，功败垂成最气人，别灰心，再来一次嘛～"},
}

FLAG_FORTUNE_MSG = {
    "吉": ["诶～抽到{hex}呢，运气不错嘛～不过Flag这种东西，卦象再好也得看你能不能坚持呢～⭐","{hex}？哼，算你走运～但别以为卦好就能躺赢哦，人家可盯着你呢～","哇～{hex}！天时地利都有了，就差你那点执行力啦，加油哦大哥哥～🎀"],
    "凶": ["噗...{hex}！这卦象也太诚实了吧～你这Flag怕是要变成墓碑了哦🎀","哎呀呀～{hex}呢～天道都说你不行诶，要不趁早把Flag删了，假装什么都没发生？🤭","{hex}！哼哼～卦象已经看穿一切了，你这Flag立得越狠，打脸来得越快呢～🎪","哦豁～{hex}！我建议你现在就截图保存，等打脸那天拿出来回味，一定很有趣～😏"],
}
SLAP_MSG = ["嘿嘿～看看人家挖到了什么宝贝？{name}的Flag哦～📜","诶嘿嘿，考古时间到！{name}同学，这份黑历史你还记得吗～？","噗，翻到好东西了！{name}曾经信誓旦旦说过的话呢～要不要来验收一下？"]
SUCCESS_MSG = ["诶～居然真的实现了？！人家都准备好嘲笑你了，这下倒是我看走眼了...哼，算你厉害！😤","居、居然做到了？！不可能不可能...好吧，这次算你赢了啦，恭喜恭喜～🎉","啊？！真的假的...我还等着笑话你呢。这次就勉为其难夸你一句：了不起！⭐"]
FAIL_MSG = ["噗哈哈哈哈！果然失败了！人家早就知道会这样啦～🤭","啊啦～这不是意料之中嘛？下次立Flag之前先照照镜子啦～💅","看吧看吧～我就说嘛。Flag这种东西就是用来倒的呀，常识常识～😘"]
FAIL_BAD_OMEN = ["哈哈哈哈哈哈！{hex}早就预言了这一切！卦不欺人，就欺你～📜✨","诶～当时{hex}的卦象不是说得很清楚了嘛？「你会失败」！你看，卦象多诚实啊～😏","噗～从你抽到{hex}那一刻起，结果就注定啦。天道好轮回，苍天饶过谁～🎪"]
PUNISH_TEMPLATES = ["在群里发「{content}」×10","把群昵称改成「{content}」挂一天","下次发言前先发「咕咕咕，{content}」"]

FORTUNE_CALLBACK = {
    "乾为天": ["☰☰ 乾为天～上吉之人说话就是硬气呢，人家今天勉强听你的好了 ✨","天行健～你今天的状态居然配得上这卦，难得难得～"],
    "坤为地": ["☷☷ 坤为地～你这话说得还挺稳重的嘛，今天装什么靠谱人设呢 🌱","地势坤～今天散发着一股老实人的气息呢，继续保持哦～"],
    "水雷屯": ["☵☳ 水雷屯～万事开头难，你这话说得挺勇，但能撑过三天吗 🤔","屯卦在此～你确定不是在给自己挖坑？人家好期待后续发展呢～"],
    "山水蒙": ["☶☵ 山水蒙～你说这话的时候自己也没想清楚吧，一脸蒙 😂","蒙卦在此～发言前先过过脑子啦，虽然你可能没有～"],
    "水天需": ["☵☰ 水天需～时机未到呢，急什么急，等着看戏ing ⏳","需卦来了～别急嘛，反正急也没用，陪人家一起等呗～"],
    "天水讼": ["☰☵ 天水讼～小心说话哦，今天容易被打脸，不过那场面一定很有趣 ⚖️","讼卦在此～你今天发言带刺呢，待会别哭着来找我～"],
    "地水师": ["☷☵ 地水师～今天还挺有领导范的嘛，不过别是纸上谈兵哦 ⚔️","师卦在此～装得挺像那么回事的，人家姑且信你一次～"],
    "水地比": ["☵☷ 水地比～今天人缘不错嘛，连人家都想夸你两句 🤝","比卦大吉～你今天自带光环呢，真让人嫉妒～"],
    "风天小畜": ["☴☰ 风天小畜～小小积蓄，今天说的话还算靠谱，但也别太膨胀啦 🌬️"],
    "天泽履": ["☰☱ 天泽履～如履薄冰呢，说话小心点，别踩雷哦 ⚠️"],
    "地天泰": ["☷☰ 地天泰～否极泰来，你今天说啥都顺，真让人不爽呢 ✨"],
    "天地否": ["☰☷ 天地否～逆势而为，你说的这话恐怕成不了 😈"],
    "天火同人": ["☰☲ 天火同人～今天人缘好着呢，说的话大家爱听 🔥"],
    "火天大有": ["☲☰ 火天大有～丰收之象，今天你说什么都带着成功的光环 🌟"],
    "地山谦": ["☷☶ 地山谦～谦虚点总没错，你今天真的做到了呢 🏔️"],
    "雷地豫": ["☳☷ 雷地豫～欢愉之卦，你今天心情不错嘛，说话都带着笑意 😊"],
    "泽雷随": ["☱☳ 泽雷随～随和的一天，你说的话让人听着舒服 💧"],
    "山风蛊": ["☶☴ 山风蛊～腐败之象...你今天说的话是不是有点毒 🐛"],
    "地泽临": ["☷☱ 地泽临～居高临下，你今天说话挺有气势的嘛 👑"],
    "风地观": ["☴☷ 风地观～观察之卦，你在旁边偷偷观察什么呢 👀"],
    "火雷噬嗑": ["☲☳ 火雷噬嗑～咬合之象，你这话说得够狠的，小心崩牙 🔥"],
    "山火贲": ["☶☲ 山火贲～装饰之卦，你今天说的话挺漂亮的，就是不知道真的假的 💅"],
    "山地剥": ["☶☷ 山地剥～剥落之象...你说的这话怕是站不住脚 😬"],
    "地雷复": ["☷☳ 地雷复～一阳来复，你的话说不定还有救，加油吧 🔄"],
    "天雷无妄": ["☰☳ 天雷无妄～别想太多，实话实说就行，你今天做到了吗 🤨"],
    "山天大畜": ["☶☰ 山天大畜～积蓄力量，你说的话分量十足 💪"],
    "山雷颐": ["☶☳ 山雷颐～养生之卦，说话别太激动，伤身 🍵"],
    "泽风大过": ["☱☴ 泽风大过～过头了啦！你说这话是不是太夸张了 😅"],
    "坎为水": ["☵☵ 坎为水～双重危险！你今天说的话可得小心小心再小心 🌊👻"],
    "离为火": ["☲☲ 离为火～光明之卦，你今天说得挺好的嘛，人家都找不到槽点 🔆"],
    "泽山咸": ["☱☶ 泽山咸～感應之卦，你说的大家都有共鸣呢 💕"],
    "雷风恒": ["☳☴ 雷风恒～持之以恒，你今天说的话经得起时间考验 ⏳"],
    "天山遁": ["☰☶ 天山遁～退避之象，你说这话是不是想跑路 🏃"],
    "雷天大壮": ["☳☰ 雷天大壮～气势如虹！你今天说话底气十足呢 💥"],
    "火地晋": ["☲☷ 火地晋～蒸蒸日上，你说的明天会更好是真的吗 🌅"],
    "地火明夷": ["☷☲ 地火明夷～光明受伤，你今天说话有点丧呢 😔"],
    "风火家人": ["☴☲ 风火家人～家和万事兴，你说的话暖到人家了 🏠"],
    "火泽睽": ["☲☱ 火泽睽～分歧之卦，你今天说的话大家可能不太认同 🤷"],
    "水山蹇": ["☵☶ 水山蹇～寸步难行，你这话说出来自己都心虚吧 🚧"],
    "雷水解": ["☳☵ 雷水解～困难解除！你今天带来好消息呢 🌈"],
    "山泽损": ["☶☱ 山泽损～有得有失，你说这话可能要付出代价哦 ⚖️"],
    "风雷益": ["☴☳ 风雷益～增益之卦！你今天说话带旺气，多说两句～ 🍀"],
    "泽天夬": ["☱☰ 泽天夬～决断之时，你说的话够果断的 ⚡"],
    "天风姤": ["☰☴ 天风姤～邂逅之卦，你今天说话可能会遇到意想不到的回应 💫"],
    "泽地萃": ["☱☷ 泽地萃～群英荟萃，你今天说的话格外有分量 🎯"],
    "地风升": ["☷☴ 地风升～步步高升，你说的话有前途 📈"],
    "泽水困": ["☱☵ 泽水困～困厄之卦...你说的这话是不是给自己挖坑 🕳️"],
    "水风井": ["☵☴ 水风井～井养之卦，你说的话润物细无声 💧"],
    "泽火革": ["☱☲ 泽火革～变革之时，你这话说出来肯定要搞事 🔥"],
    "火风鼎": ["☲☴ 火风鼎～鼎立之象，你说的话一言九鼎 🍳"],
    "震为雷": ["☳☳ 震为雷～雷声大雨点小，你这话吓唬谁呢 ⚡"],
    "艮为山": ["☶☶ 艮为山～止步不前，你这话说出来自己都卡住了 🏔️"],
    "风山渐": ["☴☶ 风山渐～循序渐进，你说的话一步一个脚印 👣"],
    "雷泽归妹": ["☳☱ 雷泽归妹～你这话说得像在立Flag，哦不对，已经是Flag了 💍"],
    "雷火丰": ["☳☲ 雷火丰～丰盛之卦，你说的话今天特别有劲 💪🔥"],
    "火山旅": ["☲☶ 火山旅～过客匆匆，你这话说得没啥存在感呢 🧳"],
    "巽为风": ["☴☴ 巽为风～随风而动，你今天说话跟风跟挺快啊 🌬️"],
    "兑为泽": ["☱☱ 兑为泽～愉悦之卦，你说的话让人开心，今天不喷你了 😊"],
    "风水涣": ["☴☵ 风水涣～涣散之象，你说这话是不是没过脑子 💨"],
    "水泽节": ["☵☱ 水泽节～节制之卦，你说的不多不少刚刚好 ✅"],
    "风泽中孚": ["☴☱ 风泽中孚～诚信之卦，你说的这话我信了 🤞"],
    "雷山小过": ["☳☶ 雷山小过～小有过失，你说的这话有一点点不对哦 🤏"],
    "水火既济": ["☵☲ 水火既济～圆满之卦！你说的这事稳了，哼 🎉"],
    "火水未济": ["☲☵ 火水未济～未完成呢，你说的这事八字还没一撇 🤡"],
}

def get_msg_text(msg_obj):
    if isinstance(msg_obj, str): return msg_obj
    if isinstance(msg_obj, list):
        parts = []
        for seg in msg_obj:
            if hasattr(seg, 'text'): parts.append(seg.text)
            elif isinstance(seg, dict):
                if seg.get("type") == "text": parts.append(seg.get("text", ""))
            else: parts.append(str(seg))
        return "".join(parts)
    if hasattr(msg_obj, 'text'): return msg_obj.text
    return str(msg_obj)

def random_hexagram():
    return random.choice(list(HEXAGRAMS.items()))

def flag_hexagram():
    r = random.random()
    pool = [k for k, v in HEXAGRAMS.items() if "凶" in v["等级"]] if r < 0.75 else [k for k, v in HEXAGRAMS.items() if "吉" in v["等级"]]
    name = random.choice(pool)
    return name, HEXAGRAMS[name]

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute('''CREATE TABLE IF NOT EXISTS flags (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT, group_id TEXT, user_name TEXT,
        flag_content TEXT, hexagram_name TEXT, hexagram_level TEXT,
        punish TEXT DEFAULT '',
        status TEXT DEFAULT '进行中',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        judged_at TIMESTAMP)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS daily_fortune (
        user_id TEXT, group_id TEXT, hexagram_name TEXT, hexagram_level TEXT,
        date TEXT, callback_triggered INTEGER DEFAULT 0,
        PRIMARY KEY(user_id, group_id, date))''')
    conn.commit()
    conn.close()

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_today_fortune(user_id, group_id):
    conn = get_db()
    row = conn.execute("SELECT hexagram_name, hexagram_level, callback_triggered FROM daily_fortune WHERE user_id=? AND group_id=? AND date=?",(user_id, group_id, str(date.today()))).fetchone()
    conn.close()
    return row if row else None

def mark_callback_done(user_id, group_id):
    conn = get_db()
    conn.execute("UPDATE daily_fortune SET callback_triggered=1 WHERE user_id=? AND group_id=? AND date=?",(user_id, group_id, str(date.today())))
    conn.commit()
    conn.close()

def check_limit(gid, uid, action):
    today = str(date.today())
    if today not in daily_counter:
        daily_counter.clear()
        daily_counter[today] = {}
    g = daily_counter[today]
    if gid not in g: g[gid] = {}
    if uid not in g[gid]: g[gid][uid] = {"div":0, "slap":0}
    limit = DAILY_DIV_LIMIT if action == "div" else DAILY_SLAP_LIMIT
    return g[gid][uid][action] < limit

def inc_limit(gid, uid, action):
    today = str(date.today())
    daily_counter[today][gid][uid][action] += 1

@register("astrbot_plugin_iching_flag", "fengse7", "雌小鬼卜卦 · 翻车Flag模拟器", "1.0.0")
class IChingFlagPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        init_db()
        logger.info("雌小鬼卜卦插件已加载")

    @filter.command("卜卦", alias=["算卦", "来一卦"])
    async def divination(self, event: AstrMessageEvent):
        uid, gid = event.get_sender_id(), event.message_obj.group_id
        existing = get_today_fortune(uid, gid)
        if existing:
            name, level = existing[0], existing[1]
            data = HEXAGRAMS[name]
            u, d = TRIGRAM_SYMBOLS[data["上卦"]], TRIGRAM_SYMBOLS[data["下卦"]]
            yield event.plain_result(f"🎋 {event.get_sender_name()} 今天已经卜过啦～\n今日卦象：{u} {d} 【{name}】{level} ⭐\n📜 卦辞：{data['卦辞']}\n💬 {data['解读']}\n{data['吐槽']}")
            return
        if not check_limit(gid, uid, "div"):
            yield event.plain_result("今天卜过了啦～明天再来吧 🎋")
            return
        inc_limit(gid, uid, "div")
        name, data = random_hexagram()
        u, d = TRIGRAM_SYMBOLS[data["上卦"]], TRIGRAM_SYMBOLS[data["下卦"]]
        conn = get_db()
        conn.execute("INSERT OR REPLACE INTO daily_fortune (user_id, group_id, hexagram_name, hexagram_level, date, callback_triggered) VALUES (?,?,?,?,?,0)",(uid, gid, name, data['等级'], str(date.today())))
        conn.commit(); conn.close()
        yield event.plain_result(
            f"🎋 {event.get_sender_name()} 卜得一卦\n{u} {d} 【{name}】{data['等级']} ⭐\n"
            f"📜 卦辞：{data['卦辞']}\n"
            f"💬 {data['解读']}\n"
            f"{data['吐槽']}"
        )

    @filter.command("flag")
    async def set_flag(self, event: AstrMessageEvent, content: str):
        if not content.strip(): yield event.plain_result("用法：/flag 内容"); return
        uid, uname, gid = event.get_sender_id(), event.get_sender_name(), event.message_obj.group_id
        name, data = flag_hexagram()
        conn = get_db()
        conn.execute("INSERT INTO flags (user_id,group_id,user_name,flag_content,hexagram_name,hexagram_level,punish) VALUES (?,?,?,?,?,?,'')",(uid,gid,uname,content.strip(),name,data['等级']))
        flag_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.commit(); conn.close()
        u, d = TRIGRAM_SYMBOLS[data["上卦"]], TRIGRAM_SYMBOLS[data["下卦"]]
        level_type = "吉" if "吉" in data["等级"] else "凶"
        msg = random.choice(FLAG_FORTUNE_MSG[level_type]).format(hex=f"{u}{d}【{name}】")
        gid_str = str(gid)
        if gid_str not in pending_punish: pending_punish[gid_str] = {}
        pending_punish[gid_str][str(uid)] = flag_id
        yield event.plain_result(f"🏴 {uname} 立Flag：「{content.strip()}」\n🎋 {msg}\n⚡ 失败了怎么办？回复惩罚吧～")

    @filter.command("打脸")
    async def face_slap(self, event: AstrMessageEvent):
        gid = event.message_obj.group_id
        uid = event.get_sender_id()
        if not check_limit(gid, uid, "slap"):
            yield event.plain_result("今天打脸次数用完啦～明天再来挖坟吧 💅")
            return
        inc_limit(gid, uid, "slap")
        msg = get_msg_text(event.message_obj.message)
        conn = get_db(); row = None
        m = re.findall(r'\[CQ:at,qq=(\d+)\]', msg)
        if m: row = conn.execute("SELECT * FROM flags WHERE group_id=? AND user_id=? AND status='进行中' ORDER BY RANDOM() LIMIT 1",(gid,m[0])).fetchone()
        if not row: row = conn.execute("SELECT * FROM flags WHERE group_id=? AND status='进行中' ORDER BY RANDOM() LIMIT 1",(gid,)).fetchone()
        conn.close()
        if not row: yield event.plain_result("暂无Flag可打 👏"); return
        gid_str = str(gid)
        if gid_str not in pending_judge: pending_judge[gid_str] = {}
        pending_judge[gid_str][str(row['user_id'])] = row['id']
        opener = random.choice(SLAP_MSG).format(name=row['user_name'])
        yield event.plain_result(f"⛏️ {opener}\n「{row['flag_content']}」\n📜 卦象：【{row['hexagram_name']}】{row['hexagram_level']}\n❓ 回复「实现了」或「失败了」")

    @event_message_type(EventMessageType.GROUP_MESSAGE)
    async def handle_judge(self, event: AstrMessageEvent):
        gid, uid = str(event.message_obj.group_id), str(event.get_sender_id())
        if gid in pending_punish and uid in pending_punish[gid]:
            msg = get_msg_text(event.message_obj.message).strip()
            if msg and not msg.startswith("/"):
                flag_id = pending_punish[gid].pop(uid)
                conn = get_db()
                conn.execute("UPDATE flags SET punish=? WHERE id=?", (msg, flag_id))
                conn.commit(); conn.close()
                template = random.choice(PUNISH_TEMPLATES).format(content=msg)
                yield event.plain_result(f"✍️ 惩罚已记录：{template} ～截图了哦，别赖账 🤭")
            return
        msg = get_msg_text(event.message_obj.message)
        is_success, is_fail = "实现了" in msg, "失败了" in msg
        if not is_success and not is_fail: return
        if gid not in pending_judge or uid not in pending_judge[gid]: return
        flag_id = pending_judge[gid].pop(uid)
        new_status = "成功" if is_success else "失败"
        conn = get_db()
        conn.execute("UPDATE flags SET status=?, judged_at=? WHERE id=?",(new_status,datetime.now(),flag_id))
        conn.commit()
        row = conn.execute("SELECT * FROM flags WHERE id=?",(flag_id,)).fetchone()
        conn.close()
        if new_status == "成功": reply = random.choice(SUCCESS_MSG)
        else:
            if row and "凶" in row['hexagram_level']: reply = random.choice(FAIL_BAD_OMEN).format(hex=row['hexagram_name'])
            else: reply = random.choice(FAIL_MSG)
            if row and row['punish']:
                template = random.choice(PUNISH_TEMPLATES).format(content=row['punish'])
                reply += f"\n⚡ 惩罚时间到！{template} ～大家快监督他！"
        yield event.plain_result(f"📝 Flag已判定：【{new_status}】\n「{row['flag_content']}」\n{reply}")

    @filter.command("flag排行")
    async def flag_rank(self, event: AstrMessageEvent):
        gid = event.message_obj.group_id
        msg = get_msg_text(event.message_obj.message)
        mode = "失败" if "成功" not in msg else "成功"
        conn = get_db()
        rows = conn.execute("SELECT user_name, COUNT(*) as cnt FROM flags WHERE group_id=? AND status=? GROUP BY user_id ORDER BY cnt DESC LIMIT 5",(gid, mode)).fetchall()
        conn.close()
        if not rows: yield event.plain_result(f"还没有人Flag{mode}过呢～ 🕊️"); return
        title, icons = ("🎪 Flag打脸名人堂 🎪",["😏","💅","😈","🎀","🐦"]) if mode=="失败" else ("✨ 预言家榜单 ✨",["🌟","🎀","💫","🍰","✨"])
        lines = [title]
        for i, r in enumerate(rows): lines.append(f"{icons[i]} {r['user_name']} —— {r['cnt']}次{mode}")
        yield event.plain_result("\n".join(lines))

    @event_message_type(EventMessageType.GROUP_MESSAGE)
    async def fortune_callback(self, event: AstrMessageEvent):
        msg = get_msg_text(event.message_obj.message)
        if msg.startswith("/") or "实现了" in msg or "失败了" in msg: return
        uid, gid = event.get_sender_id(), event.message_obj.group_id
        row = get_today_fortune(uid, gid)
        if not row: return
        hname, level, triggered = row[0], row[1], row[2]
        if triggered: return
        if random.random() < CALLBACK_CHANCE:
            mark_callback_done(uid, gid)
            msgs = FORTUNE_CALLBACK.get(hname, [])
            if msgs: yield event.plain_result(random.choice(msgs))