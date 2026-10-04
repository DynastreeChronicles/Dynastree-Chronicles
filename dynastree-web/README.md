# Dynastree Chronicles — Web trial

Responsive home + Issue 4 sample page + full PDF.

## Goal
League chat gets a **Bitly short link** → this site → readable mobile issue **and** full PDF.

## Publish on GitHub Pages (once)

1. Create a GitHub account if needed: https://github.com/join  
2. New repository: e.g. `dynastree-chronicles` (Public)  
3. Upload **everything in this folder** to the repo root  
   (index.html, css/, issues/, pdf/, README.md)  
4. Repo **Settings → Pages**  
   - Source: Deploy from a branch  
   - Branch: `main` (or `master`), folder: `/ (root)`  
5. Wait a minute. Site URL:  
   `https://<your-username>.github.io/dynastree-chronicles/`

### Upload tips
- **GitHub website:** Add file → Upload files → drag this folder’s contents → Commit  
- **GitHub Desktop:** Clone repo → copy files in → Commit → Push  

## Bitly (each week or once for “latest”)
1. https://bitly.com — free account  
2. Shorten your Pages URL (home or specific issue)  
3. Paste short link in Sleeper chat  

Optional: always Bitly the **home** URL (`index.html`) and keep “Latest issue” pointed at the newest issue page.

## Weekly later
1. Generate new issue HTML (and PDF)  
2. Add `issues/issue-05/` + PDF under `pdf/`  
3. Point home “Latest issue” at issue-05  
4. Push to GitHub  
5. Same Bitly link still works if it points at home  

## Local preview
Open `index.html` in a browser, or from this folder:
```bash
python3 -m http.server 8080
```
Then visit http://localhost:8080
