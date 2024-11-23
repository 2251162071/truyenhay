import requests

# List of proxies
proxy_list = [
    '193.202.80.221:8085'
    # Add more proxies as needed
]

# Function to rotate proxies
def get_proxy():
    global proxy_list
    proxy = proxy_list.pop(0)
    proxy_list.append(proxy)
    return {'https': 'https://' + proxy}

# Function to make a request using rotated proxy
def make_request(url):
    try:
        proxy = get_proxy()
        response = requests.get(url, proxies=proxy, timeout=20, verify=False)
        if response.status_code == 200:
            return response.text
        else:
            print(f"Request failed with status code: {response.status_code}")
            return None
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return None

# Example usage
if __name__ == "__main__":
    target_url = 'https://httpbin.org/ip'
    for _ in range(10):  # Make 10 requests
        response = make_request(target_url)
        if response:
            print(response)
        else:
            print("Request failed.")