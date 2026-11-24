import http
import json

from sms_ir import SmsIr


API_KEY = "XDOuKkAjI8x2YHHDYDbwW3ySojBavURrnbwCzdAaPf8stXLX"
linenumber = "300790"

number = "09136563913"

message = "سلام"

template_id = "859705"
parameters = [
    {"name": "CODE", "value": "1378"},{"name": "CODE2", "value": "1379"},{"name": "awdE2", "value": "1380"},{"name": "CODE", "value": "111"}
]
sms_ir = SmsIr(API_KEY,linenumber,)

# ret = sms_ir.send_sms(number,message,linenumber,)
# #print(ret)

a = sms_ir.get_line_numbers()
#print(a.text)

# a = sms_ir.send_verify_code(number,template_id,parameters,)

phone_number = '0913568040'
linenumber = 30002128094276

#print(a)
def test_sens():

      conn = http.client.HTTPSConnection("api.sms.ir")
      payload = ''
      headers = {
        'Accept': 'text/plain'
      }
      conn.request(
        "GET",
       f"/v1/send?username=MY_USERNAME&password={API_KEY}&mobile={phone_number}&line={linenumber}&text=MESSAGE_TEXT",
        payload,
        headers
        )
      res = conn.getresponse()
      data = res.read()
      print(data.decode("utf-8"))


def send_liek2like():



      conn = http.client.HTTPSConnection("api.sms.ir")
      payload = json.dumps({
        "lineNumber": linenumber,
        "messageTexts": [
          "Your Text 1",
          "Your Text 2"
        ],
        "mobiles": [
          "09135689040",
          "09130006344"
        ],
        "senddatetime": None
      })
      headers = {
        'Content-Type': 'application/json',
        'Accept': 'text/plain',
        'X-API-KEY': 'PN1TVeBeaAehFLJAKU4XdfpsFXsQguYfleO0bV4ceh6diTZid2hRXza3uSkBbDef'
      }
      conn.request("POST", "/v1/send/likeToLike", payload, headers)
      res = conn.getresponse()
      data = res.read()
      print(data.decode("utf-8"))
    

      



if __name__=='__main__':
      send_liek2like()