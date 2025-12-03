## Structure
```
.
├── index.html
├── pages/
│   ├── events/
│   │   ├── event-001.html
│   │   └── ......
│   │
│   ├── register.html
│   ├── login.html
│   ├── event-xxx.html
|   └── ......
|
├── css/
│   └── styles.css
├── js/
│   └── app.js
├── assets/
│   ├── img/
│   └── app.js
│
└── buddylink.py
    

```


### Pages
- `pages/register.html` — Registration page
- `pages/login.html` — Login page


### Local Deployment
Append the following code into C:\xampp\apache\conf\extra\httpd-vhosts.conf
```
# Assume the project is stored in  "F:/volunteer-senior"

<VirtualHost *:80>
    ServerName localhost


    ProxyRequests Off
    ProxyPreserveHost On
    ProxyPass        /api  http://127.0.0.1:5000/
    ProxyPassReverse /api  http://127.0.0.1:5000/


    Alias /vs "F:/volunteer-senior"
    <Directory "F:/volunteer-senior">
        Options Indexes FollowSymLinks
        AllowOverride All
        Require all granted
    </Directory>
</VirtualHost>
```

Append the following code into C:\xampp\apache\conf\httpd.conf

```
LoadModule proxy_module modules/mod_proxy.so
LoadModule proxy_http_module modules/mod_proxy_http.so

Include conf/extra/httpd-vhosts.conf
```
### Flask Service
Excute the following command to launch the backend service:
```
python buddylink.py
```

### Deployment
Because this project uses the transformers module, the first time you run the program it will automatically download the model <strong>facebook/bart-large-mnli</strong> from <strong>Hugging Face</strong>. Please be patient during this process.
The download and installation time depends on your network speed and computer performance, and may take 10 to 40 minutes. Thank you for your patience.

