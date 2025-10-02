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
│   └── login.html
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
