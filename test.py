import google.generativeai as genai
import toml
import time
from pathlib import Path

def test_api_key(key: str, key_number: int) -> tuple[bool, float, str]:
    """Test a single Gemini API key and return success status, response time, and any error message."""
    start_time = time.time()
    try:
        # Configure the model
        genai.configure(api_key=key)
        model = genai.GenerativeModel('gemini-1.5-flash-8b')
        
        # Try a simple generation
        response = model.generate_content("Hello")
        
        duration = time.time() - start_time
        return True, duration, ""
    except Exception as e:
        duration = time.time() - start_time
        return False, duration, str(e)

def main():
    # Read the secrets file
    secrets_path = Path('.streamlit/secrets.toml')
    if not secrets_path.exists():
        print("Error: secrets.toml file not found!")
        return

    secrets = toml.load(secrets_path)
    
    # Test each API key
    print("\nTesting Gemini API Keys...")
    print("-" * 50)
    
    all_valid = True
    for i in range(1, 6):
        key_name = f"GEMINI_API_KEY_{i}"
        key = secrets.get(key_name)
        
        if not key:
            print(f"{key_name}: NOT FOUND in secrets.toml")
            all_valid = False
            continue
            
        print(f"\nTesting {key_name}...")
        success, duration, error = test_api_key(key, i)
        
        if success:
            print(f"✅ Valid! (Response time: {duration:.2f}s)")
        else:
            print(f"❌ Invalid! (Time: {duration:.2f}s)")
            print(f"Error: {error}")
            all_valid = False
    
    print("\n" + "-" * 50)
    print("Summary:")
    print("All keys valid!" if all_valid else "Some keys are invalid!")

if __name__ == "__main__":
    main()