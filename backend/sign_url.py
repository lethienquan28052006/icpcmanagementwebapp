# sign_url.py
import time
import random
import string
import hashlib

API_KEY = "12b0d3dffa133a35baf0468e1593f8af729030c5" #my API key
API_SECRET = "9dd282d3b9afcc3973a9e15865fbae9e94098ca8" #my API secret

def generate_random_string(length=6): #generate a random string of fixed length
    """
    Generate a random string of fixed length.

    Args:
        length (int, optional): The length of the random string. Defaults to 6.

    Returns:
        str: A random alphanumeric string of the specified length.
    """
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def build_signed_url(method_name, params): #generate a signed URL for the Codeforces API
    """
    Generate a signed URL for the Codeforces API.

    Args:
        method_name (str): The API method name (e.g., 'contest.standings').
        params (dict): The parameters to include in the API request.

    Returns:
        str: The signed URL ready for use with the Codeforces API.
    """
    params["apiKey"] = API_KEY
    params["time"] = str(int(time.time()))
    sorted_params = sorted(params.items())
    param_str = '&'.join(f"{k}={v}" for k, v in sorted_params)

    rand = generate_random_string()
    base = f"{rand}/{method_name}?{param_str}#{API_SECRET}"
    hash_val = hashlib.sha512(base.encode()).hexdigest()
    apiSig = rand + hash_val
    return f"https://codeforces.com/api/{method_name}?{param_str}&apiSig={apiSig}"