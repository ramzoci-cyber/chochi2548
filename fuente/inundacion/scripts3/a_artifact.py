# Convierte el HTML completo en el cuerpo que se publica como Artifact (sin doctype, html, head, meta ni body)
import sys, re
s = open(sys.argv[1], encoding='utf-8').read()
i = s.index('<title>'); s = s[i:]
s = s.replace('</head>\n<body>\n', '', 1)
s = re.sub(r'</body>\s*</html>\s*$', '', s)
open(sys.argv[2], 'w', encoding='utf-8').write(s)
print(sys.argv[2], round(len(s.encode()) / 1e6, 2), 'MB')
