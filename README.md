# Studio Tharaavu

A responsive fictional interior-design studio website, created as a demonstration for conversations with design practices.

Original implementation with a For Living-inspired structure, Prata and Manrope typography, real licensed Pexels photography, responsive layouts, accessible navigation and a WhatsApp contact action.

## Edit and preview

Edit `content.json` to change studio details, page copy, project descriptions, photos and the WhatsApp destination. Then:

```sh
python3 render.py
python3 render.py --check
python3 -m http.server 8791
```

Open `http://localhost:8791/`. Python's standard library is sufficient; no package install is needed.

Generated HTML is committed for static hosting. Source templates live in `templates/`. Styling and browser interactions live in `styles.css` and `site.js`.

## Credits and scope

This is a fictional studio, not a claim to have designed or completed the photographed properties. Photos illustrate concept studies. Three detail images are crops of their main photo; the residence includes a verified second view.

See [credits.md](credits.md) for photo credits. Font licenses accompany their files in `assets/fonts/`.

The WhatsApp link opens a prefilled draft. The visitor decides whether to send it. The site includes no enquiry form, analytics or custom backend.

Source layout reference: [For Living](https://www.for-living.it/). No For Living source code, brand copy, logos or photographs are included.
