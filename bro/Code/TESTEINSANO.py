import WindowScreenshot

WindowScreenshot.getFullScreenshot().show()
# names = WindowScreenshot.getWindowsNames()
# name: str
# results = []

# for name in reversed(names):
#     if not len(name) == 0 and not name.isspace():
#         result = WindowScreenshot.getWindowScreenshot(name)
#         if result and result[0]:
#             results.append(result)

# if len(results) != 0:
#     image = results[0][0]
#     for result in results[1:]:
#         overlay = result[0].convert("RGBA")
#         print("position: ", (result[1], result[2]))
#         image.paste(overlay, (result[1], result[2]), overlay)

#     image.show()