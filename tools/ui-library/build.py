"""Build the original Kotama-compatible candidate library and its manifest."""
import hashlib
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

ROOT = Path(sys.argv[1])
ASSETS = []
GOLD = "#ecd4a0"
INK = "#121f30"

def path(d, fill="none", stroke=GOLD, width=2):
    return f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{width}" stroke-linecap="round" stroke-linejoin="round"/>'

def asset(group, name, title, use, w, h, content, suffix="", counted=True):
    filename = f"{group}/{name}{suffix}.svg"
    target = ROOT / filename
    target.parent.mkdir(parents=True, exist_ok=True)
    data = f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">{content}</svg>\n'
    ET.fromstring(data)
    target.write_text(data)
    meta = {"path": filename, "bytes": len(data.encode()), "sha256": hashlib.sha256(data.encode()).hexdigest()}
    if counted:
        ASSETS.append(dict(id=name, title=title, category=group, screen=use, size=[w,h],
                           source="original", theme="紺青と古金", tool="SVG / Python", model=None,
                           status="未承認", editable=filename, **meta))
    return meta

def gradient(id, colors):
    stops = "".join(f'<stop offset="{i/(len(colors)-1):.4f}" stop-color="{color}"/>' for i,color in enumerate(colors))
    return f'<linearGradient id="{id}" x2="0" y2="1">{stops}</linearGradient>'

def plated(d, colors, detail):
    return '<defs>'+gradient("face", colors)+gradient("edge", [GOLD,"#7a5738","#d9b980"])+'</defs>'+path(d,"url(#face)","url(#edge)",2)+detail

def gem(x,y,fill="#5aa39a",r=4):
    return path(f"M{x-r} {y}l{r} {-r-2} {r} {r+2} {-r} {r+2}Z",fill,"#c6ad76",1)

buttons = [
 ("command","指令ボタン","ホーム・戦闘","M7 9L16 3H176L185 9V47L176 53H16L7 47Z"),
 ("section-tab","項目タブ","ショップ・図鑑","M4 49V17L18 4H174L188 17V49Z"),
 ("confirm","決定ボタン","購入・強化","M18 4H174L190 28L174 52H18L2 28Z"),
 ("back","戻るボタン","共通","M3 28L22 4H183L189 10V46L183 52H22Z"),
 ("select","選択ブラケット","編成・スキル","M4 21V11L12 4H31M161 4H180L188 11V21M4 35V45L12 52H31M161 52H180L188 45V35"),
]
for key,title,use,d in buttons:
    decoration = path("M24 12H60M132 12H168M24 44H60M132 44H168","none","#c6ad76",0.8)+gem(18,28)+gem(174,28)
    for state,colors in {"normal":["#354c57","#1b3041","#101b2b"],"hover":["#4b766e","#254f54","#172c40"],
                         "pressed":["#101b2b","#213748","#243f48"],"selected":["#39706b","#183d46","#1a253a"],
                         "disabled":["#393b43","#2b2e37","#22242a"]}.items():
        body = path(d,"none",GOLD,2.5)+decoration if key=="select" else plated(d,colors,decoration)
        item=asset("buttons",key,title,use,192,56,body,"" if state=="normal" else "-"+state,state=="normal")
        if state=="normal":
            ASSETS[-1]["variants"]={}
        else:
            ASSETS[-1]["variants"][state]=item

panels=[
 ("window","会話ウィンドウ","会話・確認","M4 20L20 4H300L316 20V156L300 172H20L4 156Z",["#273e4a",INK,"#0a1421"]),
 ("inspector","情報パネル","戦闘・ステータス","M4 4H286L316 34V172H4Z",["#243c52","#152536","#0e1828"]),
 ("parchment","依頼書","クエスト","M9 13Q48 4 83 10T160 10T247 10T308 8L315 153Q292 172 250 165T160 168T74 164T7 168Z",["#e4cea3","#cfac76","#ae8a59"]),
 ("portrait","キャラクター枠","編成","M34 4H286L316 34V142L286 172H34L4 142V34Z",["#4c7473","#254b54","#24314a"]),
 ("minimap","地図外枠","探索","M20 4H300L316 20V156L300 172H20L4 156Z",["#2d4755",INK,"#0a1423"]),
]
for key,title,use,d,colors in panels:
    ornaments=path("M14 42V24L25 14H56M264 14H295L306 24V42M14 134V152L25 162H56M264 162H295L306 152V134","none","#caaa71",1)+gem(160,8,r=3)+gem(160,168,r=3)
    asset("panels",key,title,use,320,176,plated(d,colors,ornaments))
    if key=="window":
        border=asset("panels","window","",use,320,176,path(d,"none",GOLD)+ornaments,"-frame",False)
        ASSETS[-1]["frame"]=border
        ASSETS[-1]["border_slice"]=28

for key,title,d,detail,color in [
 ("hp","HP","M6 7H205L218 16L205 25H6Z","M14 11H192","#bb4c59"),
 ("sp","SP","M6 16L17 7H211V25H17Z","M27 11H197","#4594bd"),
 ("exp","経験値","M6 11L14 6H210L218 11V21L210 26H14L6 21Z","M38 9V14M72 9V14M106 9V14M140 9V14M174 9V14","#b58e43"),
 ("union","ユニオン","M16 5H204L218 16L204 27H16L2 16Z","M18 9H198M18 23H198","#6c80c9"),
 ("encounter","エンカウント","M7 5H197L219 16L197 27H7L16 16Z","M25 8L32 24M40 8L47 24","#b9633f"),
]:
    track=asset("gauges",key,title,"戦闘・探索",224,32,path(d,"#0b1420",GOLD,1.5)+path(detail,"none","#ad9060",1))
    fill=asset("gauges",key,"","戦闘・探索",224,32,plated(d,[GOLD,color,INK],""),"-fill",False)
    ASSETS[-1]["fill"]=fill

icons=[
 ("sword","剣","M44 9L56 7L54 20L31 43L22 34Z M17 31L35 49L30 54L12 36Z M20 44L10 54L10 59L16 59L26 49Z","#a4c5d5"),
 ("shield","盾","M32 7L53 15V31C51 44 41 53 32 59C23 53 13 44 11 31V15Z M32 15V49 M18 23H46","#4e8f8d"),
 ("staff","杖","M28 25L35 30L15 57L10 54Z M38 7L48 10L52 20L44 29L33 26L29 16Z M40 10L45 18L39 24L34 17Z","#807dc0"),
 ("potion","回復薬","M25 7H39V15H25Z M27 15V24L16 38Q9 58 32 58Q55 58 48 38L37 24V15Z M16 43Q28 38 48 44","#bb566b"),
 ("key","鍵","M44 7A13 13 0 1 1 31 28L18 41L24 47L17 54L11 48L5 54V43L30 17A13 13 0 0 1 44 7Z M43 13A6 6 0 1 0 43 25A6 6 0 1 0 43 13Z","#be9450"),
 ("chest","宝箱","M10 28L16 15H48L54 28V53H10Z M10 33H54 M26 28H38V43H26Z M16 16V32M48 16V32","#895940"),
 ("return-book","帰還の書","M12 12H48L54 18V54H16L10 48V14Z M17 17V49 M42 36Q42 26 29 27L33 22L25 27L31 34","#427c73"),
 ("fire","炎","M35 5C40 17 30 22 40 30L47 21C63 49 46 60 32 59C12 59 6 41 17 28L23 35C28 25 23 16 35 5Z M31 37C33 44 42 49 32 54C23 52 26 45 31 37Z","#b65443"),
 ("ice","氷","M32 5L49 26L44 46L32 60L19 46L14 26Z M32 5V60 M14 26L32 35L49 26","#427eab"),
 ("thunder","雷","M36 4L14 34H30L24 60L52 26H36L43 4Z","#c4a453"),
 ("stairs","階段","M9 49H55V55H9Z M15 40H55V49H15Z M25 31H55V40H25Z M35 22H55V31H35Z M45 13H55V22H45Z","#638d99"),
 ("door","扉","M12 56V29C12 15 21 7 32 7S52 15 52 29V56Z M19 56V29Q19 16 32 15Q45 16 45 29V56 M36 36H40","#8f674b"),
 ("gather","採取","M16 56Q22 36 48 12 M20 43Q7 37 10 23Q25 23 25 38 M29 33Q29 16 49 15Q48 33 29 33 M27 48Q33 35 52 38Q47 53 27 48","#518e72"),
 ("event","イベント","M32 5L40 22L58 25L45 38L48 56L32 48L16 56L19 38L6 25L24 22Z M32 20V34 M32 41V42","#9b7446"),
 ("marker","現在地","M32 5L52 54L32 45L12 54Z M32 13V44","#468f91"),
 ("foe","強敵","M15 18L7 6L24 13Q32 8 40 13L57 6L49 18L52 32L44 49L32 57L20 49L12 32Z M20 29L27 35M44 29L37 35","#944e66"),
]
for key,title,d,color in icons:
    group="map-icons" if key in {"stairs","door","gather","event","marker","foe"} else "icons"
    detail='<circle cx="32" cy="33" r="27" fill="#142332" opacity=".75"/>'
    asset(group,key,title,"探索" if group=="map-icons" else "戦闘・持ち物",64,64,
          detail+plated(d,[color,color,"#182538"],""))

asset("ornaments","chapter-seal","章紋章","階層タイトル",144,100,
      '<circle cx="72" cy="50" r="33" fill="#132636" stroke="#c4a16c" stroke-width="2"/>'
      + path("M72 17L100 65L44 65Z M72 83L44 35H100Z","none","#739f9a",1.5)
      + gem(72,50,r=8)+path("M5 50H35M109 50H139M20 45L29 50L20 55M124 45L115 50L124 55"))
asset("ornaments","vine-divider","蔦の区切り","ホーム・図鑑",240,38,
      path("M3 20Q53 5 111 20M129 20Q187 5 237 20M22 15Q25 3 43 7Q38 14 22 15M63 13Q67 31 88 26Q84 16 63 13M218 15Q215 3 197 7Q202 14 218 15M177 13Q173 31 152 26Q156 16 177 13","none","#80ac96",1.8)+gem(120,19,r=6))

manifest={"version":1,"approval":"候補・未採用","assets":ASSETS}
(ROOT / "manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n")
print(f"{len(ASSETS)} original designs")
