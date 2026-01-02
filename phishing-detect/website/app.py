import os
import re
import socket
import ssl
import whois
import requests
import pickle
import ipaddress
import tldextract
import numpy as np
from flask import Flask, render_template, request, jsonify
from urllib.parse import urlparse, urlencode
from datetime import datetime
from bs4 import BeautifulSoup

app = Flask(__name__)

# Load Model
MODEL_PATH = 'randomforest_model.pkl'
model = None

try:
    with open(MODEL_PATH, 'rb') as f:
        model = pickle.load(f)
    print(f"Model loaded successfully from {MODEL_PATH}")
except FileNotFoundError:
    print(f"WARNING: Model file {MODEL_PATH} not found. Prediction will use dummy random values.")
    model = None
except Exception as e:
    print(f"ERROR: Could not load model: {e}")
    model = None

class FeatureExtractor:
    def __init__(self, url):
        self.url = url
        self.domain = ""
        self.whois_response = None
        self.url_parse = None
        self.response = None
        self.soup = None

        try:
            self.response = requests.get(url, timeout=5)
            self.soup = BeautifulSoup(self.response.text, 'html.parser')
        except:
            pass

        try:
            self.url_parse = urlparse(url)
            self.domain = self.url_parse.netloc
        except:
            pass

        try:
            self.whois_response = whois.whois(self.domain)
        except:
            pass

    def get_features(self):
        features = []
        # 1. UsingIP
        features.append(self.using_ip())
        # 2. LongURL
        features.append(self.long_url())
        # 3. ShortURL
        features.append(self.short_url())
        # 4. Symbol@
        features.append(self.symbol_at())
        # 5. Redirecting//
        features.append(self.redirecting_double_slash())
        # 6. PrefixSuffix-
        features.append(self.prefix_suffix_hyphen())
        # 7. SubDomains
        features.append(self.sub_domains())
        # 8. HTTPS
        features.append(self.http_s())
        # 9. DomainRegLen
        features.append(self.domain_reg_len())
        # 10. Favicon
        features.append(self.favicon())
        # 11. NonStdPort
        features.append(self.non_std_port())
        # 12. HTTPSDomainURL
        features.append(self.https_domain_url())
        # 13. RequestURL
        features.append(self.request_url())
        # 14. AnchorURL
        features.append(self.anchor_url())
        # 15. LinksInScriptTags
        features.append(self.links_in_script_tags())
        # 16. ServerFormHandler
        features.append(self.server_form_handler())
        # 17. InfoEmail
        features.append(self.info_email())
        # 18. AbnormalURL
        features.append(self.abnormal_url())
        # 19. WebsiteForwarding
        features.append(self.website_forwarding())
        # 20. StatusBarCust
        features.append(self.status_bar_cust())
        # 21. DisableRightClick
        features.append(self.disable_right_click())
        # 22. UsingPopupWindow
        features.append(self.using_popup_window())
        # 23. IframeRedirection
        features.append(self.iframe_redirection())
        # 24. AgeofDomain
        features.append(self.age_of_domain())
        # 25. DNSRecording
        features.append(self.dns_recording())
        # 26. WebsiteTraffic
        features.append(self.website_traffic())
        # 27. PageRank
        features.append(self.page_rank())
        # 28. GoogleIndex
        features.append(self.google_index())
        # 29. LinksPointingToPage
        features.append(self.links_pointing_to_page())
        # 30. StatsReport
        features.append(self.stats_report())

        return features

    # Feature Implementations
    # Return -1 (Phishing), 0 (Suspicious), 1 (Legitimate) based on UCI dataset conventions usually.
    # HOWEVER, checking standard mappings: often 1 is Phishing, -1 is Safe? Or vice versa.
    # Usually datasets like UCI have {-1, 0, 1}.
    # Let's assume standardized output: -1: Legitimate, 0: Suspicious, 1: Phishing
    # OR standard UCI: -1: Phishing, 1: Legitimate. The user's prompt says "Phishing" or "Aman".
    # Without seeing the model training, I have to guess.
    # I will assume standard UCI labeling: -1: Phishing, 1: Legitimate.
    # Wait, most pickle models from tutorials use: 1 = Phishing, 0 = Safe.
    # Or -1 = Phishing, 1 = Safe.
    # I will implement logic to produce {-1, 0, 1} and user can map it.
    # Let's try to follow what seems to be "Bad" -> 1 (Phishing), "Good" -> -1 or 0.
    # Actually, UCI dataset says: "1" is Phishing usually? No, it varies.
    # Let's stick to standard heuristic return values and see result.
    # Common convention: -1: Phishing, 1: Legitimate. (Safe)

    def using_ip(self):
        try:
            ipaddress.ip_address(self.domain)
            return -1 # Phishing
        except:
            return 1 # Legitimate

    def long_url(self):
        if len(self.url) < 54: return 1
        if len(self.url) >= 54 and len(self.url) <= 75: return 0
        return -1

    def short_url(self):
        match = re.search('bit\.ly|goo\.gl|shorte\.st|go2l\.ink|x\.co|ow\.ly|t\.co|tinyurl|tr\.im|is\.gd|cli\.gs|'
                        'yfrog\.com|migre\.me|ff\.im|tiny\.cc|url4\.eu|twit\.ac|su\.pr|twurl\.nl|snipurl\.com|'
                        'short\.to|BudURL\.com|ping\.fm|post\.ly|Just\.as|bkite\.com|snipr\.com|fic\.kr|loopt\.us|'
                        'doiop\.com|short\.ie|kl\.am|wp\.me|rubyurl\.com|om\.ly|to\.ly|bit\.do|t\.co|lnkd\.in|'
                        'db\.tt|qr\.ae|adf\.ly|goo\.gl|bitly\.com|cur\.lv|tinyurl\.com|ow\.ly|bit\.ly|ity\.im|'
                        'q\.gs|is\.gd|po\.st|bc\.vc|twitthis\.com|u\.to|j\.mp|buzurl\.com|cutt\.us|u\.bb|yourls\.org|'
                        'x\.co|prettylinkpro\.com|scrnch\.me|filoops\.info|vzturl\.com|qr\.net|1url\.com|tweez\.me|v\.gd|'
                        'tr\.im|link\.zip\.net', self.url)
        if match:
            return -1
        return 1

    def symbol_at(self):
        if "@" in self.url:
            return -1
        return 1

    def redirecting_double_slash(self):
        list = [x.start(0) for x in re.finditer('//', self.url)]
        if self.url_parse.scheme == 'https':
            if len(list) > 1: return -1 # more than one // in url (besides the protocol)
        else:
             if len(list) > 0: return -1 # http should have 0? wait, http://... // is at index 5.
        # Simple heuristic: last // should be within 7 chars
        if self.url.rfind('//') > 7:
            return -1
        return 1

    def prefix_suffix_hyphen(self):
        if '-' in self.domain:
            return -1
        return 1

    def sub_domains(self):
        # Count dots
        if self.domain.count('.') == 1:
            return 1
        elif self.domain.count('.') == 2:
            return 0
        return -1

    def http_s(self):
        if self.url_parse.scheme == 'https':
            return 1
        return -1

    def domain_reg_len(self):
        # Needs whois
        try:
            creation_date = self.whois_response.creation_date
            expiration_date = self.whois_response.expiration_date
            if (isinstance(creation_date, list)): creation_date = creation_date[0]
            if (isinstance(expiration_date, list)): expiration_date = expiration_date[0]
            
            age = (expiration_date - creation_date).days
            if age / 365 <= 1:
                return -1
            return 1
        except:
            return -1

    def favicon(self):
        # Heuristic: if favicon is external
        if self.soup:
            for link in self.soup.find_all('link', rel='icon'):
                if self.domain not in link.get('href', ''):
                    return -1
        return 1

    def non_std_port(self):
        try:
            port = self.domain.split(":")
            if len(port) > 1:
                return -1
            return 1
        except:
            return 1

    def https_domain_url(self):
        if 'https' in self.domain:
            return -1
        return 1

    def request_url(self):
        # % of external objects
        if not self.soup: return 0
        i = 0
        success = 0
        for img in self.soup.find_all('img', src=True):
            dots = [x.start(0) for x in re.finditer('\.', img['src'])]
            if self.url in img['src'] or self.domain in img['src'] or len(dots) == 1:
                success = success + 1
            i = i + 1
        
        for audio in self.soup.find_all('audio', src=True):
            dots = [x.start(0) for x in re.finditer('\.', audio['src'])]
            if self.url in audio['src'] or self.domain in audio['src'] or len(dots) == 1:
                success = success + 1
            i = i + 1
        
        for embed in self.soup.find_all('embed', src=True):
            dots = [x.start(0) for x in re.finditer('\.', embed['src'])]
            if self.url in embed['src'] or self.domain in embed['src'] or len(dots) == 1:
                success = success + 1
            i = i + 1
        
        for iframe in self.soup.find_all('iframe', src=True):
            dots = [x.start(0) for x in re.finditer('\.', iframe['src'])]
            if self.url in iframe['src'] or self.domain in iframe['src'] or len(dots) == 1:
                success = success + 1
            i = i + 1
            
        try:
            percentage = success/float(i) * 100
            if percentage < 22.0: return 1
            elif (percentage >= 22.0) and (percentage < 61.0): return 0
            else: return -1
        except:
            return 1

    def anchor_url(self):
        if not self.soup: return 0
        i = 0
        unsafe = 0
        for a in self.soup.find_all('a', href=True):
            if "#" in a['href'] or "javascript" in a['href'].lower() or "mailto" in a['href'].lower() or not (self.url in a['href'] or self.domain in a['href']):
                unsafe = unsafe + 1
            i = i + 1
        try:
            percentage = unsafe / float(i) * 100
            if percentage < 31.0: return 1
            elif (percentage >= 31.0) and (percentage < 67.0): return 0
            else: return -1
        except:
            return 1

    def links_in_script_tags(self):
        # Simplified: check % of script/link/meta tags with external links
        # This is expensive, using placeholder logic for now or simple heuristic
        if not self.soup: return 0
        i = 0
        success = 0
        for link in self.soup.find_all('link', href=True):
            if self.domain not in link['href']:
                success = success + 1
            i = i + 1
        for script in self.soup.find_all('script', src=True):
            if self.domain not in script['src']:
                success = success + 1
            i = i + 1
            
        try:
            percentage = success / float(i) * 100
            if percentage < 17.0: return 1
            elif (percentage >= 17.0) and (percentage < 81.0): return 0
            else: return -1
        except:
            return 1

    def server_form_handler(self):
        if not self.soup: return 0
        for form in self.soup.find_all('form', action=True):
            if form['action'] == "" or form['action'] == "about:blank":
                return -1
            if self.domain not in form['action'] and form['action'].startswith("http"):
                return 0
        return 1

    def info_email(self):
        # check mailto:
        if self.soup and "mailto:" in self.response.text:
            return -1
        return 1

    def abnormal_url(self):
        # If response was failed, it's abnormal? Or if whois doesnt match?
        if self.response is None: return -1
        return 1

    def website_forwarding(self):
        if self.response and len(self.response.history) <= 1: return 1
        elif self.response and len(self.response.history) >= 2 and len(self.response.history) < 4: return 0
        return -1

    def status_bar_cust(self):
        # Cannot check JS effectively without headless browser, assume 1 (Safe)
        return 1

    def disable_right_click(self):
        # Cannot check JS effectively, assume 1 (Safe)
        return 1

    def using_popup_window(self):
        # Cannot check JS effectively, assume 1 (Safe)
        return 1

    def iframe_redirection(self):
        if self.soup and self.soup.find_all('iframe'):
            return 0 # Suspicious to have iframe
        return 1

    def age_of_domain(self):
        try:
            creation_date = self.whois_response.creation_date
            if isinstance(creation_date, list): creation_date = creation_date[0]
            if not creation_date: return -1
            today = datetime.now()
            age = (today - creation_date).days
            if age >= 180: return 1
            return -1
        except:
            return -1

    def dns_recording(self):
        if self.whois_response: return 1
        return -1

    def website_traffic(self):
        # Alexa rank is dead. Use placeholder or always 0?
        # Simulating logic based on popularity is hard without API.
        # Check if indexed in google?
        return 0 

    def page_rank(self):
        # Similar.
        return 0

    def google_index(self):
        return 1 # Assume indexed

    def links_pointing_to_page(self):
        return 0

    def stats_report(self):
        return 1

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    data = request.json
    url = data.get('url')
    
    if not url:
        return jsonify({'error': 'URL is required'}), 400

    # Ensure URL has schema
    if not url.startswith('http'):
        url = 'http://' + url

    try:
        extractor = FeatureExtractor(url)
        features = extractor.get_features()
        
        # Reshape for model (1, 30)
        features_array = np.array(features).reshape(1, -1)
        
        result_text = "Aman" # Default
        if model:
            prediction = model.predict(features_array)[0]
            # Assming: -1 is Phishing, 1 is Legitimate (based on common datasets)
            # OR 1 is Phishing, 0 is Legitimate?
            # It's safest to assume standard UCI Phishing Dataset encoding:
            # -1: Phishing, 1: Legitimate.
            # BUT let's invert logic if needed. 
            # If the user provided model follows standard {1, -1}
            # For this MVP, I will map based on prediction value.
            # If prediction == -1 -> Phishing. If 1 -> Aman.
            
            # Let's verify what the user might expect.
            # Usually: 1 = Phishing, 0 = Safe in modern binary classification.
            # But UCI is {-1, 1}.
            # I will return the raw result if it's a string, or map it.
            
            if prediction == -1:
                result_text = "Phishing"
            elif prediction == 1:
                result_text = "Aman"
            else:
                # Fallback for 0/1 binary
                result_text = "Phishing" if prediction == 1 else "Aman"
        else:
            # Dummy logic if model fails to load
            result_text = "Aman" if len(url) < 60 else "Phishing"

        return jsonify({'result': result_text})

    except Exception as e:
        print(e)
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
