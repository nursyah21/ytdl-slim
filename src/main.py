import yt_dlp

res = yt_dlp.YoutubeDL().extract_info("https://www.youtube.com/watch?v=DNvfNrLCzLo")

print(res) 
print('success')