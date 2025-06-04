import requests
from bs4 import BeautifulSoup
import re
import sys

def register_user(base_url, username, email, password, first_name="", last_name="", debug=False):
    # Create a session to maintain cookies
    session = requests.Session()
    
    # Get the registration page to retrieve CSRF token
    register_url = f"{base_url}/register/"
    response = session.get(register_url)
    
    if debug:
        print(f"GET Status Code: {response.status_code}")
        print(f"Cookies received: {dict(session.cookies)}")
    
    # Parse the HTML to extract the CSRF token
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Try multiple methods to find the CSRF token
    csrf_input = soup.find('input', {'name': 'csrfmiddlewaretoken'})
    
    if csrf_input:
        csrf_token = csrf_input.get('value')
    else:
        # Look for the token in the HTML content
        csrf_pattern = re.compile(r'csrftoken=([^;]+)')
        match = csrf_pattern.search(response.headers.get('Set-Cookie', ''))
        if match:
            csrf_token = match.group(1)
        else:
            print("Could not find CSRF token in the page or cookies")
            if debug:
                print("HTML content preview:")
                print(response.text[:500])
            return False
    
    if debug:
        print(f"Found CSRF Token: {csrf_token}")
    
    # Create registration data
    data = {
        'username': username,
        'email': email,
        'password': password,
        'confirm_password': password,
        'first_name': first_name,
        'last_name': last_name,
        'csrfmiddlewaretoken': csrf_token
    }
    
    # Set headers to mimic browser behavior
    headers = {
        'Referer': register_url,
        'X-CSRFToken': csrf_token,
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml',
        'Origin': base_url
    }
    
    if debug:
        print("Sending POST request with:")
        print(f"Headers: {headers}")
        print(f"Data: {data}")
        print(f"Cookies: {dict(session.cookies)}")
    
    # Submit the registration form
    response = session.post(register_url, data=data, headers=headers)
    
    if debug:
        print(f"POST Status Code: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        print(f"Response URL: {response.url}")
    
    # Check if registration was successful
    if response.status_code == 200 and "Account created successfully" in response.text:
        print("Registration successful!")
        return True
    elif response.status_code == 302 and response.url.endswith('/login/'):
        print("Registration successful! Redirected to login page.")
        return True
    else:
        print(f"Registration failed. Status code: {response.status_code}")
        # Try to extract error messages
        soup = BeautifulSoup(response.text, 'html.parser')
        error_msgs = soup.find_all(class_='message')
        if error_msgs:
            print("Error messages:")
            for msg in error_msgs:
                print(f"- {msg.text.strip()}")
        
        if debug and response.status_code == 403:
            print("\nCSRF Verification Failed. Response content:")
            print(response.text[:1000])
            
        return False

if __name__ == "__main__":
    # Configuration
    BASE_URL = "http://localhost:8000"  # Change to your server URL
    
    # Enable debug mode with command line arg
    DEBUG = "-d" in sys.argv or "--debug" in sys.argv
    
    # User details - can be customized from command line
    USERNAME = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "testuser123"
    EMAIL = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith("-") else f"{USERNAME}@example.com"
    PASSWORD = sys.argv[3] if len(sys.argv) > 3 and not sys.argv[3].startswith("-") else "securepassword123"
    FIRST_NAME = sys.argv[4] if len(sys.argv) > 4 and not sys.argv[4].startswith("-") else "Test"
    LAST_NAME = sys.argv[5] if len(sys.argv) > 5 and not sys.argv[5].startswith("-") else "User"
    
    print(f"Attempting to register user: {USERNAME}")
    
    # Register the user
    result = register_user(
        BASE_URL,
        USERNAME,
        EMAIL,
        PASSWORD,
        FIRST_NAME,
        LAST_NAME,
        DEBUG
    )
    
    if result:
        print(f"User {USERNAME} registered successfully!")
    else:
        print("Registration failed. See above for details.") 