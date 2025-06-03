import requests

url = "https://api.freelancehunt.com/v2/threads/{{thread_id}}/attachment"

payload={}
files=[
  ('attachment1',('example.jpg',open('/home/my/Downloads/example.jpg','rb'),'image/jpeg')),
  ('attachment2',('files.rar',open('/home/my/Downloads/files.rar','rb'),'application/x-rar-compressed'))
]
headers = {
  'Authorization': 'Bearer {{token}}',
  'Content-Type': 'application/x-www-form-urlencoded'
}

response = requests.request("POST", url, headers=headers, data=payload, files=files)

print(response.text)
