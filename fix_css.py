import re

with open('app/static/css/app.css', 'r') as f:
    css = f.read()

# Fix 1: Topbar RTL/LTR
css = css.replace(
'''html[dir="rtl"] .topbar {
  direction: rtl !important;
  flex-direction: row !important;
}''',
'''html[dir="rtl"] .topbar {
  direction: rtl !important;
  flex-direction: row-reverse !important;
}'''
)

css = css.replace(
'''html[dir="ltr"] .topbar {
  direction: ltr !important;
  flex-direction: row !important;
}''',
'''html[dir="ltr"] .topbar {
  direction: ltr !important;
  flex-direction: row-reverse !important;
}'''
)

# Fix 2: #notifDropdown base rules (line ~3320)
# Make it responsive with max-width and proper inset
css = css.replace(
'''  width: 290px !important;
  max-height: 380px !important;''',
'''  width: 290px !important;
  max-width: calc(100vw - 32px) !important; /* Prevent cutoff on small screens/zoom */
  max-height: 380px !important;'''
)

css = css.replace(
'''  padding: 0 !important;
  inset-inline-end: 0 !important;
  border-radius: 16px !important;''',
'''  padding: 0 !important;
  inset-inline-end: 0 !important;
  inset-inline-start: auto !important; /* Ensure it sticks to the end */
  border-radius: 16px !important;'''
)

# Fix 3: Media query 1 (line ~2378)
css = css.replace(
'''  #notifDropdown {
    position: absolute !important;
    top: 100% !important;
    left: 12px !important;
    right: 12px !important;
    width: auto !important;
    max-width: none !important;
    inset-inline-end: auto !important;
    inset-inline-start: auto !important;''',
'''  #notifDropdown {
    position: absolute !important;
    top: 100% !important;
    left: auto !important;
    right: auto !important;
    width: 290px !important;
    max-width: calc(100vw - 32px) !important;
    inset-inline-end: -40px !important; /* Adjust for mobile/zoomed screens */
    inset-inline-start: auto !important;'''
)

# Fix 4: Media query 2 (line ~3607)
css = css.replace(
'''  #notifDropdown {
    position: absolute !important;
    top: 100% !important;
    left: 12px !important;
    right: 12px !important;
    inset-inline-start: 12px !important;
    inset-inline-end: 12px !important;
    width: auto !important;
    max-width: none !important;''',
'''  #notifDropdown {
    position: absolute !important;
    top: 100% !important;
    left: auto !important;
    right: auto !important;
    inset-inline-end: -40px !important; /* Adjust for mobile */
    inset-inline-start: auto !important;
    width: 290px !important;
    max-width: calc(100vw - 32px) !important;'''
)

with open('app/static/css/app.css', 'w') as f:
    f.write(css)
