import shutil

shutil.copy2('frontend/index.html', 'public/index.html')
shutil.copy2('frontend/js/settings.js', 'public/js/settings.js')
shutil.copy2('frontend/js/settings.js', 'public/static/js/settings.js')

print("Synced frontend/index.html and settings.js to public/ and public/static/")
