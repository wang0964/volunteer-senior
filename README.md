# Volunteer & Senior Registration (Frontend Split)

This folder is organized for a simple static site workflow in VS Code.

```
.
├── index.html        # Main page (links to /css and /js)
├── css/
│   └── styles.css    # All styles
├── js/
│   └── app.js        # All client-side scripts
└── assets/
    └── img/          # Place images here (update paths accordingly)
```

## Local preview
Use the VS Code Live Server extension or run a simple server:
```bash
# Python 3
python -m http.server 5500
# then open http://localhost:5500
```

## Structure
```
.
├── index.html
├── pages/
│   ├── register.html
│   ├── login.html
│   └── event-xxx.html
|
├── css/
│   └── styles.css
├── js/
│   └── app.js
└── assets/
    └── img/
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