import os
import requests
from kreta_api import Session as KretaSession
from idp_api import IdpApiV1
from config import HEADERS
import webbrowser

class KretaTerminalApp:
    def __init__(self):
        self.session = None
        self.current_week = 0

    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def center_text(self, text, width=80):
        return text.center(width)

    def display_menu(self):
        self.clear_screen()
        print(self.center_text("KRETA Terminal"))
        print(self.center_text("=" * 20))
        print()
        print(self.center_text("[Login]"))
        print()
        print(self.center_text("Press Enter to login or 'q' to quit"))

    def login(self):
        nonce = IdpApiV1.getNonce()
        login_url = f"https://idp.e-kreta.hu/connect/authorize?client_id=kreta-ellenorzo-mobile-android&response_type=code&scope=openid%20offline_access&state=state&nonce={nonce}&redirect_uri=https://idp.e-kreta.hu/mobilelogin"
        
        print("Please login using the opened browser window.")
        print("After successful login, copy the URL you are redirected to.")
        webbrowser.open(login_url)
        
        redirect_url = input("Enter the URL you were redirected to: ")
        code = redirect_url.split("code=")[1].split("&")[0]
        
        token_url = "https://idp.e-kreta.hu/connect/token"
        data = {
            "client_id": "kreta-ellenorzo-mobile-android",
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": "https://idp.e-kreta.hu/mobilelogin"
        }
        response = requests.post(token_url, data=data, headers=HEADERS)
        
        if response.status_code == 200:
            token_data = response.json()
            self.session = KretaSession(token_data["access_token"], token_data["refresh_token"], False)
            print("Login successful!")
            return True
        else:
            print("Login failed. Please try again.")
            return False

    def display_schedule(self):
        if not self.session:
            print("Please login first.")
            return

        self.clear_screen()
        print(self.center_text("Your Schedule"))
        print(self.center_text("=" * 20))
        print()

        # Itt használjuk a KretaSession osztály getLessons metódusát
        lessons = self.session.getLessons()
        
        # Rendezzük a leckéket dátum szerint
        lessons.sort(key=lambda x: x['KezdetIdopont'])

        current_date = None
        for lesson in lessons:
            lesson_date = lesson['KezdetIdopont'].split('T')[0]
            if lesson_date != current_date:
                print(f"\n{lesson_date}:")
                current_date = lesson_date

            start_time = lesson['KezdetIdopont'].split('T')[1][:5]
            end_time = lesson['VegIdopont'].split('T')[1][:5]
            subject = lesson['TantargyNeve']
            classroom = lesson.get('TeremNeve', 'N/A')

            print(f"  {start_time} - {end_time}: {subject} ({classroom})")

        print("\nUse left/right arrow keys to navigate weeks. Press 'q' to quit.")

    def run(self):
        while True:
            self.display_menu()
            choice = input().lower()
            
            if choice == 'q':
                break
            
            if not self.session:
                if not self.login():
                    continue

            self.display_schedule()

            while True:
                key = input()
                if key == 'q':
                    return
                elif key == '\x1b[D':  # Left arrow
                    self.current_week -= 1
                    self.display_schedule()
                elif key == '\x1b[C':  # Right arrow
                    self.current_week += 1
                    self.display_schedule()

if __name__ == "__main__":
    app = KretaTerminalApp()
    app.run()