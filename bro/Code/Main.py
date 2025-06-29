import jellyfish

# print(jellyfish.jaro_similarity("casa", "caso"))         # Ex: 0.916
# print(jellyfish.levenshtein_distance("casa", "caso"))    # 1

str1 = "Translation"
str2 = "ranslation"

print(jellyfish.jaro_similarity(str1, str2))         # Ex: 0.916
print(jellyfish.levenshtein_distance(str1, str2))    # 1