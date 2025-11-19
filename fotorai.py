"""
Fotor AI Image Generator Automation Tool

This script automates the process of creating accounts, logging in, and generating
AI images using the Fotor API. It handles the complete workflow from account creation
to image download.

Note: This is an archived project and may not work with current Fotor API endpoints.
"""

import json
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import requests
from faker import Faker
from selenium import webdriver
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    WebDriverException
)
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By


# ============================================================================
# CONFIGURATION CONSTANTS
# ============================================================================

# API Endpoints
URL_FOTOR_BASE = 'https://www.fotor.com'
URL_FOTOR_AI_GENERATOR = f'{URL_FOTOR_BASE}/features/ai-image-generator/'
URL_API_REGISTER = f'{URL_FOTOR_BASE}/api/user/register/email'
URL_API_LOGIN = f'{URL_FOTOR_BASE}/api/user/login/email'
URL_API_GENERATE = f'{URL_FOTOR_BASE}/api/create/v2/generate_picture'
URL_API_GET_PICTURE = f'{URL_FOTOR_BASE}/api/create/v2/get_picture_url'

# File Paths
CHROMEDRIVER_PATH = 'chromedriver.exe'
COOKIES_FILE = 'cookies.txt'
OUTPUT_DIR = Path('.')

# Credentials - SECURITY: Use environment variables instead of hardcoding
# Set these via: $env:FOTOR_PASSWORD="your_password" (PowerShell)
# or export FOTOR_PASSWORD="your_password" (Bash)
import os
DEFAULT_PASSWORD = os.getenv('FOTOR_PASSWORD', 'password123!')  # Fallback for demo only
DEFAULT_PASSWORD_HASH = os.getenv('FOTOR_PASSWORD_HASH', '0bd1e44589ce202739759ca548a8a3f1')  # MD5 hash

# Timeouts and Delays (in seconds)
TIMEOUT_AFTER_REGISTRATION = 3
TIMEOUT_AFTER_LOGIN = 3
TIMEOUT_IMAGE_GENERATION_POLL = 5
TIMEOUT_REQUEST = 30

# Image Generation Settings
DEFAULT_IMAGE_COUNT = 5
DEFAULT_TEMPLATE_ID = '6b81f30e6a1e4b0f9aa8b8e390431504'
DEFAULT_WH_PROPORTION = '6361df0ac09cb851c66328a1'
DEFAULT_UPSCALE = '2 0.75'

# XPath Selectors (likely outdated)
XPATH_LOGIN_BUTTON = '/html/body/div[1]/div[2]/div/div[2]/div[1]/button[2]'
XPATH_EMAIL_FIELD = '//*[@id="rootLogin"]/div/div/div[2]/div[1]/div/div[5]/input'
XPATH_PASSWORD_FIELD = '//*[@id="rootLogin"]/div/div/div[2]/div[1]/div/div[6]/input'
XPATH_SUBMIT_BUTTON = '//*[@id="rootLogin"]/div/div/div[2]/div[1]/div/div[8]/div'

# HTTP Status Codes
HTTP_OK = 200
API_RATE_LIMIT_CODE = '510'



# ============================================================================
# HTTP HEADERS
# ============================================================================

def get_registration_headers() -> Dict[str, str]:
    """
    Get HTTP headers for registration and login requests.
    
    Returns:
        Dictionary containing HTTP headers
    """
    return {
        'Host': 'www.fotor.com',
        'Sec-Ch-Ua': '"Not A(Brand";v="99", "Google Chrome";v="91"',
        'X-Fotor-Sa-Project_type': 'ai_image',
        'Sec-Ch-Ua-Mobile': '?0',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'X-Fotor-Sa-Position': 'smalltool_aiimage_header',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'application/json, text/plain, */*',
        'X-Fotor-Sa-Location': f'{URL_FOTOR_AI_GENERATOR}?tooltype=aiart',
        'Sec-Ch-Ua-Platform': '"Windows"',
        'Origin': URL_FOTOR_BASE,
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Dest': 'empty',
        'Referer': f'{URL_FOTOR_AI_GENERATOR}?tooltype=aiart',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'en-US,en;q=0.9',
    }


def get_generation_headers() -> Dict[str, str]:
    """
    Get HTTP headers for image generation requests.
    
    Returns:
        Dictionary containing HTTP headers
    """
    return {
        'Content-Type': 'application/json',
        'X-App-Id': 'app-fotor-web',
        'Sec-Ch-Ua-Mobile': '?0',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.5481.178 Safari/537.36',
        'Sec-Ch-Ua-Platform': '"Windows"',
        'Origin': URL_FOTOR_BASE,
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Dest': 'empty',
        'Referer': URL_FOTOR_AI_GENERATOR,
    }


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def generate_fake_credentials() -> Tuple[str, str, str]:
    """
    Generate fake user credentials using Faker.
    
    Returns:
        Tuple containing (email, password, password_hash)
    """
    fake = Faker()
    email = fake.email(domain=fake.domain_name())
    password = DEFAULT_PASSWORD
    password_hash = DEFAULT_PASSWORD_HASH
    
    return email, password, password_hash


def configure_chrome_options() -> ChromeOptions:
    """
    Configure Chrome browser options for Selenium automation.
    
    Returns:
        Configured ChromeOptions object
    """
    options = ChromeOptions()
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-popup-blocking')
    options.add_argument('--profile-directory=Default')
    options.add_argument('--disable-plugins-discovery')
    options.add_argument('--incognito')
    # options.add_argument('--headless')  # Uncomment for headless mode
    options.add_argument('--disable-blink-features=AutomationControlled')
    
    return options


def save_cookies_to_file(cookies: Dict[str, str], filepath: str = COOKIES_FILE) -> None:
    """
    Save cookies to a text file.
    
    Args:
        cookies: Dictionary of cookie names and values
        filepath: Path to the output file
    """
    try:
        with open(filepath, 'w', encoding='utf-8') as file:
            for name, value in cookies.items():
                file.write(f'{name}={value}\n')
        print(f'Cookies saved to {filepath}')
    except IOError as error:
        print(f'Error saving cookies to file: {error}')
        raise


def load_cookies_from_file(filepath: str = COOKIES_FILE) -> Dict[str, str]:
    """
    Load cookies from a text file.
    
    The file should contain cookies in format: name=value (one per line)
    or name=value;attribute=val (semicolon-separated).
    
    Args:
        filepath: Path to the cookies file
        
    Returns:
        Dictionary containing cookies
        
    Raises:
        FileNotFoundError: If the cookies file doesn't exist
    """
    cookies = {}
    
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            for line in file:
                line = line.strip()
                if not line:
                    continue
                
                # Parse cookies: accumulate all key-value pairs from the line
                parts = line.split(';')
                line_cookie = {}  # Initialize once per line
                
                for part in parts:
                    part = part.strip()
                    if '=' in part:
                        key, value = part.split('=', 1)
                        line_cookie[key.strip()] = value.strip()
                    else:
                        # Handle attributes without values (e.g., domain)
                        line_cookie['domain'] = part
                
                # Only store cookies that contain _fotor_sid
                if '_fotor_sid' in line_cookie:
                    cookies.update(line_cookie)
        
        return cookies
    except FileNotFoundError:
        print(f'Cookies file not found: {filepath}')
        raise
    except IOError as error:
        print(f'Error reading cookies file: {error}')
        raise


# ============================================================================
# ACCOUNT MANAGEMENT
# ============================================================================

def register_account(email: str, password_hash: str) -> bool:
    """
    Register a new Fotor account.
    
    Args:
        email: User email address
        password_hash: Hashed password
        
    Returns:
        True if registration successful, False otherwise
    """
    headers = get_registration_headers()
    
    data = {
        'email': email,
        'password': password_hash,
        'userName': 'test',
        'platform': 'Fotor',
        'product_id': 'Fotor_Web_H5',
        'language': 'en_US'
    }
    
    try:
        response = requests.post(
            URL_API_REGISTER,
            headers=headers,
            data=data,
            timeout=TIMEOUT_REQUEST
        )
        
        if response.status_code == HTTP_OK:
            print(f'✓ Registration successful for {email}')
            return True
        else:
            print(f'✗ Registration failed: {response.status_code} - {response.text}')
            return False
            
    except requests.RequestException as error:
        print(f'✗ Registration request failed: {error}')
        return False


def extract_cookies_with_selenium(email: str, password: str) -> Optional[Dict[str, str]]:
    """
    Use Selenium to log in and extract session cookies.
    
    Args:
        email: User email address
        password: User password (plain text)
        
    Returns:
        Dictionary of cookies if successful, None otherwise
    """
    driver = None
    
    try:
        options = configure_chrome_options()
        driver = webdriver.Chrome(executable_path=CHROMEDRIVER_PATH, options=options)
        
        # Navigate to the login page
        print('Opening Fotor AI Generator page...')
        driver.get(URL_FOTOR_AI_GENERATOR)
        time.sleep(2)
        
        # Click the login button
        print('Clicking login button...')
        login_button = driver.find_element(By.XPATH, XPATH_LOGIN_BUTTON)
        login_button.click()
        time.sleep(1)
        
        # Fill in email
        print('Entering credentials...')
        email_field = driver.find_element(By.XPATH, XPATH_EMAIL_FIELD)
        email_field.send_keys(email)
        
        # Fill in password
        password_field = driver.find_element(By.XPATH, XPATH_PASSWORD_FIELD)
        password_field.send_keys(password)
        
        # Submit login form
        submit_button = driver.find_element(By.XPATH, XPATH_SUBMIT_BUTTON)
        submit_button.click()
        
        # Wait for login to complete
        print('Waiting for login to complete...')
        time.sleep(TIMEOUT_AFTER_LOGIN)
        
        # Extract cookies
        cookies = {}
        for cookie in driver.get_cookies():
            cookies[cookie['name']] = cookie['value']
        
        print(f'✓ Extracted {len(cookies)} cookies')
        return cookies
        
    except NoSuchElementException as error:
        print(f'✗ Could not find element (selectors may be outdated): {error}')
        return None
    except TimeoutException as error:
        print(f'✗ Timeout during browser automation: {error}')
        return None
    except WebDriverException as error:
        print(f'✗ WebDriver error: {error}')
        return None
    except Exception as error:
        print(f'✗ Unexpected error during cookie extraction: {error}')
        return None
    finally:
        if driver:
            try:
                driver.quit()
                print('Browser closed')
            except Exception as error:
                print(f'Warning: Error closing browser: {error}')


# ============================================================================
# IMAGE GENERATION
# ============================================================================

def generate_images(prompt: str, cookies: Dict[str, str], 
                   image_count: int = DEFAULT_IMAGE_COUNT) -> Optional[List[str]]:
    """
    Generate AI images using the Fotor API.
    
    Args:
        prompt: Text description for image generation
        cookies: Session cookies for authentication
        image_count: Number of images to generate
        
    Returns:
        List of task IDs if successful, None otherwise
    """
    headers = get_generation_headers()
    
    data = {
        "content": prompt,
        "upscale": DEFAULT_UPSCALE,
        "whProportion": DEFAULT_WH_PROPORTION,
        "templateId": DEFAULT_TEMPLATE_ID,
        "labelList": [],
        "pictureNums": image_count,
        "originalImageUrl": "",
        "useChannel": "vip",
        "customAppName": "fotorWeb"
    }
    
    try:
        response = requests.post(
            URL_API_GENERATE,
            headers=headers,
            data=json.dumps(data),
            cookies=cookies,
            timeout=TIMEOUT_REQUEST
        )
        
        if response.status_code != HTTP_OK:
            print(f'✗ Image generation failed: {response.status_code} - {response.text}')
            return None
        
        response_data = response.json()
        
        # Check for rate limit
        if response_data.get('code') == API_RATE_LIMIT_CODE:
            print('✗ API rate limit reached')
            return None
        
        # Extract task IDs
        task_ids = [item['taskId'] for item in response_data.get('data', [])]
        
        if task_ids:
            print(f'✓ Initiated generation of {len(task_ids)} images')
            return task_ids
        else:
            print('✗ No task IDs returned from API')
            return None
            
    except requests.RequestException as error:
        print(f'✗ Image generation request failed: {error}')
        return None
    except (KeyError, ValueError) as error:
        print(f'✗ Error parsing API response: {error}')
        return None


def wait_for_images(task_ids: List[str], cookies: Dict[str, str]) -> Optional[List[Dict]]:
    """
    Poll the API until all images are generated.
    
    Args:
        task_ids: List of task IDs to check
        cookies: Session cookies for authentication
        
    Returns:
        List of image data dictionaries if successful, None otherwise
    """
    print('Waiting for image generation to complete...')
    
    while True:
        try:
            task_ids_param = ','.join(task_ids)
            url = f'{URL_API_GET_PICTURE}?taskIds={task_ids_param}'
            
            response = requests.get(url, cookies=cookies, timeout=TIMEOUT_REQUEST)
            
            if response.status_code != HTTP_OK:
                print(f'✗ Error checking image status: {response.status_code}')
                return None
            
            response_data = response.json()
            
            # Check for rate limit
            if response_data.get('code') == API_RATE_LIMIT_CODE:
                print('✗ API rate limit reached while checking status')
                return None
            
            images_data = response_data.get('data', [])
            
            # Check if all images are ready (status == 1)
            if all(item.get('status') == 1 for item in images_data):
                print('✓ All images generated successfully')
                return images_data
            
            # Wait before polling again
            time.sleep(TIMEOUT_IMAGE_GENERATION_POLL)
            
        except requests.RequestException as error:
            print(f'✗ Error polling image status: {error}')
            return None
        except (KeyError, ValueError) as error:
            print(f'✗ Error parsing status response: {error}')
            return None


def download_images(images_data: List[Dict], output_dir: Path = OUTPUT_DIR) -> int:
    """
    Download generated images to disk.
    
    Args:
        images_data: List of dictionaries containing image URLs and task IDs
        output_dir: Directory to save images
        
    Returns:
        Number of successfully downloaded images
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)
    
    downloaded_count = 0
    
    for item in images_data:
        try:
            picture_url = item.get('pictureUrl')
            task_id = item.get('taskId')
            
            if not picture_url or not task_id:
                print(f'✗ Missing URL or task ID in image data: {item}')
                continue
            
            # Download the image
            response = requests.get(picture_url, timeout=TIMEOUT_REQUEST)
            
            if response.status_code == HTTP_OK:
                filename = output_dir / f'{task_id}.jpg'
                
                with open(filename, 'wb') as file:
                    file.write(response.content)
                
                print(f'✓ Downloaded: {filename}')
                downloaded_count += 1
            else:
                print(f'✗ Failed to download {task_id}: {response.status_code}')
                
        except requests.RequestException as error:
            print(f'✗ Download error for {task_id}: {error}')
        except IOError as error:
            print(f'✗ File write error for {task_id}: {error}')
    
    return downloaded_count


# ============================================================================
# MAIN WORKFLOW
# ============================================================================

def run_image_generation_workflow() -> None:
    """
    Execute the complete workflow: register, login, generate, and download images.
    """
    print('=' * 70)
    print('Fotor AI Image Generator - Automated Workflow')
    print('=' * 70)
    print()
    
    # Step 1: Generate credentials
    print('[1/6] Generating credentials...')
    email, password, password_hash = generate_fake_credentials()
    print(f'✓ Generated account: {email}')
    print()
    
    # Step 2: Register account
    print('[2/6] Registering account...')
    if not register_account(email, password_hash):
        print('Workflow aborted: Registration failed')
        return
    time.sleep(TIMEOUT_AFTER_REGISTRATION)
    print()
    
    # Step 3: Extract cookies via browser automation
    print('[3/6] Extracting session cookies...')
    cookies = extract_cookies_with_selenium(email, password)
    
    if not cookies:
        print('Workflow aborted: Cookie extraction failed')
        return
    
    # Save cookies to file
    save_cookies_to_file(cookies)
    print()
    
    # Step 4: Load cookies for API requests
    print('[4/6] Loading cookies...')
    try:
        cookies = load_cookies_from_file()
        print('✓ Cookies loaded successfully')
    except Exception as error:
        print(f'Workflow aborted: Could not load cookies - {error}')
        return
    print()
    
    # Step 5: Image generation loop
    print('[5/6] Starting image generation...')
    
    while True:
        try:
            prompt = input('\nEnter image prompt (or "quit" to exit): ').strip()
            
            if prompt.lower() in ('quit', 'exit', 'q'):
                print('Exiting...')
                break
            
            if not prompt:
                print('Please enter a valid prompt')
                continue
            
            # Generate images
            task_ids = generate_images(prompt, cookies)
            
            if not task_ids:
                print('Image generation failed. You may have hit the rate limit.')
                break
            
            # Wait for images to be ready
            images_data = wait_for_images(task_ids, cookies)
            
            if not images_data:
                print('Failed to retrieve generated images')
                break
            
            # Download images
            print('\n[6/6] Downloading images...')
            downloaded = download_images(images_data)
            print(f'\n✓ Successfully downloaded {downloaded}/{len(images_data)} images\n')
            
        except KeyboardInterrupt:
            print('\n\nWorkflow interrupted by user')
            break
        except Exception as error:
            print(f'\n✗ Unexpected error: {error}')
            break
    
    print('\n' + '=' * 70)
    print('Workflow completed')
    print('=' * 70)


if __name__ == '__main__':
    try:
        run_image_generation_workflow()
    except Exception as error:
        print(f'\n✗ Fatal error: {error}')
        sys.exit(1)

