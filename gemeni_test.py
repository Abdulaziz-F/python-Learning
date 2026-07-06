# Today we will learn how diffrent prompts will affect of the answers of LLM.
''' Usually, a good prompts consist of 4 thing :
   1. ROLE: To specify the role of LLM, for example, "you are a Python expert", "you are a AI teacher".
   2. Task: what's require? , for example, "Exaplain SQL Injection".
   3. Constraints: specify the condetion, for example, "Explain it in 150 words", "Use bullet points".
   4. Output Format (optional): Return the answer as points/table. 

'''
from google import genai
from google.genai import types

flag ='y'
while flag == 'y':
    client = genai.Client()
    temp=input("Detrmine the value: ")
    answer= input("What do u what to ask: ") 
    print()
    response = client.models.generate_content(
        model="gemini-2.5-flash",#You are a python instructor,
                                 #Explain Python to a complete beginner,
                                 #use simple language, geve one real-life example,
                                 #limite your answer to 120 words
        contents=answer, 
        config=types.GenerateContentConfig(temperature=temp)
    )
    #print(f"With temperature = {temp}")
    print(response.text)
    flag=input("Do u want to continue? (y/n) :")

# here we notice the answer is more specific.



