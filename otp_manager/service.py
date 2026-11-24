


import json

from otp_manager.models import OTPVar_Enum, SMS_Template, SMSServiceName_Enum
from sms_ir import SmsIr #pip install smsir-python

import http.client
import json

conn = http.client.HTTPSConnection("api.sms.ir")




def send_sms(template_obj:SMS_Template,phone_number,vars):

    ret = False
    
    if template_obj.service.sms_panel == SMSServiceName_Enum.SMS_IR:
        ret = sms_ir(template_obj,phone_number,vars)

    return ret



def sms_ir(template_obj:SMS_Template,phone_number,vars):

    api_key = template_obj.service.api_key
    linenumber = template_obj.service.line_number
    template_id = template_obj.template_id

    parameters = []
    for key,value in vars.items():
        parms = {"name":key,"value":value}
        parameters.append(parms)



    sms_ir = SmsIr(api_key,linenumber,)
    ret = sms_ir.send_verify_code(phone_number,template_id,parameters,)
    return ret.ok



def send_like2like(template_obj:SMS_Template,phone_numbers:list,text:list,date_time=None):
    
    try:
        api_key = template_obj.service.api_key
        linenumber = template_obj.service.line_number

        payload = json.dumps({
            "lineNumber": linenumber,
            "messageTexts": text,
            "mobiles": phone_numbers,
            "senddatetime": None
        })

        headers = {
            'Content-Type': 'application/json',
            'Accept': 'text/plain',
            'X-API-KEY': api_key
        }

        conn.request("POST", "/v1/send/likeToLike", payload, headers)
        res = conn.getresponse()
        data = res.read()
        return data

    except:
        return False




if __name__=='__main__':

    obj = SMS_Template.objects.first()
    phones = ['09135689040']
    text = ['salam']
    send_like2like(obj,)