import time
import random
import hashlib

import requests

app_version = "5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.128 Safari/537.36"

class YoudaoTranslator(object):
	def __init__(self):
		self.bv = hashlib.md5(app_version.encode()).hexdigest()
		self.sign_tmpl = "fanyideskweb{src}{salt}Tbh5E8=q6U3EXe+&L[4c@"

		self.session = requests.Session()
		self.session.headers.update({
			"User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.85 Safari/537.36",
			"Referer": "https://fanyi.youdao.com/"
		})	
		self.translate_host_url = "https://fanyi.youdao.com/"
		self.translate_action_url = "https://fanyi.youdao.com/translate_o?smartresult=dict&smartresult=rule"
		self.translate_speak_url = "https://tts.youdao.com/fanyivoice"

	def name(self):
		return "有道翻译"

	def icon(self):
		return "resource/youdao.png"

	def languages(self):
		return {
			"zh-CHS": "中文",
			"en": "英语",
			"ko": "韩语",
			"ja": "日语",
			"fr": "法语",
			"ru": "俄语",
			"es": "西班牙语",
			"pt": "葡萄牙语",
			"hi": "印地语",
			"ar": "阿拉伯语",
			"da": "丹麦语",
			"de": "德语",
			"el": "希腊语",
			"fi": "芬兰语",
			"it": "意大利语",
			"ms": "马来语",
			"vi": "越南语",
			"id": "印尼语",
			"nl": "荷兰语",
			"th": "泰语"
		}

	def generateSaltSign(self, src):
		lts = str(int(time.time() * 1000))
		salt = lts + str(random.randint(1, 10))
		sign = hashlib.md5(self.sign_tmpl.format(src=src, salt=salt).encode()).hexdigest()
		return {
			"lts": lts,
			"bv": self.bv,
			"salt": salt,
			"sign": sign
		}

	def preRequest(self):
		print("youdao preRequest")
		self.session.get(self.translate_host_url)

	def translate(self, src, src_lan=None, dest_lan=None):
		lans = self.languages()
		salt_sign = self.generateSaltSign(src)
		src_lan = src_lan if src_lan in lans else "AUTO"
		dest_lan = dest_lan if dest_lan in lans else "AUTO"
		data = {
			"i": src,
			"from": src_lan,
			"to": dest_lan,
			"smartresult": "dict",
			"client": "fanyideskweb",
			"doctype": "json",
			"version": "2.1",
			"keyfrom": "fanyi.web",
			"action": "FY_BY_REALTlME"
		}
		data.update(salt_sign)
		resp = self.session.post(self.translate_action_url, data=data)
		resp_json = resp.json()
		error_code = resp_json["errorCode"]
		if error_code != 0:
			return "", "", f"翻译接口错误, 错误码: {error_code}", ""
		result_list = []
		for trans_result in resp_json["translateResult"]:
			result_list.append(trans_result[0]["tgt"])
		result = "\n".join(result_list)
		smart_result = ""
		if resp_json.get("smartResult"):
			smart_result_array = resp_json["smartResult"]["entries"]
			smart_result = "".join(smart_result_array)
			if smart_result.endswith("\r\n"):
				smart_result = smart_result[0:-2]
		lan_type = resp_json["type"]
		lan = lan_type.split("2")[0]
		to = lan_type.split("2")[1]
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
		'''
		return bytes
		'''
		leng = {
			"en": "eng",
			"ja": "jap",
			"ko": "ko",
			"fr": "fr"
		}
		if lan not in leng:
			return None
		params = {
			"word": src,
			"le": leng[lan],
			"keyfrom": "speaker-target"
		}
		resp = self.session.get(self.translate_speak_url, params=params, stream=True)
		return resp.raw.read()

def main():
	ydt = YoudaoTranslator()
	ydt.preRequest()
	ydt.translate("Is there a QString function which takes an int and outputs it as a QString?")

if __name__ == '__main__':
	main()