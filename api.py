from flask import Flask, request, jsonify
import requests
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import threading
import json
from datetime import datetime

app = Flask(__name__)

class RefreshBot:
    def __init__(self):
        self.is_running = False
        self.thread = None
        self.chrome_options = Options()
        self.chrome_options.add_argument('--headless')
        self.driver = None

    def check_status(self, status_url):
        """Check status of bots from the API"""
        try:
            response = requests.get(status_url)
            data = json.loads(response.text)
            print(f"\nStatus check at {datetime.now().strftime('%H:%M:%S')}:")
            print(f"Response content: {data}")
            
            conditions = {
                'binanc': data["binanc"].get("additional_info") == "No additional info" and 
                         data["binanc"].get("is_running") is False,
                'sdx': data["sdx"].get("additional_info") == "No additional info" and 
                      data["sdx"].get("is_running") is False
            }
            print(f"Check results: {conditions}")
            return conditions
            
        except Exception as e:
            print(f"Error checking status: {e}")
            return {'binanc': False, 'sdx': False}

    def refresh_urls(self, interval):
        """Main refresh loop"""
        print(f"\nStarting bot with {interval} seconds interval")
        self.driver = webdriver.Chrome(options=self.chrome_options)
        status_url = "https://mmbot.shop/api/binanc/status"
        urls = {
            'binanc': 'https://mmbot.shop/api/binanc/binanc/start',
            'sdx': 'https://mmbot.shop/api/binanc/sdx/start'
        }

        cycle_count = 0
        while self.is_running:
            try:
                cycle_count += 1
                print(f"\nCheck cycle #{cycle_count} at {datetime.now().strftime('%H:%M:%S')}")
                conditions = self.check_status(status_url)
                
                for bot_type, should_refresh in conditions.items():
                    if should_refresh:
                        print(f"Refreshing {bot_type}...")
                        self.driver.get(urls[bot_type])
                        print(f"Successfully refreshed {bot_type}")
                    else:
                        print(f"No refresh needed for {bot_type}")
                
                print(f"Waiting {interval} seconds until next check...")
                time.sleep(interval)
            except Exception as e:
                print(f"Error in refresh cycle: {e}")
                time.sleep(interval)
        
        print("Bot stopped")
        self.driver.quit()

    def start_refresh(self, interval=300):
        """Start the refresh bot"""
        if not self.is_running:
            self.is_running = True
            self.thread = threading.Thread(
                target=self.refresh_urls,
                args=(interval,)
            )
            self.thread.start()
            return True
        return False

    def stop_refresh(self):
        """Stop the refresh bot"""
        if self.is_running:
            self.is_running = False
            if self.thread:
                self.thread.join()
            return True
        return False

bot = RefreshBot()

@app.route('/start')
def start():
    interval = int(request.args.get('interval', 300))
    success = bot.start_refresh(interval)
    
    return jsonify({
        'status': 'started' if success else 'already running',
        'message': 'Bot started successfully' if success else 'Bot is already running'
    })

@app.route('/stop')
def stop():
    success = bot.stop_refresh()
    return jsonify({
        'status': 'stopped' if success else 'not running',
        'message': 'Bot stopped successfully' if success else 'Bot is not running'
    })

@app.route('/status')
def status():
    return jsonify({
        'status': 'running' if bot.is_running else 'stopped',
        'message': 'Bot is running' if bot.is_running else 'Bot is stopped'
    })

if __name__ == '__main__':
    # Run the app on all network interfaces
    app.run(debug=True, port=5000, host='0.0.0.0')