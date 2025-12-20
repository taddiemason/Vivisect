# Synetica Logo Files

This directory should contain the Synetica branding logos for the Vivisect GUI.

## Required Files

Place the following logo file in this directory:

- **synetica-logo.png** - The main Synetica logo (full logo with text)
  - Recommended size: Width: 400-600px, transparent background (PNG)
  - Used in: Header (40px height) and Footer (24px height)

## Logo Specifications

### Header Logo
- Height: 40px (auto-width)
- Position: Top left, next to "Vivisect Forensics" title
- Format: PNG with transparency preferred

### Footer Logo
- Height: 24px (auto-width)
- Position: Center of footer
- Format: PNG with transparency preferred

## Adding Your Logo

1. Save your Synetica logo as `synetica-logo.png`
2. Place it in this directory: `src/web/static/images/`
3. Restart the web server
4. The logo will automatically appear in the header and footer

## Notes

- The logo has a fallback - if the file is missing, it will simply not display
- SVG format is also supported if you prefer vector graphics
- Make sure the logo has good contrast against both light backgrounds
