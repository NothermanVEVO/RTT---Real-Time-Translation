# import jellyfish

# # print(jellyfish.jaro_similarity("casa", "caso"))         # Ex: 0.916
# # print(jellyfish.levenshtein_distance("casa", "caso"))    # 1

# str1 = "Translation"
# str2 = "ranslation"

# print(jellyfish.jaro_similarity(str1, str2))         # Ex: 0.916
# print(jellyfish.levenshtein_distance(str1, str2))    # 1
import TextProcess
import time

TextProcess.create("Inglês")

str1 = ""
str2 = ""

start = time.time()

str1 = "scaredofghosts?"
print("Antes da correção: ", str1)
print("Depois da correção: ", TextProcess.correct_phrase(str1))
print("------------------------------------------------")
str1 = "h1, where can 1 g0"
print("Antes da correção: ", str1)
print("Depois da correção: ", TextProcess.correct_phrase(str1))
print("------------------------------------------------")
str1 = "h1, wh3re can i 6o"
print("Antes da correção: ", str1)
print("Depois da correção: ", TextProcess.correct_phrase(str1))

print("Tempo de correção: ", time.time() - start)