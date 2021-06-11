import re
import ctypes

import requests

def int_overflow(val):
	maxint = 2147483647
	if not -maxint-1 <= val <= maxint:
		val = (val + (maxint + 1)) % (2 * (maxint + 1)) - maxint - 1
	return val

def left_shitf(n, i):
	return int_overflow(n << i)

def unsigned_right_shitf(n ,i):
	# 数字小于0，则转为32位无符号uint
	if n < 0:
		n = ctypes.c_uint32(n).value
	# 正常位移位数是为正数，但是为了兼容js之类的，负数就右移变成左移好了
	if i < 0:
		return - int_overflow(n << abs(i))
	#print(n)
	return int_overflow(n >> i)

class BaiduTranslator(object):
	def __init__(self):
		self.token = None
		self.gtk = None

		self.session = requests.Session()
		self.session.headers.update({
			"User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.85 Safari/537.36",
			"Origin": "https://fanyi.baidu.com/",
			"Referer": "https://fanyi.baidu.com/",
			"X-Requested-With": "XMLHttpRequest"
		})	

		self.translate_host_url = "https://fanyi.baidu.com/"
		self.translate_language_detect_url = "https://fanyi.baidu.com/langdetect"
		self.translate_action_url = "https://fanyi.baidu.com/v2transapi"
		self.translate_speak_url = "https://fanyi.baidu.com/gettts"

	def name(self):
		return "百度翻译"

	def icon(self):
		return "resource/baidu.png"

	def languages(self):
		return {
			"zh": "中文",
			"jp": "日语",
			# "jpka": "日语假名",
			"th": "泰语",
			"fra": "法语",
			"en": "英语",
			"spa": "西班牙语",
			"kor": "韩语",
			"tr": "土耳其语",
			"vie": "越南语",
			"ms": "马来语",
			"de": "德语",
			"ru": "俄语",
			"ir": "伊朗语",
			"ara": "阿拉伯语",
			"est": "爱沙尼亚语",
			"be": "白俄罗斯语",
			"bul": "保加利亚语",
			"hi": "印地语",
			"is": "冰岛语",
			"pl": "波兰语",
			"fa": "波斯语",
			"dan": "丹麦语",
			"tl": "菲律宾语",
			"fin": "芬兰语",
			"nl": "荷兰语",
			"ca": "加泰罗尼亚语",
			"cs": "捷克语",
			"hr": "克罗地亚语",
			"lv": "拉脱维亚语",
			"lt": "立陶宛语",
			"rom": "罗马尼亚语",
			"af": "南非语",
			"no": "挪威语",
			"pt_BR": "巴西语",
			"pt": "葡萄牙语",
			"swe": "瑞典语",
			"sr": "塞尔维亚语",
			"eo": "世界语",
			"sk": "斯洛伐克语",
			"slo": "斯洛文尼亚语",
			"sw": "斯瓦希里语",
			"uk": "乌克兰语",
			"iw": "希伯来语",
			"el": "希腊语",
			"hu": "匈牙利语",
			"hy": "亚美尼亚语",
			"it": "意大利语",
			"id": "印尼语",
			"sq": "阿尔巴尼亚语",
			"am": "阿姆哈拉语",
			"as": "阿萨姆语",
			"az": "阿塞拜疆语",
			"eu": "巴斯克语",
			"bn": "孟加拉语",
			"bs": "波斯尼亚语",
			"gl": "加利西亚语",
			"ka": "格鲁吉亚语",
			"gu": "古吉拉特语",
			"ha": "豪萨语",
			"ig": "伊博语",
			"iu": "因纽特语",
			"ga": "爱尔兰语",
			"zu": "祖鲁语",
			"kn": "卡纳达语",
			"kk": "哈萨克语",
			"ky": "吉尔吉斯语",
			"lb": "卢森堡语",
			"mk": "马其顿语",
			"mt": "马耳他语",
			"mi": "毛利语",
			"mr": "马拉提语",
			"ne": "尼泊尔语",
			"or": "奥利亚语",
			"pa": "旁遮普语",
			"qu": "凯楚亚语",
			"tn": "塞茨瓦纳语",
			"si": "僧加罗语",
			"ta": "泰米尔语",
			"tt": "塔塔尔语",
			"te": "泰卢固语",
			"ur": "乌尔都语",
			"uz": "乌兹别克语",
			"cy": "威尔士语",
			"yo": "约鲁巴语",
			"yue": "粤语",
			"wyw": "文言文",
			"cht": "中文繁体"
		}

	def generateSign(self, src):
		def generateSignDetail(sign, key):
			for i in range(0, len(key), 3):
				code = key[i+2]
				if code >= "a":
					code = ord(code) - 87
				else:
					code = int(code)
				if key[i+1] == "+":
					code = unsigned_right_shitf(sign, code) 
				else:
					code = left_shitf(sign, code)
				if key[i] == "+":
					sign = int_overflow(sign + code & 4294967295)
				else:
					sign = int_overflow(sign ^ code)
			return sign
		def genCharCodes(src):
			v = 0
			S = []
			while v < len(src):
				A = ord(src[v])
				if A < 128:
					S.append(A)
				else:
					if int_overflow(64512 & A) == 55296 and len(src) > v + 1 and int_overflow(64512 & ord(src[v+1])) == 56320:
						v += 1
						A = 65536 + left_shitf(int_overflow(1023 & A), 10) + int_overflow(1023 & ord(src[v]))
						S.append(int_overflow(unsigned_right_shitf(A, 18) | 240))
						S.append(int_overflow(int_overflow(unsigned_right_shitf(A, 12) & 63) | 128))
					else:
						S.append(int_overflow(unsigned_right_shitf(A, 12) | 224))
						S.append(int_overflow(int_overflow(unsigned_right_shitf(A, 6) & 63) | 128))
					S.append(int_overflow(int_overflow(63 & A) | 128))
				v += 1
			return S

		src_length = len(src)
		if src_length > 30:
			src = src[0:10] + src[int(src_length/2)-5:(int(src_length/2)-5)+10] + src[src_length-10:]
		char_codes = genCharCodes(src)
		gtk_array = self.gtk.split(".")
		gtk_front = int(gtk_array[0])
		gtk_backend = int(gtk_array[1])
		key1 = "+-3^+b+-f"
		key2 = "+-a^+6"
		sign = gtk_front
		for char_code in char_codes:
			sign += char_code
			sign = generateSignDetail(sign, key2)
		sign = generateSignDetail(sign, key1)
		sign = int_overflow(sign ^ gtk_backend)
		if sign < 0:
			sign = int_overflow(2147483647 & sign) + 2147483648
		if sign < 0:
			print("warning: sign < 0")
		sign = sign % 1000000
		return f"{str(sign)}.{int_overflow(sign ^ gtk_front)}" 

	def preRequest(self):
		print("baidu preRequest")
		self.session.get(self.translate_host_url)
		resp = self.session.get(self.translate_host_url)
		resp_text = resp.text
		self.token = re.findall("token: '(.*?)'", resp_text)[0]
		self.gtk = re.findall(";window.gtk = '(.*?)'", resp_text)[0]
		cookies = {
			"REALTIME_TRANS_SWITCH": "1",
			"FANYI_WORD_SWITCH": "1",
			"HISTORY_SWITCH": "1",
			"SOUND_SPD_SWITCH": "1",
			"SOUND_PREFER_SWITCH": "1"
		}
		for k, v in cookies.items():
			self.session.cookies.set(k, v, domain="fanyi.baidu.com")

	def languageDetect(self, src):
		resp = self.session.post(self.translate_language_detect_url, data={"query": src})
		resp_json = resp.json()
		return resp_json["lan"]

	def translate(self, src, src_lan=None, dest_lan=None):
		# You must clear the space before and after, 
		# otherwise the 998 error will be returned, 
		# and the sign generation will be incorrect
		lans = self.languages()
		src = src.strip()
		lan = None
		to = None
		if src_lan is not None and src_lan in lans:
			lan = src_lan
		else:
			lan = self.languageDetect(src)
			lan = lan if lan in lans else "en"
		if dest_lan is not None and dest_lan in lans:
			to = dest_lan
		else:
			to = "zh" if lan != "zh" else "en"

		params = {
			"from": lan,
			"to": to
		}
		data = {
			"from": lan,
			"to": to,
			"query": src,
			"simple_means_flag": "3",
			"sign": self.generateSign(src),
			"token": self.token,
			"domain": "common"
		}
		resp = self.session.post(self.translate_action_url, params=params, data=data)
		resp_json = resp.json()
		result_list = []
		for trans_result in resp_json["trans_result"]["data"]:
			result_list.append(trans_result["dst"])
		result = "\n".join(result_list)
		smart_result = ""
		if resp_json.get("dict_result") and resp_json["dict_result"].get("simple_means"):
			parts = resp_json["dict_result"]["simple_means"]["symbols"][0]["parts"]
			smart_result_array = []
			for part in parts:
				p = part.get("part", "")
				means = []
				for mean in part["means"]:
					if isinstance(mean, str):
						means.append(mean)
					elif isinstance(mean, dict):
						means.append(mean["text"])
				means = "； ".join(means)
				smart_result_array.append(f"{p} {means}")
			smart_result = "\r\n".join(smart_result_array)
		object_ = {
			"translator": self, 
			"src_lan": lan,
			"dest_lan": to,
			"src": src,
			"dest": result,
			"extend": smart_result,
		}
		return object_

	def speak(self, src, lan):
		params = {
			"lan": lan,
			"text": src,
			"spd": "5",
			"source": "web"
		}
		resp = self.session.get(self.translate_speak_url, params=params, stream=True)
		return resp.raw.read()

def main():
	bdt = BaiduTranslator()
	bdt.preRequest()
	s = bdt.translate("json")
	print(s)

if __name__ == '__main__':
	main()