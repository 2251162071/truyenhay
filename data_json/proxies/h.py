import urllib3

# Thông tin proxy
proxy_url = "https://93.177.116.221:8085"

# Tạo HTTP proxy manager với urllib3
http = urllib3.ProxyManager(proxy_url)

# # Gửi yêu cầu HTTP
# url = "https://httpbin.org/ip"
# response = http.request("GET", url)
# print("HTTP response:", response.data.decode('utf-8'))

# Gửi yêu cầu HTTPS
https_url = "https://httpbin.org/ip"
response = http.request("GET", https_url)
print("HTTPS response:", response.data.decode('utf-8'))
