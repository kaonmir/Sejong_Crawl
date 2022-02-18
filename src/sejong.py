# %%
import os.path
import os
import csv
import requests
from bs4 import BeautifulSoup as bs

# %%
# 0 = 즉위년, 1 = 1년 ...


def getMonthKeysFromYear(year):
    res = requests.get(
        "http://sillok.history.go.kr/search/inspectionMonthList.do?id=kda")
    soup = bs(res.content, "html.parser")
    body_year = soup.find("ul", "king_year2").findAll("ul", "clear2")[year]

    key = list(map(lambda a: a.text, body_year.findAll("a")))
    value = list(map(lambda a: a["href"].split("(")[1].split(
        ",")[0].replace('\'', ""), body_year.findAll("a")))
    return [key, value]

# %%


def isSiteValid(res):
    return "조선왕조실록 : 요청하신 페이지를 찾을 수 없습니다." not in res.text


def getDayUrlFromMonthKey(monthKey, start=1, end=33):
    answer = []
    for day in range(start, end):
        articles = []
        for article in range(1, 100):
            url = f'http://sillok.history.go.kr/id/{monthKey}{day:02d}_{article:03d}'
            res = requests.get(url)
            if not isSiteValid(res):
                break
            articles.append(url)
        answer.append([day, articles])
    return answer

# %%

# output: volume, date, hangul, hanza


def getFromUrl(url):
    res = requests.get(url)
    if not isSiteValid(res):
        raise "Invalid url on getFromUrl function"
    soup = bs(res.content, "html.parser")
    gakju = ""

    # finding volume and date
    parent = soup.find("span", "tit_loc")
    child = parent.find("span")
    child.extract()  # extract child tag from parent tag
    volume, date = list(
        map(lambda x: x.strip(), parent.text.strip().split(",")))

    # finding hangul
    hangul = soup.find("div", "ins_left_in").find("div", "ins_view_pd")
    # Remove footnotes
    foots = hangul.findAll("a", "footnote_super")
    for foot in foots:
        foot.find("sup").extract()
        foot.string = foot.text + "@@"
    foots = hangul.findAll("ul", "ins_source")
    for foot in foots:
        foot.extract()
    footnotes = hangul.find("ul", "ins_footnote").find("li", "clear2")
    if footnotes != None:
        gakju = "\n[註 ".join(
            list(map(lambda f: f.strip(), footnotes.text.split("[註 ")))).strip()
    # Paragraph
    paragraph_p = list(map(lambda p: p.text.strip(),
                       hangul.findAll("p", "paragraph")))
    paragraph_hangul = "\n\n".join(paragraph_p)

    # finding hanza
    hanza = soup.find("div", "ins_right_in").find("div", "ins_view_pd")
    removeables = hanza.findAll("ul", "ins_source")
    for removeable in removeables:
        removeable.extract()
    paragraph_p = list(map(lambda p: p.text.strip(),
                       hanza.findAll("p", "paragraph")))
    paragraph_hanza = "\n\n".join(paragraph_p)

    return [volume, date, paragraph_hangul, paragraph_hanza, gakju]


# %%

ganz = []

with open('ganz.csv', newline='', encoding="UTF8") as csvfile:
    spamreader = csv.reader(csvfile, delimiter=',')
    for row in spamreader:
        ganz.append(list(row))


def getGanzFromHangul(hangul):
    answer = "---없습니다.---"
    for g in ganz:
        if hangul == g[2]:
            answer = g[1]
            break
    return answer


def ganji(year):
    cheongan = ["경", "신", "임", "계", "갑", "을", "병", "정", "무", "기"]
    jiji = ["신", "유", "술", "해", "자", "축", "인", "묘", "진", "사", "오", "미"]
    sibiji = ["원숭이", "닭", "개", "돼지", "쥐", "소", "호랑이", "토끼", "용", "뱀", "말", "양"]
    ganji1 = year % 10
    ganji2 = year % 12

    return cheongan[ganji1] + jiji[ganji2]


# %%
# Output: [volume, date, hangul, hanza]
def getFromDay(monthKey, day):
    days = getDayUrlFromMonthKey(monthKey, day, day+1)

    hanguls = []
    hanza_answer = ""
    gakjus = ""

    if len(days[0]) == 0:
        return

    for url in days[0][1]:
        print(".", end="")
        volume, date, hangul, hanza, gakju = getFromUrl(url)

        hanguls.append(hangul.strip())
        hanza_answer = hanza_answer + "\n" + hanza
        gakjus = gakjus + "\n" + gakju
        gakjus = gakjus.strip()

    day_h = date.split(" ")[-2]
    return volume, date, day_h + "일(" + getGanzFromHangul(day_h) + "日-" + str(day) + "일)에 " + "\n\n○ ".join(hanguls), hanza_answer, gakjus


# %%


def _safe_open_w(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    return open(path, 'w', encoding="UTF8")


def saveFile(year, month, hangul, hanza, gakju):
    path = f'/content/drive/MyDrive/Sejong/{year}/{month}'
    with _safe_open_w(f'{path} 국역.txt') as f:
        f.write(hangul)
    with _safe_open_w(f'{path} 원문.txt') as f:
        f.write(hanza)
    with _safe_open_w(f'{path} 주석.txt') as f:
        f.write(gakju)


def getFromMonthKey(year, month, monthKey):
    print(f"{year}년 {month}의 정보를 추출합니다.")
    months = getDayUrlFromMonthKey(monthKey)
    hanguls = []
    hanzas = []
    gakjus = ""
    for day, urls in months:
        if len(urls) == 0:
            continue
        print(f"{day}(", end="")
        volume, date, hangul, hanza, gakju = getFromDay(monthKey, day)
        hanguls.append(hangul)
        hanzas.append(hanza)
        gakjus = gakjus + "\n" + gakju
        gakjus = gakjus.strip()
        print(f") ", end="")
    print("")

    # ---
    # print (f"{month}의 정보를 파일로 만듭니다.")
    hangul = "\n\n".join(hanguls)
    hanza = "\n\n".join(hanzas)

    year_hangul = f"세종 {year}년"
    if year == 0:
        year_hangul = "세종 즉위년"

    # 세종 즉위년 (1418년) 무술년 (무술년) 8월
    gan = ganji(year+1418)
    title_hangul = f"{year_hangul} ({year+1418}년) {gan}년 ({getGanzFromHangul(gan)}年) {month}"
    # 원문 (세종실록 1권, 세종 즉위년 8월)
    title_hanza = f"원문 ({volume}, {year_hangul} {month})"

    saveFile(year_hangul, month, volume + "\n" + title_hangul +
             "\n\n" + hangul, title_hanza + "\n" + hanza, gakjus)


# %%
def getFromYear(year, start=0, end=15):
    months, monthKeys = getMonthKeysFromYear(year)
    for idx, [month, monthKey] in enumerate(zip(months, monthKeys)):
        if idx < start or end < idx:
            continue
        getFromMonthKey(year, month, monthKey)

# %%
