from google import genai
from google.genai import types

flag ='y'
while flag == 'y':
    client = genai.Client()
    temp=input("Detrmine the value: ")
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents="what is the capital",
        config=types.GenerateContentConfig(temperature=temp)
    )
    #print(f"With temperature = {temp}")
    print(response.text)
    flag=input("Do u want to continue? (y/n) :")
