import openai


#openai.api_key = "ENTER YOUR API KEY HERE"


def request_api(messages,model,request=True):
    if not request:
        print("Request not sent")
        return 1,"The Request has not been sent due to user input" 
    return_value = 1
    response = ""
    try:
        response = openai.chat.completions.create(
                model = model,
                messages = messages
        )
    except Exception as e:
        response = str(e)
        return_value = -1
    if return_value==1:
        return 1 , response.choices[0].message.content
    else:
        return return_value,response



