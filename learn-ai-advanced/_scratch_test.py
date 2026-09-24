import math, re, zlib

_STOPWORDS = {'the','a','an','in','on','at','of','to','for','and','or','is','was','were','are','be','it','its','this','that','with','as','by','from','up','also','today'}

def embed(text, dim):
    words = re.findall(r'[a-z0-9]+', text.lower())
    words = [w for w in words if w not in _STOPWORDS]
    vec = [0.0]*dim
    for w in words:
        b = zlib.crc32(w.encode()) % dim
        vec[b] += 1.0 + len(w)/10
    norm = math.sqrt(sum(v*v for v in vec)) or 1.0
    return [v/norm for v in vec]

def cos(a,b):
    return sum(x*y for x,y in zip(a,b))

DOC = """Acme Corp released its Q2 earnings report today. In Q2, revenue grew 15%
year over year, driven by strong demand in the cloud division. Operating
margin improved to 22%, up from 18% in the prior quarter. The company
also announced a new product line launching in Q3, targeting small and
medium businesses. Management raised full-year guidance, citing continued
momentum in enterprise contracts. The CFO noted that headcount grew 8%
in Q2, primarily in engineering and sales roles. Customer churn remained
flat at 4%, in line with historical averages."""
DOC = re.sub(r'\s+', ' ', DOC.strip())

def chunk(text, size=220, overlap=40):
    chunks=[]
    start=0
    while start < len(text):
        end = start+size
        chunks.append(text[start:end].strip())
        if end >= len(text): break
        start = end-overlap
    return chunks

chunks = chunk(DOC)
queries = [
    'What was Q2 revenue growth?',
    "What is the CEO's favorite programming language?",
    'What color is the sky on Mars?',
]
for dim in [64,128,256]:
    print('DIM', dim)
    cvecs = [embed(c, dim) for c in chunks]
    for q in queries:
        qv = embed(q, dim)
        scores = sorted([(cos(qv,cv), c[:40]) for cv,c in zip(cvecs,chunks)], reverse=True)
        print(' Q:', q)
        for s,c in scores:
            print('   %.2f %s' % (s,c))
